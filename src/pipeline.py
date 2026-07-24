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

    def _retrieve_candidates(self, query: str):
        candidates = self.retriever.retrieve(query, top_k=self.config.retrieval.top_k)

        if self.reranker is not None:
            candidates = self.reranker.rerank(query, candidates)

        if self.config.diversification.enabled:
            candidates = mmr_select(candidates, self.config.diversification)

        return candidates

    def answer(self, query: str) -> str:
        """Answer a query by running it through the full pipeline.

        Args:
            query: The user's natural language question.

        Returns:
            The generated answer text.
        """
        candidates = self._retrieve_candidates(query)
        return self.llm.generate(query, candidates)

    def answer_with_contexts(self, query: str) -> tuple[str, list[str]]:
        """Answer a query, also returning the context chunk texts used.

        Used by eval/ragas_eval.py, which needs the actual retrieved/reranked/
        diversified contexts (not just the final answer) to score
        context_precision, context_recall, faithfulness, and answer_relevancy.

        Args:
            query: The user's natural language question.

        Returns:
            A tuple of (generated answer, list of context chunk texts).
        """
        candidates = self._retrieve_candidates(query)
        answer = self.llm.generate(query, candidates)
        contexts = [sc.chunk.text for sc in candidates]
        return answer, contexts

    def evaluate(self, run_name: str | None = None) -> dict[str, float]:
        """Score this (already-ingested) pipeline against config.eval's eval
        set with RAGAS, appending results to config.eval.output_workbook_path.

        Args:
            run_name: Short identifier for this run, used as the new sheet
                name in the output workbook. Defaults to
                "{retrieval.technique}+{reranking.method}".

        Returns:
            The mean RAGAS metric scores for this run (also written to the
            workbook's "Final Analysis" sheet).
        """
        from src.evaluation import append_run_to_workbook, load_eval_set, score_pipeline

        eval_set = load_eval_set(self.config.eval.eval_set_path, self.config.eval.num_questions)
        mean_scores, detail_rows = score_pipeline(self, eval_set)

        run_name = run_name or f"{self.config.retrieval.technique}+{self.config.reranking.method}"
        append_run_to_workbook(
            self.config.eval.output_workbook_path, run_name, self.config, mean_scores, detail_rows
        )
        return mean_scores
