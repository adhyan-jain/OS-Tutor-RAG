"""Sparse lexical retrieval using BM25."""

from __future__ import annotations

from src.config import RetrievalConfig
from src.schemas import Chunk, ScoredChunk


class BM25Retriever:
    """Retrieves chunks by BM25 lexical scoring."""

    def __init__(self, config: RetrievalConfig) -> None:
        """Initialize the retriever with config.

        Args:
            config: Retrieval parameters (top_k).
        """
        raise NotImplementedError

    def index(self, chunks: list[Chunk]) -> None:
        """Build/update the BM25 index from a list of Chunks.

        Args:
            chunks: Chunks to index.
        """
        raise NotImplementedError

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Retrieve the most relevant chunks to a query via BM25.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of results.

        Returns:
            ScoredChunks ranked by descending BM25 score.
        """
        raise NotImplementedError
