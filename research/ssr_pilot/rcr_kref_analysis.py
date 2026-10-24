"""
k-reference evaluation, attenuation law, and an inverse-|V| (Horvitz-Thompson) correction.

Motivation (see manuscript Section 4.7): reference matching under a uniformly random
reference keeps only 10-18% of true pairwise gaps. Three questions that need no new
generations:

  Q1  Attenuation law. Is the expected E2 score predicted by E3 / |V(x)|?
      A valid output that equals exactly one valid reference matches a uniform reference
      with probability 1/|V(x)|, so E[E2] ~= E3 / |V|. The fit is checked per
      (world, model) cell, and the implied fraction of each pairwise gap that survives is
      compared with the observed one.
  Q2  k-reference remedy. If an output passes when it matches ANY of k sampled references,
      how do detection power, reversal rate and oracle-ranking recovery change with k?
      (k = |V(x)| recovers the oracle.)
  Q3  Correction. Multiplying a world's single-reference score by |V(x)| (or the average
      match over k references times |V(x)|) is unbiased for E3 when each valid output
      equals exactly one reference. How well does the corrected estimator recover the
      oracle gap and detect the oracle-significant differences?

All inputs are the same frozen 1,152 generations.
"""

import glob
import json
import os
import re
from typing import Dict, List

import numpy as np

from research.ssr_pilot import families as F
from research.ssr_pilot import render
from research.ssr_pilot.core.oracle import evaluate_oracle
from research.ssr_pilot.core.provenance import capture_provenance
from research.ssr_pilot.core.valid_space import build_all_valid_spaces
from research.ssr_pilot.rcr_extended_analysis import holm_rows, pair_list, sign_flip_pvalues
from research.ssr_pilot.worlds import load_worlds

RESULTS_DIR = "research/ssr_pilot/results/rcrc"
RUNS_DIR = "research/ssr_pilot/runs"
SEED = 20261020
D_DRAWS = 2000
N_FLIPS = 20000
ALPHA = 0.05
K_GRID = [1, 2, 3, 5, 10, 25, 50, 10**6]  # 10**6 == all references
PER_WORLD_GENS = 12


def build_match_tensors():
    """
    match[w]  : bool (n_models, 12, n_refs)  E2 match of each generation to each reference
    valid[w]  : bool (n_models, 12)           E3 verdict of each generation
    Also returns n_refs, world ids, model list, run paths.
    """
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    world_ids = sorted(worlds)
    vs = build_all_valid_spaces(worlds_list)
    rendered = {(i, v): render.render_variant(w, v) for i, w in worlds.items() for v in render.VARIANTS}

    paths = sorted(glob.glob(f"{RUNS_DIR}/*.jsonl"))
    records = []
    for p in paths:
        with open(p) as f:
            records.extend(json.loads(l) for l in f if l.strip())
    assert len(records) == 1152
    models = sorted({r["model"] for r in records})
    m_pos = {m: i for i, m in enumerate(models)}

    norm_refs = {}
    for w_id in world_ids:
        w = worlds[w_id]
        sols = vs[w_id].valid_solutions
        norm_refs[w_id] = [F.normalize_schedule(s) if w["family"] == "scheduling" else tuple(s) for s in sols]
    n_refs = {w: len(norm_refs[w]) for w in world_ids}

    match = {w: np.zeros((len(models), PER_WORLD_GENS, n_refs[w]), dtype=bool) for w in world_ids}
    valid = {w: np.zeros((len(models), PER_WORLD_GENS), dtype=bool) for w in world_ids}
    slot = {(w, m): 0 for w in world_ids for m in models}
    for rec in records:
        w_id, model = rec["world"], rec["model"]
        world = worlds[w_id]
        s2c = rendered[(w_id, rec["variant"])]["s2c"]
        raw = rec["response"]
        truncated = rec.get("done_reason") == "length"
        verdict = evaluate_oracle(world, raw, truncated=truncated, shown2canon=s2c)
        sem = verdict.semantic_valid == "TRUE"
        steps, _ = F.parse(world, raw, s2c)
        j = slot[(w_id, model)]
        slot[(w_id, model)] += 1
        mi = m_pos[model]
        valid[w_id][mi, j] = sem
        # D3(b): outputs that mention entities outside the world never count as a match.
        if steps is not None and verdict.reason != "unknown_entity":
            nc = F.normalize_schedule(steps) if world["family"] == "scheduling" else tuple(steps)
            for r, nr in enumerate(norm_refs[w_id]):
                match[w_id][mi, j, r] = (nc == nr)
    assert all(v == PER_WORLD_GENS for v in slot.values())
    return match, valid, np.array([n_refs[w] for w in world_ids]), world_ids, models, paths


