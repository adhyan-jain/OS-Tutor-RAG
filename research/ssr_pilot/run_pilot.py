"""
Generation runner for the SSR pilot (resumable; one model at a time).

    python -m research.ssr_pilot.run_pilot --attackers              # pseudo-models, no LLM
    python -m research.ssr_pilot.run_pilot --models qwen3:8b,...    # real models via Ollama

Every call is appended to <runs>/<model>.jsonl with the prompt hash, settings
and raw response, and skipped if its key is already present. A manifest with
the frozen-file hashes is written first.
"""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from typing import Dict, List

import requests

from research.ssr_pilot import attackers as A
from research.ssr_pilot import render
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.worlds import WORLD_DIR, load_worlds

ROOT = "research/ssr_pilot"
RUNS = f"{ROOT}/runs"
RUNS_DRY = f"{ROOT}/runs_dry"
MANIFESTS = f"{ROOT}/manifests"
PREREG = "docs/research/SSR_PILOT_PREREG.md"
MODELS = ["qwen3:8b", "llama3.1:8b", "gemma2:9b", "mistral:7b-instruct"]
SEEDS = (0, 1, 2, 3)
SETTINGS = {"temperature": 0.7, "top_p": 0.95, "num_ctx": 4096, "num_predict": 600}  # frozen (prereg §2)
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe(name: str) -> str:
    return name.replace(":", "_").replace("/", "_")


def call_key(model: str, prompt_sha: str, seed: int) -> str:
    return hashlib.sha256(json.dumps([model, prompt_sha, seed, SETTINGS], sort_keys=True).encode()).hexdigest()


def tasks(worlds: List[Dict]) -> List[Dict]:
    out = []
    for w in worlds:
        for v in render.VARIANTS:
            r = render.render_variant(w, v)
            for s in SEEDS:
                out.append({"world": w, "variant": v, "seed": s, "rendered": r})
    return out


def manifest(kind: str, models: List[str], worlds: List[Dict]) -> Dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    ps = hashlib.sha256("".join(t["rendered"]["prompt_sha256"] for t in tasks(worlds)).encode()).hexdigest()
    digests = {}
    try:
        for m in requests.get(f"{OLLAMA}/api/tags", timeout=10).json()["models"]:
            digests[m["name"]] = m.get("digest")
    except requests.RequestException:
        pass
    return {"kind": kind, "created": datetime.datetime.now().isoformat(timespec="seconds"), "git_head": head,
            "models": {m: digests.get(m) or digests.get(f"{m}:latest") for m in models},
            "settings": SETTINGS, "seeds": list(SEEDS), "variants": list(render.VARIANTS),
            "n_worlds": len(worlds), "n_calls_per_model": len(tasks(worlds)),
            "sha256": {"prereg": sha256_file(PREREG), "worlds_index": sha256_file(f"{WORLD_DIR}/_index.json"),
                       "render.py": sha256_file(f"{ROOT}/render.py"), "all_prompts": ps,
                       "oracle.py": sha256_file(f"{ROOT}/oracle.py"), "families.py": sha256_file(f"{ROOT}/families.py")}}


class Log:
    def __init__(self, path: str):
        self.path, self.keys = path, set()
        if os.path.exists(path):
            self.keys = {json.loads(l)["key"] for l in open(path) if l.strip()}

    def add(self, rec: Dict) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        self.keys.add(rec["key"])


def ollama_generate(model: str, prompt: str, seed: int) -> Dict:
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
            "options": {**SETTINGS, "seed": seed}}
    if model.startswith("qwen3"):
        body["think"] = False
    t0 = time.time()
    last = None
    for attempt in range(3):
        try:
            r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=900)
            r.raise_for_status()
            o = r.json()
            return {"response": o["message"]["content"], "done_reason": o.get("done_reason"),
                    "eval_count": o.get("eval_count"), "prompt_eval_count": o.get("prompt_eval_count"),
                    "latency_s": round(time.time() - t0, 2)}
        except requests.RequestException as e:
            last = e
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"ollama call failed 3x for {model}: {last}")


def run_model(model: str, worlds: List[Dict], log_dir: str) -> None:
    log = Log(f"{log_dir}/{safe(model)}.jsonl")
    todo = [t for t in tasks(worlds)
            if call_key(model, t["rendered"]["prompt_sha256"], t["seed"]) not in log.keys]
    print(f"[{model}] {len(todo)} to run ({len(log.keys)} cached)", flush=True)
    t0 = time.time()
    for i, t in enumerate(todo, 1):
        out = ollama_generate(model, t["rendered"]["prompt"], t["seed"])
        log.add({"key": call_key(model, t["rendered"]["prompt_sha256"], t["seed"]), "model": model,
                 "world": t["world"]["id"], "variant": t["variant"], "seed": t["seed"],
                 "prompt_sha256": t["rendered"]["prompt_sha256"],
                 "ts": datetime.datetime.now().isoformat(timespec="seconds"), **out})
        if i % 25 == 0:
            per = (time.time() - t0) / i
            print(f"[{model}] {i}/{len(todo)} {per:.1f}s/call eta {per * (len(todo) - i) / 60:.0f} min", flush=True)


def run_attackers(worlds: List[Dict], log_dir: str) -> None:
    banks = {w["id"]: load_bank(w) for w in worlds}
    for name in A.GENERATORS:
        model = f"attacker:{name}"
        log = Log(f"{log_dir}/{safe(model)}.jsonl")
        for t in tasks(worlds):
            key = call_key(model, t["rendered"]["prompt_sha256"], t["seed"])
            if key in log.keys:
                continue
            text = A.generate(name, t["world"], banks[t["world"]["id"]], t["variant"], t["seed"])
            log.add({"key": key, "model": model, "world": t["world"]["id"], "variant": t["variant"],
                     "seed": t["seed"], "prompt_sha256": t["rendered"]["prompt_sha256"], "response": text,
                     "done_reason": "stop"})
        print(f"[{model}] done", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    ap.add_argument("--attackers", action="store_true")
    ap.add_argument("--limit-worlds", type=int, default=None, help="smoke test only")
    a = ap.parse_args(argv)
    worlds = load_worlds()[: a.limit_worlds] if a.limit_worlds else load_worlds()
    os.makedirs(MANIFESTS, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    if a.attackers:
        m = manifest("attackers", [f"attacker:{g}" for g in A.GENERATORS], worlds)
        json.dump(m, open(f"{MANIFESTS}/attackers_{stamp}.json", "w"), indent=1)
        run_attackers(worlds, RUNS_DRY)
    if a.models:
        models = a.models.split(",")
        m = manifest("llm", models, worlds)
        json.dump(m, open(f"{MANIFESTS}/llm_{stamp}.json", "w"), indent=1)
        print(json.dumps(m["sha256"], indent=1))
        for model in models:
            run_model(model, worlds, RUNS)


if __name__ == "__main__":
    main(sys.argv[1:])
