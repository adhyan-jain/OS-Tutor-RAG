"""
Forensic Uncertainty and Numerical Error Audit for RCR Pairwise Reversal Estimator.

Rigorously computes:
1. Exact DP population parameter theta_p = 2 * p_+ * p_- for each of the 6 model pairs.
2. Degree-2 U-statistic reversal estimator U_p = 2 * N_+ * N_- / (M * (M - 1)) from 50,000 MC draws.
3. Hajek projection h1_p(R) and full 6x6 covariance matrix Sigma_1 across shared reference vectors.
4. Exact finite-sample U-statistic variance and standard error for each pair.
5. Variance and SE of the 6-pair mean accounting for inter-pair dependencies (variance inflation factor).
6. Unrounded error metrics: signed errors (MC - Exact and Exact - MC), MAE, MaxAE.
7. Reconciliation of all historical reversal figures (18.61%, 17.56%, 17.23%, 17.18%, 17.1518%).
"""

import json
import os
from typing import Dict, List
import numpy as np

from research.ssr_pilot.rcr_extended_analysis import (
    build_score_tensors,
    sample_reference_vectors,
    draw_world_scores,
    pair_list,
    EVALUATORS,
    N_DRAWS,
    SEED_DRAWS,
)

RESULTS_PATH = "research/ssr_pilot/results/rcrc/uncertainty_audit.json"


