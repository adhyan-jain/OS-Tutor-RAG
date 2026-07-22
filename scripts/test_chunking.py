"""Manual smoke test for chunking strategies against ingested data/raw/ files."""

from __future__ import annotations

from pathlib import Path

from src.chunking import chunk_document
from src.config import ChunkingConfig
from src.ingestion.extract_docx import extract_docx
from src.ingestion.extract_ppt import extract_ppt

RAW_DIR = Path("data/raw")


def _print_sample(label: str, chunks) -> None:
    print(f"  sample ({label}, {len(chunks)} chunks):")
    for c in chunks[:2]:
        print(f"    chunk_id: {c.chunk_id}")
        print(f"    text:     {c.text[:150]!r}")
        print(f"    metadata: {c.metadata}")


def main() -> None:
    if not RAW_DIR.exists():
        print(f"{RAW_DIR} does not exist yet — add sample .pptx/.docx files there and re-run.")
        return

    pptx_files = sorted(RAW_DIR.glob("*.pptx"))
    docx_files = sorted(RAW_DIR.glob("*.docx"))

    if not pptx_files and not docx_files:
        print(f"No .pptx or .docx files found in {RAW_DIR} — add sample files and re-run.")
        return

    config = ChunkingConfig()

    first_pptx_chunks = None
    for path in pptx_files:
        doc = extract_ppt(path)
        chunks = chunk_document(doc, config)
        print(f"{path.name}: {len(chunks)} chunks (structure_aware, pptx)")
        if first_pptx_chunks is None:
            first_pptx_chunks = chunks

    first_docx_chunks = None
    for path in docx_files:
        docs = extract_docx(path)
        total = 0
        for doc in docs:
            chunks = chunk_document(doc, config)
            total += len(chunks)
            if first_docx_chunks is None and chunks:
                first_docx_chunks = chunks
        print(f"{path.name}: {total} chunks across {len(docs)} section(s) (structure_aware, docx)")

    print()
    if first_pptx_chunks:
        _print_sample("pptx", first_pptx_chunks)
    if first_docx_chunks:
        _print_sample("docx", first_docx_chunks)


if __name__ == "__main__":
    main()
