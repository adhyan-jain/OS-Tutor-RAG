"""
Experiment harness for PREREGISTRATION_V2 (E1 generation, E2 judging with
reference ablations, mitigation arm, noise floor, E3b secondary judge).

Backends
  ollama:<model>   real model via local Ollama (Phase B; needs user approval)
  mock:oracle      sanity baseline: validator as judge, random valid trace as generator
  mock:exact_match sanity baseline: accept iff candidate == reference; generates R1
  mock:random      sanity baseline: coin-flip judge, random candidate generator
Mock backends exist to dry-run the pipeline and check the analysis code.
They are labelled as sanity baselines everywhere and are never "models".
"""

import argparse
import datetime
import hashlib
import random
import re
import sys
import time
from typing import Dict, Iterable, List, Optional

from research.benchmark.generator import _system, load
from research.evaluation import prompts
from research.evaluation.llm_client import RawLog, call_key, model_available, ollama_chat, safe_name
from research.simulator.traces import format_events, format_schedule, normalize_schedule, parse_events, parse_schedule
from research.simulator.validators import validate

BENCH = "research/benchmark/benchmark_v2.json"
RAW_DIR = "research/results/raw"
MOCK_DIR = "research/results/raw_mock"

ID_E2 = [("R2", r) for r in ["none", "R1", "R3", "self", "R1_reworded", "I2", "irrelevant"]] + \
        [("I", r) for r in ["none", "R1", "R3"]] + [("R1", r) for r in ["none", "self", "R3"]]
OTHER_E2 = [("R2", r) for r in ["none", "R1", "R3", "self"]] + [("I", r) for r in ["none", "R1"]]
NOISE_FRACTION = 0.10
NOISE_SEED = 7


# ------------------------------------------------------------------ cells

def resolve_reference(inst, cand_key, ref_key):
    """-> (reference trace or None, reference style or None)."""
    if ref_key == "none":
        return None, None
    if ref_key == "self":
        return inst[cand_key], None
    if ref_key == "R1_reworded":
        return inst["R1"], ("table" if inst["format"] == "arrow" else "arrow")
    if ref_key == "irrelevant":
        return inst["irrelevant_ref"], None
    return inst[ref_key], None


def build_cells(instances: List[Dict]) -> List[Dict]:
    cells = []
    for inst in instances:
        cells.append({"cell_id": f"{inst['id']}|E1", "exp": "E1", "kind": "generate", "inst": inst,
                      "prompt": prompts.generation_prompt(inst)})
        conds = ID_E2 if inst["split"] == "id" else OTHER_E2
        for cand, ref in conds:
            r, style = resolve_reference(inst, cand, ref)
            cells.append({"cell_id": f"{inst['id']}|E2|{cand}|{ref}", "exp": "E2", "kind": "judge", "inst": inst,
                          "cand": cand, "ref": ref,
                          "prompt": prompts.judge_prompt(inst, inst[cand], r, style)})
        if inst["split"] == "id":
            for cand in ["R2", "I"]:
                cells.append({"cell_id": f"{inst['id']}|E2M|{cand}|R1", "exp": "E2M", "kind": "judge", "inst": inst,
                              "cand": cand, "ref": "R1",
                              "prompt": prompts.judge_prompt(inst, inst[cand], inst["R1"], mitigation=True)})
    return cells


def noise_cells(cells: List[Dict]) -> List[Dict]:
    judge = [c for c in cells if c["exp"] == "E2"]
    rng = random.Random(NOISE_SEED)
    pick = sorted(rng.sample(range(len(judge)), round(NOISE_FRACTION * len(judge))))
    return [{**judge[i], "exp": "NOISE", "replicate": 1, "cell_id": judge[i]["cell_id"] + "|rep1"} for i in pick]


def e3b_cells(instances_by_id: Dict[str, Dict], e1_outputs: Dict[str, Dict[str, Optional[tuple]]]) -> List[Dict]:
    """Secondary ranking: one fixed judge scores every model's E1 output with reference R1."""
    cells = []
    for gen_model, outs in sorted(e1_outputs.items()):
        for iid, trace in sorted(outs.items()):
            if trace is None:
                continue
            inst = instances_by_id[iid]
            cells.append({"cell_id": f"{iid}|E3B|{gen_model}", "exp": "E3B", "kind": "judge", "inst": inst,
                          "gen_model": gen_model,
                          "prompt": prompts.judge_prompt(inst, trace, inst["R1"])})
    return cells


# ------------------------------------------------------------------ parsing

_VERDICT = re.compile(r"\b(INVALID|VALID)\b")


def parse_judge(text: str) -> Optional[bool]:
    m = _VERDICT.search(text.upper())
    return None if m is None else m.group(1) == "VALID"


