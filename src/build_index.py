"""Incrementally build/update the retrieval index from data/raw/.

Tracks ingested files by content hash in data/index/manifest.json. On each
run, only new or changed files are re-extracted and re-chunked (cached
per-file chunk pickles live in data/processed/); unchanged files are loaded
from cache. The full combined chunk set is then used to rebuild and save the
hybrid (dense + BM25) index, since this script always fully re-embeds
(see scripts/reindex.py for the incremental-embedding path that only pays
embedding cost for new/changed files).

Run this whenever new course material is dropped into data/raw/:
    PYTHONPATH=. .venv/bin/python -m src.build_index
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.chunking import chunk_document
from src.config import ChunkingConfig, PathConfig, RetrievalConfig
from src.ingestion.extract_docx import extract_docx
from src.ingestion.extract_pdf import extract_pdf
from src.ingestion.extract_ppt import extract_ppt
from src.ingestion.manifest import (
    chunking_signature,
    file_hash,
    load_manifest,
    record_file,
    save_manifest,
)
from src.retrieval.hybrid_rrf import HybridRRFRetriever
from src.schemas import Chunk

_EXTRACTORS = {
    ".pptx": lambda path: [extract_ppt(path)],
    ".docx": lambda path: extract_docx(path),
    ".pdf": lambda path: [extract_pdf(path)],
}


def _processed_path(processed_dir: Path, filename: str) -> Path:
    safe_name = filename.replace("/", "_")
    return processed_dir / f"{safe_name}.chunks.pkl"


@dataclass
class DiffResult:
    """Result of diffing data/raw/ against the manifest and (re)chunking.

    Shared by src/build_index.py (full rebuild) and scripts/reindex.py
    (incremental update) so both scripts diff files, extract/chunk, and
    update the manifest identically -- only what they do with the resulting
    chunks (full re-embed vs. embed-only-the-new-ones) differs.
    """

    all_chunks: list[Chunk] = field(default_factory=list)
    # Chunks belonging only to files that were new/changed this run -- what
    # an incremental index update needs to embed.
    new_chunks: list[Chunk] = field(default_factory=list)
    new_or_changed_files: list[str] = field(default_factory=list)
    reused_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)


def diff_and_chunk(paths: PathConfig, chunking_config: ChunkingConfig, retrieval_config: RetrievalConfig) -> DiffResult:
    """Diff data/raw/ against the manifest, (re)chunk what changed, and update the manifest in memory.

    Reads/reuses cached per-file chunk pickles from data/processed/ for files
    whose content hash and chunking signature are unchanged; extracts and
    re-chunks (writing a fresh cache pickle) everything else. Does NOT save
    the manifest -- callers save it themselves after also updating the
    retrieval index, so a crash between chunking and index-save doesn't leave
    the manifest claiming an index state that was never persisted.

    Args:
        paths: Filesystem locations (data/raw, data/processed, index_dir).
        chunking_config: Chunking settings -- part of the cache-reuse fingerprint.
        retrieval_config: Used only for its index_dir, to load the manifest.

    Returns:
        A DiffResult with the full chunk set, the new/changed subset, and
        bookkeeping for logging.
    """
    paths.data_processed_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(retrieval_config.index_dir)
    current_chunking_signature = chunking_signature(chunking_config)

    raw_files = sorted(
        p for p in paths.data_raw_dir.iterdir() if p.suffix.lower() in _EXTRACTORS
    )
    skipped = sorted(
        p.name for p in paths.data_raw_dir.iterdir()
        if p.is_file() and p.suffix.lower() not in _EXTRACTORS
    )

    result = DiffResult(manifest=manifest, skipped_files=skipped)

    for path in raw_files:
        current_hash = file_hash(path)
        entry = manifest["files"].get(path.name)
        cache_path = _processed_path(paths.data_processed_dir, path.name)

        # Reuse cached chunks only if both the file's contents and the chunking
        # settings that produced them are unchanged -- otherwise editing
        # ChunkingConfig would silently keep serving chunks built the old way.
        chunking_unchanged = entry is not None and entry.get("chunking_signature") == current_chunking_signature
        if entry and entry["hash"] == current_hash and chunking_unchanged and cache_path.exists():
            with open(cache_path, "rb") as f:
                chunks = pickle.load(f)
            result.reused_files.append(path.name)
        else:
            documents = _EXTRACTORS[path.suffix.lower()](path)
            chunks = [
                chunk
                for document in documents
                for chunk in chunk_document(document, chunking_config)
            ]
            with open(cache_path, "wb") as f:
                pickle.dump(chunks, f)
            record_file(manifest, path.name, current_hash, len(chunks), current_chunking_signature)
            result.new_or_changed_files.append(path.name)
            result.new_chunks.extend(chunks)

        result.all_chunks.extend(chunks)

    # Drop manifest/cache entries for files no longer present in data/raw/.
    removed_filenames = set(manifest["files"]) - {p.name for p in raw_files}
    for filename in removed_filenames:
        del manifest["files"][filename]
        _processed_path(paths.data_processed_dir, filename).unlink(missing_ok=True)
    result.removed_files = sorted(removed_filenames)

    return result


def main() -> None:
    paths = PathConfig()
    chunking_config = ChunkingConfig()
    retrieval_config = RetrievalConfig()

    result = diff_and_chunk(paths, chunking_config, retrieval_config)

    print(f"Files processed (new/changed): {len(result.new_or_changed_files)}")
    print(f"Files reused from cache: {len(result.reused_files)}")
    if result.removed_files:
        print(f"Files removed from manifest (no longer in data/raw/): {result.removed_files}")
    if result.skipped_files:
        print(f"Skipped (unsupported extension): {result.skipped_files}")
    print(f"Total chunks indexed: {len(result.all_chunks)}")

    print("Building hybrid (dense + BM25) index...")
    retriever = HybridRRFRetriever(retrieval_config)
    retriever.build_index(result.all_chunks)
    retriever.save_index()
    save_manifest(retrieval_config.index_dir, result.manifest)
    print(f"Index and manifest saved to {retrieval_config.index_dir}")


if __name__ == "__main__":
    main()
