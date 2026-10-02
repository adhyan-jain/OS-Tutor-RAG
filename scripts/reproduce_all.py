#!/usr/bin/env python3
"""
Reproduce the v2 reference-sensitivity study end to end.

    python scripts/reproduce_all.py                      # benchmark + tests + leakage + mock dry run
    python scripts/reproduce_all.py --models qwen3:8b,gemma2:9b,...   # Phase B: real models via Ollama

Steps: regenerate benchmark (adversarially filtered, seed 20261002) -> label
tests -> leakage audit (frozen thresholds) -> experiments -> analysis.
Every output carries the SHA-256 of docs/PREREGISTRATION_V2.md.

Replaces AGY's script, whose oracle rejected every trace and whose "models"
were hand-coded heuristics.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.benchmark.audit_leakage import run as run_leakage  # noqa: E402
from research.benchmark.generator import generate_filtered, save  # noqa: E402
from research.evaluation import analysis, experiments  # noqa: E402

BENCH = "research/benchmark/benchmark_v2.json"
# Documented in PREREGISTRATION_V2 §9 D2/D3: concurrency fails the adjacent-pair and
# embedding attackers (which also pulls the pooled embedding result over the threshold).
KNOWN_FAILURES = {"binary/concurrency/local_plausibility", "binary/concurrency/bge_embedding",
                  "binary/pooled/bge_embedding"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="", help="comma list of Ollama models (Phase B); empty = mock dry run")
    ap.add_argument("--skip-benchmark", action="store_true", help="reuse the existing benchmark_v2.json")
    ap.add_argument("--skip-leakage", action="store_true")
    a = ap.parse_args()

    if not a.skip_benchmark:
        print("[1/5] generating benchmark")
        save(generate_filtered(), BENCH)
    print("[2/5] label tests")
    if subprocess.run([sys.executable, "-m", "pytest", "tests/research", "-q"]).returncode:
        sys.exit("label tests failed")
    if not a.skip_leakage:
        print("[3/5] leakage audit")
        rep = run_leakage(BENCH, "research/results/leakage_audit_v2.json")
        unexpected = set(rep["failures"]) - KNOWN_FAILURES
        if unexpected:
            sys.exit(f"leakage audit failed beyond documented deviation D2: {sorted(unexpected)}")
    if a.models:
        backends = ",".join(f"ollama:{m}" for m in a.models.split(","))
        log_dir, out = experiments.RAW_DIR, "research/results/analysis_v2.json"
    else:
        backends = "mock:oracle,mock:exact_match,mock:random"
        log_dir, out = experiments.MOCK_DIR, "research/results/analysis_v2_mock.json"
    print(f"[4/5] experiments: {backends}")
    experiments.main(["--backends", backends])
    print("[5/5] analysis")
    rep = analysis.analyse(log_dir, out)
    if rep["included_models"]:
        analysis.run_e3b(log_dir, "ollama" if a.models else "mock", rep)
        rep = analysis.analyse(log_dir, out)
    d = rep["decision"] or {}
    print(json.dumps({k: v for k, v in d.items() if k != "holm"}, indent=1, default=str))


if __name__ == "__main__":
    main()
