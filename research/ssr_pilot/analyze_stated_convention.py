"""
Analysis script for the stated-convention arm of the SSR pilot.
Compares stated-convention outputs against the original pilot baseline.

    uv run python -m research.ssr_pilot.analyze_stated_convention

Outputs results to research/ssr_pilot/results/stated_convention/
"""

import argparse
import glob
import json
import os
from collections import Counter
from typing import Dict, List

import numpy as np

from research.evaluation import metrics as M
from research.ssr_pilot import attackers as A
from research.ssr_pilot.analyze import (
    analyze,
    attacker_table,
    ci,
    decide,
    passes_k1,
    frr,
    load_scored,
    summarize,
    _j,
    _f,
    _x,
)
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.render import VARIANTS, render_variant
from research.ssr_pilot.run_pilot import RUNS, PREREG, sha256_file
from research.ssr_pilot.scoring import score_record
from research.ssr_pilot.worlds import WORLD_DIR, load_worlds

RUNS_STATED = "research/ssr_pilot/runs_stated_convention"
RESULTS_STATED = "research/ssr_pilot/results/stated_convention"


def load_scored_stated(run_dir: str) -> List[Dict]:
    worlds = {w["id"]: w for w in load_worlds()}
    banks = {i: load_bank(w) for i, w in worlds.items()}
    rendered = {(i, v): render_variant(w, v, stated_convention=True) for i, w in worlds.items() for v in VARIANTS}
    out = []
    for path in sorted(glob.glob(f"{run_dir}/*.jsonl")):
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                out.append(score_record(worlds[r["world"]], rendered[(r["world"], r["variant"])],
                                        banks[r["world"]], r))
    return out


def paired_diff_ci(vals_before, vals_after, groups):
    diffs = [a - b for a, b in zip(vals_after, vals_before)]
    return M.cluster_bootstrap_ci(diffs, groups, n_boot=2000, seed=0)


def format_ci(c):
    if not c or c.get("mean") is None:
        return "—"
    return f"{c['mean']:.3f} [{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}]"


