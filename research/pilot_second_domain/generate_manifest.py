"""
Generates the cryptographic provenance manifest for the second-domain Blocks World confirmatory study.
"""

import datetime
import hashlib
import json
import os
import subprocess
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest() -> dict:
    git_head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    git_status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout.strip()

    # Query Ollama model digests
    digests = {}
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10).json()
        for m in r.get("models", []):
            digests[m["name"]] = m.get("digest")
    except Exception as e:
        digests["error"] = str(e)

    models = ["qwen3:8b", "gemma2:9b", "llama3.1:8b", "mistral:7b-instruct"]
    settings = {"temperature": 0.7, "top_p": 0.9, "num_predict": 512}

    files_to_hash = [
        "research/docs/SECOND_DOMAIN_PREREGISTRATION.md",
        "research/pilot_second_domain/blocks_world_tasks.py",
        "research/pilot_second_domain/blocks_world_rcr_pilot.py",
        "research/pilot_second_domain/run_blocks_world_confirmatory.py",
        "research/pilot_second_domain/analyze_blocks_world_confirmatory.py",
        "research/pilot_second_domain/analyze_blocks_world_supplementary.py",
        "research/pilot_second_domain/verify_reference_spaces.py",
        "research/pilot_second_domain/results/blocks_world_confirmatory_as_executed_20261013.json",
        "research/pilot_second_domain/results/blocks_world_supplementary.json",
        "research/pilot_second_domain/results/reference_space_verification.json",
        "tests/test_second_domain_pilot.py",
        "tests/test_second_domain_confirmatory.py",
    ]

    # Add run files if they exist
    for m in models:
        safe_name = m.replace(":", "_").replace("/", "_")
        p = f"research/pilot_second_domain/runs/{safe_name}.jsonl"
        if os.path.exists(p):
            files_to_hash.append(p)

    results_file = "research/pilot_second_domain/results/blocks_world_confirmatory.json"
    if os.path.exists(results_file):
        files_to_hash.append(results_file)

    manifest_data = {
        "domain": "Discrete_Classical_Planning_Blocks_World",
        "study_type": "Confirmatory_Preregistered_Replication",
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "git_commit": git_head,
        "git_status_clean": len(git_status) == 0,
        "environment": {
            "gpu": "NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)",
            "cuda_driver": "NVIDIA-SMI 615.71.09",
            "runtime": "Ollama local inference",
            "host_os": "Linux x86_64",
        },
        "models": {m: digests.get(m) for m in models},
        "generation_parameters": {
            "settings": settings,
            "variants": ["v0", "v1", "v2"],
            "seeds": [0, 1, 2, 3],
            "n_tasks": 24,
            "generations_per_task": 12,
            "generations_per_model": 288,
            "total_generations": 1152,
        },
        "sha256": {f: sha256_file(f) for f in files_to_hash if os.path.exists(f)},
    }

    out_path = "research/pilot_second_domain/manifest.json"
    with open(out_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_data


if __name__ == "__main__":
    m = generate_manifest()
    print("Manifest generated at research/pilot_second_domain/manifest.json")
