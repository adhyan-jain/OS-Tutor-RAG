"""
Tests for exact_margin_distribution.py and robustness_certificate.py.

All tests use synthetic toy data and run in <5 seconds.
"""

from collections import defaultdict
import pytest
import numpy as np
from research.ssr_pilot.rcrc.exact_margin_distribution import (
    per_task_diff_distribution,
    dp_convolve_margin_distributions,
    compute_exact_pairwise_margin,
)
from research.ssr_pilot.rcrc.robustness_certificate import (
    tv_distance,
    tv_bound_on_expected_margin_change,
    certify_margin_sign,
    tv_budget_for_canonical_bias,
)


def test_always_wins():
    """Every reference gives D = +1/12, so P(M > 0) = 1."""
    K = 12
    task_data = [
        {"c_A": [1, 1], "c_B": [0, 0], "n_refs": 2},
        {"c_A": [2, 2], "c_B": [1, 1], "n_refs": 2},
        {"c_A": [5, 5, 5], "c_B": [4, 4, 4], "n_refs": 3},
    ]
    res = compute_exact_pairwise_margin(task_data, K=K, q_type="uniform")
    assert res["p_positive"] == pytest.approx(1.0)
    assert res["p_negative"] == 0.0
    assert res["p_zero"] == 0.0
    assert res["winner_reversal_probability"] == 0.0
    assert res["expected_margin"] == pytest.approx(1.0 / 12.0)


def test_always_tie():
    """Every reference gives D = 0, so P(M = 0) = 1."""
    K = 12
    task_data = [
        {"c_A": [3, 3], "c_B": [3, 3], "n_refs": 2},
        {"c_A": [0, 0, 0], "c_B": [0, 0, 0], "n_refs": 3},
    ]
    res = compute_exact_pairwise_margin(task_data, K=K, q_type="uniform")
    assert res["p_zero"] == pytest.approx(1.0)
    assert res["p_positive"] == 0.0
    assert res["p_negative"] == 0.0
    assert res["winner_reversal_probability"] == 0.0
    assert res["expected_margin"] == 0.0


def test_probs_sum_to_one():
    """Output probabilities sum to 1.0 within 1e-10."""
    K = 12
    task_data = [
        {"c_A": [0, 3, 6], "c_B": [2, 1, 4], "n_refs": 3},
        {"c_A": [1, 5], "c_B": [4, 2], "n_refs": 2},
        {"c_A": [3, 2, 8, 1], "c_B": [1, 2, 5, 0], "n_refs": 4},
    ]
    res = compute_exact_pairwise_margin(task_data, K=K, q_type="uniform")
    total_prob = sum(res["margin_distribution"].values())
    assert total_prob == pytest.approx(1.0, abs=1e-10)
    assert (res["p_positive"] + res["p_negative"] + res["p_zero"]) == pytest.approx(1.0, abs=1e-10)


def test_winner_reversal_identity():
    """Verify 2 * p_+ * p_- equals computed reversal probability."""
    K = 12
    task_data = [
        {"c_A": [0, 6], "c_B": [6, 0], "n_refs": 2},
        {"c_A": [2, 8], "c_B": [5, 1], "n_refs": 2},
    ]
    res = compute_exact_pairwise_margin(task_data, K=K, q_type="uniform")
    expected_rev = 2.0 * res["p_positive"] * res["p_negative"]
    assert res["winner_reversal_probability"] == pytest.approx(expected_rev)


