"""Multi Query retrieval: generate several reformulated versions of the query
with an LLM, retrieve for each independently with a wrapped base retriever,
and fuse the rankings via RRF."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Protocol

from src.config import GenerationConfig, RetrievalConfig
from src.generation.local_llm import LocalLLM
from src.retrieval.hybrid_rrf import reciprocal_rank_fusion
from src.schemas import Chunk, ScoredChunk
from src.token_tracking import LLMCallTracker


class _BaseRetriever(Protocol):
    def build_index(self, chunks: list[Chunk]) -> None: ...
    def save_index(self, index_dir: Path | None = None) -> None: ...
    def load_index(self, index_dir: Path | None = None) -> None: ...
    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]: ...


class MultiQueryRetriever:
    """Wraps a base retriever (dense, bm25, or hybrid_rrf -- not hyde), fusing
    rankings across several LLM-reformulated query variants via RRF."""

    def __init__(
        self,
        base_retriever: _BaseRetriever,
        config: RetrievalConfig,
        generation_config: GenerationConfig | None = None,
        tracker: LLMCallTracker | None = None,
    ) -> None:
        """Initialize the retriever with a base retriever and generation backend.

        Args:
            base_retriever: The underlying retriever to fan queries out to
                (e.g. a DenseRetriever, BM25Retriever, or HybridRRFRetriever).
            config: Retrieval parameters (top_k, rrf_k, num_query_variants).
            generation_config: Parameters for the LLM used to generate query
                reformulations. Defaults to GenerationConfig().
            tracker: Optional LLMCallTracker to log this retriever's LLM calls to.
        """
        self.base = base_retriever
        self.config = config
        self.llm = LocalLLM(generation_config or GenerationConfig(), tracker=tracker)

    def build_index(self, chunks: list[Chunk]) -> None:
        """Build the wrapped retriever's index from a list of Chunks.

        Args:
            chunks: Chunks to embed/index.
        """
        self.base.build_index(chunks)

    def save_index(self, index_dir: Path | None = None) -> None:
        """Persist the wrapped retriever's index to disk.

        Args:
            index_dir: Directory to write to. Defaults to config.index_dir.
        """
        self.base.save_index(index_dir)

    def load_index(self, index_dir: Path | None = None) -> None:
        """Load the wrapped retriever's previously saved index from disk.

        Args:
            index_dir: Directory to read from. Defaults to config.index_dir.
        """
        self.base.load_index(index_dir)

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Generate query reformulations, retrieve each with the base retriever,
        and fuse via RRF -- always, regardless of the base retriever's own
        fusion behavior (e.g. hybrid_rrf already RRF-fuses dense+bm25 per
        variant; this adds a second RRF pass across variants).

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

        ranked_lists = [self.base.retrieve(q, top_k=pool_k) for q in all_queries]

        fusion_config = self.config if top_k is None else replace(self.config, top_k=top_k)

        fused = reciprocal_rank_fusion(ranked_lists, fusion_config)
        return [
            ScoredChunk(chunk=sc.chunk, score=sc.score, source="multi_query", rank=sc.rank) for sc in fused
        ]