def parse_generation(inst: Dict, text: str):
    if inst["domain"] == "scheduling":
        names = [p["pid"] for p in inst["problem"]["processes"]]
        return parse_schedule(text, names)
    return parse_events(text, list(inst["problem"]["threads"]))


# ------------------------------------------------------------------ backends

def mock_response(backend: str, cell: Dict, rng: random.Random) -> str:
    inst = cell["inst"]
    fmt = format_schedule if inst["domain"] == "scheduling" else format_events
    if cell["kind"] == "generate":
        if backend == "oracle":
            tr = _system(inst["problem"]).sample(rng)
        elif backend == "exact_match":
            tr = inst["R1"]
        else:
            tr = inst[rng.choice(["R1", "R2", "I"])]
        return "TRACE: " + fmt(tr, "arrow")
    trace = inst[cell["cand"]] if "cand" in cell else _extract_candidate(cell)
    if backend == "oracle":
        return "VALID" if validate(inst["problem"], trace)[0] else "INVALID"
    if backend == "exact_match":
        ref = resolve_reference(inst, cell["cand"], cell["ref"])[0] if "cand" in cell else inst["R1"]
        if ref is None:
            return "INVALID"
        same = (normalize_schedule(trace) == normalize_schedule(ref)) if inst["domain"] == "scheduling" \
            else tuple(trace) == tuple(ref)
        return "VALID" if same else "INVALID"
    return rng.choice(["VALID", "INVALID"])


def _extract_candidate(cell):
    text = cell["prompt"].split("Candidate execution trace:\n", 1)[1].split("\n\nQuestion:", 1)[0]
    return parse_generation(cell["inst"], "TRACE: " + text)


# ------------------------------------------------------------------ runner

def run(backend: str, cells: List[Dict], log_dir: str, progress_every: int = 200) -> Dict:
    kind, name = backend.split(":", 1)
    log = RawLog(f"{log_dir}/{safe_name(name)}.jsonl")
    todo = [c for c in cells if call_key(name, c["prompt"], c["kind"], c.get("replicate", 0)) not in log.done]
    print(f"[{backend}] {len(cells)} cells, {len(cells) - len(todo)} cached, {len(todo)} to run", flush=True)
    if kind == "ollama" and todo:
        err = model_available(name)
        if err:
            raise SystemExit(f"[{backend}] {err}")
    rng = random.Random(0)
    t0 = time.time()
    for i, c in enumerate(todo, 1):
        rep = c.get("replicate", 0)
        if kind == "ollama":
            out = ollama_chat(name, c["prompt"], c["kind"])
        else:
            out = {"response": mock_response(name, c, rng), "latency_s": 0.0}
        rec = {"key": call_key(name, c["prompt"], c["kind"], rep), "model": name, "backend": kind,
               "cell_id": c["cell_id"], "exp": c["exp"], "kind": c["kind"], "replicate": rep,
               "instance_id": c["inst"]["id"], "split": c["inst"]["split"],
               "cand": c.get("cand"), "ref": c.get("ref"), "gen_model": c.get("gen_model"),
               "prompt_sha256": hashlib.sha256(c["prompt"].encode()).hexdigest(),
               "ts": datetime.datetime.now().isoformat(timespec="seconds"), **out}
        log.append(rec)
        if i % progress_every == 0:
            rate = (time.time() - t0) / i
            print(f"[{backend}] {i}/{len(todo)}  {rate:.2f}s/call  eta {rate * (len(todo) - i) / 60:.0f} min",
                  flush=True)
    return {"backend": backend, "n_cells": len(cells), "ran": len(todo)}


def main(argv: Iterable[str] = None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--backends", required=True,
                    help="comma list, e.g. mock:oracle,mock:exact_match or ollama:gemma2:9b")
    ap.add_argument("--stages", default="main,noise", help="main,noise (E3b is run by analysis.py --e3b)")
    ap.add_argument("--limit", type=int, default=None, help="first N instances per split (smoke tests only)")
    a = ap.parse_args(argv)
    data = load(BENCH)
    inst = data["instances"]
    if a.limit:
        seen = {}
        keep = []
        for i in inst:
            seen[i["split"]] = seen.get(i["split"], 0) + 1
            if seen[i["split"]] <= a.limit:
                keep.append(i)
        inst = keep
    cells = build_cells(inst)
    stages = a.stages.split(",")
    todo = (cells if "main" in stages else []) + (noise_cells(cells) if "noise" in stages else [])
    for b in a.backends.split(","):
        run(b, todo, MOCK_DIR if b.startswith("mock:") else RAW_DIR)


if __name__ == "__main__":
    main(sys.argv[1:])