def float_sign_flip_p(diffs: np.ndarray, signs: np.ndarray, chunk: int = 2000) -> np.ndarray:
    """Two-sided sign-flip p-values for real-valued per-world differences, shape (n, 24)."""
    obs = np.abs(diffs.sum(axis=1))
    out = np.empty(len(diffs))
    nf = signs.shape[0]
    for s in range(0, len(diffs), chunk):
        perm = np.abs(signs @ diffs[s:s + chunk].T)
        ge = (perm >= obs[s:s + chunk][None, :] - 1e-9).sum(axis=0)
        out[s:s + chunk] = (ge + 1) / (nf + 1)
    out[obs < 1e-12] = 1.0
    return out


def decisions_from_diffs(per_world_diffs: Dict[int, np.ndarray], pairs, signs, integer: bool):
    """per_world_diffs[pair_idx] has shape (D, 24). Returns (decisions (D,6) in {-1,0,1}, mean diffs (D,6))."""
    D = next(iter(per_world_diffs.values())).shape[0]
    raw = np.empty((D, len(pairs)))
    dm = np.empty((D, len(pairs)))
    for k in range(len(pairs)):
        d = per_world_diffs[k]
        dm[:, k] = d.mean(axis=1)
        raw[:, k] = sign_flip_pvalues(d, signs) if integer else float_sign_flip_p(d, signs)
    adj = holm_rows(raw)
    return np.where(adj < ALPHA, np.where(dm > 0, 1, -1), 0), dm


