"""Provenance stamp written into every results file (prereg freeze = SHA-256)."""

import datetime
import hashlib
import subprocess

PREREG_PATH = "docs/PREREGISTRATION_V2.md"
FROZEN_FILES = [PREREG_PATH, "research/evaluation/prompts.py", "research/benchmark/benchmark_v2.json"]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stamp() -> dict:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "research", "scripts", "docs"],
                                    capture_output=True, text=True).stdout.strip())
    except OSError:
        head, dirty = "unknown", True
    hashes = {}
    for p in FROZEN_FILES:
        try:
            hashes[p] = sha256_file(p)
        except FileNotFoundError:
            hashes[p] = None
    return {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "git_head": head,
        "worktree_dirty": dirty,
        "sha256": hashes,
    }
