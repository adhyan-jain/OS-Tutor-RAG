"""Diversify a ranked chunk list using Maximal Marginal Relevance."""

from __future__ import annotations

from src.config import DiversificationConfig
from src.schemas import ScoredChunk


def mmr_select(
    candidates: list[ScoredChunk],
    config: DiversificationConfig,
) -> list[ScoredChunk]:
    """Select a diverse subset of candidates via MMR.

    Args:
        candidates: ScoredChunks to select from, assumed pre-ranked by relevance.
        config: Diversification parameters (lambda, top_k).

    Returns:
        A reduced, diversified list of ScoredChunks.
    """
    raise NotImplementedError
