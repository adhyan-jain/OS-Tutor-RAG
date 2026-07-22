"""Shared data model for the RAG pipeline: Document, Chunk, ScoredChunk."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from src.config import ChunkingConfig


@dataclass
class Document:
    """A single source document extracted from a raw file (PPT, DOCX, ...)."""

    doc_id: str
    source_path: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk of a Document produced by a chunking strategy."""

    chunk_id: str
    doc_id: str
    text: str
    start_index: int
    end_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredChunk:
    """A Chunk annotated with a relevance score from retrieval/reranking."""

    chunk: Chunk
    score: float
    source: str
    rank: Optional[int] = None


# Interface every chunking strategy module must implement: a `chunk` function
# taking a Document and ChunkingConfig and returning its list of Chunks.
ChunkerFn = Callable[["Document", "ChunkingConfig"], list[Chunk]]
