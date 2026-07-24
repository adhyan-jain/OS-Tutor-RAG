"""Tracks which raw files have already been ingested/embedded, keyed by
content hash, so re-running the index build only reprocesses new or
changed files instead of the whole corpus."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MANIFEST_FILENAME = "manifest.json"


def file_hash(path: Path) -> str:
    """Compute a stable content hash for a file.

    Args:
        path: File to hash.

    Returns:
        Hex-encoded SHA-256 digest of the file's contents.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(index_dir: Path) -> dict[str, Any]:
    """Load the ingestion manifest from an index directory.

    Args:
        index_dir: Directory containing (or to contain) manifest.json.

    Returns:
        The manifest dict, with an empty "files" mapping if none exists yet.
    """
    manifest_path = index_dir / _MANIFEST_FILENAME
    if not manifest_path.exists():
        return {"files": {}}
    with open(manifest_path) as f:
        return json.load(f)


def save_manifest(index_dir: Path, manifest: dict[str, Any]) -> None:
    """Persist the ingestion manifest to an index directory.

    Args:
        index_dir: Directory to write manifest.json into.
        manifest: The manifest dict to save.
    """
    index_dir.mkdir(parents=True, exist_ok=True)
    with open(index_dir / _MANIFEST_FILENAME, "w") as f:
        json.dump(manifest, f, indent=2)


def record_file(manifest: dict[str, Any], filename: str, hash_: str, num_chunks: int) -> None:
    """Record/update a file's entry in the manifest (mutates in place).

    Args:
        manifest: The manifest dict (as returned by load_manifest).
        filename: The raw file's name (relative to data/raw/).
        hash_: The file's current content hash.
        num_chunks: Number of chunks produced from this file.
    """
    manifest["files"][filename] = {
        "hash": hash_,
        "num_chunks": num_chunks,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
