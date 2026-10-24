"""
RCR Claude-family follow-up: executes the frozen analysis plan in
docs/research/RCR_CLAUDE_FAMILY_PREREG.md (H1-H4) on research/ssr_pilot/runs_claude/.

    python -m research.ssr_pilot.rcr_claude_analysis

1. Re-runs the unchanged extended (50,000-draw) and k-reference analyses with their
   input/output paths pointed at the Claude runs, writing to results/rcrc_claude/.
2. Computes the canonical inflation factor CIF_m = observed canonical-matching valid outputs /
   outputs expected if the model chose uniformly from V(x), with world-level bootstrap CIs,
   for the Claude models (confirmatory) and the four local models (context only).
3. Evaluates H1-H4 and writes hypotheses.json.
"""

import glob
import json
import os
from typing import Dict, List

import numpy as np

from research.ssr_pilot import families as F
from research.ssr_pilot import rcr_extended_analysis as X
from research.ssr_pilot import rcr_kref_analysis as K
from research.ssr_pilot import render
from research.ssr_pilot.core.oracle import evaluate_oracle
from research.ssr_pilot.core.valid_space import build_all_valid_spaces
from research.ssr_pilot.worlds import load_worlds

CLAUDE_RUNS = "research/ssr_pilot/runs_claude"
LOCAL_RUNS = "research/ssr_pilot/runs"
OUT = "research/ssr_pilot/results/rcrc_claude"
N_BOOT = 5000
SEED = 20261024
MIN_VALID = 20


def per_world_counts(paths: List[str]):
    """models -> arrays over worlds: n_gen, n_valid, n_canon (valid & matches reference 0), expected canon."""
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    world_ids = sorted(worlds)
    wpos = {w: i for i, w in enumerate(world_ids)}
    vs = build_all_valid_spaces(worlds_list)
    rendered = {(i, v): render.render_variant(w, v) for i, w in worlds.items() for v in render.VARIANTS}
    n_refs = {}
    canon = {}
    for w_id in world_ids:
        w = worlds[w_id]
        sols = vs[w_id].valid_solutions
        n_refs[w_id] = len(sols)
        s0 = sols[0]
        canon[w_id] = F.normalize_schedule(s0) if w["family"] == "scheduling" else tuple(s0)
    acc: Dict[str, Dict[str, np.ndarray]] = {}
    for p in paths:
        for line in open(p):
            if not line.strip():
                continue
            rec = json.loads(line)
            m, w_id = rec["model"], rec["world"]
            a = acc.setdefault(m, {k: np.zeros(len(world_ids)) for k in ("gen", "valid", "canon", "expected")})
            world = worlds[w_id]
            s2c = rendered[(w_id, rec["variant"])]["s2c"]
            verdict = evaluate_oracle(world, rec["response"], truncated=rec.get("done_reason") == "length",
                                      shown2canon=s2c)
            ok = verdict.semantic_valid == "TRUE"
            i = wpos[w_id]
            a["gen"][i] += 1
            if not ok:
                continue
            a["valid"][i] += 1
            a["expected"][i] += 1.0 / n_refs[w_id]
            steps, _ = F.parse(world, rec["response"], s2c)
            if steps is not None and verdict.reason != "unknown_entity":
                nc = F.normalize_schedule(steps) if world["family"] == "scheduling" else tuple(steps)
                a["canon"][i] += float(nc == canon[w_id])
    fam = [worlds[w]["family"] for w in world_ids]
    return acc, world_ids, fam


def cif_table(acc, models):
    rng = np.random.default_rng(SEED)
    n_w = len(next(iter(acc.values()))["gen"])
    boot = rng.integers(0, n_w, size=(N_BOOT, n_w))
    rows, boot_cif = {}, {}
    for m in models:
        a = acc[m]
        cif = a["canon"].sum() / a["expected"].sum() if a["expected"].sum() > 0 else float("nan")
        b = a["canon"][boot].sum(axis=1) / np.maximum(a["expected"][boot].sum(axis=1), 1e-12)
        boot_cif[m] = b
        lo, hi = np.percentile(b, [2.5, 97.5])
        rows[m] = {"n_gen": int(a["gen"].sum()), "n_valid": int(a["valid"].sum()),
                   "validity": float(a["valid"].sum() / a["gen"].sum()),
                   "canon_matches_among_valid": int(a["canon"].sum()),
                   "expected_if_uniform": float(a["expected"].sum()),
                   "canon_share_of_valid": float(a["canon"].sum() / max(a["valid"].sum(), 1)),
                   "cif": float(cif), "cif_ci95": [float(lo), float(hi)]}
    return rows, boot_cif


