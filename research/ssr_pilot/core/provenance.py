"""
Provenance recorder for RCR experiments.
"""

import datetime
import os
import platform
import subprocess
import sys
from typing import Dict


def capture_provenance(experiment_name: str, extra_meta: Optional[Dict] = None) -> Dict:
    """
    Captures complete system, git, python, and runtime provenance metadata.
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
    }
    if extra_meta:
        prov.update(extra_meta)
    return prov
