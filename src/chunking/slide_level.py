"""Chunk a slide deck one chunk per slide, rather than one per bullet.

The parent-child split that `structure_aware` applies to decks exists to keep
matching precise while letting generation read something substantial. That
trade is worth making when the parent is large -- a PDF page runs to ~534
tokens around a 48-token child -- but a slide averages only 72 tokens, so the
whole slide is already an ordinary chunk size.

Splitting it anyway leaves ~13-token children to embed, which is very little
text for an embedding model to characterise, and 513 of them where 66 slides
exist. This strategy tests the alternative: index the slide itself. No parent
is recorded, because the chunk already is the unit generation would expand to.
"""

from __future__ import annotations

from src.config import ChunkingConfig
from src.schemas import Chunk, Document


def slide_level_chunk(document: Document, config: ChunkingConfig) -> list[Chunk]:
    """Split a slide deck into one Chunk per slide with content.

    Title-only divider slides carry their heading forward onto the next slide
    with content, matching structure_aware's handling, so a section heading is
    not lost and does not become a contentless chunk.

    Args:
        document: A Document with ``metadata["slides"]`` from extract_ppt.
        config: Chunking parameters (unused; slides are not further split).

    Returns:
        One Chunk per content-bearing slide, text being the heading followed by
        its bullets.
    """
    chunks: list[Chunk] = []
    cursor = 0
    pending_heading: str | None = None

    for slide in document.metadata.get("slides", []):
        slide_number = slide["slide_number"]
        title = (slide.get("title") or "").strip() or None
        bullets = [b.strip() for b in slide.get("bullets", []) if b and b.strip()]

        if not bullets:
            if title:
                pending_heading = f"{pending_heading} / {title}" if pending_heading else title
            continue

        heading = " / ".join(p for p in (pending_heading, title) if p) or None
        pending_heading = None

        text = "\n".join(([heading] if heading else []) + bullets)
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}__chunk{len(chunks)}",
                doc_id=document.doc_id,
                text=text,
                start_index=cursor,
                end_index=cursor + len(text),
                metadata={
                    "source_type": "pptx",
                    "strategy": "slide_level",
                    "slide_number": slide_number,
                    "slide_title": heading,
                    # Parent id matches structure_aware's so eval sets citing
                    # slides score both strategies against the same ground truth.
                    "parent_id": f"{document.doc_id}__slide{slide_number}",
                },
            )
        )
        cursor += len(text) + 1

    return chunks


# Public interface name matching src.schemas.ChunkerFn.
chunk = slide_level_chunk
