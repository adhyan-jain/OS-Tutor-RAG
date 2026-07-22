"""Rerank retrieved chunks using a cross-encoder relevance model."""

from __future__ import annotations

from src.config import RerankingConfig
from src.schemas import ScoredChunk


class CrossEncoderReranker:
    """Reranks ScoredChunks by scoring (query, chunk) pairs with a cross-encoder."""

    def __init__(self, config: RerankingConfig) -> None:
        """Initialize the reranker with a cross-encoder model.

        Args:
            config: Reranking parameters (model name, top_n).
        """
        raise NotImplementedError

    def rerank(self, query: str, candidates: list[ScoredChunk]) -> list[ScoredChunk]:
        """Rerank candidate chunks for a query.

        Args:
            query: Natural language query text.
            candidates: ScoredChunks to rerank.

        Returns:
            ScoredChunks re-ordered by cross-encoder relevance score.
        """
        raise NotImplementedError
