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

# Set True at the end of load_index() iff the retriever actually ended up
# with a loaded/built index. Read by GET /health so a deploy host's health
# check can distinguish "process is up" from "index failed to load and /chat
# will error on retrieval".
index_loaded = False


def load_index() -> None:
    """Load the retrieval index into whichever retriever object actually
    needs it (a plain DenseRetriever by default, but this also works if
    config ever wraps it, e.g. MultiQueryRetriever, since that class proxies
    load_index() to its wrapped base retriever).

    Startup order:
    1. If a local index already exists on disk, just load it.
    2. Otherwise, if data/raw/ has source files, do a full local rebuild.
    3. Otherwise, log a clear warning and continue without a loaded index
       (chat will fail on retrieval, but startup shouldn't crash over it).
    """
    global index_loaded
    index_dir = pipeline.config.retrieval.index_dir
    local_index_exists = (index_dir / "dense.faiss").exists()

    if local_index_exists:
        logger.info("Using existing local index.")
        pipeline.retriever.load_index()
    else:
        raw_dir = pipeline.config.paths.data_raw_dir
        has_raw_files = raw_dir.exists() and any(raw_dir.iterdir())
        if has_raw_files:
            logger.info("No local index -- rebuilding from data/raw/...")
            from src.build_index import diff_and_chunk
            from src.ingestion.manifest import save_manifest

            paths = pipeline.config.paths
            chunking_config = pipeline.config.chunking
            retrieval_config = pipeline.config.retrieval
            result = diff_and_chunk(paths, chunking_config, retrieval_config)
            pipeline.retriever.build_index(result.all_chunks)
            pipeline.retriever.save_index()
            save_manifest(retrieval_config.index_dir, result.manifest)
            logger.info("Rebuilt index from data/raw/.")
        else:
            logger.warning(
                "No index available (no local index, no data/raw/ files). "
                "Starting up without a loaded index -- /chat will fail on retrieval until one exists."
            )
            return

    index_loaded = True
    logger.info("Index loaded for retriever: %s", type(pipeline.retriever).__name__)
