"""Rerank retrieved chunks using an LLM as the relevance judge."""

from __future__ import annotations

from dataclasses import replace

from src.config import GenerationConfig, RerankingConfig
from src.generation.local_llm import LocalLLM
from src.schemas import ScoredChunk
from src.token_tracking import LLMCallTracker


class LLMReranker:
    """Reranks ScoredChunks by prompting an LLM to judge relevance."""

    def __init__(
        self,
        config: RerankingConfig,
        generation_config: GenerationConfig | None = None,
        tracker: LLMCallTracker | None = None,
    ) -> None:
        """Initialize the reranker with a generation backend.

        Args:
            config: Reranking parameters (top_n).
            generation_config: Parameters for the LLM used to score relevance.
                Defaults to GenerationConfig().
            tracker: Optional LLMCallTracker to log this reranker's LLM calls to.
        """
        self.config = config
        self.llm = LocalLLM(generation_config or GenerationConfig(), tracker=tracker)

    def rerank(
        self, query: str, candidates: list[ScoredChunk], top_n: int | None = None
    ) -> list[ScoredChunk]:
        """Rerank candidate chunks for a query using LLM relevance judgments.

        Prompts the LLM once per candidate for a 0-10 relevance score
        (pointwise scoring), then sorts descending. Note this is the one stage
        whose cost scales with the candidate pool rather than the final
        selection, so a wide RetrievalConfig.candidate_pool_multiplier is
        considerably more expensive here than for a cross-encoder.

        Args:
            query: Natural language query text.
            candidates: ScoredChunks to rerank.
            top_n: Optional override for how many to keep. The pipeline widens
                this when diversification runs next, so MMR has more candidates
                than it will select.

        Returns:
            The top ``top_n`` (default ``config.top_n``) ScoredChunks re-ordered
            by descending LLM-judged relevance score.
        """
        if not candidates:
            return []

        scored = [
            (sc, self.llm.score_relevance(query, sc.chunk.text)) for sc in candidates
        ]
        reranked = sorted(scored, key=lambda pair: pair[1], reverse=True)[: top_n or self.config.top_n]

        return [
            replace(sc, score=score, source="llm_rerank", rank=rank)
            for rank, (sc, score) in enumerate(reranked, start=1)
        ]