def generate_comparison_report(orig_res: Dict, stated_res: Dict, recs_orig: List[Dict], recs_stated: List[Dict], out_dir: str):
    models = sorted(orig_res["models"])
    worlds = load_worlds()
    groups_orig = [r["world"] for r in recs_orig]
    groups_stated = [r["world"] for r in recs_stated]

    # Map records by (model, world, variant, seed) for direct pairing
    key_fn = lambda r: (r["model"], r["world"], r["variant"], r["seed"])
    orig_map = {key_fn(r): r for r in recs_orig}
    stated_map = {key_fn(r): r for r in recs_stated}
    common_keys = sorted(set(orig_map.keys()).intersection(set(stated_map.keys())))

    # Newly accepted outputs analysis
    newly_accepted_canonical = sum(1 for k in common_keys if not orig_map[k]["A_norm"] and stated_map[k]["A_norm"])
    newly_accepted_semantic = sum(1 for k in common_keys if not orig_map[k]["B"] and stated_map[k]["B"])
    newly_accepted_canonical_was_b = sum(1 for k in common_keys if not orig_map[k]["A_norm"] and orig_map[k]["B"] and stated_map[k]["A_norm"])

    # Decision logic
    orig_frr = orig_res["pooled"]["FRR_norm"]["mean"]
    stated_frr = stated_res["pooled"]["FRR_norm"]["mean"]
    frr_diff = stated_frr - orig_frr

    if stated_frr < 0.10:
        verdict = "B) phenomenon substantially collapses"
    elif stated_frr >= 0.50 and frr_diff > -0.15:
        verdict = "A) phenomenon survives convention disclosure"
    else:
        verdict = "C) mixed/inconclusive"

    lines = [
        "# SSR Pilot Stated-Convention Arm Results & Comparison",
        "",
        "## Summary & Decision Note",
        "",
        f"**Decision Note:** **{verdict}**",
        "",
        f"- **Pooled FRR (original baseline):** {format_ci(orig_res['pooled']['FRR_norm'])}",
        f"- **Pooled FRR (stated-convention arm):** {format_ci(stated_res['pooled']['FRR_norm'])}",
        f"- **Change in Pooled FRR:** {stated_frr - orig_frr:+.3f}",
        f"- **Newly Canonical-Accepted outputs ($A_{{norm}}$):** {newly_accepted_canonical} / {len(common_keys)}",
        f"  - Of which were already semantically valid ($B$) under original pilot: {newly_accepted_canonical_was_b}",
        f"- **Newly Semantically Accepted outputs ($B$):** {newly_accepted_semantic} / {len(common_keys)}",
        "",
        "## Mechanical Criteria (K0-K5) Comparison",
        "",
        "| Criterion | Original Pilot | Stated-Convention Arm |",
        "|---|---|---|",
    ]
    for k in ["K0", "K1", "K2", "K3", "K4", "K5"]:
        pass_orig = "PASS" if orig_res["criteria"][k] else "FAIL"
        pass_stated = "PASS" if stated_res["criteria"][k] else "FAIL"
        lines.append(f"| **{k}** | {pass_orig} | {pass_stated} |")

    lines.extend([
        "",
        "## Per-Model Metrics (Original vs Stated-Convention)",
        "",
        "| Model | Arm | B (Semantic) | A_norm | A_strict | C | FRR_norm | UNVERIF |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for m in models:
        so = orig_res["per_model"][m]
        ss = stated_res["per_model"][m]
        lines.append(f"| **{m}** | Original | {format_ci(so['B'])} | {format_ci(so['A_norm'])} | {format_ci(so['A_strict'])} | {format_ci(so['C'])} | {format_ci(so['FRR_norm'])} | {so['unverifiable_rate']:.3f} |")
        lines.append(f"| | Stated-Conv | {format_ci(ss['B'])} | {format_ci(ss['A_norm'])} | {format_ci(ss['A_strict'])} | {format_ci(ss['C'])} | {format_ci(ss['FRR_norm'])} | {ss['unverifiable_rate']:.3f} |")

    lines.extend([
        f"| **Pooled** | Original | {format_ci(orig_res['pooled']['B'])} | {format_ci(orig_res['pooled']['A_norm'])} | {format_ci(orig_res['pooled']['A_strict'])} | {format_ci(orig_res['pooled']['C'])} | {format_ci(orig_res['pooled']['FRR_norm'])} | {orig_res['pooled']['unverifiable_rate']:.3f} |",
        f"| | Stated-Conv | {format_ci(stated_res['pooled']['B'])} | {format_ci(stated_res['pooled']['A_norm'])} | {format_ci(stated_res['pooled']['A_strict'])} | {format_ci(stated_res['pooled']['C'])} | {format_ci(stated_res['pooled']['FRR_norm'])} | {stated_res['pooled']['unverifiable_rate']:.3f} |",
        "",
        "## FRR_norm by Mechanism Family",
        "",
        "| Family | Original | Stated-Convention |",
        "|---|---|---|",
    ])
    for fam in sorted(orig_res["by_family"].keys()):
        lines.append(f"| **{fam}** | {format_ci(orig_res['by_family'][fam])} | {format_ci(stated_res['by_family'][fam])} |")

    lines.extend([
        "",
        "## FRR_norm by Surface Variant",
        "",
        "| Variant | Original | Stated-Convention |",
        "|---|---|---|",
    ])
    for v in VARIANTS:
        lines.append(f"| **{v}** | {format_ci(orig_res['by_variant'][v])} | {format_ci(stated_res['by_variant'][v])} |")

    lines.extend([
        "",
        "## Failure Taxonomy Shift",
        "",
        "Share of outputs by classification category:",
        "",
    ])

    cats = sorted(set(list(orig_res["pooled"]["taxonomy"].keys()) + list(stated_res["pooled"]["taxonomy"].keys())))
    lines.append("| Category | Original Baseline | Stated-Convention |")
    lines.append("|---|---|---|")
    for cat in cats:
        co = orig_res["pooled"]["taxonomy"].get(cat, 0.0)
        cs = stated_res["pooled"]["taxonomy"].get(cat, 0.0)
        lines.append(f"| {cat} | {co:.3f} | {cs:.3f} |")

    os.makedirs(out_dir, exist_ok=True)
    report_path = f"{out_dir}/REPORT.md"
    with open(report_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Report written to {report_path}")


def main():
    worlds = load_worlds()
    banks = {w["id"]: load_bank(w) for w in worlds}
    k0 = A.k0_gate(A.build_rows(worlds, banks))

    print("Loading original pilot records...")
    recs_orig = load_scored(RUNS)
    models = sorted({r["model"] for r in recs_orig})
    orig_res = analyze(recs_orig, k0, models)

    print("Loading stated-convention arm records...")
    recs_stated = load_scored_stated(RUNS_STATED)
    stated_res = analyze(recs_stated, k0, models)

    os.makedirs(RESULTS_STATED, exist_ok=True)
    json.dump({**stated_res}, open(f"{RESULTS_STATED}/analysis.json", "w"), indent=1, default=_j)
    with open(f"{RESULTS_STATED}/records.jsonl", "w") as f:
        for r in recs_stated:
            f.write(json.dumps(r) + "\n")

    generate_comparison_report(orig_res, stated_res, recs_orig, recs_stated, RESULTS_STATED)


if __name__ == "__main__":
    main()
