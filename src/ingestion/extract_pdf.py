"""Extract text and metadata from PDF files into Documents."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from src.schemas import Document


def extract_pdf(file_path: Path) -> Document:
    """Extract a Document from a single PDF file.

    Each page's extracted text is captured as a separate entry in
    ``metadata["pages"]``, mirroring extract_ppt.py's per-slide structure.
    The Document's ``text`` is the concatenation of all page texts.

    Args:
        file_path: Path to the .pdf file.

    Returns:
        A Document containing the concatenated page text and page-level metadata.
    """
    reader = PdfReader(file_path)

    pages_metadata: list[dict[str, object]] = []
    text_parts: list[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        pages_metadata.append({"page_number": page_number, "text": page_text})
        if page_text:
            text_parts.append(page_text)

    return Document(
        doc_id=file_path.stem,
        source_path=str(file_path),
        text="\n".join(text_parts),
        metadata={
            "source_type": "pdf",
            "page_count": len(reader.pages),
            "pages": pages_metadata,
        },
    )
