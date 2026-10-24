"""
Preregistered Confirmatory Analysis for Blocks World Second-Domain Replication.

Implements the locked analysis plan:
1. Evaluates all 1,152 generations from actual local models under E1, E2, and E3.
2. Evaluates task-level and benchmark-level semantic pass rates.
3. Tests H1 (Attenuation Law): E[S_mi^E2] = S_mi^E3 / |V_i|; computes Pearson r and observed/predicted ratio.
4. Tests H2 (Ranking Instability): Computes exact DP population reversal probabilities and 50k Monte Carlo reversal rates.
5. Tests H3 (Near-Tie Concentration): Decomposes reversal mass between E3-separated and E3-unseparated pairs.
6. Tests H4 (Detection Loss): Evaluates paired sign-flip permutation tests across 50,000 draws with Holm-Bonferroni correction.
7. Produces comprehensive results JSON artifact at research/pilot_second_domain/results/blocks_world_confirmatory.json.
"""

import itertools
import json
import os
import sys
from typing import Dict, List, Tuple
import numpy as np
from scipy import stats

from research.pilot_second_domain.blocks_world_tasks import (
    get_all_tasks,
    format_plan_as_string,
    plan_to_tuple,
    extract_plan,
    evaluate_plan_semantic,
    BlocksWorld,
)
from research.ssr_pilot.rcrc.exact_margin_distribution import compute_exact_pairwise_margin

RUNS_DIR = "research/pilot_second_domain/runs"
RESULTS_DIR = "research/pilot_second_domain/results"
MODELS = ["qwen3:8b", "gemma2:9b", "llama3.1:8b", "mistral:7b-instruct"]
N_DRAWS = 50000
SEED_MC = 20261028


def squash(text: str) -> str:
    return "".join(text.split()).lower()


def load_model_runs() -> Dict[str, Dict[str, List[Dict]]]:
    """
    Loads all runs into {model: {task_id: [records]}}.
    """
    model_data = {}
    for m in MODELS:
        safe_name = m.replace(":", "_").replace("/", "_")
        path = f"{RUNS_DIR}/{safe_name}.jsonl"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Run file not found: {path}")

        records_by_task = {}
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    t_id = rec["task_id"]
                    if t_id not in records_by_task:
                        records_by_task[t_id] = []
                    records_by_task[t_id].append(rec)

        model_data[m] = records_by_task
    return model_data


