"""HyDE (Hypothetical Document Embeddings) retrieval: generate a hypothetical
answer with an LLM, then retrieve using its embedding as the query."""

from __future__ import annotations

from src.config import RetrievalConfig
from src.schemas import ScoredChunk


class HyDERetriever:
    """Retrieves chunks using embeddings of an LLM-generated hypothetical answer."""

    def __init__(self, config: RetrievalConfig) -> None:
        """Initialize the retriever with a generation backend and dense index.

        Args:
            config: Retrieval parameters (embedding model, top_k).
        """
        raise NotImplementedError

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Generate a hypothetical answer to the query and retrieve by its embedding.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of results.

        Returns:
            ScoredChunks ranked by similarity to the hypothetical answer.
        """
        raise NotImplementedError
