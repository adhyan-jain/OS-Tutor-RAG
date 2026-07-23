"""Hybrid retrieval combining dense and sparse results via Reciprocal Rank Fusion."""

from __future__ import annotations

from pathlib import Path

from src.config import RetrievalConfig
from src.retrieval.dense import DenseRetriever
from src.retrieval.sparse_bm25 import BM25Retriever
from src.schemas import Chunk, ScoredChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    config: RetrievalConfig,
) -> list[ScoredChunk]:
    """Fuse multiple ranked ScoredChunk lists using RRF.

    Each chunk's fused score is the sum of ``1 / (rrf_k + rank)`` across every
    ranked list it appears in (rank is 1-indexed); chunks absent from a list
    simply don't contribute a term for it.

    Args:
        ranked_lists: One ranked list of ScoredChunks per retriever.
        config: Retrieval parameters (rrf_k constant, top_k).

    Returns:
        A single fused ranking of ScoredChunks, descending by fused score.
    """
    fused_scores: dict[str, float] = {}
    chunk_by_id: dict[str, Chunk] = {}

    for ranked_list in ranked_lists:
        for rank, scored_chunk in enumerate(ranked_list, start=1):
            chunk_id = scored_chunk.chunk.chunk_id
            chunk_by_id[chunk_id] = scored_chunk.chunk
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + 1.0 / (config.rrf_k + rank)

    ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)

    return [
        ScoredChunk(chunk=chunk_by_id[chunk_id], score=fused_scores[chunk_id], source="hybrid_rrf", rank=rank)
        for rank, chunk_id in enumerate(ranked_ids[: config.top_k], start=1)
    ]


class HybridRRFRetriever:
    """Retrieves chunks by fusing DenseRetriever and BM25Retriever rankings via RRF."""

    def __init__(self, config: RetrievalConfig) -> None:
        """Initialize the underlying dense and BM25 retrievers.

        Args:
            config: Retrieval parameters shared by both underlying retrievers.
        """
        self.config = config
        self.dense = DenseRetriever(config)
        self.bm25 = BM25Retriever(config)

    def build_index(self, chunks: list[Chunk]) -> None:
        """Build both the dense and BM25 indexes from a list of Chunks.

        Args:
            chunks: Chunks to embed/index for both retrievers.
        """
        self.dense.build_index(chunks)
        self.bm25.build_index(chunks)

    def save_index(self, index_dir: Path | None = None) -> None:
        """Persist both underlying indexes to disk.

        Args:
            index_dir: Directory to write to. Defaults to config.index_dir.
        """
        self.dense.save_index(index_dir)
        self.bm25.save_index(index_dir)

    def load_index(self, index_dir: Path | None = None) -> None:
        """Load both underlying indexes from disk.

        Args:
            index_dir: Directory to read from. Defaults to config.index_dir.
        """
        self.dense.load_index(index_dir)
        self.bm25.load_index(index_dir)

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Retrieve chunks by fusing dense and BM25 rankings with RRF.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of fused results.

        Returns:
            ScoredChunks ranked by descending fused RRF score.
        """
        pool_k = top_k or self.config.top_k
        dense_results = self.dense.retrieve(query, top_k=pool_k)
        bm25_results = self.bm25.retrieve(query, top_k=pool_k)

        fusion_config = self.config
        if top_k is not None:
            from dataclasses import replace

            fusion_config = replace(self.config, top_k=top_k)

        return reciprocal_rank_fusion([dense_results, bm25_results], fusion_config)
