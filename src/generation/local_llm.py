"""Local LLM generation backend.

Loads Llama-3.1-8B-Instruct via vLLM for answer generation given a query and
retrieved context chunks. Also supports an "ollama" backend for local
dev/testing against a running Ollama server (e.g. gemma2:9b, llama3),
since the full model may not fit in this machine's GPU memory.
"""

from __future__ import annotations

import re

from src.config import GenerationConfig
from src.schemas import ScoredChunk

_RELEVANCE_PROMPT_TEMPLATE = (
    "On a scale of 0 to 10, how relevant is the following passage to "
    "answering the question? Respond with only the integer score, nothing else.\n\n"
    "Question: {query}\n\nPassage: {passage}\n\nRelevance score (0-10):"
)
_SCORE_RE = re.compile(r"-?\d+(\.\d+)?")

_HYDE_PROMPT_TEMPLATE = (
    "Write a short, factual passage (2-4 sentences) that directly answers "
    "the following question, as if it were an excerpt from an operating "
    "systems textbook. Do not mention that this is hypothetical.\n\n"
    "Question: {query}\n\nPassage:"
)

_RAG_PROMPT_TEMPLATE = (
    "Answer the question using only the context below. If the context "
    "doesn't contain the answer, say so.\n\n"
    "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
)

_MULTI_QUERY_PROMPT_TEMPLATE = (
    "Generate {n} different ways to phrase the following question, so that "
    "searching with each version could surface different relevant documents. "
    "Respond with exactly {n} lines, one reformulation per line, no numbering "
    "or extra commentary.\n\nQuestion: {query}\n\nReformulations:"
)


class LocalLLM:
    """Wraps a local LLM, either served via vLLM or a running Ollama instance."""

    def __init__(self, config: GenerationConfig) -> None:
        """Load the model (vllm backend) or record connection info (ollama backend).

        Args:
            config: Generation parameters (model name, backend, max_tokens,
                temperature, gpu_memory_utilization, ollama_base_url).
        """
        self.config = config

        if config.backend == "vllm":
            from vllm import LLM

            self._llm = LLM(model=config.model_name, gpu_memory_utilization=config.gpu_memory_utilization)
        elif config.backend == "ollama":
            self._llm = None  # requests are made per-call in _complete()
        else:
            raise ValueError(f"Unsupported generation backend: {config.backend!r}")

    def _complete(self, prompt: str) -> str:
        if self.config.backend == "vllm":
            from vllm import SamplingParams

            sampling_params = SamplingParams(
                max_tokens=self.config.max_tokens, temperature=self.config.temperature
            )
            outputs = self._llm.generate([prompt], sampling_params)
            return outputs[0].outputs[0].text.strip()

        import requests

        response = requests.post(
            f"{self.config.ollama_base_url}/api/generate",
            json={
                "model": self.config.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    def generate(self, query: str, context: list[ScoredChunk]) -> str:
        """Generate an answer to the query grounded in the given context chunks.

        Args:
            query: The user's natural language question.
            context: ScoredChunks to include as retrieved context.

        Returns:
            The generated answer text.
        """
        context_text = "\n\n".join(sc.chunk.text for sc in context)
        prompt = _RAG_PROMPT_TEMPLATE.format(context=context_text, query=query)
        return self._complete(prompt)

    def generate_hypothetical_document(self, query: str) -> str:
        """Generate a hypothetical answer passage for a query (for HyDE retrieval).

        Args:
            query: The user's natural language question.

        Returns:
            A short, unretrieved passage that plausibly answers the query.
        """
        prompt = _HYDE_PROMPT_TEMPLATE.format(query=query)
        return self._complete(prompt)

    def generate_query_variants(self, query: str, n: int) -> list[str]:
        """Generate n reformulated versions of a query (for Multi Query retrieval).

        Args:
            query: The user's natural language question.
            n: Number of reformulations to request.

        Returns:
            A list of up to n reformulated query strings (fewer if the LLM's
            response doesn't contain that many non-empty lines).
        """
        prompt = _MULTI_QUERY_PROMPT_TEMPLATE.format(n=n, query=query)
        response = self._complete(prompt)
        lines = [line.strip("-*0123456789. \t") for line in response.splitlines()]
        return [line for line in lines if line][:n]

    def score_relevance(self, query: str, passage: str) -> float:
        """Prompt the LLM to score a passage's relevance to a query, 0-10.

        Args:
            query: Natural language query text.
            passage: Candidate passage text to judge.

        Returns:
            The parsed relevance score (0.0 if the response can't be parsed).
        """
        prompt = _RELEVANCE_PROMPT_TEMPLATE.format(query=query, passage=passage)
        response = self._complete(prompt)
        match = _SCORE_RE.search(response)
        return float(match.group()) if match else 0.0
