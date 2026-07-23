"""Rerank retrieved chunks using a cross-encoder relevance model."""

from __future__ import annotations

from dataclasses import replace

from src.config import RerankingConfig
from src.schemas import ScoredChunk


class CrossEncoderReranker:
    """Reranks ScoredChunks by scoring (query, chunk) pairs with a cross-encoder."""

    def __init__(self, config: RerankingConfig) -> None:
        """Initialize the reranker with a cross-encoder model.

        Args:
            config: Reranking parameters (model name, top_n).
        """
        from sentence_transformers import CrossEncoder

        self.config = config
        self.model = CrossEncoder(config.cross_encoder_model_name)

    def rerank(self, query: str, candidates: list[ScoredChunk]) -> list[ScoredChunk]:
        """Rerank candidate chunks for a query.

        Args:
            query: Natural language query text.
            candidates: ScoredChunks to rerank.

        Returns:
            The top ``config.top_n`` ScoredChunks re-ordered by descending
            cross-encoder relevance score.
        """
        if not candidates:
            return []

        pairs = [(query, sc.chunk.text) for sc in candidates]
        scores = self.model.predict(pairs)

        reranked = sorted(
            zip(candidates, scores), key=lambda pair: pair[1], reverse=True
        )[: self.config.top_n]

        return [
            replace(sc, score=float(score), source="cross_encoder", rank=rank)
            for rank, (sc, score) in enumerate(reranked, start=1)
        ]