def test_enumeration_vs_dp():
    """2 tasks, 2 refs each: compare DP convolution against brute-force enumeration."""
    K = 12
    c_A0, c_B0 = [2, 5], [1, 2]
    c_A1, c_B1 = [0, 4], [3, 1]
    q0 = np.array([0.4, 0.6])
    q1 = np.array([0.3, 0.7])

    task_data = [
        {"c_A": c_A0, "c_B": c_B0, "n_refs": 2},
        {"c_A": c_A1, "c_B": c_B1, "n_refs": 2},
    ]
    dp_res = compute_exact_pairwise_margin(task_data, K=K, q_type=[q0, q1])

    # Full enumeration over 2 x 2 outcomes
    enum_dist = defaultdict(float)
    for r0 in range(2):
        for r1 in range(2):
            d0 = (c_A0[r0] - c_B0[r0]) / K
            d1 = (c_A1[r1] - c_B1[r1]) / K
            m = (d0 + d1) / 2.0
            enum_dist[m] += q0[r0] * q1[r1]

    # Compare distributions
    assert len(dp_res["margin_distribution"]) == len(enum_dist)
    for m_val, prob in enum_dist.items():
        matching_p = [dp_p for dp_m, dp_p in dp_res["margin_distribution"].items() if abs(dp_m - m_val) < 1e-12]
        assert len(matching_p) == 1
        assert matching_p[0] == pytest.approx(prob, abs=1e-12)


def test_enumeration_invariance():
    """Permuting the order of references within a task does not change the result."""
    K = 12
    task_data1 = [
        {"c_A": [1, 5, 2], "c_B": [3, 1, 4], "n_refs": 3},
        {"c_A": [0, 6], "c_B": [2, 1], "n_refs": 2},
    ]
    # Permuted within each task
    task_data2 = [
        {"c_A": [2, 1, 5], "c_B": [4, 3, 1], "n_refs": 3},
        {"c_A": [6, 0], "c_B": [1, 2], "n_refs": 2},
    ]

    res1 = compute_exact_pairwise_margin(task_data1, K=K, q_type="uniform")
    res2 = compute_exact_pairwise_margin(task_data2, K=K, q_type="uniform")

    assert res1["expected_margin"] == pytest.approx(res2["expected_margin"], abs=1e-12)
    assert res1["variance_margin"] == pytest.approx(res2["variance_margin"], abs=1e-12)
    assert res1["p_positive"] == pytest.approx(res2["p_positive"], abs=1e-12)
    assert res1["p_negative"] == pytest.approx(res2["p_negative"], abs=1e-12)
    assert res1["winner_reversal_probability"] == pytest.approx(res2["winner_reversal_probability"], abs=1e-12)


def test_mc_cross_check():
    """Monte Carlo estimate with 10,000 samples matches DP within 3 * sigma."""
    K = 12
    rng = np.random.default_rng(20261013)
    N = 4
    task_data = [
        {"c_A": [2, 6, 1], "c_B": [4, 1, 3], "n_refs": 3},
        {"c_A": [5, 2, 0], "c_B": [1, 3, 4], "n_refs": 3},
        {"c_A": [0, 4, 3], "c_B": [2, 2, 1], "n_refs": 3},
        {"c_A": [3, 5, 6], "c_B": [1, 2, 0], "n_refs": 3},
    ]
    dp_res = compute_exact_pairwise_margin(task_data, K=K, q_type="uniform")

    n_samples = 10000
    sample_margins = []
    for _ in range(n_samples):
        draw_diffs = []
        for t in task_data:
            r = rng.integers(0, t["n_refs"])
            d = (t["c_A"][r] - t["c_B"][r]) / K
            draw_diffs.append(d)
        sample_margins.append(float(np.mean(draw_diffs)))

    mc_mean = float(np.mean(sample_margins))
    mc_se = dp_res["std_margin"] / np.sqrt(n_samples)

    # 3-sigma bound
    assert abs(mc_mean - dp_res["expected_margin"]) < 3.0 * mc_se


def test_tv_distance_symmetric():
    """TV distance is symmetric: TV(q1, q2) == TV(q2, q1)."""
    q1 = np.array([0.2, 0.5, 0.3])
    q2 = np.array([0.1, 0.6, 0.3])
    assert tv_distance(q1, q2) == pytest.approx(tv_distance(q2, q1))


