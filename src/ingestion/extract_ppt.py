"""Extract text and metadata from PowerPoint (.ppt/.pptx) files into Documents."""

from __future__ import annotations

from pathlib import Path

from src.schemas import Document


def extract_ppt(file_path: Path) -> Document:
    """Extract a Document from a single PPT/PPTX file.

    Args:
        file_path: Path to the .ppt or .pptx file.

    Returns:
        A Document containing the concatenated slide text and slide-level metadata.
    """
    raise NotImplementedError