def run() -> Dict:
    os.makedirs(OUT, exist_ok=True)
    # 1. unchanged analyses, re-pointed at the Claude runs
    X.RUNS_DIR, X.RESULTS_DIR = CLAUDE_RUNS, OUT
    K.RUNS_DIR, K.RESULTS_DIR = CLAUDE_RUNS, OUT
    ext = X.run()
    K.run()

    # 2. canonical inflation
    c_paths = sorted(glob.glob(f"{CLAUDE_RUNS}/*.jsonl"))
    l_paths = sorted(glob.glob(f"{LOCAL_RUNS}/*.jsonl"))
    acc_c, world_ids, fam = per_world_counts(c_paths)
    acc_l, _, _ = per_world_counts(l_paths)
    claude_models, local_models = sorted(acc_c), sorted(acc_l)
    cif_c, boot_c = cif_table(acc_c, claude_models)
    cif_l, _ = cif_table(acc_l, local_models)

    eligible = [m for m in claude_models if cif_c[m]["n_valid"] >= MIN_VALID]
    spread_obs = spread_ci = None
    if len(eligible) >= 2:
        obs = [cif_c[m]["cif"] for m in eligible]
        spread_obs = float(max(obs) - min(obs))
        sp = np.max([boot_c[m] for m in eligible], axis=0) - np.min([boot_c[m] for m in eligible], axis=0)
        spread_ci = [float(np.percentile(sp, 2.5)), float(np.percentile(sp, 97.5))]

    # per-family validity (exploratory)
    fam_idx = {f: [i for i, x in enumerate(fam) if x == f] for f in sorted(set(fam))}
    fam_valid = {m: {f: float(acc_c[m]["valid"][ix].sum() / acc_c[m]["gen"][ix].sum())
                     for f, ix in fam_idx.items()} for m in claude_models}

    # 3. hypotheses
    e3 = ext["score_context"]["E3_SEMANTIC_ORACLE"]["canonical_scores"]
    e2 = ext["score_context"]["E2_NORMALIZED_MATCH"]["canonical_scores"]
    h1_n = sum(1 for m in claude_models if cif_c[m]["validity"] >= 0.30)

    det = ext["detection_vs_oracle"]["E2_NORMALIZED_MATCH"]
    sep = [v for v in det.values() if v["oracle_decision"] != "NON_SIGNIFICANT"]
    h2_pooled = float(np.mean([v["correct_direction_significant"] for v in sep])) if sep else None

    order = sorted(claude_models, key=lambda m: -e3[m])
    adj = []
    for a, b in zip(order, order[1:]):
        r3 = e3[a] / e3[b] if e3[b] > 0 else float("inf")
        r2 = e2[a] / e2[b] if e2[b] > 0 else float("inf")
        f = max(r2 / r3, r3 / r2) if (np.isfinite(r2) and np.isfinite(r3) and r2 > 0 and r3 > 0) else float("inf")
        adj.append({"pair": f"{a}>{b}", "e3_ratio": r3, "e2_canonical_ratio": r2, "distortion_factor": f})

    h3_all_gt1 = bool(eligible) and all(cif_c[m]["cif"] > 1 for m in eligible)
    hyp = {
        "H1_floor": {"models_with_validity_ge_30pct": h1_n, "of": len(claude_models), "supported": h1_n >= 3,
                     "validity": {m: cif_c[m]["validity"] for m in claude_models}},
        "H2_detection_loss": {"n_oracle_separated_pairs": len(sep), "n_pairs": len(det),
                              "pooled_E2_detection_rate_uniform_ref": h2_pooled,
                              "supported": (h2_pooled is not None and h2_pooled < 0.5)},
        "H3_canonical_inflation": {"min_valid_for_eligibility": MIN_VALID, "eligible_models": eligible,
                                   "cif": {m: cif_c[m]["cif"] for m in claude_models},
                                   "all_eligible_cif_gt_1": h3_all_gt1,
                                   "cif_spread_max_minus_min": spread_obs, "cif_spread_ci95": spread_ci,
                                   "spread_ci_excludes_zero": bool(spread_ci and spread_ci[0] > 0),
                                   "supported": h3_all_gt1 and bool(spread_ci and spread_ci[0] > 0)},
        "H4_ranking_distortion": {"adjacent_pairs_in_e3_order": adj,
                                  "max_distortion_factor": max([x["distortion_factor"] for x in adj], default=None),
                                  "supported": any(x["distortion_factor"] > 1.5 for x in adj),
                                  "e2_kendall_tau_b_mean_uniform_refs":
                                      ext["legacy_crosscheck"]["E2_NORMALIZED_MATCH"]["kendall_tau_b_mean"]},
    }
    out = {"claude_models": claude_models, "cif_claude": cif_c, "cif_local_context_only": cif_l,
           "validity_by_family_claude": fam_valid, "hypotheses": hyp, "n_boot": N_BOOT, "seed": SEED}
    with open(f"{OUT}/hypotheses.json", "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    res = run()
    print(json.dumps(res["hypotheses"], indent=2))
    for m, r in res["cif_claude"].items():
        print(m, f"valid={r['validity']:.1%} canon/valid={r['canon_share_of_valid']:.1%} "
                 f"CIF={r['cif']:.2f} CI={[round(x, 2) for x in r['cif_ci95']]}")
