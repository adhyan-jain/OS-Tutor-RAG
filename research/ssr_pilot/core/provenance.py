"""
Provenance recorder for RCR experiments.
"""

import datetime
import hashlib
import importlib.metadata
import os
import platform
import subprocess
import sys
from typing import Dict, List, Optional


_KEY_PACKAGES = ["numpy", "scipy", "pytest"]


def _package_versions() -> Dict[str, str]:
    versions = {}
    for pkg in _KEY_PACKAGES:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "unknown"
    return versions


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def capture_provenance(experiment_name: str, extra_meta: Optional[Dict] = None,
                       input_files: Optional[List[str]] = None) -> Dict:
    """
    Captures complete system, git, python, and runtime provenance metadata.
    `input_files` is an optional list of paths whose SHA-256 hashes are recorded.
    """
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        git_sha = "unknown"
        git_branch = "unknown"

    prov = {
        "experiment_name": experiment_name,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_sha": git_sha,
        "git_branch": git_branch,
        "python_version": sys.version,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "pid": os.getpid(),
        "package_versions": _package_versions(),
    }
    if input_files:
        prov["input_file_sha256"] = {p: sha256_file(p) for p in input_files if os.path.exists(p)}
    if extra_meta:
        prov.update(extra_meta)
    return prov
