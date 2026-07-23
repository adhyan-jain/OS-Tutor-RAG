"""Rerank retrieved chunks using an LLM as the relevance judge."""

from __future__ import annotations

from dataclasses import replace

from src.config import GenerationConfig, RerankingConfig
from src.generation.local_llm import LocalLLM
from src.schemas import ScoredChunk


class LLMReranker:
    """Reranks ScoredChunks by prompting an LLM to judge relevance."""

    def __init__(self, config: RerankingConfig, generation_config: GenerationConfig | None = None) -> None:
        """Initialize the reranker with a generation backend.

        Args:
            config: Reranking parameters (top_n).
            generation_config: Parameters for the LLM used to score relevance.
                Defaults to GenerationConfig().
        """
        self.config = config
        self.llm = LocalLLM(generation_config or GenerationConfig())

    def rerank(self, query: str, candidates: list[ScoredChunk]) -> list[ScoredChunk]:
        """Rerank candidate chunks for a query using LLM relevance judgments.

        Prompts the LLM once per candidate for a 0-10 relevance score
        (pointwise scoring), then sorts descending.

        Args:
            query: Natural language query text.
            candidates: ScoredChunks to rerank.

        Returns:
            The top ``config.top_n`` ScoredChunks re-ordered by descending
            LLM-judged relevance score.
        """
        if not candidates:
            return []

        scored = [
            (sc, self.llm.score_relevance(query, sc.chunk.text)) for sc in candidates
        ]
        reranked = sorted(scored, key=lambda pair: pair[1], reverse=True)[: self.config.top_n]

        return [
            replace(sc, score=score, source="llm_rerank", rank=rank)
            for rank, (sc, score) in enumerate(reranked, start=1)
        ]
