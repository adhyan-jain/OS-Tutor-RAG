"""Chunking strategy dispatcher: picks a strategy per document source type."""

from __future__ import annotations

from src.chunking.semantic import semantic_chunk
from src.chunking.structure_aware import structure_aware_chunk
from src.config import ChunkingConfig
from src.schemas import Chunk, Document

_STRATEGIES = {
    "structure_aware": structure_aware_chunk,
    "semantic": semantic_chunk,
}


def chunk_document(document: Document, config: ChunkingConfig) -> list[Chunk]:
    """Chunk a Document using the strategy configured for its source type.

    Looks up ``document.metadata["source_type"]`` in
    ``config.strategy_by_source_type``, falling back to
    ``config.default_strategy`` when absent or unmapped.

    Args:
        document: The source Document to chunk.
        config: Chunking parameters, including the strategy mapping.

    Returns:
        A list of Chunks produced by the selected strategy.
    """
    source_type = document.metadata.get("source_type")
    strategy_name = config.strategy_by_source_type.get(source_type, config.default_strategy)
    return _STRATEGIES[strategy_name](document, config)
