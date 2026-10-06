"""
Tests for statistical significance decision stability using world-level sign-flip permutation tests.
"""

import pytest
import numpy as np
from research.ssr_pilot.rcrc.significance_metrics import (
    compute_world_level_sign_flip_pvalue,
    holm_bonferroni_correction,
)


def test_world_level_sign_flip_pvalue_zero():
    # Equal differences yield p=1.0
    diffs = np.zeros(24)
    p_val = compute_world_level_sign_flip_pvalue(diffs, n_flips=1000)
    assert p_val == 1.0


def test_world_level_sign_flip_pvalue_large_diff():
    # Clear positive shift across all 24 worlds — should be highly significant.
    diffs = np.ones(24) * 0.5
    p_val = compute_world_level_sign_flip_pvalue(diffs, n_flips=1000)
    assert p_val < 0.05


def test_world_level_sign_flip_requires_24_worlds():
    # The preregistered test requires exactly N=24 worlds.
    with pytest.raises(AssertionError):
        compute_world_level_sign_flip_pvalue(np.ones(23) * 0.5, n_flips=100)


def test_sign_flip_mc_plus1_correction():
    # The +1 continuity correction means p_val = (count + 1) / (n_flips + 1).
    # When obs_stat is larger than ALL permuted means, count=0, so p_val = 1/(n_flips+1), not 0.
    diffs = np.ones(24) * 1.0  # maximally obvious signal
    p_val = compute_world_level_sign_flip_pvalue(diffs, n_flips=100, seed=42)
    assert p_val > 0.0, "MC +1 correction must ensure p_val > 0 even for a perfect signal"
    assert p_val <= 2 / 101, f"Expected p_val ≈ 1/101 for perfect signal, got {p_val}"


def test_holm_bonferroni_correction():
    raw_p = {
        "pair1": 0.01,
        "pair2": 0.04,
        "pair3": 0.10,
    }
    corrected = holm_bonferroni_correction(raw_p)
    assert corrected["pair1"] == 0.03  # 0.01 * 3
    assert corrected["pair2"] == 0.08  # max(0.03, 0.04 * 2)
    assert corrected["pair3"] == 0.10  # max(0.08, 0.10 * 1)


def test_holm_bonferroni_running_max_enforced():
    # When adjusted value for a later pair would be lower than the earlier pair's adjusted value,
    # the running max must enforce monotonicity (step-down property).
    raw_p = {
        "pair1": 0.001,   # adjusted = 0.003
        "pair2": 0.049,   # adjusted = 0.098, running_max = 0.098
        "pair3": 0.051,   # adjusted = 0.051, but running_max = max(0.098, 0.051) = 0.098
    }
    corrected = holm_bonferroni_correction(raw_p)
    vals = [corrected["pair1"], corrected["pair2"], corrected["pair3"]]
    assert vals[0] <= vals[1] <= vals[2], f"Holm values must be non-decreasing: {vals}"
    assert corrected["pair3"] == corrected["pair2"], "Running max must enforce monotonicity"


def test_holm_bonferroni_single_pair():
    # Edge case: m=1 pair — adjusted == raw.
    corrected = holm_bonferroni_correction({"only": 0.03})
    assert corrected["only"] == pytest.approx(0.03)