def test_tv_bound_holds():
    """Verify |mu(q) - mu(q0)| <= (2/N) * sum_i TV(q_i, q^0_i) for a concrete example."""
    K = 12
    task_data = [
        {"c_A": [2, 8], "c_B": [1, 3], "n_refs": 2},
        {"c_A": [0, 4], "c_B": [3, 1], "n_refs": 2},
    ]
    q0_list = [np.array([0.5, 0.5]), np.array([0.5, 0.5])]
    q1_list = [np.array([0.8, 0.2]), np.array([0.3, 0.7])]

    res0 = compute_exact_pairwise_margin(task_data, K=K, q_type=q0_list)
    res1 = compute_exact_pairwise_margin(task_data, K=K, q_type=q1_list)

    mu0 = res0["expected_margin"]
    mu1 = res1["expected_margin"]

    tv0 = tv_distance(q0_list[0], q1_list[0])
    tv1 = tv_distance(q0_list[1], q1_list[1])
    bound = tv_bound_on_expected_margin_change([tv0, tv1], N=2)

    assert abs(mu1 - mu0) <= bound + 1e-12


def test_certificate_certifies_when_margin_large():
    """certify=True when margin >> budget."""
    expected_margin = 0.5
    tv_budget = 0.1
    cert = certify_margin_sign(expected_margin, tv_budget)
    assert cert["certified"] is True
    assert cert["certified_sign"] == 1
    assert "invariant" in cert["certifying_condition"]


def test_certificate_fails_when_margin_small():
    """certify=False when margin < budget."""
    expected_margin = 0.05
    tv_budget = 0.1
    cert = certify_margin_sign(expected_margin, tv_budget)
    assert cert["certified"] is False
    assert cert["certified_sign"] is None
    assert "flip" in cert["certifying_condition"]


def test_reversal_identity_by_enumeration():
    """For 1 task with 2 refs (p_+ = 0.3, p_- = 0.7), reversal prob = 2 * 0.3 * 0.7."""
    K = 12
    # ref 0: c_A=2, c_B=0 (D = +2/12 > 0)
    # ref 1: c_A=0, c_B=2 (D = -2/12 < 0)
    task_data = [{"c_A": [2, 0], "c_B": [0, 2], "n_refs": 2}]
    q = np.array([0.3, 0.7])

    res = compute_exact_pairwise_margin(task_data, K=K, q_type=[q])

    assert res["p_positive"] == pytest.approx(0.3)
    assert res["p_negative"] == pytest.approx(0.7)
    assert res["p_zero"] == pytest.approx(0.0)

    # Brute-force enumeration of pairs of draws (r1, r2)
    # R1 > 0 with prob 0.3, R1 < 0 with prob 0.7
    # Reversal occurs iff (R1 > 0, R2 < 0) or (R1 < 0, R2 > 0)
    enum_reversal = (0.3 * 0.7) + (0.7 * 0.3)  # 0.42
    assert res["winner_reversal_probability"] == pytest.approx(enum_reversal)
    assert res["winner_reversal_probability"] == pytest.approx(2.0 * 0.3 * 0.7)


def test_certificate_sufficient_not_necessary_counterexample():
    """
    Demonstrates that the certificate condition is sufficient, NOT necessary.
    Counterexample:
      Task 1 with 2 references, where D(r1) = +0.5 and D(r2) = +0.4.
      Under ANY distribution q on [r1, r2], E_q[D] in [0.4, 0.5] > 0.
      The sign of E_q[D] is strictly positive for all distributions (even TV = 1.0).
      Yet for baseline q0 = (0.5, 0.5) (mu0 = 0.45) and TV budget B = 0.30:
        tv_bound = 2 * 0.30 = 0.60 > 0.45 = mu0
      The TV certificate FAILS (certify=False), even though the sign CANNOT flip!
    """
    # 1. Verification of true mathematical invariance across grid of distributions
    for p in np.linspace(0.0, 1.0, 101):
        expected_D = 0.5 * p + 0.4 * (1.0 - p)
        assert expected_D > 0.0, "Sign must remain positive under all distributions"

    # 2. Verification of certificate behavior
    mu0 = 0.45
    budget_B = 0.30
    bound = 2.0 * budget_B  # 0.60
    cert = certify_margin_sign(mu0, bound)

    # The certificate fails despite true invariance:
    assert cert["certified"] is False
    assert cert["certified_sign"] is None
    assert "cannot certify" in cert["certifying_condition"]