def run_uncertainty_audit() -> Dict:
    # 1. Load exact DP results
    with open("research/ssr_pilot/results/rcrc/exact_dp_analysis.json") as f:
        exact_dp_full = json.load(f)
    exact_dp_e2 = exact_dp_full["evaluators"]["E2_NORMALIZED_MATCH"]

    # 2. Build score tensors and sample 50,000 draws (seed 20261016)
    scores, n_refs, world_ids, models, run_paths = build_score_tensors()
    idx = sample_reference_vectors(n_refs, N_DRAWS, SEED_DRAWS)
    pw = draw_world_scores(scores["E2_NORMALIZED_MATCH"], idx)
    bench = pw.mean(axis=1)  # shape: (50000, 4)

    pairs = pair_list(models)
    pair_names = [f"{models[i]}_vs_{models[j]}" for i, j in pairs]
    M = N_DRAWS

    # 3. Indicator variables per draw k and pair p
    X_pos = np.zeros((M, len(pairs)), dtype=bool)
    X_neg = np.zeros((M, len(pairs)), dtype=bool)
    X_zero = np.zeros((M, len(pairs)), dtype=bool)

    for p, (i, j) in enumerate(pairs):
        diff = bench[:, i] - bench[:, j]
        X_pos[:, p] = diff > 1e-9
        X_neg[:, p] = diff < -1e-9
        X_zero[:, p] = np.abs(diff) <= 1e-9

    N_pos = X_pos.sum(axis=0)
    N_neg = X_neg.sum(axis=0)
    N_zero = X_zero.sum(axis=0)

    p_hat_pos = N_pos / M
    p_hat_neg = N_neg / M
    p_hat_zero = N_zero / M

    # U-statistic per pair
    U_p = 2.0 * N_pos * N_neg / (M * (M - 1))

    # Exact DP parameters
    theta_exact = np.array([exact_dp_e2["per_pair"][pname]["winner_reversal_probability"] for pname in pair_names])
    p_exact_pos = np.array([exact_dp_e2["per_pair"][pname]["p_positive"] for pname in pair_names])
    p_exact_neg = np.array([exact_dp_e2["per_pair"][pname]["p_negative"] for pname in pair_names])
    p_exact_zero = np.array([exact_dp_e2["per_pair"][pname]["p_zero"] for pname in pair_names])

    # 4. Hajek projection for each draw k, pair p
    # h1_p(R_k) = p_neg * I(pos) + p_pos * I(neg)
    h1_sample = np.zeros((M, len(pairs)), dtype=np.float64)
    h1_exact = np.zeros((M, len(pairs)), dtype=np.float64)
    for p in range(len(pairs)):
        h1_sample[:, p] = p_hat_neg[p] * X_pos[:, p] + p_hat_pos[p] * X_neg[:, p]
        h1_exact[:, p] = p_exact_neg[p] * X_pos[:, p] + p_exact_pos[p] * X_neg[:, p]

    # Covariance matrices of first projection
    Sigma1_sample = np.cov(h1_sample, rowvar=False)
    Sigma1_exact = np.cov(h1_exact, rowvar=False)

    # 5. Exact Hoeffding degree-2 U-statistic finite-sample variance per pair
    zeta1_analytical = p_exact_pos * p_exact_neg * (p_exact_pos + p_exact_neg - 4.0 * p_exact_pos * p_exact_neg)
    zeta2_analytical = theta_exact * (1.0 - theta_exact)
    var_U_analytical = 4.0 * (M - 2) / (M * (M - 1)) * zeta1_analytical + 2.0 / (M * (M - 1)) * zeta2_analytical
    se_U_analytical = np.sqrt(var_U_analytical)

    var_U_sample = 4.0 * np.diag(Sigma1_sample) / M
    se_U_sample = np.sqrt(var_U_sample)

    # 6. Aggregate 6-pair mean analysis
    mean_U = float(np.mean(U_p))
    mean_exact = float(np.mean(theta_exact))

    # Variance of the 6-pair mean accounting for shared reference vectors (joint covariance)
    var_mean_U_joint = float((4.0 / (36.0 * M)) * np.sum(Sigma1_sample))
    se_mean_U_joint = float(np.sqrt(var_mean_U_joint))

    # Naive variance assuming pair independence
    var_mean_U_naive = float((1.0 / 36.0) * np.sum(var_U_sample))
    se_mean_U_naive = float(np.sqrt(var_mean_U_naive))
    vif = float(var_mean_U_joint / var_mean_U_naive)

    # 7. Unrounded errors
    err_mc_minus_exact = U_p - theta_exact
    err_exact_minus_mc = theta_exact - U_p
    abs_errors = np.abs(err_mc_minus_exact)

    mean_signed_err_mc_exact = float(np.mean(err_mc_minus_exact))
    mean_signed_err_exact_mc = float(np.mean(err_exact_minus_mc))
    mae = float(np.mean(abs_errors))
    max_ae = float(np.max(abs_errors))
    max_ae_pair = pair_names[int(np.argmax(abs_errors))]

    # Per-pair results dictionary
    per_pair = {}
    for p, pname in enumerate(pair_names):
        per_pair[pname] = {
            "exact_dp_theta": float(theta_exact[p]),
            "p_exact_positive": float(p_exact_pos[p]),
            "p_exact_negative": float(p_exact_neg[p]),
            "p_exact_zero": float(p_exact_zero[p]),
            "mc_u_statistic": float(U_p[p]),
            "p_sample_positive": float(p_hat_pos[p]),
            "p_sample_negative": float(p_hat_neg[p]),
            "p_sample_zero": float(p_hat_zero[p]),
            "error_mc_minus_exact": float(err_mc_minus_exact[p]),
            "error_exact_minus_mc": float(err_exact_minus_mc[p]),
            "abs_error": float(abs_errors[p]),
            "se_analytical": float(se_U_analytical[p]),
            "se_sample": float(se_U_sample[p]),
            "z_score": float(err_mc_minus_exact[p] / se_U_analytical[p]),
        }

    # Historical reconciliation
    historical_reconciliation = {
        "legacy_pre_d9_defect": {
            "value": 0.186137,
            "display": "18.61%",
            "provenance": "PAPER_FINAL.md (legacy), FINAL_STATISTICS.md (seed 20261005)",
            "defect_description": "Omitted rule D3(b); 7 mistral:7b outputs with unknown entities counted as E2 matches.",
            "status": "SUPERSEDED_BY_DEFECT_CORRECTION",
        },
        "corrected_mc_seed_20261005": {
            "value": 0.1755719028,
            "display": "17.56%",
            "provenance": "rcr_summary.json (seed 20261005)",
            "status": "VALID_MONTE_CARLO_SAMPLE_SEED_20261005",
        },
        "corrected_mc_seed_20261007": {
            "value": 0.1723479798,
            "display": "17.23%",
            "provenance": "reference_distribution_sensitivity.json (seed 20261007)",
            "status": "VALID_MONTE_CARLO_SAMPLE_SEED_20261007",
        },
        "corrected_mc_seed_20261016": {
            "value": 0.1717702517,
            "display": "17.18%",
            "provenance": "extended_analysis.json (seed 20261016)",
            "status": "VALID_MONTE_CARLO_SAMPLE_SEED_20261016",
        },
        "exact_dp_population_parameter": {
            "value": 0.1715180100,
            "display": "17.1518%",
            "provenance": "exact_dp_analysis.json",
            "status": "GROUND_TRUTH_POPULATION_PARAMETER",
        },
    }

    out = {
        "n_draws": M,
        "seed_draws": SEED_DRAWS,
        "n_models": len(models),
        "n_pairs": len(pairs),
        "exact_dp_six_pair_mean": mean_exact,
        "mc_six_pair_mean": mean_U,
        "mean_signed_error_mc_minus_exact": mean_signed_err_mc_exact,
        "mean_signed_error_exact_minus_mc": mean_signed_err_exact_mc,
        "mean_absolute_error": mae,
        "max_absolute_error": max_ae,
        "max_absolute_error_pair": max_ae_pair,
        "se_six_pair_mean_joint_covariance": se_mean_U_joint,
        "se_six_pair_mean_naive_independent": se_mean_U_naive,
        "variance_inflation_factor": vif,
        "aggregate_z_score": float(mean_signed_err_mc_exact / se_mean_U_joint),
        "per_pair": per_pair,
        "joint_covariance_matrix_sigma1": Sigma1_sample.tolist(),
        "historical_reconciliation": historical_reconciliation,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)

    return out


if __name__ == "__main__":
    res = run_uncertainty_audit()
    print("Audit run complete.")
    print(f"Exact DP Mean:         {res['exact_dp_six_pair_mean']:.10f}")
    print(f"Monte Carlo Mean:      {res['mc_six_pair_mean']:.10f}")
    print(f"Mean Signed (MC - Ex): {res['mean_signed_error_mc_minus_exact']:+.10f}")
    print(f"Mean Signed (Ex - MC): {res['mean_signed_error_exact_minus_mc']:+.10f}")
    print(f"MAE:                   {res['mean_absolute_error']:.10f}")
    print(f"MaxAE:                 {res['max_absolute_error']:.10f} ({res['max_absolute_error_pair']})")
    print(f"SE (Joint Cov):        {res['se_six_pair_mean_joint_covariance']:.10f}")
    print(f"SE (Naive Indep):      {res['se_six_pair_mean_naive_independent']:.10f}")
    print(f"VIF:                   {res['variance_inflation_factor']:.4f}")
    print(f"Aggregate z:           {res['aggregate_z_score']:+.4f}")
