"""
Extended RCR analysis (post-audit completion pass).

Addresses three gaps found in the adversarial review of the manuscript:

  G1  Significance stability was computed on only 200 of 50,000 reference draws and
      was summarised without separating the evaluators. Here the world-level paired
      sign-flip test (Holm-Bonferroni over 6 pairs) is run on ALL 50,000 draws for
      E1, E2 and E3 and reported per evaluator.
  G2  Near-tie hypothesis: pairwise winner reversals might be an artefact of
      statistically indistinguishable models. Reversals are decomposed by whether the
      pair is separated under the reference-independent oracle E3.
  G3  Detection analysis: treating the E3 world-level test as ground truth, how often
      do E1/E2 miss a real difference (false negative) or assert a spurious or
      wrong-direction one?

The candidate generations are the same frozen 1,152 records. The reference-vector
sampler is vectorised and uses its own seed, so draws differ from the legacy loop in
analysis.py; agreement of the headline statistics with the legacy values is reported
as a cross-check (`legacy_crosscheck`).
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
from research.ssr_pilot.rcr_reference_distribution_sensitivity import (
    compute_pairwise_reversal_probability,
    fast_kendall_tau_b_matrix,
)
from research.ssr_pilot.worlds import load_worlds

RESULTS_DIR = "research/ssr_pilot/results/rcrc"
RUNS_DIR = "research/ssr_pilot/runs"
EVALUATORS = ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"]
N_DRAWS = 50000
N_FLIPS = 20000
SEED_DRAWS = 20261016
SEED_FLIPS = 20261017
ALPHA = 0.05
PER_WORLD_GENS = 12  # 3 surface variants x 4 seeds per (world, model)
# Count outputs that mention entities outside the world as non-matches for E1/E2 (prereg D3(b)).
STRICT_UNKNOWN_ENTITY = os.environ.get("RCR_LEGACY_UNKNOWN_ENTITY", "") != "1"


def build_score_tensors():
    """scores[e] has shape (n_worlds, max_refs, n_models); also returns counts and ids."""
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    world_ids = sorted(worlds)
    valid_spaces = build_all_valid_spaces(worlds_list)
    rendered = {(i, v): render.render_variant(w, v) for i, w in worlds.items() for v in render.VARIANTS}

    records = []
    paths = sorted(glob.glob(f"{RUNS_DIR}/*.jsonl"))
    for path in paths:
        with open(path) as f:
            records.extend(json.loads(l) for l in f if l.strip())
    assert len(records) == 1152, f"expected 1152 records, got {len(records)}"
    models = sorted({r["model"] for r in records})

    n_refs = {w: len(valid_spaces[w].valid_solutions) for w in world_ids}
    norm_refs, fmt_refs = {}, {}
    for w_id in world_ids:
        w = worlds[w_id]
        sols = valid_spaces[w_id].valid_solutions
        norm_refs[w_id] = [F.normalize_schedule(s) if w["family"] == "scheduling" else tuple(s) for s in sols]
        fmt_refs[w_id] = [re.sub(r"\s+", " ", F.format_steps(w, s)).strip() for s in sols]

    max_refs = max(n_refs.values())
    sums = {e: np.zeros((len(world_ids), max_refs, len(models))) for e in EVALUATORS}
    counts = np.zeros((len(world_ids), len(models)))
    w_pos = {w: i for i, w in enumerate(world_ids)}
    m_pos = {m: i for i, m in enumerate(models)}

    for rec in records:
        w_id, model = rec["world"], rec["model"]
        world = worlds[w_id]
        s2c = rendered[(w_id, rec["variant"])]["s2c"]
        truncated = rec.get("done_reason") == "length"
        raw = rec["response"]
        verdict = evaluate_oracle(world, raw, truncated=truncated, shown2canon=s2c)
        sem_ok = verdict.semantic_valid == "TRUE"
        steps, _ = F.parse(world, raw, s2c)
        wi, mi = w_pos[w_id], m_pos[model]
        counts[wi, mi] += 1
        k = n_refs[w_id]
        sums["E3_SEMANTIC_ORACLE"][wi, :k, mi] += float(sem_ok)
        # Preregistered deviation D3(b) (same rule as research/ssr_pilot/scoring.py): the parser drops
        # tokens outside the world, so an output that mentions unknown entities must not count as a match.
        if steps is None or (STRICT_UNKNOWN_ENTITY and verdict.reason == "unknown_entity"):
            continue
        norm_c = F.normalize_schedule(steps) if world["family"] == "scheduling" else tuple(steps)
        region, _ = F._region(raw)
        region_sq = re.sub(r"\s+", " ", region).strip()
        for r in range(k):
            sums["E2_NORMALIZED_MATCH"][wi, r, mi] += float(norm_c == norm_refs[w_id][r])
            sums["E1_CANONICAL_EXACT"][wi, r, mi] += float(region_sq == fmt_refs[w_id][r])

    assert np.all(counts == PER_WORLD_GENS), "every (world, model) cell must have 12 generations"
    scores = {e: sums[e] / PER_WORLD_GENS for e in EVALUATORS}
    return scores, np.array([n_refs[w] for w in world_ids]), world_ids, models, paths


def sample_reference_vectors(n_refs: np.ndarray, n_draws: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.stack([rng.integers(0, int(k), size=n_draws) for k in n_refs], axis=1)


def draw_world_scores(tensor: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Per-draw, per-world, per-model scores: shape (n_draws, n_worlds, n_models)."""
    n_worlds = tensor.shape[0]
    return np.stack([tensor[w, idx[:, w], :] for w in range(n_worlds)], axis=1)


