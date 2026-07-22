"""Hybrid retrieval combining dense and sparse results via Reciprocal Rank Fusion."""

from __future__ import annotations

from src.config import RetrievalConfig
from src.schemas import ScoredChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    config: RetrievalConfig,
) -> list[ScoredChunk]:
    """Fuse multiple ranked ScoredChunk lists using RRF.

    Args:
        ranked_lists: One ranked list of ScoredChunks per retriever.
        config: Retrieval parameters (rrf_k constant, top_k).

    Returns:
        A single fused ranking of ScoredChunks.
    """
    raise NotImplementedError
