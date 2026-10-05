"""
Generation runner for the stated-convention arm of the SSR pilot.

    python -m research.ssr_pilot.run_stated_convention --models qwen3:8b,llama3.1:8b,gemma2:9b,mistral:7b-instruct

Runs output to research/ssr_pilot/runs_stated_convention/<model>.jsonl
with the prompt hash, settings, and raw response.
"""

import argparse
import datetime
import json
import os
import sys
from typing import Dict, List

from research.ssr_pilot import render
from research.ssr_pilot.run_pilot import (
    call_key,
    manifest,
    ollama_generate,
    safe,
    Log,
    MANIFESTS,
    SETTINGS,
    SEEDS,
    MODELS,
)
from research.ssr_pilot.worlds import load_worlds

ROOT = "research/ssr_pilot"
RUNS_STATED_CONVENTION = f"{ROOT}/runs_stated_convention"


def tasks(worlds: List[Dict]) -> List[Dict]:
    out = []
    for w in worlds:
        for v in render.VARIANTS:
            r = render.render_variant(w, v, stated_convention=True)
            for s in SEEDS:
                out.append({"world": w, "variant": v, "seed": s, "rendered": r})
    return out


def run_model(model: str, worlds: List[Dict], log_dir: str) -> None:
    log = Log(f"{log_dir}/{safe(model)}.jsonl")
    todo = [
        t
        for t in tasks(worlds)
        if call_key(model, t["rendered"]["prompt_sha256"], t["seed"]) not in log.keys
    ]
    print(f"[{model}] {len(todo)} to run ({len(log.keys)} cached)", flush=True)
    t0 = datetime.datetime.now()
    for i, t in enumerate(todo, 1):
        out = ollama_generate(model, t["rendered"]["prompt"], t["seed"])
        log.add(
            {
                "key": call_key(model, t["rendered"]["prompt_sha256"], t["seed"]),
                "model": model,
                "world": t["world"]["id"],
                "variant": t["variant"],
                "seed": t["seed"],
                "prompt_sha256": t["rendered"]["prompt_sha256"],
                "stated_convention": True,
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                **out,
            }
        )
        if i % 25 == 0 or i == len(todo):
            elapsed = (datetime.datetime.now() - t0).total_seconds()
            per = elapsed / i
            print(
                f"[{model}] {i}/{len(todo)} {per:.1f}s/call eta {per * (len(todo) - i) / 60:.1f} min",
                flush=True,
            )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--limit-worlds", type=int, default=None, help="smoke test only")
    a = ap.parse_args(argv)

    worlds = load_worlds()[: a.limit_worlds] if a.limit_worlds else load_worlds()
    os.makedirs(MANIFESTS, exist_ok=True)
    os.makedirs(RUNS_STATED_CONVENTION, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")

    models = a.models.split(",")
    m = manifest("llm_stated_convention", models, worlds)
    m["stated_convention"] = True
    json.dump(m, open(f"{MANIFESTS}/llm_stated_convention_{stamp}.json", "w"), indent=1)
    print("Manifest created for stated-convention arm.")

    for model in models:
        run_model(model, worlds, RUNS_STATED_CONVENTION)


if __name__ == "__main__":
    main(sys.argv[1:])
