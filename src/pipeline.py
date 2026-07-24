"""End-to-end RAG pipeline: ingestion -> chunking -> retrieval -> reranking ->
diversification -> generation.

Every stage's behavior is driven entirely by PipelineConfig — swapping
retrieval technique, reranking method, or whether diversification runs is a
config change (e.g. ``config.retrieval.technique = "dense"``), never a code
edit.
"""

from __future__ import annotations

from src.chunking import chunk_document
from src.config import PipelineConfig
from src.diversification.mmr import mmr_select
from src.generation.local_llm import LocalLLM
from src.reranking.cross_encoder import CrossEncoderReranker
from src.reranking.llm_rerank import LLMReranker
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid_rrf import HybridRRFRetriever
from src.retrieval.hyde import HyDERetriever
from src.retrieval.multi_query import MultiQueryRetriever
from src.retrieval.sparse_bm25 import BM25Retriever
from src.schemas import Document


class RAGPipeline:
    """Orchestrates the full retrieval-augmented generation pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        """Initialize all pipeline stages from config.

        Args:
            config: Aggregated configuration for every pipeline stage.
        """
        self.config = config
        self.llm = LocalLLM(config.generation)
        self.retriever = self._build_retriever()
        self.reranker = self._build_reranker()

    def _build_retriever(self):
        technique = self.config.retrieval.technique
        if technique == "dense":
            return DenseRetriever(self.config.retrieval)
        if technique == "bm25":
            return BM25Retriever(self.config.retrieval)
        if technique == "hybrid_rrf":
            return HybridRRFRetriever(self.config.retrieval)
        if technique == "hyde":
            return HyDERetriever(self.config.retrieval, self.config.generation)
        if technique == "multi_query":
            return MultiQueryRetriever(self.config.retrieval, self.config.generation)
        raise ValueError(f"Unknown retrieval technique: {technique!r}")

    def _build_reranker(self):
        method = self.config.reranking.method
        if method == "cross_encoder":
            return CrossEncoderReranker(self.config.reranking)
        if method == "llm_rerank":
            return LLMReranker(self.config.reranking, self.config.generation)
        if method == "none":
            return None
        raise ValueError(f"Unknown reranking method: {method!r}")

    def ingest(self, documents: list[Document]) -> None:
        """Run chunking and indexing for a batch of documents.

        Args:
            documents: Source Documents to chunk and index.
        """
        chunks = [
            chunk
            for document in documents
            for chunk in chunk_document(document, self.config.chunking)
        ]
        self.retriever.build_index(chunks)

    def answer(self, query: str) -> str:
        """Answer a query by running it through the full pipeline.

        Args:
            query: The user's natural language question.

        Returns:
            The generated answer text.
        """
        candidates = self.retriever.retrieve(query, top_k=self.config.retrieval.top_k)

        if self.reranker is not None:
            candidates = self.reranker.rerank(query, candidates)

        if self.config.diversification.enabled:
            candidates = mmr_select(candidates, self.config.diversification)

        return self.llm.generate(query, candidates)
