"""
Tests for statistical significance decision stability using world-level sign-flip permutation tests.
"""

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
    # Clear positive shift across all 24 worlds
    diffs = np.ones(24) * 0.5
    p_val = compute_world_level_sign_flip_pvalue(diffs, n_flips=1000)
    assert p_val < 0.05


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
