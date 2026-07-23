"""Sparse lexical retrieval using BM25."""

from __future__ import annotations

import pickle
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from src.config import RetrievalConfig
from src.schemas import Chunk, ScoredChunk

_STATE_FILENAME = "bm25.pkl"
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever:
    """Retrieves chunks by BM25 lexical scoring."""

    def __init__(self, config: RetrievalConfig) -> None:
        """Initialize the retriever with config.

        Args:
            config: Retrieval parameters (top_k, index_dir).
        """
        self.config = config
        self.bm25: BM25Okapi | None = None
        self.chunks: list[Chunk] = []

    def build_index(self, chunks: list[Chunk]) -> None:
        """Build/update the BM25 index from a list of Chunks.

        Args:
            chunks: Chunks to index.
        """
        self.chunks = list(chunks)
        tokenized_corpus = [_tokenize(c.text) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def save_index(self, index_dir: Path | None = None) -> None:
        """Persist the BM25 index and chunk list to disk.

        Args:
            index_dir: Directory to write to. Defaults to config.index_dir.
        """
        if self.bm25 is None:
            raise RuntimeError("No index to save — call build_index() first.")
        index_dir = Path(index_dir or self.config.index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        with open(index_dir / _STATE_FILENAME, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)

    def load_index(self, index_dir: Path | None = None) -> None:
        """Load a previously saved BM25 index and chunk list from disk.

        Args:
            index_dir: Directory to read from. Defaults to config.index_dir.
        """
        index_dir = Path(index_dir or self.config.index_dir)
        with open(index_dir / _STATE_FILENAME, "rb") as f:
            state = pickle.load(f)
        self.bm25 = state["bm25"]
        self.chunks = state["chunks"]

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Retrieve the most relevant chunks to a query via BM25.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of results.

        Returns:
            ScoredChunks ranked by descending BM25 score.
        """
        if self.bm25 is None:
            raise RuntimeError("No index loaded — call build_index() or load_index() first.")
        k = top_k or self.config.top_k
        scores = self.bm25.get_scores(_tokenize(query))
        ranked_indices = np.argsort(scores)[::-1][:k]

        return [
            ScoredChunk(chunk=self.chunks[idx], score=float(scores[idx]), source="bm25", rank=rank)
            for rank, idx in enumerate(ranked_indices, start=1)
        ]
