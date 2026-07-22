"""Chunk documents by semantic similarity between adjacent text segments.

Intended for long-form prose (e.g. textbook chapters) where structural
markers (slides/headings) are absent or too coarse. Splits text into
sentences, embeds each, and starts a new chunk wherever the cosine
similarity between consecutive sentence embeddings drops below
``config.semantic_similarity_threshold`` — i.e. wherever the topic shifts.
"""

from __future__ import annotations

import re

from src.config import ChunkingConfig
from src.schemas import Chunk, Document

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _cosine_similarity(a, b) -> float:
    import numpy as np

    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def _group_by_similarity_shift(
    sentences: list[str],
    embeddings,
    threshold: float,
    chunk_size: int,
) -> list[list[str]]:
    groups: list[list[str]] = [[sentences[0]]]
    group_lengths = [len(sentences[0])]

    for i in range(1, len(sentences)):
        similarity = _cosine_similarity(embeddings[i - 1], embeddings[i])
        would_overflow = group_lengths[-1] + len(sentences[i]) > chunk_size
        if similarity < threshold or would_overflow:
            groups.append([sentences[i]])
            group_lengths.append(len(sentences[i]))
        else:
            groups[-1].append(sentences[i])
            group_lengths[-1] += len(sentences[i])

    return groups


def semantic_chunk(document: Document, config: ChunkingConfig) -> list[Chunk]:
    """Split a Document into Chunks based on semantic coherence.

    Args:
        document: The source Document to chunk.
        config: Chunking parameters (chunk_size cap, semantic_similarity_threshold,
            semantic_embedding_model_name).

    Returns:
        A list of Chunks, each spanning a run of sentences whose embeddings
        stay above the similarity threshold with their neighbors.
    """
    sentences = _split_sentences(document.text)
    if not sentences:
        return []
    if len(sentences) == 1:
        return [
            Chunk(
                chunk_id=f"{document.doc_id}__chunk0",
                doc_id=document.doc_id,
                text=sentences[0],
                start_index=0,
                end_index=len(sentences[0]),
                metadata={"source_type": document.metadata.get("source_type"), "strategy": "semantic"},
            )
        ]

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.semantic_embedding_model_name)
    embeddings = model.encode(sentences)

    groups = _group_by_similarity_shift(
        sentences, embeddings, config.semantic_similarity_threshold, config.chunk_size
    )

    chunks: list[Chunk] = []
    cursor = 0
    for index, group in enumerate(groups):
        text = " ".join(group)
        start_index = document.text.find(group[0], cursor)
        if start_index == -1:
            start_index = cursor
        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}__chunk{index}",
                doc_id=document.doc_id,
                text=text,
                start_index=start_index,
                end_index=start_index + len(text),
                metadata={"source_type": document.metadata.get("source_type"), "strategy": "semantic"},
            )
        )
        cursor = start_index + len(text)

    return chunks


# Public interface name matching src.schemas.ChunkerFn.
chunk = semantic_chunk
