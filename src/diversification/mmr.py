"""Diversify a ranked chunk list using Maximal Marginal Relevance."""

from __future__ import annotations

from src.config import DiversificationConfig
from src.embedding_cache import encode_cached
from src.schemas import ScoredChunk


def _normalize_scores(candidates: list[ScoredChunk]) -> list[float]:
    scores = [sc.score for sc in candidates]
    lo, hi = min(scores), max(scores)
    if hi == lo:
        return [1.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def mmr_select(
    candidates: list[ScoredChunk],
    config: DiversificationConfig,
) -> list[ScoredChunk]:
    """Select a diverse subset of candidates via MMR.

    At each step picks the candidate maximizing
    ``lambda * relevance - (1 - lambda) * max_similarity_to_already_selected``,
    where relevance is the candidate's min-max normalized input score and
    similarity is cosine similarity between embeddings of
    ``config.embedding_model_name``.

    Args:
        candidates: ScoredChunks to select from, assumed pre-ranked by relevance.
        config: Diversification parameters (lambda, top_k, embedding model).

    Returns:
        A reduced, diversified list of ScoredChunks (length <= config.top_k).
    """
    if not candidates:
        return []

    import numpy as np

    # Cached: MMR runs per query over chunks from a fixed corpus, so the same
    # texts would otherwise be re-embedded once per question for a whole run.
    embeddings = encode_cached(
        config.embedding_model_name, [sc.chunk.text for sc in candidates]
    )
    relevance = _normalize_scores(candidates)

    selected_indices: list[int] = []
    remaining_indices = list(range(len(candidates)))

    while remaining_indices and len(selected_indices) < config.top_k:
        best_index = None
        best_value = float("-inf")

        for i in remaining_indices:
            if selected_indices:
                similarity_to_selected = max(
                    float(np.dot(embeddings[i], embeddings[j])) for j in selected_indices
                )
            else:
                similarity_to_selected = 0.0

            value = config.lambda_param * relevance[i] - (1 - config.lambda_param) * similarity_to_selected
            if value > best_value:
                best_value = value
                best_index = i

        selected_indices.append(best_index)
        remaining_indices.remove(best_index)

    return [
        ScoredChunk(
            chunk=candidates[i].chunk,
            score=candidates[i].score,
            source=candidates[i].source,
            rank=rank,
        )
        for rank, i in enumerate(selected_indices, start=1)
    ]
