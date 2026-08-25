"""Builds the single shared RAGPipeline instance used by every request.

Constructing RAGPipeline loads the embedding model, so this must happen once
at process startup, not per-request. Routers import `pipeline` from here
rather than constructing their own.
"""

from __future__ import annotations

import logging
import os

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
    1. If S3 is configured (S3_BUCKET set), try to download the latest index
       from S3 into the local index_dir first, so a fresh deploy picks up
       whatever a previous run built rather than an empty/stale local dir.
    2. If S3 wasn't configured, or had nothing to download:
       - and a local index already exists on disk, just load it (S3 sync is
         best-effort, not required for local dev).
       - and data/raw/ has source files, do a full local rebuild and push it
         to S3 as the new baseline (only if S3 IS configured -- otherwise
         just build locally).
       - and neither exists, log a clear warning and continue without a
         loaded index (chat will fail on retrieval, but startup shouldn't
         crash over it).
    """
    global index_loaded
    index_dir = pipeline.config.retrieval.index_dir
    s3_bucket = os.environ.get("S3_BUCKET")

    downloaded = False
    if s3_bucket:
        from src.indexing.s3_sync import download_index

        try:
            downloaded = download_index(index_dir)
        except Exception:
            logger.exception("S3 index download failed -- falling back to local state.")
            downloaded = False
    else:
        logger.info("S3_BUCKET not set -- S3 sync disabled, using local index only.")

    local_index_exists = (index_dir / "dense.faiss").exists()

    if downloaded:
        logger.info("Loaded index from S3.")
        pipeline.retriever.load_index()
    elif local_index_exists:
        logger.info("No index in S3 (or S3 unconfigured); using existing local index.")
        pipeline.retriever.load_index()
    else:
        raw_dir = pipeline.config.paths.data_raw_dir
        has_raw_files = raw_dir.exists() and any(raw_dir.iterdir())
        if has_raw_files:
            logger.info("No index in S3 or locally -- rebuilding from data/raw/...")
            from src.build_index import diff_and_chunk
            from src.ingestion.manifest import save_manifest

            paths = pipeline.config.paths
            chunking_config = pipeline.config.chunking
            retrieval_config = pipeline.config.retrieval
            result = diff_and_chunk(paths, chunking_config, retrieval_config)
            pipeline.retriever.build_index(result.all_chunks)
            pipeline.retriever.save_index()
            save_manifest(retrieval_config.index_dir, result.manifest)

            if s3_bucket:
                from src.indexing.s3_sync import upload_index

                try:
                    upload_index(index_dir)
                    logger.info("No index in S3, rebuilt from data/raw/ and uploaded.")
                except Exception:
                    logger.exception("Rebuilt index locally, but upload to S3 failed.")
            else:
                logger.info("No index in S3, rebuilt from data/raw/ (S3 unconfigured, not uploaded).")
        else:
            logger.warning(
                "No index available anywhere (no S3 index, no local index, no data/raw/ files). "
                "Starting up without a loaded index -- /chat will fail on retrieval until one exists."
            )
            return

    index_loaded = True
    logger.info("Index loaded for retriever: %s", type(pipeline.retriever).__name__)
