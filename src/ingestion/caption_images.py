"""Caption diagrams/screenshots embedded in slide decks via a local
vision-capable Ollama model, so they become searchable text instead of being
invisible to the pipeline entirely.

Runs only at indexing time (src/build_index.py's diff_and_chunk, shared by
scripts/reindex.py), never in the live API path -- generation only ever reads
the chunk text this produces, it never calls a vision model itself.

A caption failure (vision model not pulled, Ollama unreachable, bad image
bytes) must not break ingestion: these are an enrichment, not a requirement,
so any error is caught and logged, leaving that one image simply uncaptioned
-- exactly the pre-existing behavior (images were invisible before this
module existed at all).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from pathlib import Path

import requests

from src.schemas import Document

logger = logging.getLogger("ingestion.caption_images")

_CAPTION_PROMPT = (
    "Describe this diagram from an operating systems course slide in 1-3 "
    "sentences, focused on what concept it illustrates and the key "
    "relationships or labels shown (e.g. what connects to what, what stage "
    "follows what). Be factual and specific -- name the actual labeled "
    "components -- since this caption will be indexed as searchable text "
    "alongside the slide."
)

_CACHE_FILENAME = "image_caption_cache.json"


def _cache_path(processed_dir: Path) -> Path:
    return processed_dir / _CACHE_FILENAME


def _load_cache(processed_dir: Path) -> dict[str, str]:
    path = _cache_path(processed_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(processed_dir: Path, cache: dict[str, str]) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    _cache_path(processed_dir).write_text(json.dumps(cache, indent=2), encoding="utf-8")


def caption_image_bytes(
    image_bytes: bytes,
    ollama_base_url: str,
    model_name: str,
    processed_dir: Path,
) -> str:
    """Caption one image, cached by content hash (independent of the
    file-level manifest, since an image's bytes can outlive edits made
    elsewhere in the same slide deck).

    Returns "" if captioning fails for any reason -- callers must treat that
    as "no caption available", not an error.
    """
    digest = hashlib.sha256(image_bytes).hexdigest()
    cache = _load_cache(processed_dir)
    if digest in cache:
        return cache[digest]

    try:
        response = requests.post(
            f"{ollama_base_url}/api/generate",
            json={
                "model": model_name,
                "prompt": _CAPTION_PROMPT,
                "images": [base64.b64encode(image_bytes).decode("ascii")],
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 200},
            },
            timeout=90,
        )
        response.raise_for_status()
        caption = response.json()["response"].strip()
    except Exception:
        logger.exception("Image captioning failed for one image -- leaving it uncaptioned.")
        return ""

    cache[digest] = caption
    _save_cache(processed_dir, cache)
    return caption


def enrich_pptx_images(
    document: Document,
    ollama_base_url: str,
    model_name: str,
    processed_dir: Path,
) -> None:
    """Caption every image on every slide of a pptx Document, appending each
    caption as a bullet on its slide (mutates document.metadata["slides"] in
    place).

    A captioned bullet ("[Diagram] ...") flows through exactly the same path
    as any other bullet in src/chunking/structure_aware.py's `_chunk_pptx` --
    it becomes one title-qualified, independently retrievable child chunk,
    the same as a table row. No chunking changes needed for this to work.
    """
    slides = document.metadata.get("slides", [])
    if not any(slide.get("image_blobs") for slide in slides):
        return  # common case (no images on this deck) -- skip entirely, no Ollama call

    for slide in slides:
        image_blobs = slide.pop("image_blobs", [])
        for blob in image_blobs:
            caption = caption_image_bytes(blob, ollama_base_url, model_name, processed_dir)
            if caption:
                slide.setdefault("bullets", []).append(f"[Diagram] {caption}")
