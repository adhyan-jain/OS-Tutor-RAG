"""Dense (embedding-based) retrieval over a chunk index."""

from __future__ import annotations

from src.config import RetrievalConfig
from src.schemas import Chunk, ScoredChunk


class DenseRetriever:
    """Retrieves chunks by cosine similarity of dense embeddings."""

    def __init__(self, config: RetrievalConfig) -> None:
        """Initialize the retriever with an embedding model and config.

        Args:
            config: Retrieval parameters (model name, top_k).
        """
        raise NotImplementedError

    def index(self, chunks: list[Chunk]) -> None:
        """Build/update the dense index from a list of Chunks.

        Args:
            chunks: Chunks to embed and index.
        """
        raise NotImplementedError

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Retrieve the most similar chunks to a query.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of results.

        Returns:
            ScoredChunks ranked by descending similarity.
        """
        raise NotImplementedError
