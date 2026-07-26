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
from src.token_tracking import count_tokens


def _window_around_child(parent_text: str, child_text: str, max_tokens: int) -> str:
    """Return at most `max_tokens` of `parent_text` centred on `child_text`.

    Parents are not uniformly sized: a slide fits comfortably under any sane
    budget, while a PDF page can run to ~900 tokens. Truncating from the start
    of an oversized parent would often cut the matched passage off entirely, so
    the window grows outward from the child instead, keeping the surrounding
    sentences that give it context. Falls back to a head slice when the child's
    text can't be located verbatim in the parent.
    """
    start = parent_text.find(child_text)
    if start == -1:
        words = parent_text.split()
        head = " ".join(words)
        while words and count_tokens(head) > max_tokens:
            words = words[: int(len(words) * 0.8) or len(words) - 1]
            head = " ".join(words)
        return head

    end = start + len(child_text)
    # Grow symmetrically in characters, then trim to the token budget. ~4 chars
    # per token is a rough but adequate guide for choosing the span to test.
    budget_chars = max_tokens * 4
    pad = max(0, (budget_chars - len(child_text)) // 2)
    window_start = max(0, start - pad)
    window_end = min(len(parent_text), end + pad)

    window = parent_text[window_start:window_end]
    while count_tokens(window) > max_tokens and len(window) > len(child_text):
        trim = max(1, (len(window) - len(child_text)) // 4)
        window = window[trim:] if window_start > 0 else window[:-trim]

    return window.strip()


def expand_to_parents(candidates: list[ScoredChunk], max_parent_tokens: int = 250) -> list[ScoredChunk]:
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
        max_parent_tokens: Cap on what one parent may contribute. Parents
            within the cap are substituted whole; larger ones are windowed
            around the matched child (see ContextExpansionConfig for why the
            cap exists and what it measured).

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

        text = parent_text
        if count_tokens(parent_text) > max_parent_tokens:
            text = _window_around_child(parent_text, scored_chunk.chunk.text, max_parent_tokens)

        expanded.append(replace(scored_chunk, chunk=replace(scored_chunk.chunk, text=text)))

    return [replace(sc, rank=rank) for rank, sc in enumerate(expanded, start=1)]
