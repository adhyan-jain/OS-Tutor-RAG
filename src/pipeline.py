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
from src.context_expansion import expand_to_parents
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
from src.token_tracking import LLMCallTracker


class RAGPipeline:
    """Orchestrates the full retrieval-augmented generation pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        """Initialize all pipeline stages from config.

        Args:
            config: Aggregated configuration for every pipeline stage.
        """
        self.config = config
        # Shared across self.llm and any retriever/reranker that makes its own
        # LLM calls (hyde, multi_query, llm_rerank), so one run's full LLM
        # usage/cost can be reported together (see evaluation.py).
        self.tracker = LLMCallTracker()
        self.llm = LocalLLM(config.generation, tracker=self.tracker)
        self.retriever = self._build_retriever()
        self.reranker = self._build_reranker()

    def _build_retriever(self):
        technique = self.config.retrieval.technique
        use_multi_query = self.config.retrieval.use_multi_query

        if technique == "hyde":
            if use_multi_query:
                raise ValueError("use_multi_query cannot be combined with technique='hyde'")
            return HyDERetriever(self.config.retrieval, self.config.generation, tracker=self.tracker)

        if technique == "dense":
            base = DenseRetriever(self.config.retrieval)
        elif technique == "bm25":
            base = BM25Retriever(self.config.retrieval)
        elif technique == "hybrid_rrf":
            base = HybridRRFRetriever(self.config.retrieval)
        else:
            raise ValueError(f"Unknown retrieval technique: {technique!r}")

        if use_multi_query:
            return MultiQueryRetriever(base, self.config.retrieval, self.config.generation, tracker=self.tracker)
        return base

    def _build_reranker(self):
        method = self.config.reranking.method
        if method == "cross_encoder":
            return CrossEncoderReranker(self.config.reranking)
        if method == "llm_rerank":
            return LLMReranker(self.config.reranking, self.config.generation, tracker=self.tracker)
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

    def _stage_sizes(self) -> tuple[int, int]:
        """How many candidates to retrieve, and how many the reranker keeps.

        Each filtering stage needs to be handed more candidates than it keeps,
        or it cannot filter. With the plain configured sizes, retrieving 10,
        reranking to 5 and asking MMR for 5 leaves MMR selecting 5 out of 5 --
        it can only reorder, never diversify. So the pool is widened whenever a
        downstream stage will narrow it, and reranking passes through extra
        candidates when diversification runs after it.

        Returns:
            A tuple of (candidate pool size to retrieve, reranker top_n).
        """
        retrieval = self.config.retrieval
        rerank_enabled = self.reranker is not None
        mmr_enabled = self.config.diversification.enabled

        if not rerank_enabled and not mmr_enabled:
            return retrieval.top_k, self.config.reranking.top_n

        rerank_n = self.config.reranking.top_n
        if rerank_enabled and mmr_enabled:
            rerank_n = max(rerank_n, self.config.diversification.top_k * 2)

        narrowest = rerank_n if rerank_enabled else self.config.diversification.top_k
        pool_k = max(retrieval.top_k, narrowest * retrieval.candidate_pool_multiplier)
        return pool_k, rerank_n

    def _retrieve_candidates(self, query: str):
        pool_k, rerank_n = self._stage_sizes()
        candidates = self.retriever.retrieve(query, top_k=pool_k)

        if self.reranker is not None:
            candidates = self.reranker.rerank(query, candidates, top_n=rerank_n)

        if self.config.diversification.enabled:
            candidates = mmr_select(candidates, self.config.diversification)

        # Last step, after every selection stage: matching stays on precise
        # child chunks, but generation reads the slide/section they came from.
        if self.config.context_expansion.enabled:
            candidates = expand_to_parents(
                candidates, max_parent_tokens=self.config.context_expansion.max_parent_tokens
            )

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
        diversified contexts (not just the final answer) to score every
        RAGAS metric in src.evaluation.METRIC_NAMES.

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
        mean_scores, detail_rows, eval_tracker = score_pipeline(self, eval_set)

        retrieval_label = self.config.retrieval.technique
        if self.config.retrieval.use_multi_query:
            retrieval_label += "+multi_query"
        run_name = run_name or f"{retrieval_label}+{self.config.reranking.method}"
        append_run_to_workbook(
            self.config.eval.output_workbook_path,
            run_name,
            self.config,
            mean_scores,
            detail_rows,
            self.tracker,
            eval_tracker,
        )
        return mean_scores
