"""HyDE (Hypothetical Document Embeddings) retrieval: generate a hypothetical
answer with an LLM, then retrieve using its embedding as the query."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.config import GenerationConfig, RetrievalConfig
from src.generation.local_llm import LocalLLM
from src.retrieval.dense import DenseRetriever
from src.schemas import Chunk, ScoredChunk


class HyDERetriever:
    """Retrieves chunks using embeddings of an LLM-generated hypothetical answer."""

    def __init__(self, config: RetrievalConfig, generation_config: GenerationConfig | None = None) -> None:
        """Initialize the retriever with a generation backend and dense index.

        Args:
            config: Retrieval parameters (embedding model, top_k, index_dir) —
                shared with DenseRetriever so HyDE can reuse the same FAISS index.
            generation_config: Parameters for the LLM used to generate the
                hypothetical answer. Defaults to GenerationConfig().
        """
        self.config = config
        self.dense = DenseRetriever(config)
        self.llm = LocalLLM(generation_config or GenerationConfig())

    def build_index(self, chunks: list[Chunk]) -> None:
        """Build the underlying dense index from a list of Chunks.

        Args:
            chunks: Chunks to embed and index.
        """
        self.dense.build_index(chunks)

    def save_index(self, index_dir: Path | None = None) -> None:
        """Persist the underlying dense index to disk (same files as DenseRetriever).

        Args:
            index_dir: Directory to write to. Defaults to config.index_dir.
        """
        self.dense.save_index(index_dir)

    def load_index(self, index_dir: Path | None = None) -> None:
        """Load a previously saved dense index from disk (same files as DenseRetriever).

        Args:
            index_dir: Directory to read from. Defaults to config.index_dir.
        """
        self.dense.load_index(index_dir)

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Generate a hypothetical answer to the query and retrieve by its embedding.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of results.

        Returns:
            ScoredChunks ranked by similarity to the hypothetical answer.
        """
        hypothetical_answer = self.llm.generate_hypothetical_document(query)
        dense_results = self.dense.retrieve(hypothetical_answer, top_k=top_k)
        return [replace(sc, source="hyde") for sc in dense_results]
