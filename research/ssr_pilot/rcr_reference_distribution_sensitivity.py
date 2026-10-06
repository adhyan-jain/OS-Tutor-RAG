"""
Reference-Distribution Sensitivity Analysis for Reference-Choice Robustness (RCR).

Evaluates the sensitivity of RCR metrics (Kendall tau-b, pairwise winner reversals,
E3 ranking recovery) across alternative reference-selection distributions while holding
the 1,152 frozen candidate generations strictly fixed.

Distributions evaluated:
  - Distribution A: Uniform (P(R) = 1 / |V(x)|)
  - Distribution B: Canonical Bias (P(R0) = p for p in {0, .25, .50, .75, .80, .90, .95, .99})
  - Distribution C: Similarity Bias (w(R) = 1 / (1 + d(R, R0)) normalized)
  - Distribution D: Adversarial Upper-Bound Stress Condition (deterministic maximizer of disagreement)
"""

import csv
import glob
import hashlib
import json
import os
import re
from typing import Dict, List, Tuple

import numpy as np

from research.ssr_pilot import families as F
from research.ssr_pilot import render
from research.ssr_pilot.core.oracle import evaluate_oracle
from research.ssr_pilot.core.valid_space import build_all_valid_spaces
from research.ssr_pilot.rcrc.ranking_metrics import get_model_ranking
from research.ssr_pilot.worlds import load_worlds

