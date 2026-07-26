"""Expand retrieved child chunks back into their parent structural units.

Small-to-big retrieval: structure_aware chunking deliberately emits tiny child
chunks (one slide bullet or title, averaging ~50 characters on this corpus) so
that embedding and lexical matching operate on precise units. Those same chunks
are far too small to answer from -- a retrieved slide title carries no content
-- so each child records its containing slide/section as ``parent_text``, and
generation is meant to read the parent rather than the child.

This module performs that final swap, after retrieval, reranking and
diversification have finished selecting. Selection stays precise; only what
reaches the LLM gets widened.
"""

from __future__ import annotations

from dataclasses import replace

from src.schemas import ScoredChunk


def expand_to_parents(candidates: list[ScoredChunk]) -> list[ScoredChunk]:
    """Replace each chunk's text with its parent's, dropping duplicate parents.

    Several selected children commonly come from the same slide or section;
    substituting parents blindly would repeat that parent's full text once per
    child and crowd the prompt. The first (highest-ranked) child of each parent
    wins and the rest are dropped, so ranking order is preserved and the
    context list shrinks rather than duplicating.

    Chunks with no ``parent_text`` (semantic chunking doesn't produce one) pass
    through unchanged, which is what makes this safe to run unconditionally.

    Args:
        candidates: Final selected ScoredChunks, in rank order.

    Returns:
        ScoredChunks with parent text substituted where available, re-ranked
        contiguously from 1.
    """
    expanded: list[ScoredChunk] = []
    seen_parents: set[str] = set()

    for scored_chunk in candidates:
        parent_text = scored_chunk.chunk.metadata.get("parent_text")
        if not parent_text:
            expanded.append(scored_chunk)
            continue

        parent_id = scored_chunk.chunk.metadata.get("parent_id") or parent_text
        if parent_id in seen_parents:
            continue
        seen_parents.add(parent_id)

        expanded.append(
            replace(scored_chunk, chunk=replace(scored_chunk.chunk, text=parent_text))
        )

    return [replace(sc, rank=rank) for rank, sc in enumerate(expanded, start=1)]
