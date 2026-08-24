"""Dense (embedding-based) retrieval over a FAISS chunk index."""

from __future__ import annotations

import pickle
from pathlib import Path

import faiss
import numpy as np

from src.config import RetrievalConfig
from src.schemas import Chunk, ScoredChunk

_INDEX_FILENAME = "dense.faiss"
_CHUNKS_FILENAME = "dense_chunks.pkl"

# Embedding a corpus is the dominant cost of build_index (minutes on CPU for
# bge-large). A mass eval sweep rebuilds the index once per config variant,
# but the embeddings depend only on the chunk texts and the model -- not on
# retrieval technique, reranking, or diversification -- so the same corpus
# gets re-embedded dozens of times identically. Memoized on exactly those two
# inputs.
_CORPUS_EMBEDDING_CACHE: dict[tuple[str, str], "np.ndarray"] = {}


def _corpus_cache_key(model_name: str, texts: list[str]) -> tuple[str, str]:
    import hashlib

    digest = hashlib.sha256("\x00".join(texts).encode("utf-8")).hexdigest()
    return (model_name, digest)


class DenseRetriever:
    """Retrieves chunks by cosine similarity of dense embeddings (FAISS)."""

    def __init__(self, config: RetrievalConfig) -> None:
        """Initialize the retriever with an embedding model and config.

        Args:
            config: Retrieval parameters (model name, top_k, index_dir).
        """
        from src.embedding_cache import get_embedding_model

        self.config = config
        self.model = get_embedding_model(config.dense_model_name)
        self.index: faiss.Index | None = None
        self.chunks: list[Chunk] = []

    def _embed(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype("float32")

    def build_index(self, chunks: list[Chunk]) -> None:
        """Embed chunks and build an in-memory FAISS index.

        Args:
            chunks: Chunks to embed and index.
        """
        self.chunks = list(chunks)
        texts = [c.text for c in self.chunks]

        key = _corpus_cache_key(self.config.dense_model_name, texts)
        if key not in _CORPUS_EMBEDDING_CACHE:
            _CORPUS_EMBEDDING_CACHE[key] = self._embed(texts)
        embeddings = _CORPUS_EMBEDDING_CACHE[key]

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

    def add_chunks(self, new_chunks: list[Chunk]) -> None:
        """Embed only `new_chunks` and append them to the existing FAISS index.

        Used by the incremental reindex path (scripts/reindex.py): unlike
        build_index(), which re-embeds every chunk passed to it, this only
        pays embedding cost for the chunks handed to it here. Call
        load_index() first (or build_index() with no chunks yet) to seed
        self.index/self.chunks if an index already exists on disk; if no
        index has been built/loaded yet, this creates one from scratch.

        IndexFlatIP supports cheap incremental .add() -- there's no need to
        rebuild the whole FAISS structure the way BM25Retriever.build_index()
        must be re-run in full (see HybridRRFRetriever.add_chunks).

        Args:
            new_chunks: Newly added/changed chunks to embed and append.
        """
        if not new_chunks:
            return
        texts = [c.text for c in new_chunks]
        embeddings = self._embed(texts)

        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings)
        self.chunks.extend(new_chunks)

    def save_index(self, index_dir: Path | None = None) -> None:
        """Persist the FAISS index and chunk list to disk.

        Args:
            index_dir: Directory to write to. Defaults to config.index_dir.
        """
        if self.index is None:
            raise RuntimeError("No index to save — call build_index() first.")
        index_dir = Path(index_dir or self.config.index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / _INDEX_FILENAME))
        with open(index_dir / _CHUNKS_FILENAME, "wb") as f:
            pickle.dump(self.chunks, f)

    def load_index(self, index_dir: Path | None = None) -> None:
        """Load a previously saved FAISS index and chunk list from disk.

        Args:
            index_dir: Directory to read from. Defaults to config.index_dir.
        """
        index_dir = Path(index_dir or self.config.index_dir)
        self.index = faiss.read_index(str(index_dir / _INDEX_FILENAME))
        with open(index_dir / _CHUNKS_FILENAME, "rb") as f:
            self.chunks = pickle.load(f)

    def retrieve(self, query: str, top_k: int | None = None) -> list[ScoredChunk]:
        """Retrieve the most similar chunks to a query.

        Args:
            query: Natural language query text.
            top_k: Optional override for number of results.

        Returns:
            ScoredChunks ranked by descending cosine similarity.
        """
        if self.index is None:
            raise RuntimeError("No index loaded — call build_index() or load_index() first.")
        k = top_k or self.config.top_k
        query_embedding = self._embed([query])
        scores, indices = self.index.search(query_embedding, k)

        results: list[ScoredChunk] = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
            if idx == -1:
                continue
            results.append(
                ScoredChunk(chunk=self.chunks[idx], score=float(score), source="dense", rank=rank)
            )
        return results