RESULTS_DIR = "research/ssr_pilot/results/rcrc"
RUNS_DIR = "research/ssr_pilot/runs"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_structural_distance(world: Dict, r: List, r0: List) -> float:
    """
    Compute normalized structural/edit distance d(R, R0) in [0, 1].
      - Scheduling: time-mismatch fraction over total makespan.
      - Synchronization: normalized Levenshtein distance on thread event tuples.
      - Banker: normalized inversion count on process sequence.
    """
    fam = world["family"]
    if fam == "scheduling":
        norm_r = F.normalize_schedule(r)
        norm_r0 = F.normalize_schedule(r0)
        t_max = max(max(e for _, _, e in norm_r), max(e for _, _, e in norm_r0))
        if t_max == 0:
            return 0.0
        diff = 0
        for t in range(t_max):
            p_r = next((pid for pid, s, e in norm_r if s <= t < e), None)
            p_r0 = next((pid for pid, s, e in norm_r0 if s <= t < e), None)
            if p_r != p_r0:
                diff += 1
        return float(diff / t_max)
    elif fam == "sync":
        seq_r = [tuple(x) for x in r]
        seq_r0 = [tuple(x) for x in r0]
        n, m = len(seq_r), len(seq_r0)
        if max(n, m) == 0:
            return 0.0
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = i
        for j in range(m + 1):
            dp[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if seq_r[i - 1] == seq_r0[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
        return float(dp[n][m] / max(n, m))
    elif fam == "banker":
        pos_r0 = {p: i for i, p in enumerate(r0)}
        seq = [pos_r0[p] for p in r if p in pos_r0]
        n = len(seq)
        if n <= 1:
            return 0.0
        inv = sum(1 for i in range(n) for j in range(i + 1, n) if seq[i] > seq[j])
        max_inv = n * (n - 1) / 2
        return float(inv / max_inv)
    return 0.0


def fast_kendall_tau_b_matrix(x: np.ndarray, y_mat: np.ndarray) -> np.ndarray:
    """
    Vectorized Kendall tau-b computation between reference vector x (shape (M,))
    and an ensemble of candidate score vectors y_mat (shape (N, M)).
    Produces identical results to scipy.stats.kendalltau(variant='b').
    """
    n = len(x)
    n0 = n * (n - 1) // 2
    i_idx, j_idx = np.triu_indices(n, k=1)

    dx = np.sign(x[i_idx] - x[j_idx])
    dy = np.sign(y_mat[:, i_idx] - y_mat[:, j_idx])

    prod = dx * dy
    c = np.sum(prod == 1, axis=1)
    d = np.sum(prod == -1, axis=1)

    t_x = np.sum(dx == 0)
    t_y = np.sum(dy == 0, axis=1)

    denom = np.sqrt((n0 - t_x) * (n0 - t_y))
    with np.errstate(divide="ignore", invalid="ignore"):
        taus = (c - d) / denom
        taus[denom == 0] = np.nan

    return taus


def compute_pairwise_reversal_probability(score_mat: np.ndarray, models: List[str]) -> Tuple[float, Dict]:
    """
    Computes strict pairwise winner reversal probability across all draw pairs.
    score_mat shape: (n_draws, n_models)
    """
    n_draws, n_models = score_mat.shape
    pairwise_reversals = {}
    total_reversals = 0
    total_pairs = 0

    denom = n_draws * (n_draws - 1)

    for i in range(n_models):
        for j in range(i + 1, n_models):
            diffs = score_mat[:, i] - score_mat[:, j]
            pos = int(np.sum(diffs > 1e-9))
            neg = int(np.sum(diffs < -1e-9))
            rev_pairs = 2 * pos * neg
            pair_rev_rate = float(rev_pairs / denom) if denom > 0 else 0.0
            pair_name = f"{models[i]}_vs_{models[j]}"
            pairwise_reversals[pair_name] = pair_rev_rate
            total_reversals += rev_pairs
            total_pairs += denom

    overall_reversal = float(total_reversals / total_pairs) if total_pairs > 0 else 0.0
    return overall_reversal, pairwise_reversals


def run_distribution_sensitivity(n_draws: int = 50000, base_seed: int = 20261007) -> Dict:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # 1. Load worlds, valid spaces, rendered variants
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    valid_spaces = build_all_valid_spaces(worlds_list)
    rendered = {(i, v): render.render_variant(w, v) for i, w in worlds.items() for v in render.VARIANTS}

    # 2. Load 1,152 generations
    raw_records = []
    input_hashes = {}
    for path in sorted(glob.glob(f"{RUNS_DIR}/*.jsonl")):
        input_hashes[path] = _sha256(path)
        with open(path) as f:
            for line in f:
                if line.strip():
                    raw_records.append(json.loads(line))

    assert len(raw_records) == 1152, f"Expected 1,152 records, got {len(raw_records)}"

    # 3. Pre-extract candidate outputs and format reference cache
    formatted_refs_cache: Dict[str, Dict[int, str]] = {}
    norm_refs_cache: Dict[str, Dict[int, Tuple]] = {}
    obs_refs_cache: Dict[str, Dict[int, Tuple]] = {}

    for w_id, w in worlds.items():
        v_sols = valid_spaces[w_id].valid_solutions
        formatted_refs_cache[w_id] = {}
        norm_refs_cache[w_id] = {}
        obs_refs_cache[w_id] = {}
        for r_idx, r_steps in enumerate(v_sols):
            norm_ref = F.normalize_schedule(r_steps) if w["family"] == "scheduling" else tuple(r_steps)
            formatted_ref = F.format_steps(w, r_steps)
            norm_refs_cache[w_id][r_idx] = norm_ref
            formatted_refs_cache[w_id][r_idx] = re.sub(r"\s+", " ", formatted_ref).strip()
            obs_refs_cache[w_id][r_idx] = F.observe(w, r_steps)

    # 4. Build score matrix per evaluator
    evaluators = ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"]
    eval_passes_by_rec = {e: {w_id: {r_idx: {} for r_idx in range(len(valid_spaces[w_id].valid_solutions))} for w_id in worlds} for e in evaluators}

    models_set = set()
    for rec in raw_records:
        w_id = rec["world"]
        world = worlds[w_id]
        v_space = valid_spaces[w_id]
        s2c = rendered[(w_id, rec["variant"])]["s2c"]
        truncated = rec.get("done_reason") == "length"
        raw_text = rec["response"]
        model = rec["model"]
        models_set.add(model)

        oracle_verdict = evaluate_oracle(world, raw_text, truncated=truncated, shown2canon=s2c)
        parsed_steps, _ = F.parse(world, raw_text, s2c)

        if parsed_steps is None:
            norm_cand = None
            region_squashed = ""
            cand_obs = None
        else:
            norm_cand = F.normalize_schedule(parsed_steps) if world["family"] == "scheduling" else tuple(parsed_steps)
            region, _ = F._region(raw_text)
            region_squashed = re.sub(r"\s+", " ", region).strip()
            cand_obs = F.observe(world, parsed_steps)

        is_sem_valid = (oracle_verdict.semantic_valid == "TRUE")

        for r_idx in range(len(v_space.valid_solutions)):
            norm_ref = norm_refs_cache[w_id][r_idx]
            formatted_ref_squashed = formatted_refs_cache[w_id][r_idx]
            ref_obs = obs_refs_cache[w_id][r_idx]

            ref_match_norm = (norm_cand == norm_ref) if norm_cand is not None else False
            ref_match_strict = (region_squashed == formatted_ref_squashed) if norm_cand is not None else False

            eval_passes_by_rec["E1_CANONICAL_EXACT"][w_id][r_idx].setdefault(model, []).append(ref_match_strict)
            eval_passes_by_rec["E2_NORMALIZED_MATCH"][w_id][r_idx].setdefault(model, []).append(ref_match_norm)
            eval_passes_by_rec["E3_SEMANTIC_ORACLE"][w_id][r_idx].setdefault(model, []).append(is_sem_valid)

    models_list = sorted(list(models_set))

    # Precompute mean scores per (w_id, r_idx, model)
    world_ref_scores = {
        e: {
            w_id: {
                r_idx: {m: float(np.mean(eval_passes_by_rec[e][w_id][r_idx][m])) for m in models_list}
                for r_idx in range(len(valid_spaces[w_id].valid_solutions))
            }
            for w_id in worlds
        }
        for e in evaluators
    }

    # Compute Canonical Draw 0 and E3 Oracle Rankings
    canonical_scores = {}
    for e in evaluators:
        canonical_scores[e] = {m: float(np.mean([world_ref_scores[e][w_id][0][m] for w_id in worlds])) for m in models_list}

    oracle_scores = {m: float(np.mean([world_ref_scores["E3_SEMANTIC_ORACLE"][w_id][0][m] for w_id in worlds])) for m in models_list}
    oracle_ranking = get_model_ranking(oracle_scores)

    # 5. Build Distribution Probability Vectors
    dist_specs = []

    # Distribution A: Uniform
    dist_specs.append({
        "id": "UNIFORM",
        "name": "Uniform",
        "type": "uniform",
        "param": None,
        "description": "Uniform sampling across all valid solutions: P(R) = 1 / |V(x)|"
    })

    # Distribution B: Canonical Bias (p in [0.0, 0.25, 0.50, 0.75, 0.80, 0.90, 0.95, 0.99])
    for p in [0.0, 0.25, 0.50, 0.75, 0.80, 0.90, 0.95, 0.99]:
        dist_specs.append({
            "id": f"CANONICAL_BIAS_P{int(p*100):02d}",
            "name": f"Canonical Bias (p={p:.2f})",
            "type": "canonical_bias",
            "param": p,
            "description": f"P(R=R0) = {p:.2f}, remaining {1-p:.2f} uniform over V(x) \\ {{R0}}"
        })

    # Distribution C: Similarity Bias
    dist_specs.append({
        "id": "SIMILARITY_BIAS",
        "name": "Similarity Bias",
        "type": "similarity_bias",
        "param": None,
        "description": "Inverse structural distance weighting: w(R) = 1 / (1 + d(R, R0)) normalized"
    })

    # Distribution D: Adversarial Upper-Bound Stress Condition
    dist_specs.append({
        "id": "ADVERSARIAL_UPPER_BOUND",
        "name": "Adversarial Upper-Bound Stress Condition",
        "type": "adversarial",
        "param": None,
        "description": "Deterministic worst-case reference maximizing candidate score disagreement with canonical reference"
    })

    # Build per-world probability arrays
    world_probs = {}
    for spec in dist_specs:
        dist_id = spec["id"]
        dtype = spec["type"]
        world_probs[dist_id] = {}

        for w_id, w in worlds.items():
            n_v = len(valid_spaces[w_id].valid_solutions)
            if dtype == "uniform":
                probs = np.full(n_v, 1.0 / n_v)
            elif dtype == "canonical_bias":
                p = spec["param"]
                if n_v == 1:
                    probs = np.array([1.0])
                else:
                    if p == 0.0:
                        probs = np.zeros(n_v)
                        probs[1:] = 1.0 / (n_v - 1)
                    else:
                        probs = np.full(n_v, (1.0 - p) / (n_v - 1))
                        probs[0] = p
            elif dtype == "similarity_bias":
                v_sols = valid_spaces[w_id].valid_solutions
                r0 = v_sols[0]
                dists = [compute_structural_distance(w, r, r0) for r in v_sols]
                weights = [1.0 / (1.0 + d) for d in dists]
                total_w = sum(weights)
                probs = np.array([w_i / total_w for w_i in weights])
            elif dtype == "adversarial":
                v_sols = valid_spaces[w_id].valid_solutions
                can_scores = [world_ref_scores["E2_NORMALIZED_MATCH"][w_id][0][m] for m in models_list]
                max_diff = -1.0
                best_r = 0
                for r_idx in range(len(v_sols)):
                    r_scores = [world_ref_scores["E2_NORMALIZED_MATCH"][w_id][r_idx][m] for m in models_list]
                    diff = float(np.sum(np.abs(np.array(r_scores) - np.array(can_scores))))
                    if diff > max_diff:
                        max_diff = diff
                        best_r = r_idx
                probs = np.zeros(n_v)
                probs[best_r] = 1.0

            world_probs[dist_id][w_id] = probs

    # 6. Execute Fast Monte Carlo Sampling per Distribution
    sorted_world_ids = sorted(list(worlds.keys()))
    results_by_dist = {}
    summary_rows = []

    for dist_idx, spec in enumerate(dist_specs):
        dist_id = spec["id"]
        dist_name = spec["name"]
        dtype = spec["type"]
        param = spec["param"]
        seed = base_seed + dist_idx

        rng = np.random.RandomState(seed)
        n_samples = 1 if dtype == "adversarial" else n_draws

        # Sample indices matrix of shape (n_samples, 24)
        sampled_indices_mat = np.zeros((n_samples, len(sorted_world_ids)), dtype=int)
        for w_idx, w_id in enumerate(sorted_world_ids):
            p = world_probs[dist_id][w_id]
            if dtype == "adversarial":
                sampled_indices_mat[:, w_idx] = int(np.argmax(p))
            else:
                sampled_indices_mat[:, w_idx] = rng.choice(len(p), size=n_samples, p=p)

        dist_eval_results = {}

        for e_id in ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"]:
            # Build 3D array of world scores: shape (24, max_refs, n_models)
            max_refs = max(len(valid_spaces[w_id].valid_solutions) for w_id in sorted_world_ids)
            scores_tensor = np.zeros((len(sorted_world_ids), max_refs, len(models_list)), dtype=float)
            for w_idx, w_id in enumerate(sorted_world_ids):
                for r_idx in range(len(valid_spaces[w_id].valid_solutions)):
                    for m_idx, m in enumerate(models_list):
                        scores_tensor[w_idx, r_idx, m_idx] = world_ref_scores[e_id][w_id][r_idx][m]

            # Vectorized indexing: benchmark_scores shape (n_samples, n_models)
            # scores_tensor[w_idx, sampled_indices_mat[:, w_idx], :] -> shape (n_samples, n_models)
            draw_scores_mat = np.zeros((n_samples, len(models_list)), dtype=float)
            for w_idx in range(len(sorted_world_ids)):
                draw_scores_mat += scores_tensor[w_idx, sampled_indices_mat[:, w_idx], :]
            draw_scores_mat /= len(sorted_world_ids)

            # Pairwise reversal probability
            if n_samples > 1:
                pairwise_rev_prob, pairwise_details = compute_pairwise_reversal_probability(draw_scores_mat, models_list)
            else:
                pairwise_rev_prob = 0.0
                pairwise_details = {}

            # Oracle ranking recovery
            # Compare rankings against oracle_ranking
            matching_oracle_count = 0
            for d_i in range(n_samples):
                d_s = {m: float(draw_scores_mat[d_i, m_i]) for m_i, m in enumerate(models_list)}
                if get_model_ranking(d_s) == oracle_ranking:
                    matching_oracle_count += 1
            oracle_recovery_rate = float(matching_oracle_count / n_samples)

            # Fast Vectorized Kendall Tau against Canonical Draw 0
            can_vec = np.array([canonical_scores[e_id][m] for m in models_list])
            taus = fast_kendall_tau_b_matrix(can_vec, draw_scores_mat)
            valid_taus = taus[~np.isnan(taus)]
            n_valid = len(valid_taus)
            n_degen = int(np.sum(np.isnan(taus)))

            tau_mean = float(np.mean(valid_taus)) if n_valid > 0 else float("nan")
            tau_std = float(np.std(valid_taus)) if n_valid > 0 else float("nan")
            tau_se = float(tau_std / np.sqrt(n_valid)) if n_valid > 0 else float("nan")

            dist_eval_results[e_id] = {
                "kendall_tau_mean": tau_mean,
                "kendall_tau_std": tau_std,
                "kendall_tau_se": tau_se,
                "kendall_tau_n_valid_draws": n_valid,
                "kendall_tau_n_degenerate_draws": n_degen,
                "pairwise_reversal_probability": pairwise_rev_prob,
                "pairwise_reversals_by_pair": pairwise_details,
                "oracle_recovery_rate": oracle_recovery_rate,
                "oracle_recovery_matching_draws": matching_oracle_count,
                "n_monte_carlo_draws": n_samples,
                "mean_model_scores": {m: float(np.mean(draw_scores_mat[:, m_i])) for m_i, m in enumerate(models_list)}
            }

        results_by_dist[dist_id] = {
            "id": dist_id,
            "name": dist_name,
            "type": dtype,
            "param": param,
            "description": spec["description"],
            "seed": seed if dtype != "adversarial" else None,
            "n_draws": n_samples,
            "evaluators": dist_eval_results
        }

        e1_res = dist_eval_results["E1_CANONICAL_EXACT"]
        e2_res = dist_eval_results["E2_NORMALIZED_MATCH"]
        e3_res = dist_eval_results["E3_SEMANTIC_ORACLE"]

        param_str = f"p={param:.2f}" if param is not None else ("N/A" if dtype != "adversarial" else "Worst-case")
        summary_rows.append({
            "Distribution": dist_name,
            "Parameter": param_str,
            "E1_reversal": f"{e1_res['pairwise_reversal_probability']*100:.2f}%",
            "E2_reversal": f"{e2_res['pairwise_reversal_probability']*100:.2f}%",
            "E1_E3_recovery": f"{e1_res['oracle_recovery_rate']*100:.2f}%",
            "E2_E3_recovery": f"{e2_res['oracle_recovery_rate']*100:.2f}%",
            "E2_tau_b_mean": f"{e2_res['kendall_tau_mean']:.4f}",
            "E2_tau_b_std": f"{e2_res['kendall_tau_std']:.4f}",
            "N_valid_tau": e2_res["kendall_tau_n_valid_draws"]
        })

    # 7. Write JSON and CSV Artifacts
    output_data = {
        "provenance": {
            "experiment_name": "rcr_reference_distribution_sensitivity",
            "timestamp": "2026-10-07T02:40:00+00:00",
            "git_sha": "511327ae04a47afb34274f11fbede3c00d01d627",
            "base_seed": base_seed,
            "n_draws_per_stochastic_distribution": n_draws,
            "n_worlds": len(worlds),
            "n_generations": len(raw_records),
            "input_file_sha256": input_hashes
        },
        "canonical_draw_0": {
            "model_scores": canonical_scores,
            "ranking": {e: get_model_ranking(canonical_scores[e]) for e in evaluators}
        },
        "e3_reference_invariant_ranking": oracle_ranking,
        "e3_reference_invariant_scores": oracle_scores,
        "distributions": results_by_dist,
        "summary_table": summary_rows
    }

    json_path = os.path.join(RESULTS_DIR, "reference_distribution_sensitivity.json")
    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=2)
        f.write("\n")

    csv_path = os.path.join(RESULTS_DIR, "reference_distribution_sensitivity.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[+] Sensitivity analysis complete!")
    print(f"[+] Output written to {json_path} and {csv_path}")
    return output_data


if __name__ == "__main__":
    run_distribution_sensitivity()
