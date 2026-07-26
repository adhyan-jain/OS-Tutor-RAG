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
        from src.embedding_cache import get_cross_encoder

        self.config = config
        self.model = get_cross_encoder(config.cross_encoder_model_name)

    def rerank(
        self, query: str, candidates: list[ScoredChunk], top_n: int | None = None
    ) -> list[ScoredChunk]:
        """Rerank candidate chunks for a query.

        Args:
            query: Natural language query text.
            candidates: ScoredChunks to rerank.
            top_n: Optional override for how many to keep. The pipeline widens
                this when diversification runs next, so MMR has more candidates
                than it will select.

        Returns:
            The top ``top_n`` (default ``config.top_n``) ScoredChunks re-ordered
            by descending cross-encoder relevance score.
        """
        if not candidates:
            return []

        pairs = [(query, sc.chunk.text) for sc in candidates]
        scores = self.model.predict(pairs)

        reranked = sorted(
            zip(candidates, scores), key=lambda pair: pair[1], reverse=True
        )[: top_n or self.config.top_n]

        return [
            replace(sc, score=float(score), source="cross_encoder", rank=rank)
            for rank, (sc, score) in enumerate(reranked, start=1)
        ]
