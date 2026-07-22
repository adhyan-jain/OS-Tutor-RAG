"""End-to-end RAG pipeline: ingestion -> chunking -> retrieval -> reranking ->
diversification -> generation."""

from __future__ import annotations

from src.config import PipelineConfig
from src.schemas import Document


class RAGPipeline:
    """Orchestrates the full retrieval-augmented generation pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        """Initialize all pipeline stages from config.

        Args:
            config: Aggregated configuration for every pipeline stage.
        """
        raise NotImplementedError

    def ingest(self, documents: list[Document]) -> None:
        """Run ingestion, chunking, and indexing for a batch of documents.

        Args:
            documents: Source Documents to process and index.
        """
        raise NotImplementedError

    def answer(self, query: str) -> str:
        """Answer a query by running it through the full pipeline.

        Args:
            query: The user's natural language question.

        Returns:
            The generated answer text.
        """
        raise NotImplementedError
