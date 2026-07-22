"""Extract text and metadata from Word (.docx) files into Documents."""

from __future__ import annotations

from pathlib import Path

from src.schemas import Document


def extract_docx(file_path: Path) -> Document:
    """Extract a Document from a single DOCX file.

    Args:
        file_path: Path to the .docx file.

    Returns:
        A Document containing the concatenated paragraph text and metadata.
    """
    raise NotImplementedError
