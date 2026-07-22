"""Rerank retrieved chunks using an LLM as the relevance judge."""

from __future__ import annotations

from src.config import RerankingConfig
from src.schemas import ScoredChunk


class LLMReranker:
    """Reranks ScoredChunks by prompting an LLM to judge relevance."""

    def __init__(self, config: RerankingConfig) -> None:
        """Initialize the reranker with a generation backend.

        Args:
            config: Reranking parameters (top_n).
        """
        raise NotImplementedError

    def rerank(self, query: str, candidates: list[ScoredChunk]) -> list[ScoredChunk]:
        """Rerank candidate chunks for a query using LLM relevance judgments.

        Args:
            query: Natural language query text.
            candidates: ScoredChunks to rerank.

        Returns:
            ScoredChunks re-ordered by LLM-judged relevance.
        """
        raise NotImplementedError
