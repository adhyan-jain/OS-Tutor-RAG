"""Incrementally update the local retrieval index.

Unlike `src/build_index.py` (which always re-embeds the full corpus), this
script only pays embedding cost for new/changed files: it loads whatever
dense+BM25 index already exists on disk, appends embeddings for just the
new/changed chunks to the FAISS index, rebuilds the (cheap) BM25 structure
from the full current chunk set, and saves the result locally.

Run manually whenever new course material is dropped into data/raw/:
    PYTHONPATH=. .venv/bin/python -m scripts.reindex
or:
    PYTHONPATH=. .venv/bin/python scripts/reindex.py
"""

from __future__ import annotations

import logging
import time

from src.build_index import diff_and_chunk
from src.config import ChunkingConfig, PathConfig, RetrievalConfig
from src.ingestion.manifest import save_manifest
from src.retrieval.hybrid_rrf import HybridRRFRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.reindex")


def main() -> None:
    paths = PathConfig()
    chunking_config = ChunkingConfig()
    retrieval_config = RetrievalConfig()

    logger.info("Diffing data/raw/ against manifest...")
    result = diff_and_chunk(paths, chunking_config, retrieval_config)

    logger.info("Files new/changed: %d %s", len(result.new_or_changed_files), result.new_or_changed_files)
    logger.info("Files reused from cache: %d", len(result.reused_files))
    if result.removed_files:
        logger.info("Files removed from manifest (no longer in data/raw/): %s", result.removed_files)
    if result.skipped_files:
        logger.info("Skipped (unsupported extension): %s", result.skipped_files)
    logger.info("Total chunks in corpus: %d (new: %d)", len(result.all_chunks), len(result.new_chunks))

    retriever = HybridRRFRetriever(retrieval_config)
    index_exists = (retrieval_config.index_dir / "dense.faiss").exists()

    if index_exists:
        logger.info("Loading existing index from %s...", retrieval_config.index_dir)
        retriever.load_index()
    else:
        logger.info("No existing index found -- starting fresh.")

    if not result.new_chunks and index_exists:
        logger.info("No new/changed files -- index is already up to date. Skipping re-embed.")
    else:
        embed_start = time.monotonic()
        # Dense: embed only the new/changed chunks and append them to
        # whatever FAISS index was just loaded (or start fresh if none was).
        # BM25: rebuilt from the FULL chunk set every time -- O(corpus) but
        # cheap (tokenizing+indexing is fast; embedding is what's expensive).
        retriever.add_chunks(result.new_chunks, result.all_chunks)
        embed_elapsed = time.monotonic() - embed_start
        logger.info(
            "Embedded %d new chunk(s) from %d file(s) in %.2fs (BM25 rebuilt over all %d chunks).",
            len(result.new_chunks),
            len(result.new_or_changed_files),
            embed_elapsed,
            len(result.all_chunks),
        )

    retriever.save_index()
    save_manifest(retrieval_config.index_dir, result.manifest)
    logger.info("Index and manifest saved to %s", retrieval_config.index_dir)


if __name__ == "__main__":
    main()
