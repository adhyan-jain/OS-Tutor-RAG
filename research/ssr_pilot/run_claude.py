"""
Generation runner for the RCR Claude-family follow-up (resumable, parallel).

    python -m research.ssr_pilot.run_claude --models claude-sonnet-5-5,claude-haiku-5-5

Same worlds, variants, repeats and prompts as run_pilot.py; the model is called through
headless `claude -p` with no tools, a minimal system prompt, thinking off and no
settings/hooks/MCP, from an empty directory. Records go to runs_claude/<model>.jsonl
with the run_pilot schema, so the frozen original runs/ directory is untouched.
Plan and hypotheses: docs/research/RCR_CLAUDE_FAMILY_PREREG.md.
"""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from research.ssr_pilot.run_pilot import MANIFESTS, ROOT, Log, safe, sha256_file, tasks
from research.ssr_pilot.worlds import WORLD_DIR, load_worlds

RUNS_CLAUDE = f"{ROOT}/runs_claude"
PREREG = "docs/research/RCR_CLAUDE_FAMILY_PREREG.md"
MODELS = ["claude-sonnet-5-5", "claude-haiku-5-5", "claude-sonnet-4-5", "claude-haiku-4-5"]
SYSTEM = "You are a helpful assistant."
SETTINGS = {"interface": "claude -p", "tools": "none", "thinking": "off", "system": SYSTEM,
            "sampling": "provider defaults (temperature/top_p/max_tokens not controllable)"}
FLAGS = ["--tools", "", "--system-prompt", SYSTEM, "--setting-sources", "", "--settings",
         '{"disableAllHooks":true}', "--disable-slash-commands", "--no-session-persistence",
         "--strict-mcp-config", "--exclude-dynamic-system-prompt-sections", "--output-format", "json"]
RATE_LIMIT_MARKERS = ("rate limit", "usage limit", "overloaded", "429", "529")


def call_key(model: str, prompt_sha: str, seed: int) -> str:
    return hashlib.sha256(json.dumps([model, prompt_sha, seed, SETTINGS], sort_keys=True).encode()).hexdigest()


def claude_generate(model: str, prompt: str, cwd: str) -> Dict:
    env = {**os.environ, "MAX_THINKING_TOKENS": "0"}
    t0 = time.time()
    last = ""
    for attempt in range(5):
        p = subprocess.run(["claude", "-p", "--model", model, *FLAGS], input=prompt, capture_output=True,
                           text=True, cwd=cwd, env=env, timeout=600)
        try:
            o = json.loads(p.stdout)
            if not o.get("is_error"):
                return {"response": o["result"],
                        "done_reason": "length" if o.get("stop_reason") == "max_tokens" else "stop",
                        "eval_count": o["usage"]["output_tokens"], "cost_usd": o.get("total_cost_usd"),
                        "latency_s": round(time.time() - t0, 2)}
            last = str(o.get("result"))
        except (json.JSONDecodeError, KeyError):
            last = (p.stdout + p.stderr)[:300]
        limited = any(m in last.lower() for m in RATE_LIMIT_MARKERS)
        time.sleep(90 if limited else 5 * (attempt + 1))
    raise RuntimeError(f"{model}: 5 failed attempts, last: {last[:200]}")


def run_model(model: str, worlds: List[Dict], workers: int, cwd: str) -> int:
    log = Log(f"{RUNS_CLAUDE}/{safe(model)}.jsonl")
    todo = [t for t in tasks(worlds) if call_key(model, t["rendered"]["prompt_sha256"], t["seed"]) not in log.keys]
    print(f"[{model}] {len(todo)} to run ({len(log.keys)} cached)", flush=True)
    lock, failures, done, t0 = threading.Lock(), [], [0], time.time()

    def work(t):
        out = claude_generate(model, t["rendered"]["prompt"], cwd)
        rec = {"key": call_key(model, t["rendered"]["prompt_sha256"], t["seed"]), "model": model,
               "world": t["world"]["id"], "variant": t["variant"], "seed": t["seed"],
               "prompt_sha256": t["rendered"]["prompt_sha256"],
               "ts": datetime.datetime.now().isoformat(timespec="seconds"), **out}
        with lock:
            log.add(rec)
            done[0] += 1
            if done[0] % 24 == 0:
                per = (time.time() - t0) / done[0]
                print(f"[{model}] {done[0]}/{len(todo)} {per:.1f}s/call eta {per * (len(todo) - done[0]) / 60:.0f} min",
                      flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, t): t for t in todo}
        for f in as_completed(futs):
            try:
                f.result()
            except Exception as e:  # permanent failure: reported, picked up on rerun
                failures.append(f"{futs[f]['world']['id']}/{futs[f]['variant']}/{futs[f]['seed']}: {e}")
    if failures:
        print(f"[{model}] {len(failures)} permanent failures (rerun to retry): {failures[:3]}", flush=True)
    return len(failures)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit-worlds", type=int, default=None, help="smoke test only")
    a = ap.parse_args(argv)
    worlds = load_worlds()[: a.limit_worlds] if a.limit_worlds else load_worlds()
    models = a.models.split(",")
    os.makedirs(MANIFESTS, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    ver = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    ps = hashlib.sha256("".join(t["rendered"]["prompt_sha256"] for t in tasks(worlds)).encode()).hexdigest()
    m = {"kind": "claude_family", "created": datetime.datetime.now().isoformat(timespec="seconds"),
         "git_head": head, "claude_cli": ver, "models": models, "settings": SETTINGS,
         "n_worlds": len(worlds), "n_calls_per_model": len(tasks(worlds)),
         "sha256": {"prereg": sha256_file(PREREG), "worlds_index": sha256_file(f"{WORLD_DIR}/_index.json"),
                    "render.py": sha256_file(f"{ROOT}/render.py"), "all_prompts": ps,
                    "oracle.py": sha256_file(f"{ROOT}/oracle.py"), "families.py": sha256_file(f"{ROOT}/families.py")}}
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    json.dump(m, open(f"{MANIFESTS}/claude_{stamp}.json", "w"), indent=1)
    print(json.dumps(m["sha256"], indent=1), flush=True)
    with tempfile.TemporaryDirectory() as cwd:
        bad = sum(run_model(model, worlds, a.workers, cwd) for model in models)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
