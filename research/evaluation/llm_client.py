"""
Ollama chat client with a resumable JSONL cache.

Every call is appended to research/results/raw/<model>.jsonl with the prompt
hash, decoding options and raw response, so all analysis is recomputed from
raw predictions. A call whose key is already in the file is never repeated,
which makes long runs resumable after interruption.
"""

import hashlib
import json
import os
import time
from typing import Dict, Optional

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OPTIONS = {"temperature": 0, "seed": 0, "num_ctx": 4096}  # frozen (PREREGISTRATION_V2 §4)
MAX_TOKENS = {"judge": 8, "generate": 400}


def safe_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def call_key(model: str, prompt: str, kind: str, replicate: int) -> str:
    blob = json.dumps([model, prompt, kind, replicate, OPTIONS, MAX_TOKENS[kind]], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


class RawLog:
    def __init__(self, path: str):
        self.path = path
        self.done: Dict[str, Dict] = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.strip():
                        rec = json.loads(line)
                        self.done[rec["key"]] = rec

    def append(self, rec: Dict) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        self.done[rec["key"]] = rec


def ollama_chat(model: str, prompt: str, kind: str, timeout: int = 300) -> Dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {**OPTIONS, "num_predict": MAX_TOKENS[kind]},
    }
    if model.startswith("qwen3"):
        body["think"] = False
    t0 = time.time()
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=timeout)
    r.raise_for_status()
    out = r.json()
    return {"response": out["message"]["content"], "latency_s": round(time.time() - t0, 3),
            "eval_count": out.get("eval_count"), "prompt_eval_count": out.get("prompt_eval_count"),
            "done_reason": out.get("done_reason")}


def model_available(model: str) -> Optional[str]:
    try:
        tags = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10).json()["models"]
    except requests.RequestException as e:
        return f"ollama unreachable: {e}"
    names = {m["name"] for m in tags}
    if model in names or f"{model}:latest" in names:
        return None
    return f"model {model} not pulled"
