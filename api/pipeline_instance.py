"""Builds the single shared RAGPipeline instance used by every request.

Constructing RAGPipeline loads the embedding model, so this must happen once
at process startup, not per-request. Routers import `pipeline` from here
rather than constructing their own.
"""

from __future__ import annotations

import logging

from src.config import PipelineConfig
from src.pipeline import RAGPipeline

logger = logging.getLogger("api.pipeline_instance")

pipeline = RAGPipeline(PipelineConfig())


def load_index() -> None:
    """Load the on-disk FAISS/BM25 index into whichever retriever object
    actually needs it (a plain DenseRetriever by default, but this also
    works if config ever wraps it, e.g. MultiQueryRetriever, since that
    class proxies load_index() to its wrapped base retriever).
    """
    pipeline.retriever.load_index()
    logger.info("Index loaded for retriever: %s", type(pipeline.retriever).__name__)
