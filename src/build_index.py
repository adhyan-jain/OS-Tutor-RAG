"""Incrementally build/update the retrieval index from data/raw/.

Tracks ingested files by content hash in data/index/manifest.json. On each
run, only new or changed files are re-extracted and re-chunked (cached
per-file chunk pickles live in data/processed/); unchanged files are loaded
from cache. The full combined chunk set is then used to rebuild and save the
hybrid (dense + BM25) index, since FAISS-flat/BM25 don't support incremental
merge cheaply at this corpus size.

Run this whenever new course material is dropped into data/raw/:
    PYTHONPATH=. .venv/bin/python -m src.build_index
"""

from __future__ import annotations

import pickle
from pathlib import Path

from src.chunking import chunk_document
from src.config import ChunkingConfig, PathConfig, RetrievalConfig
from src.ingestion.extract_docx import extract_docx
from src.ingestion.extract_pdf import extract_pdf
from src.ingestion.extract_ppt import extract_ppt
from src.ingestion.manifest import file_hash, load_manifest, record_file, save_manifest
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


def main() -> None:
    paths = PathConfig()
    chunking_config = ChunkingConfig()
    retrieval_config = RetrievalConfig()

    paths.data_processed_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(retrieval_config.index_dir)

    raw_files = sorted(
        p for p in paths.data_raw_dir.iterdir() if p.suffix.lower() in _EXTRACTORS
    )
    skipped = sorted(
        p.name for p in paths.data_raw_dir.iterdir()
        if p.is_file() and p.suffix.lower() not in _EXTRACTORS
    )

    all_chunks: list[Chunk] = []
    new_or_changed = 0
    reused = 0

    for path in raw_files:
        current_hash = file_hash(path)
        entry = manifest["files"].get(path.name)
        cache_path = _processed_path(paths.data_processed_dir, path.name)

        if entry and entry["hash"] == current_hash and cache_path.exists():
            with open(cache_path, "rb") as f:
                chunks = pickle.load(f)
            reused += 1
        else:
            documents = _EXTRACTORS[path.suffix.lower()](path)
            chunks = [
                chunk
                for document in documents
                for chunk in chunk_document(document, chunking_config)
            ]
            with open(cache_path, "wb") as f:
                pickle.dump(chunks, f)
            record_file(manifest, path.name, current_hash, len(chunks))
            new_or_changed += 1

        all_chunks.extend(chunks)

    # Drop manifest/cache entries for files no longer present in data/raw/.
    removed_filenames = set(manifest["files"]) - {p.name for p in raw_files}
    for filename in removed_filenames:
        del manifest["files"][filename]
        _processed_path(paths.data_processed_dir, filename).unlink(missing_ok=True)

    print(f"Files processed (new/changed): {new_or_changed}")
    print(f"Files reused from cache: {reused}")
    if removed_filenames:
        print(f"Files removed from manifest (no longer in data/raw/): {sorted(removed_filenames)}")
    if skipped:
        print(f"Skipped (unsupported extension): {skipped}")
    print(f"Total chunks indexed: {len(all_chunks)}")

    print("Building hybrid (dense + BM25) index...")
    retriever = HybridRRFRetriever(retrieval_config)
    retriever.build_index(all_chunks)
    retriever.save_index()
    save_manifest(retrieval_config.index_dir, manifest)
    print(f"Index and manifest saved to {retrieval_config.index_dir}")


if __name__ == "__main__":
    main()