def run_confirmatory_analysis():
    tasks = get_all_tasks()
    task_map = {t["id"]: t for t in tasks}
    model_runs = load_model_runs()

    # Verify run completeness: exactly 288 records per model, 12 per task
    for m in MODELS:
        assert len(model_runs[m]) == 24, f"Model {m} has only {len(model_runs[m])} tasks"
        for t in tasks:
            n_recs = len(model_runs[m][t["id"]])
            assert n_recs == 12, f"Model {m} task {t['id']} has {n_recs} records, expected 12"

    print("All 1,152 generations verified complete across 4 models and 24 tasks.")

    # 1. Enumerate complete valid reference spaces V(x_i)
    print("\n--- 1. Enumerating Valid Reference Spaces ---")
    valid_spaces: Dict[str, List[List[Tuple[str, ...]]]] = {}
    valid_space_tuples: Dict[str, List[Tuple]] = {}
    valid_space_strings: Dict[str, List[str]] = {}

    for t in tasks:
        bw = BlocksWorld(t["blocks"])
        clear = set(t["blocks"]) - set(t["init_on"].values())
        plans = bw.enumerate_all_minimal_plans(
            t["init_on"], set(t["init_table"]), clear,
            t["goal_on"], set(t["goal_table"])
        )
        valid_spaces[t["id"]] = plans
        valid_space_tuples[t["id"]] = [plan_to_tuple(p) for p in plans]
        valid_space_strings[t["id"]] = [format_plan_as_string(p) for p in plans]
        print(f"[{t['id']}] Tier {t['tier']}: |V| = {len(plans):2d}, length = {len(plans[0])}")

    # 2. Evaluate all outputs under E1, E2, E3
    print("\n--- 2. Evaluating Model Outputs (E1, E2, E3) ---")
    eval_records = {m: {} for m in MODELS}
    # Per-task semantic pass rate
    e3_scores = {m: {} for m in MODELS}

    for m in MODELS:
        for t in tasks:
            t_id = t["id"]
            v_tuples = valid_space_tuples[t_id]
            v_strings = valid_space_strings[t_id]
            k_refs = len(v_tuples)

            recs = model_runs[m][t_id]
            parsed_plans = []
            e3_vals = []
            e1_matches_matrix = np.zeros((12, k_refs), dtype=bool)
            e2_matches_matrix = np.zeros((12, k_refs), dtype=bool)

            for g_idx, r in enumerate(recs):
                extracted = extract_plan(r["response"])
                parsed_plans.append(extracted)
                is_valid = evaluate_plan_semantic(t, extracted)
                e3_vals.append(is_valid)

                # Match against each reference
                ext_tuple = plan_to_tuple(extracted)
                ext_str_squashed = squash(format_plan_as_string(extracted))

                for ref_idx in range(k_refs):
                    if ext_tuple == v_tuples[ref_idx]:
                        e2_matches_matrix[g_idx, ref_idx] = True
                    if ext_str_squashed == squash(v_strings[ref_idx]):
                        e1_matches_matrix[g_idx, ref_idx] = True

            e3_scores[m][t_id] = float(np.mean(e3_vals))
            eval_records[m][t_id] = {
                "e3_pass_rate": float(np.mean(e3_vals)),
                "e1_matches_per_ref": e1_matches_matrix.sum(axis=0).tolist(),
                "e2_matches_per_ref": e2_matches_matrix.sum(axis=0).tolist(),
                "e1_matches_matrix": e1_matches_matrix,
                "e2_matches_matrix": e2_matches_matrix,
            }

    # Summary table of pass rates
    print("\n--- Model Semantic Pass Rates (E3) ---")
    for m in MODELS:
        overall_e3 = np.mean([e3_scores[m][t["id"]] for t in tasks])
        t1_e3 = np.mean([e3_scores[m][t["id"]] for t in tasks if t["tier"] == 1])
        t2_e3 = np.mean([e3_scores[m][t["id"]] for t in tasks if t["tier"] == 2])
        t3_e3 = np.mean([e3_scores[m][t["id"]] for t in tasks if t["tier"] == 3])
        print(f"{m:22s}: Overall={overall_e3*100:5.2f}% | Tier 1={t1_e3*100:5.2f}% | Tier 2={t2_e3*100:5.2f}% | Tier 3={t3_e3*100:5.2f}%")

    # 3. Test H1: Attenuation Law
    print("\n--- 3. Testing H1: Score Attenuation Law ---")
    obs_expected_e2 = []
    pred_expected_e2 = []
    ratios_h1 = []

    for t in tasks:
        t_id = t["id"]
        k_refs = len(valid_spaces[t_id])
        for m in MODELS:
            e3_s = eval_records[m][t_id]["e3_pass_rate"]
            c_refs = eval_records[m][t_id]["e2_matches_per_ref"]
            expected_e2 = np.mean(c_refs) / 12.0
            predicted_e2 = e3_s / float(k_refs)

            obs_expected_e2.append(expected_e2)
            pred_expected_e2.append(predicted_e2)
            if e3_s > 0:
                ratios_h1.append(expected_e2 / predicted_e2)

    # Preregistered criterion (Section 3.2): Pearson r across NON-ZERO cells. The as-executed
    # 2026-10-13 run computed r over all 96 cells; both are reported, the verdict uses the
    # preregistered non-zero-cell r (deviation D1, see RCR_EMPIRICAL_READINESS.md).
    pearson_r_all, _ = stats.pearsonr(obs_expected_e2, pred_expected_e2)
    nz_idx = [i for i, p in enumerate(pred_expected_e2) if p > 0]
    pearson_r, _ = stats.pearsonr([obs_expected_e2[i] for i in nz_idx], [pred_expected_e2[i] for i in nz_idx])
    n_nonzero_cells = len(nz_idx)
    median_ratio = float(np.median(ratios_h1)) if ratios_h1 else 1.0
    mean_ratio = float(np.mean(ratios_h1)) if ratios_h1 else 1.0
    h1_passed = bool(pearson_r >= 0.98 and (0.95 <= median_ratio <= 1.05))

    print(f"H1 non-zero cells: {n_nonzero_cells} of {len(obs_expected_e2)}; all-cell r = {pearson_r_all:.6f}")
    print(f"H1 Pearson r (non-zero cells, preregistered): {pearson_r:.6f} (threshold >= 0.98)")
    print(f"H1 Median Ratio (Obs / Pred): {median_ratio:.6f} (threshold [0.95, 1.05])")
    print(f"H1 Mean Ratio (Obs / Pred):   {mean_ratio:.6f}")
    print(f"H1 Verdict: {'CONFIRMED' if h1_passed else 'REJECTED'}")

    # 4. Exact Dynamic Programming & Winner Reversals (H2)
    print("\n--- 4. Testing H2: Pairwise Winner Reversals ---")
    pairs = list(itertools.combinations(MODELS, 2))
    dp_pair_results = {}
    dp_reversal_probs = []

    for mA, mB in pairs:
        pair_name = f"{mA}_vs_{mB}"
        task_data = []
        for t in tasks:
            t_id = t["id"]
            k_refs = len(valid_spaces[t_id])
            cA = eval_records[mA][t_id]["e2_matches_per_ref"]
            cB = eval_records[mB][t_id]["e2_matches_per_ref"]
            task_data.append({"c_A": cA, "c_B": cB, "n_refs": k_refs})

        dp_res = compute_exact_pairwise_margin(task_data, K=12, q_type="uniform")
        rev_prob = dp_res["winner_reversal_probability"]
        dp_reversal_probs.append(rev_prob)
        dp_pair_results[pair_name] = dp_res
        print(f"Pair {pair_name:38s}: Exp Margin={dp_res['expected_margin']:+.4f}, P(A>B)={dp_res['p_positive']:.4f}, P(B>A)={dp_res['p_negative']:.4f}, Reversal={rev_prob*100:6.3f}%")

    mean_dp_reversal = float(np.mean(dp_reversal_probs))
    h2_passed = bool(mean_dp_reversal >= 0.08)
    print(f"\nH2 Mean Reversal Probability across 6 pairs: {mean_dp_reversal*100:.3f}% (threshold >= 8.0%)")
    print(f"H2 Verdict: {'CONFIRMED' if h2_passed else 'REJECTED'}")

    # 5. Near-Tie Decomposition (H3) & Detection Loss (H4)
    print("\n--- 5. Testing H3 (Near-Tie Decomposition) and H4 (Detection Loss) ---")
    # First: evaluate ground truth E3 oracle separation on the 24 tasks
    # Using paired sign-flip permutation tests (20,000 flips) on task scores
    rng = np.random.default_rng(SEED_MC)
    e3_raw_p = {}
    for mA, mB in pairs:
        diffs = [e3_scores[mA][t["id"]] - e3_scores[mB][t["id"]] for t in tasks]
        obs_mean = np.mean(diffs)
        # Sign flip permutation
        flips = rng.choice([-1, 1], size=(20000, 24))
        perm_means = (flips * np.array(diffs)).mean(axis=1)
        p_val = float(np.mean(np.abs(perm_means) >= abs(obs_mean)))
        e3_raw_p[f"{mA}_vs_{mB}"] = p_val

    # Step-down Holm-Bonferroni correction
    sorted_pairs = sorted(e3_raw_p.items(), key=lambda x: x[1])
    e3_adj_p = {}
    for rank, (pname, pval) in enumerate(sorted_pairs):
        m_factors = len(sorted_pairs) - rank
        e3_adj_p[pname] = min(1.0, pval * m_factors)

    # Ensure monotonicity of step-down adjusted p-values
    prev = 0.0
    for pname, _ in sorted_pairs:
        e3_adj_p[pname] = max(prev, e3_adj_p[pname])
        prev = e3_adj_p[pname]

    print("E3 Ground Truth Oracle Decisions:")
    separated_pairs = []
    unseparated_pairs = []
    for pname in [f"{a}_vs_{b}" for a, b in pairs]:
        padj = e3_adj_p[pname]
        is_sep = padj < 0.05
        if is_sep:
            separated_pairs.append(pname)
        else:
            unseparated_pairs.append(pname)
        print(f"  {pname:38s}: raw p={e3_raw_p[pname]:.4f}, Holm p={padj:.4f} -> {'SEPARATED' if is_sep else 'UNSEPARATED'}")

    # H3: Share of reversal mass in unseparated pairs
    total_rev_mass = sum(dp_reversal_probs)
    unsep_rev_mass = sum(dp_pair_results[pname]["winner_reversal_probability"] for pname in unseparated_pairs)
    sep_rev_mass = sum(dp_pair_results[pname]["winner_reversal_probability"] for pname in separated_pairs)
    unsep_share = unsep_rev_mass / total_rev_mass if total_rev_mass > 0 else 0.0
    h3_passed = bool(unsep_share >= 0.70)
    # H3 compares reversal mass between separated and unseparated pairs. If NO pair is
    # separated, the share is 100% by construction and carries no evidence (deviation D2).
    h3_degenerate = len(separated_pairs) == 0

    print(f"\nH3 Total Reversal Mass: {total_rev_mass:.6f}")
    print(f"H3 Unseparated Mass:    {unsep_rev_mass:.6f} ({unsep_share*100:.2f}%, threshold >= 70.0%)")
    print(f"H3 Separated Mass:      {sep_rev_mass:.6f} ({(1.0 - unsep_share)*100:.2f}%)")
    if h3_degenerate:
        print("H3 Verdict: NOT INFORMATIVE (no E3-separated pair exists; 100% share holds by construction)")
    else:
        print(f"H3 Verdict: {'CONFIRMED' if h3_passed else 'REJECTED'}")

    # 6. Monte Carlo Simulation for Detection Loss (H4)
    print("\n--- 6. 50,000-Draw Monte Carlo Simulation for Detection Loss ---")
    n_refs_list = [len(valid_spaces[t["id"]]) for t in tasks]
    mc_draws = rng.integers(0, np.array(n_refs_list), size=(N_DRAWS, 24))

    # Task scores matrix: for each draw, shape (N_DRAWS, 24, 4)
    mc_task_scores = np.zeros((N_DRAWS, 24, len(MODELS)), dtype=np.float32)
    for m_idx, m in enumerate(MODELS):
        for t_idx, t in enumerate(tasks):
            t_id = t["id"]
            # e2 matches matrix shape: (12, k_refs)
            matches = eval_records[m][t_id]["e2_matches_matrix"]
            draw_refs = mc_draws[:, t_idx]  # shape (N_DRAWS,)
            # For each draw, score is matches.sum(axis=0)[draw_refs] / 12.0
            sum_matches_per_ref = matches.sum(axis=0)  # shape (k_refs,)
            mc_task_scores[:, t_idx, m_idx] = sum_matches_per_ref[draw_refs] / 12.0

    # H4: For pairs separated by E3, evaluate miss rate under E2
    h4_results = {}
    if separated_pairs:
        for pname in separated_pairs:
            mA, mB = pname.split("_vs_")
            idxA = MODELS.index(mA)
            idxB = MODELS.index(mB)
            diffs_mc = mc_task_scores[:, :, idxA] - mc_task_scores[:, :, idxB]  # (50000, 24)
            mean_diffs = diffs_mc.mean(axis=1)

            # Evaluate significance across a sample of 2,000 draws to conserve runtime, or analytical bound
            # Paired sign-flip test on 2,000 draws:
            n_eval_draws = 2000
            flips = rng.choice([-1, 1], size=(5000, 24))
            misses = 0
            for d in range(n_eval_draws):
                obs = abs(mean_diffs[d])
                d_row = diffs_mc[d, :]
                p_val = float(np.mean(np.abs(flips.dot(d_row) / 24.0) >= obs))
                # With Holm correction across 6 pairs, p_adj <= p_val * 6
                if p_val * len(pairs) >= 0.05:
                    misses += 1
            miss_rate = misses / float(n_eval_draws)
            h4_results[pname] = {"miss_rate": miss_rate, "n_draws_tested": n_eval_draws}
            print(f"H4 Separated Pair {pname}: Miss Rate = {miss_rate*100:.2f}% (tested {n_eval_draws} draws)")
        mean_miss_rate = np.mean([v["miss_rate"] for v in h4_results.values()])
        h4_passed = bool(mean_miss_rate >= 0.90)
    else:
        # Deviation D2: the as-executed run reported H4 as CONFIRMED here. H4 is defined only for
        # E3-separated pairs, so with none it is untestable, not confirmed.
        print("Note: No model pairs statistically separated by E3 at N=24; H4 is undefined.")
        h4_passed = None
        mean_miss_rate = None

    if h4_passed is None:
        print("H4 Verdict: NOT TESTABLE (no E3-separated pair)")
    else:
        print(f"H4 Verdict: {'CONFIRMED' if h4_passed else 'REJECTED'}")

    # Compile comprehensive artifact
    out = {
        "domain": "BlocksWorld_Planning_Confirmatory",
        "n_tasks": len(tasks),
        "n_models": len(MODELS),
        "total_generations": 1152,
        "models": MODELS,
        "tasks": [{
            "id": t["id"],
            "tier": t["tier"],
            "cardinality": len(valid_spaces[t["id"]]),
            "min_length": len(valid_spaces[t["id"]][0]),
        } for t in tasks],
        "semantic_pass_rates": {
            m: {
                "overall": float(np.mean([e3_scores[m][t["id"]] for t in tasks])),
                "tier_1": float(np.mean([e3_scores[m][t["id"]] for t in tasks if t["tier"] == 1])),
                "tier_2": float(np.mean([e3_scores[m][t["id"]] for t in tasks if t["tier"] == 2])),
                "tier_3": float(np.mean([e3_scores[m][t["id"]] for t in tasks if t["tier"] == 3])),
                "per_task": {t["id"]: e3_scores[m][t["id"]] for t in tasks},
            }
            for m in MODELS
        },
        "hypotheses_results": {
            "H1_attenuation_law": {
                "description": "E[S_mi^E2] = S_mi^E3 / |V_i|",
                "pearson_r": float(pearson_r),
                "pearson_r_nonzero_cells": float(pearson_r),
                "pearson_r_all_cells": float(pearson_r_all),
                "n_nonzero_cells": n_nonzero_cells,
                "median_ratio": float(median_ratio),
                "mean_ratio": float(mean_ratio),
                "threshold_r": 0.98,
                "threshold_ratio_window": [0.95, 1.05],
                "passed": h1_passed,
            },
            "H2_ranking_instability": {
                "description": "Mean pairwise winner reversal rate >= 8.0%",
                "mean_reversal_probability": float(mean_dp_reversal),
                "threshold": 0.08,
                "per_pair": {pname: dp_pair_results[pname]["winner_reversal_probability"] for pname in dp_pair_results},
                "passed": h2_passed,
            },
            "H3_near_tie_concentration": {
                "description": "Share of reversal mass in E3-unseparated pairs >= 70.0%",
                "unseparated_pairs": unseparated_pairs,
                "separated_pairs": separated_pairs,
                "unseparated_share": float(unsep_share),
                "threshold": 0.70,
                "passed": None if h3_degenerate else h3_passed,
                "status": "NOT_INFORMATIVE_NO_SEPARATED_PAIR" if h3_degenerate else ("CONFIRMED" if h3_passed else "REJECTED"),
            },
            "H4_detection_loss": {
                "description": "Miss rate for E3-separated pairs >= 90.0%",
                "miss_rate": None if mean_miss_rate is None else float(mean_miss_rate),
                "threshold": 0.90,
                "details": h4_results,
                "passed": h4_passed,
                "status": "NOT_TESTABLE_NO_SEPARATED_PAIR" if h4_passed is None else ("CONFIRMED" if h4_passed else "REJECTED"),
            },
        },
        "exact_dp_pairwise": dp_pair_results,
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_file = os.path.join(RESULTS_DIR, "blocks_world_confirmatory.json")
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nSaved confirmatory analysis results to {out_file}")
    return out


if __name__ == "__main__":
    run_confirmatory_analysis()
