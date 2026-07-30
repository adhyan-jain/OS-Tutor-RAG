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
from src.token_tracking import LLMCallTracker

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

# Two prompts, selected by GenerationConfig.prompt_style, so the difference can
# be measured rather than assumed.
#
# "strict" is the original: answer, or state that the context does not cover it.
# Its weakness is that it offers only those two options, so a question the
# context answers halfway tends to produce a refusal or -- worse, observed in
# practice -- a partial answer silently completed from the model's own
# knowledge, which is unfaithful without being flagged.
_RAG_PROMPT_STRICT = (
    "Answer the question using only the context below. If the context "
    "doesn't contain the answer, say so.\n\n"
    "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
)

# "part_coverage" asks for the same grounding but makes partial answers the
# expected outcome rather than an off-script one, which matters because most
# questions in this eval set ask two things at once.
_RAG_PROMPT_PART_COVERAGE = (
    "Answer the question using only the context below.\n\n"
    "If the question has several parts, answer each part the context supports, "
    "and say plainly which parts it does not cover. Do not fill gaps with "
    "knowledge that is absent from the context. If the context supports none of "
    "the question, say so.\n\n"
    "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
)

# "few_shot" keeps the strict instruction and adds two worked examples, to
# align the *shape* of the answer rather than its content. Measured motivation:
# answers were losing points to formatting rather than substance -- one scored
# 0.56 while being content-identical to its reference, penalised because it
# split a single reference statement across two bullets, and the correctness
# metric compares statement sets. The examples are drawn from the course
# material's own phrasing and deliberately answer in continuous prose.
_RAG_PROMPT_FEW_SHOT = (
    "Answer the question using only the context below. If the context "
    "doesn't contain the answer, say so.\n\n"
    "Answer in continuous prose, stating each fact once. Do not add preamble "
    "about the context.\n\n"
    "Example question: What does the OS do when it creates a process?\n"
    "Example answer: The OS allocates memory and creates the memory image, "
    "loads the code and data from the executable on disk, creates the runtime "
    "stack and heap, and opens basic files.\n\n"
    "Example question: What are user mode and kernel mode?\n"
    "Example answer: CPU hardware has multiple privilege levels: user mode "
    "runs user code, and kernel mode runs OS code such as system calls.\n\n"
    "Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
)

# "cot" keeps the few-shot answer shape and puts a short reasoning step in
# front of it. The reasoning is asked for in a separate, labelled section so it
# can be stripped before scoring: RAGAS compares the *answer* against the
# reference, and leaving reasoning in the answer text would inflate the
# statement count and depress both answer_correctness and faithfulness for
# reasons that have nothing to do with whether reasoning helped.
#
# The example is worked in the same two-part shape most of this eval set's
# questions take, since that is where reasoning has something to do: decide
# which parts the context covers, then answer in the aligned prose shape.
_RAG_PROMPT_COT = (
    "Answer the question using only the context below. If the context "
    "doesn't contain the answer, say so.\n\n"
    "First, under the heading 'Reasoning:', work out in one or two sentences "
    "which parts of the context bear on the question. Then, under the heading "
    "'Answer:', give the answer in continuous prose, stating each fact once, "
    "with no preamble about the context and no reference to the reasoning.\n\n"
    "Example question: What does the OS do when it creates a process, and what "
    "privilege level does that code run at?\n"
    "Reasoning: The context describes process creation as loading an "
    "executable and setting up its memory, and separately describes the CPU's "
    "privilege levels; both parts are covered.\n"
    "Answer: The OS allocates memory and creates the memory image, loads the "
    "code and data from the executable on disk, creates the runtime stack and "
    "heap, and opens basic files. This is OS code, so it runs in kernel mode, "
    "while user code runs in user mode.\n\n"
    "Context:\n{context}\n\nQuestion: {query}\n\nReasoning:"
)

_RAG_PROMPT_TEMPLATES = {
    "strict": _RAG_PROMPT_STRICT,
    "part_coverage": _RAG_PROMPT_PART_COVERAGE,
    "few_shot": _RAG_PROMPT_FEW_SHOT,
    "cot": _RAG_PROMPT_COT,
}

