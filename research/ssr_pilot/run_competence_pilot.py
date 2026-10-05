"""
Competence-filter mini-pilot runner (stated-convention arm, stronger models).

    python -m research.ssr_pilot.run_competence_pilot --status             # print the gate state and exit
    python -m research.ssr_pilot.run_competence_pilot --smoke              # 9 calls per model
    python -m research.ssr_pilot.run_competence_pilot                      # full run, one model at a time

Conditions are identical to the stated-convention arm (same worlds, prompts,
seeds, settings). What this adds:
  * a GPU/RAM gate: if another job holds the GPU or RAM is short, poll every
    300 s and start only when free; re-check every 25 calls;
  * resource logging to results/competence_pilot/resource_log.md;
  * crash handling: on an Ollama failure wait, then resume from the JSONL
    (no duplicate trials);
  * a manifest stamped with the SHA-256 of the frozen decision rubric.
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

from research.ssr_pilot import render
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.run_pilot import (MANIFESTS, Log, call_key, manifest, ollama_generate, safe,
                                          sha256_file)
from research.ssr_pilot.run_stated_convention import tasks
from research.ssr_pilot.worlds import load_worlds

ROOT = "research/ssr_pilot"
RUNS = f"{ROOT}/runs_competence_pilot"
OUT = f"{ROOT}/results/competence_pilot"
RUBRIC = f"{OUT}/decision_rubric.md"
SELECTION = f"{OUT}/model_selection.md"
RESOURCE_LOG = f"{OUT}/resource_log.md"

MODELS = ["gemma3:12b", "olmo2:7b"]
MODEL_GB = {"gemma3:12b": 2.0, "olmo2:7b": 2.0}
POLL_S = 5  # re-poll the gate every 5 seconds
MAX_WAIT_S = 12 * 3600
CHECK_EVERY = 25
RAM_HEADROOM_GB = 1.5
IDLE_VRAM_MIB = 1500  # with none of our models resident, more than this means someone else holds the GPU
IDLE_UTIL = 20
FOREIGN_PATTERNS = ["ssr_bench"]  # the other project that shares this GPU / Ollama server
MAX_RESTARTS = 3
SMOKE_WORLDS = ["sched_01", "sync_01", "bank_01"]


# ---------------------------------------------------------------- system state

def sh(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def ram_available_gb() -> float:
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    return 0.0


def gpu_state() -> Dict:
    row = sh("nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits").strip()
    used, total, util = (float(x) for x in row.split(",")) if row else (0.0, 0.0, 0.0)
    return {"vram_used_mib": used, "vram_total_mib": total, "util_pct": util}


def ollama_loaded() -> List[str]:
    lines = sh("ollama ps").strip().splitlines()[1:]
    return [l.split()[0] for l in lines if l.strip()]


def installed() -> List[str]:
    lines = sh("ollama list").strip().splitlines()[1:]
    return [l.split()[0] for l in lines if l.strip()]


def download_pending() -> bool:
    """True while any `ollama pull` is running (the bracket keeps this grep from matching itself)."""
    return bool(sh("ps -eo args | grep '[o]llama pull'").strip())


def foreign_jobs() -> List[str]:
    out = []
    for line in sh("ps -eo pid,args").splitlines():
        if any(p in line for p in FOREIGN_PATTERNS) and "run_competence_pilot" not in line and "grep" not in line:
            out.append(line.strip()[:120])
    return out


def decide_busy(model: str, need_gb: float, jobs: List[str], loaded: List[str], gpu: Dict, ram_gb: float) -> List[str]:
    """Empty list = free. Pure function of its inputs so the gate logic can be unit-tested."""
    reasons = []
    if jobs:
        reasons.append(f"foreign job running: {jobs[0]}")
    foreign_models = [m for m in loaded if m != model]
    if foreign_models:
        reasons.append(f"foreign model resident in Ollama: {foreign_models}")
    if model not in loaded and not foreign_models:
        if gpu["vram_used_mib"] > IDLE_VRAM_MIB:
            reasons.append(f"GPU memory in use by another process: {gpu['vram_used_mib']:.0f} MiB")
        if gpu["util_pct"] > IDLE_UTIL:
            reasons.append(f"GPU utilisation {gpu['util_pct']:.0f}% from another process")
    if ram_gb < need_gb and model not in loaded:
        reasons.append(f"RAM available {ram_gb:.1f} GB < required {need_gb:.1f} GB")
    return reasons


def busy_reasons(model: str, need_gb: float) -> List[str]:
    return decide_busy(model, need_gb, foreign_jobs(), ollama_loaded(), gpu_state(), ram_available_gb())


def snapshot() -> str:
    g = gpu_state()
    return (f"VRAM {g['vram_used_mib']:.0f}/{g['vram_total_mib']:.0f} MiB, util {g['util_pct']:.0f}%, "
            f"RAM avail {ram_available_gb():.1f} GB, ollama ps {ollama_loaded() or '-'}")


def log_event(msg: str) -> None:
    os.makedirs(OUT, exist_ok=True)
    new = not os.path.exists(RESOURCE_LOG)
    with open(RESOURCE_LOG, "a") as f:
        if new:
            f.write("# Competence pilot — resource log\n\nTimestamps are local time. One line per event.\n\n")
        f.write(f"- `{datetime.datetime.now().isoformat(timespec='seconds')}` {msg} — {snapshot()}\n")
    print(msg, flush=True)


def wait_until_free(model: str, need_gb: float, label: str) -> bool:
    t0, polls = time.time(), 0
    while True:
        reasons = busy_reasons(model, need_gb)
        if not reasons:
            log_event(f"[{model}] gate free ({label}) after {polls} busy poll(s)")
            return True
        log_event(f"[{model}] gate BUSY ({label}), poll {polls}: " + "; ".join(reasons))
        if time.time() - t0 > MAX_WAIT_S:
            log_event(f"[{model}] gave up waiting after {MAX_WAIT_S / 3600:.0f} h: " + "; ".join(reasons))
            return False
        time.sleep(POLL_S)
        polls += 1


# ---------------------------------------------------------------- pre-flight and manifest

def preflight(worlds: List[Dict]) -> None:
    """Every prompt states the convention and none contains the reference trace."""
    for w in worlds:
        ref = load_bank(w)["reference"]
        for v in render.VARIANTS:
            r = render.render_variant(w, v, stated_convention=True)
            assert "Convention for tie-breaking:" in r["prompt"], (w["id"], v)
            assert f"TRACE: {render.reference_text(w, ref, r)}" not in r["prompt"], (w["id"], v)


def build_manifest(models: List[str], worlds: List[Dict]) -> Dict:
    m = manifest("llm_competence_pilot", models, worlds)
    prompts = hashlib.sha256("".join(t["rendered"]["prompt_sha256"] for t in tasks(worlds)).encode()).hexdigest()
    m["sha256"]["all_prompts"] = prompts  # stated-convention prompts, not the plain ones
    m["sha256"]["decision_rubric"] = sha256_file(RUBRIC)
    m["sha256"]["model_selection"] = sha256_file(SELECTION)
    m["stated_convention"] = True
    m["competence_pilot"] = True
    m["model_order"] = models
    return m


# ---------------------------------------------------------------- running

def select_todo(model: str, worlds: List[Dict], log: Log, smoke: bool) -> List[Dict]:
    todo = [t for t in tasks(worlds) if call_key(model, t["rendered"]["prompt_sha256"], t["seed"]) not in log.keys]
    if smoke:  # one world per mechanism family, all three variants, seed 0 (9 calls)
        todo = [t for t in todo if t["seed"] == 0 and t["world"]["id"] in SMOKE_WORLDS]
    return todo


def run_model(model: str, worlds: List[Dict], smoke: bool) -> str:
    """Returns 'done' | 'not_installed' | 'gave_up' | 'failed'."""
    while model not in installed():
        if not download_pending():
            log_event(f"[{model}] NOT INSTALLED and no download in progress — skipping")
            return "not_installed"
        log_event(f"[{model}] waiting for its download to finish")
        time.sleep(POLL_S)
    need = MODEL_GB[model] + RAM_HEADROOM_GB
    log = Log(f"{RUNS}/{safe(model)}.jsonl")
    todo = select_todo(model, worlds, log, smoke)
    if not todo:
        log_event(f"[{model}] nothing to run ({len(log.keys)} cached)")
        return "done"
    if not wait_until_free(model, need, "before load"):
        return "gave_up"
    log_event(f"[{model}] START {'smoke' if smoke else 'full'}: {len(todo)} to run, {len(log.keys)} cached")
    t0, restarts, i = time.time(), 0, 0
    while i < len(todo):
        if i and i % CHECK_EVERY == 0:
            wait_until_free(model, need, f"checkpoint {i}")
            per = (time.time() - t0) / i
            log_event(f"[{model}] {i}/{len(todo)} {per:.1f}s/call eta {per * (len(todo) - i) / 60:.0f} min")
        t = todo[i]
        try:
            out = ollama_generate(model, t["rendered"]["prompt"], t["seed"])
        except SystemExit as e:  # three failed attempts inside ollama_generate
            restarts += 1
            log_event(f"[{model}] Ollama failure #{restarts} at call {i}: {e}")
            if restarts > MAX_RESTARTS:
                log_event(f"[{model}] FAILED after {MAX_RESTARTS} restarts; completed outputs preserved")
                return "failed"
            time.sleep(60)
            continue  # retry the same call; the JSONL already holds everything finished
        log.add({"key": call_key(model, t["rendered"]["prompt_sha256"], t["seed"]), "model": model,
                 "world": t["world"]["id"], "variant": t["variant"], "seed": t["seed"],
                 "prompt_sha256": t["rendered"]["prompt_sha256"], "stated_convention": True,
                 "competence_pilot": True, "ts": datetime.datetime.now().isoformat(timespec="seconds"), **out})
        i += 1
    per = (time.time() - t0) / max(1, len(todo))
    log_event(f"[{model}] END {'smoke' if smoke else 'full'}: {len(todo)} calls, {per:.1f}s/call, "
              f"{(time.time() - t0) / 60:.0f} min")
    sh(f"ollama stop {model}")  # free VRAM/RAM before the next model
    return "done"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--smoke", action="store_true", help="3 worlds (one per family) x 3 variants x seed 0 per model")
    ap.add_argument("--status", action="store_true", help="print the gate state and exit")
    a = ap.parse_args(argv)
    models = a.models.split(",")
    if a.status:
        print(json.dumps({"busy_reasons": {m: busy_reasons(m, MODEL_GB.get(m, 9.0) + RAM_HEADROOM_GB) for m in models},
                          "installed": [m for m in models if m in installed()], "snapshot": snapshot()}, indent=1))
        return
    worlds = load_worlds()
    preflight(worlds)
    os.makedirs(MANIFESTS, exist_ok=True)
    os.makedirs(RUNS, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    m = build_manifest(models, worlds)
    m["smoke"] = a.smoke
    json.dump(m, open(f"{MANIFESTS}/llm_competence_pilot_{'smoke_' if a.smoke else ''}{stamp}.json", "w"), indent=1)
    status = {}
    for model in models:
        status[model] = run_model(model, worlds, a.smoke)
    log_event("STATUS " + json.dumps(status))
    json.dump(status, open(f"{OUT}/run_status{'_smoke' if a.smoke else ''}.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
