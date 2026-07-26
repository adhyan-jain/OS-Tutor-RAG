"""Chunking strategy dispatcher: picks a strategy per document source type."""

from __future__ import annotations

from src.chunking.page_aware import page_aware_chunk
from src.chunking.semantic import semantic_chunk
from src.chunking.structure_aware import structure_aware_chunk
from src.config import ChunkingConfig
from src.schemas import Chunk, Document

_STRATEGIES = {
    "structure_aware": structure_aware_chunk,
    "page_aware": page_aware_chunk,
    "semantic": semantic_chunk,
}

# Chunking the same document under the same settings is deterministic, but not
# cheap -- semantic chunking embeds every sentence. A mass eval sweep re-chunks
# the whole corpus per config variant while only a handful of distinct chunking
# settings actually appear across them, so results are memoized on the settings
# that affect output.
_CHUNK_CACHE: dict[tuple, list[Chunk]] = {}


def _cache_key(document: Document, config: ChunkingConfig, strategy_name: str) -> tuple:
    return (
        document.doc_id,
        document.source_path,
        len(document.text),
        strategy_name,
        config.chunk_size,
        config.chunk_overlap,
        config.semantic_similarity_threshold,
        config.semantic_embedding_model_name,
    )


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

    key = _cache_key(document, config, strategy_name)
    if key not in _CHUNK_CACHE:
        _CHUNK_CACHE[key] = _STRATEGIES[strategy_name](document, config)
    return _CHUNK_CACHE[key]
