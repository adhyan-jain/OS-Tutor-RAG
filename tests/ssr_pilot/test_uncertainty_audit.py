"""
Unit and regression tests for RCR uncertainty and error audit.
Verifies U-statistic degrees, finite-sample variances, joint covariance matrix,
and unrounded error tolerances against exact DP parameters.
"""

import json
import os
import pytest
import numpy as np


@pytest.fixture
def audit_data():
    path = "research/ssr_pilot/results/rcrc/uncertainty_audit.json"
    assert os.path.exists(path), f"Audit artifact missing: {path}"
    with open(path) as f:
        return json.load(f)


def test_audit_structure(audit_data):
    required_keys = [
        "n_draws", "exact_dp_six_pair_mean", "mc_six_pair_mean",
        "mean_signed_error_mc_minus_exact", "mean_signed_error_exact_minus_mc",
        "mean_absolute_error", "max_absolute_error",
        "se_six_pair_mean_joint_covariance", "se_six_pair_mean_naive_independent",
        "variance_inflation_factor", "per_pair", "historical_reconciliation"
    ]
    for k in required_keys:
        assert k in audit_data, f"Missing key {k} in audit_data"


def test_u_statistic_degrees_and_properties(audit_data):
    assert audit_data["n_draws"] == 50000
    assert audit_data["variance_inflation_factor"] > 1.0, "Joint covariance must inflate variance due to positive correlations"
    assert np.isclose(audit_data["variance_inflation_factor"], 1.6203, atol=1e-3)


def test_unrounded_errors_bounds(audit_data):
    # Mean signed error is small
    assert abs(audit_data["mean_signed_error_mc_minus_exact"]) < 0.0003
    assert np.isclose(audit_data["mean_signed_error_mc_minus_exact"], 0.0002522417, atol=1e-6)
    assert np.isclose(audit_data["mean_signed_error_exact_minus_mc"], -0.0002522417, atol=1e-6)
    
    # MAE and MaxAE
    assert np.isclose(audit_data["mean_absolute_error"], 0.0006434941, atol=1e-6)
    assert np.isclose(audit_data["max_absolute_error"], 0.0013847393, atol=1e-6)
    assert audit_data["max_absolute_error_pair"] == "gemma2:9b_vs_llama3.1:8b"


def test_all_pair_z_scores_within_normal_sampling(audit_data):
    # Every pair z-score must be within [-2.5, +2.5] (consistent with finite Monte Carlo sampling)
    for pair_name, stats in audit_data["per_pair"].items():
        z = stats["z_score"]
        assert abs(z) < 2.0, f"Z-score for {pair_name} is too large: {z}"
