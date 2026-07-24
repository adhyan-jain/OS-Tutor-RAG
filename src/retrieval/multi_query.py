"""Multi Query retrieval: generate several reformulated versions of the query
with an LLM, retrieve for each independently, and fuse the rankings via RRF."""

from __future__ import annotations

from pathlib import Path

from src.config import GenerationConfig, RetrievalConfig
from src.generation.local_llm import LocalLLM
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid_rrf import reciprocal_rank_fusion
from src.schemas import Chunk, ScoredChunk


class MultiQueryRetriever:
    """Retrieves chunks by fusing rankings across several LLM-reformulated queries."""

    def __init__(self, config: RetrievalConfig, generation_config: GenerationConfig | None = None) -> None:
        """Initialize the retriever with a generation backend and dense index.

        Args:
            config: Retrieval parameters (embedding model, top_k, index_dir,
                num_query_variants) -- shared with DenseRetriever so this can
                reuse the same FAISS index.
            generation_config: Parameters for the LLM used to generate query
                reformulations. Defaults to GenerationConfig().
        """
        self.config = config
        self.dense = DenseRetriever(config)
        self.llm = LocalLLM(generation_config or GenerationConfig())

    def build_index(self, chunks: list[Chunk]) -> None:
        """Build the underlying dense index from a list of Chunks.

        Args:
            chunks: Chunks to embed and index.
        """
        self.dense.build_index(chunks)

    def save_index(self, index_dir: Path | None = None) -> None:
        """Persist the underlying dense index to disk (same files as DenseRetriever).

        Args:
            index_dir: Directory to write to. Defaults to config.index_dir.
        """
        self.dense.save_index(index_dir)

    def load_index(self, index_dir: Path | None = None) -> None:
        """Load a previously saved dense index from disk (same files as DenseRetriever).

        Args:
            index_dir: Directory to read from. Defaults to config.index_dir.
        """
        self.dense.load_index(index_dir)

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Generate query reformulations, retrieve for each, and fuse via RRF.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of fused results.

        Returns:
            ScoredChunks ranked by descending fused RRF score across the
            original query and all reformulations.
        """
        pool_k = top_k or self.config.top_k
        variants = self.llm.generate_query_variants(query, self.config.num_query_variants)
        all_queries = [query, *variants]

        ranked_lists = [self.dense.retrieve(q, top_k=pool_k) for q in all_queries]

        fusion_config = self.config
        if top_k is not None:
            from dataclasses import replace

            fusion_config = replace(self.config, top_k=top_k)

        fused = reciprocal_rank_fusion(ranked_lists, fusion_config)
        return [
            ScoredChunk(chunk=sc.chunk, score=sc.score, source="multi_query", rank=sc.rank) for sc in fused
        ]