def sign_flip_pvalues(diffs: np.ndarray, signs: np.ndarray, chunk: int = 4000) -> np.ndarray:
    """
    Two-sided paired sign-flip Monte Carlo p-values (+1 correction) for each row of
    `diffs` (n, 24). Differences are multiples of 1/12, so they are scaled to exact
    integers; every comparison is therefore exact in float32.
    """
    z = np.rint(diffs * PER_WORLD_GENS).astype(np.float32)
    obs = np.abs(z.sum(axis=1))
    out = np.empty(len(z))
    n_flips = signs.shape[0]
    for s in range(0, len(z), chunk):
        zc = z[s:s + chunk]
        perm = np.abs(signs @ zc.T)  # (n_flips, chunk)
        ge = (perm >= obs[s:s + chunk][None, :]).sum(axis=0)
        out[s:s + chunk] = (ge + 1) / (n_flips + 1)
    out[obs == 0] = 1.0
    return out


def holm_rows(p: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni step-down adjusted p-values, applied independently to each row."""
    m = p.shape[1]
    order = np.argsort(p, axis=1)
    sorted_p = np.take_along_axis(p, order, axis=1)
    adj = np.minimum(1.0, sorted_p * (m - np.arange(m))[None, :])
    adj = np.maximum.accumulate(adj, axis=1)
    out = np.empty_like(adj)
    np.put_along_axis(out, order, adj, axis=1)
    return out


def pair_list(models: List[str]):
    return [(i, j) for i in range(len(models)) for j in range(i + 1, len(models))]


def run() -> Dict:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    scores, n_refs, world_ids, models, run_paths = build_score_tensors()
    pairs = pair_list(models)
    pair_names = [f"{models[i]}_vs_{models[j]}" for i, j in pairs]
    idx = sample_reference_vectors(n_refs, N_DRAWS, SEED_DRAWS)
    signs = np.random.default_rng(SEED_FLIPS).choice(
        np.array([-1.0, 1.0], dtype=np.float32), size=(N_FLIPS, len(world_ids))
    )

    per_world = {e: draw_world_scores(scores[e], idx) for e in EVALUATORS}
    bench = {e: per_world[e].mean(axis=1) for e in EVALUATORS}  # (n_draws, n_models)

    canonical = {e: scores[e][:, 0, :].mean(axis=0) for e in EVALUATORS}
    oracle_scores = scores["E3_SEMANTIC_ORACLE"][:, 0, :].mean(axis=0)
    pi = [i for i, _ in pairs]
    pj = [j for _, j in pairs]

    # ---- headline cross-check against the legacy loop -----------------------------
    crosscheck = {}
    for e in EVALUATORS:
        rev, per_pair_rev = compute_pairwise_reversal_probability(bench[e], models)
        taus = fast_kendall_tau_b_matrix(canonical[e], bench[e])
        valid = taus[~np.isnan(taus)]
        d_or = np.sign(oracle_scores[pi] - oracle_scores[pj])
        d_b = np.sign(bench[e][:, pi] - bench[e][:, pj])
        recovery = float(np.mean(np.all(d_b == d_or[None, :], axis=1)))
        crosscheck[e] = {
            "pairwise_reversal_probability": rev,
            "kendall_tau_b_mean": float(valid.mean()),
            "kendall_tau_b_n_valid": int(len(valid)),
            "oracle_recovery_rate": recovery,
            "per_pair_reversal_probability": per_pair_rev,
        }

    # ---- G1: full-draw significance ------------------------------------------------
    decisions, adj_ps, diffs_mean = {}, {}, {}
    for e in EVALUATORS:
        raw = np.empty((N_DRAWS, len(pairs)))
        dmean = np.empty((N_DRAWS, len(pairs)))
        for k, (i, j) in enumerate(pairs):
            d = per_world[e][:, :, i] - per_world[e][:, :, j]  # (n_draws, 24)
            dmean[:, k] = d.mean(axis=1)
            raw[:, k] = sign_flip_pvalues(d, signs)
        adj = holm_rows(raw)
        dec = np.where(adj < ALPHA, np.where(dmean > 0, 1, -1), 0)  # +1 A wins, -1 B wins, 0 n.s.
        adj_ps[e], decisions[e], diffs_mean[e] = adj, dec, dmean

    # Oracle (reference-independent) per-pair world-level test = ground-truth decision
    e3_dec = decisions["E3_SEMANTIC_ORACLE"][0]
    e3_adj = adj_ps["E3_SEMANTIC_ORACLE"][0]
    e3_gap = diffs_mean["E3_SEMANTIC_ORACLE"][0]
    assert np.all(decisions["E3_SEMANTIC_ORACLE"] == e3_dec[None, :]), "E3 must be reference-invariant"

    label = {1: "SIGNIFICANT_A_WINS", -1: "SIGNIFICANT_B_WINS", 0: "NON_SIGNIFICANT"}
    significance, detection = {}, {}
    for e in EVALUATORS:
        sig, det = {}, {}
        for k, name in enumerate(pair_names):
            dec = decisions[e][:, k]
            truth = int(e3_dec[k])
            sig[name] = {
                "p_not_significant": float(np.mean(dec == 0)),
                "p_significant_a_wins": float(np.mean(dec == 1)),
                "p_significant_b_wins": float(np.mean(dec == -1)),
                "mean_adj_p": float(adj_ps[e][:, k].mean()),
                "min_adj_p": float(adj_ps[e][:, k].min()),
                "max_adj_p": float(adj_ps[e][:, k].max()),
                "decision_is_constant": bool(len(np.unique(dec)) == 1),
            }
            det[name] = {
                "oracle_decision": label[truth],
                "agree_with_oracle": float(np.mean(dec == truth)),
                "miss_true_difference": float(np.mean(dec == 0)) if truth != 0 else None,
                "correct_direction_significant": float(np.mean(dec == truth)) if truth != 0 else None,
                "wrong_direction_significant": float(np.mean(dec == -truth)) if truth != 0 else None,
                "spurious_significant": float(np.mean(dec != 0)) if truth == 0 else None,
            }
        significance[e], detection[e] = sig, det

    # ---- G2: near-tie decomposition of reversals ----------------------------------
    near_tie = {}
    for e in ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH"]:
        rows = {}
        tot_rev = tot_sep = tot_ns = 0.0
        for k, (i, j) in enumerate(pairs):
            d = bench[e][:, i] - bench[e][:, j]
            pos, neg = int(np.sum(d > 1e-9)), int(np.sum(d < -1e-9))
            rev = 2 * pos * neg / (N_DRAWS * (N_DRAWS - 1))
            opposes = None
            if e3_gap[k] != 0:
                # evaluator's strict winner is the opposite of the oracle's
                opposes = float(np.mean(np.sign(d) == -np.sign(e3_gap[k])))
            rows[pair_names[k]] = {
                "oracle_mean_gap": float(e3_gap[k]),
                "oracle_adj_p": float(e3_adj[k]),
                "oracle_separated": bool(e3_dec[k] != 0),
                "reversal_probability": float(rev),
                "p_tied_score": float(np.mean(np.abs(d) <= 1e-9)),
                "p_winner_opposes_oracle_gap": opposes,
            }
            tot_rev += rev
            if e3_dec[k] != 0:
                tot_sep += rev
            else:
                tot_ns += rev
        sep = [r["reversal_probability"] for r in rows.values() if r["oracle_separated"]]
        ns = [r["reversal_probability"] for r in rows.values() if not r["oracle_separated"]]
        near_tie[e] = {
            "pairs": rows,
            "reversal_mass_share_in_oracle_nonseparated_pairs": float(tot_ns / tot_rev) if tot_rev else None,
            "reversal_mass_share_in_oracle_separated_pairs": float(tot_sep / tot_rev) if tot_rev else None,
            "mean_reversal_nonseparated_pairs": float(np.mean(ns)) if ns else None,
            "mean_reversal_separated_pairs": float(np.mean(sep)) if sep else None,
        }

    # ---- G5: direct test of the evaluator effect on each pairwise gap ---------------
    # A significant result under one evaluator and a non-significant one under another is
    # not itself evidence of a difference between them. Test the difference directly:
    # per-world expected reference-matching gap (uniform reference) vs the oracle gap,
    # world-level paired bootstrap (the world is the statistical unit).
    rng_b = np.random.default_rng(SEED_FLIPS + 1)
    n_boot = 5000
    boot_idx = rng_b.integers(0, len(world_ids), size=(n_boot, len(world_ids)))
    effect = {}
    for ev in ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH"]:
        exp_w = np.stack([scores[ev][w, :n_refs[w], :].mean(axis=0) for w in range(len(world_ids))])  # (24, models)
        orc_w = scores["E3_SEMANTIC_ORACLE"][:, 0, :]  # reference-independent
        rows = {}
        for k, (i, j) in enumerate(pairs):
            dw = (orc_w[:, i] - orc_w[:, j]) - (exp_w[:, i] - exp_w[:, j])  # oracle gap minus matching gap, per world
            boots = dw[boot_idx].mean(axis=1)
            lo, hi = np.percentile(boots, [2.5, 97.5])
            rows[pair_names[k]] = {
                "oracle_gap": float((orc_w[:, i] - orc_w[:, j]).mean()),
                "expected_matching_gap_uniform_reference": float((exp_w[:, i] - exp_w[:, j]).mean()),
                "evaluator_effect_on_gap": float(dw.mean()),
                "ci95_low": float(lo),
                "ci95_high": float(hi),
                "ci_excludes_zero": bool(lo > 0 or hi < 0),
            }
        effect[ev] = rows

    # ---- G4: per-mechanism-family breakdown (within-benchmark robustness) ------------
    fam_of = {w["id"]: w["family"] for w in load_worlds()}
    families = sorted(set(fam_of.values()))
    by_family = {}
    for fam in families:
        cols = [k for k, w in enumerate(world_ids) if fam_of[w] == fam]
        fam_out = {"n_worlds": len(cols)}
        for e in EVALUATORS:
            fb = per_world[e][:, cols, :].mean(axis=1)
            fcanon = scores[e][cols, 0, :].mean(axis=0)
            rev, _ = compute_pairwise_reversal_probability(fb, models)
            taus = fast_kendall_tau_b_matrix(fcanon, fb)
            ok = taus[~np.isnan(taus)]
            fam_out[e] = {
                "pairwise_reversal_probability": rev,
                "kendall_tau_b_mean": float(ok.mean()) if len(ok) else None,
                "kendall_tau_b_n_valid": int(len(ok)),
                "mean_score_by_model": dict(zip(models, map(float, fb.mean(axis=0)))),
            }
        by_family[fam] = fam_out

    score_context = {
        e: {
            "canonical_scores": dict(zip(models, map(float, canonical[e]))),
            "mean_draw_scores": dict(zip(models, map(float, bench[e].mean(axis=0)))),
            "sd_draw_scores": dict(zip(models, map(float, bench[e].std(axis=0)))),
        }
        for e in EVALUATORS
    }

    out = {
        "provenance": capture_provenance(
            "rcr_extended_analysis",
            extra_meta={
                "n_draws": N_DRAWS, "n_sign_flips": N_FLIPS, "draw_seed": SEED_DRAWS,
                "flip_seed": SEED_FLIPS, "alpha": ALPHA, "n_worlds": len(world_ids),
                "sign_flip_scope": "ALL draws (no subsampling)",
            },
            input_files=run_paths,
        ),
        "models": models,
        "pairs": pair_names,
        "legacy_crosscheck": crosscheck,
        "significance_all_draws": significance,
        "detection_vs_oracle": detection,
        "near_tie_decomposition": near_tie,
        "evaluator_effect_on_gap": effect,
        "by_family": by_family,
        "score_context": score_context,
    }
    with open(f"{RESULTS_DIR}/extended_analysis.json", "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    res = run()
    for e, c in res["legacy_crosscheck"].items():
        print(e, round(c["pairwise_reversal_probability"], 4), round(c["kendall_tau_b_mean"], 4),
              round(c["oracle_recovery_rate"], 4))
