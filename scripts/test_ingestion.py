"""Manual smoke test for the PPT/DOCX extractors against files in data/raw/."""

from __future__ import annotations

from pathlib import Path

from src.ingestion.extract_docx import extract_docx
from src.ingestion.extract_ppt import extract_ppt

RAW_DIR = Path("data/raw")


def _print_sample(label: str, doc) -> None:
    print(f"  sample ({label}):")
    print(f"    doc_id:   {doc.doc_id}")
    print(f"    text:     {doc.text[:300]!r}")
    print(f"    metadata: {doc.metadata}")


def main() -> None:
    if not RAW_DIR.exists():
        print(f"{RAW_DIR} does not exist yet — add sample .pptx/.docx files there and re-run.")
        return

    pptx_files = sorted(RAW_DIR.glob("*.pptx"))
    docx_files = sorted(RAW_DIR.glob("*.docx"))

    if not pptx_files and not docx_files:
        print(f"No .pptx or .docx files found in {RAW_DIR} — add sample files and re-run.")
        return

    first_ppt_doc = None
    for path in pptx_files:
        doc = extract_ppt(path)
        print(f"{path.name}: 1 Document ({doc.metadata['slide_count']} slides)")
        if first_ppt_doc is None:
            first_ppt_doc = doc

    first_docx_doc = None
    for path in docx_files:
        docs = extract_docx(path)
        print(f"{path.name}: {len(docs)} Document(s)")
        if first_docx_doc is None and docs:
            first_docx_doc = docs[0]

    print()
    if first_ppt_doc is not None:
        _print_sample("pptx", first_ppt_doc)
    if first_docx_doc is not None:
        _print_sample("docx", first_docx_doc)


if __name__ == "__main__":
    main()
