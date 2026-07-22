"""Chunk documents by respecting structural boundaries (slides, headings, paragraphs).

Uses a parent-child pattern: small "child" chunks are what get embedded and
retrieved, while each child carries its containing structural unit's full
text as a "parent" chunk in metadata, so the generation stage can expand a
matched child back out to its full slide/section for context.
"""

from __future__ import annotations

from src.config import ChunkingConfig
from src.schemas import Chunk, Document


def _make_chunk(
    document: Document,
    index: int,
    text: str,
    start_index: int,
    parent_id: str,
    parent_text: str,
    extra_metadata: dict[str, object],
) -> Chunk:
    return Chunk(
        chunk_id=f"{document.doc_id}__chunk{index}",
        doc_id=document.doc_id,
        text=text,
        start_index=start_index,
        end_index=start_index + len(text),
        metadata={
            "parent_id": parent_id,
            "parent_text": parent_text,
            **extra_metadata,
        },
    )


def _chunk_pptx(document: Document, config: ChunkingConfig) -> list[Chunk]:
    chunks: list[Chunk] = []
    cursor = 0

    for slide in document.metadata.get("slides", []):
        slide_number = slide["slide_number"]
        parent_id = f"{document.doc_id}__slide{slide_number}"
        parent_parts = [p for p in (slide.get("title"), *slide.get("bullets", [])) if p]
        parent_text = "\n".join(parent_parts)

        if not parent_text:
            continue

        # One child chunk per bullet (plus the title, if present) — small
        # units for embedding that each point back at the full slide.
        for child_text in parent_parts:
            chunks.append(
                _make_chunk(
                    document,
                    len(chunks),
                    child_text,
                    cursor,
                    parent_id,
                    parent_text,
                    {"source_type": "pptx", "slide_number": slide_number},
                )
            )
            cursor += len(child_text) + 1

    return chunks


def _split_into_windows(text: str, chunk_size: int, chunk_overlap: int) -> list[tuple[int, str]]:
    """Split text into overlapping character windows, breaking on whitespace."""
    if len(text) <= chunk_size:
        return [(0, text)] if text else []

    windows: list[tuple[int, str]] = []
    start = 0
    step = max(chunk_size - chunk_overlap, 1)

    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        window = text[start:end].strip()
        if window:
            windows.append((start, window))
        if end >= len(text):
            break
        start += step

    return windows


def _chunk_section(document: Document, config: ChunkingConfig) -> list[Chunk]:
    """Chunk a single-section Document (e.g. a DOCX section) into overlapping
    child windows, each carrying the full section as its parent text."""
    parent_id = document.doc_id
    parent_text = document.text

    if not parent_text.strip():
        return []

    windows = _split_into_windows(parent_text, config.chunk_size, config.chunk_overlap)
    return [
        _make_chunk(
            document,
            index,
            window_text,
            start_index,
            parent_id,
            parent_text,
            {
                "source_type": document.metadata.get("source_type"),
                "heading": document.metadata.get("heading"),
                "section_path": document.metadata.get("section_path"),
            },
        )
        for index, (start_index, window_text) in enumerate(windows)
    ]


def structure_aware_chunk(document: Document, config: ChunkingConfig) -> list[Chunk]:
    """Split a Document into Chunks along structural boundaries.

    PPTX documents (identified by ``metadata["slides"]``) are split per-slide
    into one child chunk per title/bullet, each carrying the full slide as
    parent context. All other documents (e.g. a single DOCX section) are
    split into overlapping windows of ``config.chunk_size``/``chunk_overlap``,
    each carrying the full section as parent context.

    Args:
        document: The source Document to chunk.
        config: Chunking parameters (chunk size, overlap).

    Returns:
        A list of Chunks covering the document's structural units.
    """
    if "slides" in document.metadata:
        return _chunk_pptx(document, config)
    return _chunk_section(document, config)


# Public interface name matching src.schemas.ChunkerFn.
chunk = structure_aware_chunk
