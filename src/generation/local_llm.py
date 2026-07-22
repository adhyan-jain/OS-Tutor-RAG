"""Local LLM generation backend.

Loads Llama-3.1-8B-Instruct via vLLM for answer generation given a query and
retrieved context chunks.
"""

from __future__ import annotations

from src.config import GenerationConfig
from src.schemas import ScoredChunk


class LocalLLM:
    """Wraps a locally-served vLLM instance of Llama-3.1-8B-Instruct."""

    def __init__(self, config: GenerationConfig) -> None:
        """Load the model via vLLM.

        Args:
            config: Generation parameters (model name, max_tokens, temperature,
                gpu_memory_utilization).
        """
        raise NotImplementedError

    def generate(self, query: str, context: list[ScoredChunk]) -> str:
        """Generate an answer to the query grounded in the given context chunks.

        Args:
            query: The user's natural language question.
            context: ScoredChunks to include as retrieved context.

        Returns:
            The generated answer text.
        """
        raise NotImplementedError