def run() -> Dict:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    match, valid, n_refs, world_ids, models, paths = build_match_tensors()
    nW, nM = len(world_ids), len(models)
    pairs = pair_list(models)
    names = [f"{models[i]}_vs_{models[j]}" for i, j in pairs]
    rng = np.random.default_rng(SEED)
    signs32 = np.random.default_rng(SEED + 1).choice(np.array([-1.0, 1.0], dtype=np.float32), size=(N_FLIPS, nW))
    signs64 = signs32.astype(np.float64)

    # Reference-independent ground truth
    e3 = np.stack([valid[w].mean(axis=1) for w in world_ids])  # (24, models)
    oracle_bench = e3.mean(axis=0)
    oracle_gap = np.array([oracle_bench[i] - oracle_bench[j] for i, j in pairs])
    oracle_sign = np.sign(oracle_gap)
    od = {k: (e3[:, i] - e3[:, j])[None, :] for k, (i, j) in enumerate(pairs)}
    o_dec, _ = decisions_from_diffs(od, pairs, signs32, integer=True)
    o_dec = o_dec[0]

    # ---- Q1: attenuation law --------------------------------------------------------
    # expected E2 per (world, model) under a uniform reference = mean over refs and generations of match
    exp_e2 = np.stack([match[w].mean(axis=(1, 2)) for w in world_ids])            # (24, models)
    pred = e3 / n_refs[:, None]
    cell_mask = (e3 > 0)
    obs_c, pred_c = exp_e2[cell_mask], pred[cell_mask]
    corr = float(np.corrcoef(obs_c, pred_c)[0, 1])
    ratio = obs_c / pred_c
    n_valid_total = int(sum(valid[w].sum() for w in world_ids))
    n_valid_nomatch = int(sum(((match[w].sum(axis=2) == 0) & valid[w]).sum() for w in world_ids))
    n_valid_multi = int(sum(((match[w].sum(axis=2) > 1) & valid[w]).sum() for w in world_ids))
    n_invalid_match = int(sum(((match[w].sum(axis=2) > 0) & ~valid[w]).sum() for w in world_ids))
    pair_rows = {}
    for k, (i, j) in enumerate(pairs):
        og = (e3[:, i] - e3[:, j]).mean()
        eg = (exp_e2[:, i] - exp_e2[:, j]).mean()
        pg = ((e3[:, i] - e3[:, j]) / n_refs).mean()
        pair_rows[names[k]] = {
            "oracle_gap": float(og), "observed_expected_e2_gap": float(eg), "predicted_expected_e2_gap": float(pg),
            "observed_retention": float(eg / og) if og != 0 else None,
            "predicted_retention": float(pg / og) if og != 0 else None,
        }
    attenuation = {
        "model": "E[E2 | uniform reference] = E3 / |V(x)| per (world, model) cell",
        "n_cells_with_positive_E3": int(cell_mask.sum()),
        "pearson_r_observed_vs_predicted": corr,
        "median_ratio_observed_over_predicted": float(np.median(ratio)),
        "mean_ratio_observed_over_predicted": float(ratio.mean()),
        "valid_generations_total": n_valid_total,
        "valid_generations_matching_no_reference": n_valid_nomatch,
        "valid_generations_matching_more_than_one_reference": n_valid_multi,
        "invalid_generations_matching_a_reference": n_invalid_match,
        "pairs": pair_rows,
    }

    # ---- Q2: k-reference match-any ---------------------------------------------------
    sep_pairs = [k for k in range(len(pairs)) if o_dec[k] != 0]
    ns_pairs = [k for k in range(len(pairs)) if o_dec[k] == 0]
    kref = {}
    for K in K_GRID:
        per_world = np.zeros((D_DRAWS, nW, nM))
        for wi, w in enumerate(world_ids):
            n = int(n_refs[wi])
            k = min(K, n)
            if k >= n:
                mask = np.ones((D_DRAWS, n), dtype=bool)
            else:
                ranks = rng.random((D_DRAWS, n)).argsort(axis=1).argsort(axis=1)
                mask = ranks < k
            hit = (match[w].astype(np.float32) @ mask.T.astype(np.float32)) > 0  # (models, 12, D)
            per_world[:, wi, :] = hit.mean(axis=1).T
        diffs = {k2: per_world[:, :, i] - per_world[:, :, j] for k2, (i, j) in enumerate(pairs)}
        dec, dm = decisions_from_diffs(diffs, pairs, signs32, integer=True)
        rev = []
        for k2 in range(len(pairs)):
            d = dm[:, k2]
            pos, neg = int(np.sum(d > 1e-9)), int(np.sum(d < -1e-9))
            rev.append(2 * pos * neg / (D_DRAWS * (D_DRAWS - 1)))
        sgn = np.sign(np.where(np.abs(dm) < 1e-9, 0, dm))
        recovery = float(np.mean(np.all(sgn == oracle_sign[None, :], axis=1)))
        kref["all" if K >= 10**6 else str(K)] = {
            "mean_reversal_all_pairs": float(np.mean(rev)),
            "oracle_ordering_recovery": recovery,
            "detect_oracle_separated_pairs": {names[k]: float(np.mean(dec[:, k] == o_dec[k])) for k in sep_pairs},
            "false_positive_any_nonseparated_pair": float(np.mean(np.any(dec[:, ns_pairs] != 0, axis=1))),
            "wrong_direction_any_pair": float(np.mean(np.any((dec != 0) & (dec != o_dec[None, :]), axis=1))),
            "mean_gap_retained_separated_pairs": {names[k]: float(dm[:, k].mean() / oracle_gap[k]) for k in sep_pairs},
        }

    # ---- Q3: inverse-|V| correction --------------------------------------------------
    corr_out = {}
    for K in [1, 3, 10]:
        est = np.zeros((D_DRAWS, nW, nM))
        for wi, w in enumerate(world_ids):
            n = int(n_refs[wi])
            k = min(K, n)
            ranks = rng.random((D_DRAWS, n)).argsort(axis=1).argsort(axis=1)
            mask = (ranks < k).astype(np.float32)
            frac = (match[w].astype(np.float32) @ mask.T) / k  # mean match over selected refs (models,12,D)
            est[:, wi, :] = frac.mean(axis=1).T * n             # Horvitz-Thompson: x |V|
        diffs = {k2: est[:, :, i] - est[:, :, j] for k2, (i, j) in enumerate(pairs)}
        dec, dm = decisions_from_diffs(diffs, pairs, signs64, integer=False)
        corr_out[str(K)] = {
            "mean_estimated_gap_over_oracle_gap_separated": {names[k]: float(dm[:, k].mean() / oracle_gap[k]) for k in sep_pairs},
            "sd_of_estimated_gap_separated": {names[k]: float(dm[:, k].std()) for k in sep_pairs},
            "detect_oracle_separated_pairs": {names[k]: float(np.mean(dec[:, k] == o_dec[k])) for k in sep_pairs},
            "false_positive_any_nonseparated_pair": float(np.mean(np.any(dec[:, ns_pairs] != 0, axis=1))),
            "wrong_direction_any_pair": float(np.mean(np.any((dec != 0) & (dec != o_dec[None, :]), axis=1))),
            "mean_bias_all_pairs": float(np.mean([dm[:, k].mean() - oracle_gap[k] for k in range(len(pairs))])),
        }

    out = {
        "provenance": capture_provenance(
            "rcr_kref_analysis",
            extra_meta={"seed": SEED, "draws_per_setting": D_DRAWS, "n_flips": N_FLIPS,
                        "k_grid": [k if k < 10**6 else "all" for k in K_GRID]},
            input_files=paths,
        ),
        "models": models,
        "pairs": names,
        "oracle_gap": dict(zip(names, map(float, oracle_gap))),
        "oracle_decision": dict(zip(names, map(int, o_dec))),
        "attenuation_law": attenuation,
        "k_reference": kref,
        "inverse_V_correction": corr_out,
    }
    with open(f"{RESULTS_DIR}/kref_attenuation.json", "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    r = run()
    a = r["attenuation_law"]
    print("attenuation r=%.3f median ratio=%.2f valid=%d nomatch=%d multi=%d invalid_match=%d" % (
        a["pearson_r_observed_vs_predicted"], a["median_ratio_observed_over_predicted"],
        a["valid_generations_total"], a["valid_generations_matching_no_reference"],
        a["valid_generations_matching_more_than_one_reference"], a["invalid_generations_matching_a_reference"]))