# Prompts whose output carries a reasoning section that must not reach the
# scorer; see _strip_reasoning.
_REASONING_PROMPT_STYLES = {"cot"}
# Tolerates the markdown the model wraps headings in ("**Answer:**", "### Answer:").
_ANSWER_HEADING_RE = re.compile(r"^[#*\s]*answer[*\s]*:[*\s]*", re.IGNORECASE | re.MULTILINE)


def _strip_reasoning(text: str) -> str:
    """Return the text after the final 'Answer:' heading, or all of it.

    A local 8B model does not always emit the heading (and can be cut off by
    max_tokens mid-reasoning). Falling back to the full text keeps such a row
    scoreable rather than blank -- it scores badly, which is the honest result
    for a prompt whose format the model failed to follow.
    """
    matches = list(_ANSWER_HEADING_RE.finditer(text))
    return text[matches[-1].end():].strip() if matches else text.strip()

_MULTI_QUERY_PROMPT_TEMPLATE = (
    "Generate {n} different ways to phrase the following question, so that "
    "searching with each version could surface different relevant documents. "
    "Respond with exactly {n} lines, one reformulation per line, no numbering "
    "or extra commentary.\n\nQuestion: {query}\n\nReformulations:"
)


class LocalLLM:
    """Wraps a local LLM, either served via vLLM or a running Ollama instance."""

    def __init__(self, config: GenerationConfig, tracker: LLMCallTracker | None = None) -> None:
        """Load the model (vllm backend) or record connection info (ollama backend).

        Args:
            config: Generation parameters (model name, backend, max_tokens,
                temperature, gpu_memory_utilization, ollama_base_url).
            tracker: Optional LLMCallTracker to log every call's token usage
                to, for later cost reporting. No tracking if omitted.
        """
        self.config = config
        self.tracker = tracker

        if config.backend == "vllm":
            from vllm import LLM

            self._llm = LLM(model=config.model_name, gpu_memory_utilization=config.gpu_memory_utilization)
        elif config.backend == "ollama":
            self._llm = None  # requests are made per-call in _complete()
        else:
            raise ValueError(f"Unsupported generation backend: {config.backend!r}")

    def _complete(self, prompt: str, purpose: str = "unspecified") -> str:
        if self.config.backend == "vllm":
            from vllm import SamplingParams

            sampling_params = SamplingParams(
                max_tokens=self.config.max_tokens, temperature=self.config.temperature
            )
            outputs = self._llm.generate([prompt], sampling_params)
            text = outputs[0].outputs[0].text.strip()
        else:
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
            text = response.json()["response"].strip()

        if self.tracker is not None:
            self.tracker.record(purpose, prompt, text)
        return text

    def generate(self, query: str, context: list[ScoredChunk]) -> str:
        """Generate an answer to the query grounded in the given context chunks.

        Args:
            query: The user's natural language question.
            context: ScoredChunks to include as retrieved context.

        Returns:
            The generated answer text.
        """
        context_text = "\n\n".join(sc.chunk.text for sc in context)
        template = _RAG_PROMPT_TEMPLATES[self.config.prompt_style]
        prompt = template.format(context=context_text, query=query)
        answer = self._complete(prompt, purpose="generate_answer")
        if self.config.prompt_style in _REASONING_PROMPT_STYLES:
            answer = _strip_reasoning(answer)
        return answer

    def generate_hypothetical_document(self, query: str) -> str:
        """Generate a hypothetical answer passage for a query (for HyDE retrieval).

        Args:
            query: The user's natural language question.

        Returns:
            A short, unretrieved passage that plausibly answers the query.
        """
        prompt = _HYDE_PROMPT_TEMPLATE.format(query=query)
        return self._complete(prompt, purpose="hyde_hypothetical")

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
        response = self._complete(prompt, purpose="multi_query_variants")
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
        response = self._complete(prompt, purpose="llm_rerank_score")
        match = _SCORE_RE.search(response)
        return float(match.group()) if match else 0.0
