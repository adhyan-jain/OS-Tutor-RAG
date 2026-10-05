"""Labels in impact_analysis must follow the predefined definitions, never looser."""

import numpy as np

from research.ssr_pilot import impact_analysis as IA


def test_weak_reversal_needs_opposite_nonzero_signs():
    assert IA.weak_reversal(0.1, -0.1)
    assert not IA.weak_reversal(0.1, 0.2)
    assert not IA.weak_reversal(0.0, -0.1)  # a tie is not a reversal


def test_decisive_reversal_needs_both_cis_to_exclude_zero():
    assert IA.decisive_reversal(0.1, -0.1, [0.02, 0.2], [-0.2, -0.02])
    assert not IA.decisive_reversal(0.1, -0.1, [-0.02, 0.2], [-0.2, -0.02])  # A's CI spans 0
    assert not IA.decisive_reversal(0.1, 0.1, [0.02, 0.2], [0.02, 0.2])  # same direction


def test_decision_reversal_counts_decided_vs_undecided():
    assert IA.decision_reversal(0.1, [-0.05, 0.2], 0.1, [0.02, 0.2])  # undecided vs decided
    assert not IA.decision_reversal(0.1, [0.02, 0.2], 0.2, [0.05, 0.3])


def test_supported_significance_requires_effect_ci():
    assert IA.supported_significance_change(True, [0.01, 0.1])
    assert not IA.supported_significance_change(True, [-0.01, 0.1])  # 'significant' vs 'not' alone is not enough
    assert not IA.supported_significance_change(False, [0.01, 0.1])


def test_gap_ratio_undefined_for_tiny_gaps():
    assert IA.gap_ratio(0.01, 0.2) is None
    assert IA.gap_ratio(0.1, 0.2) == 2.0


def test_rank_vector_ties_share_best_rank():
    assert IA.rank_vector(np.array([0.3, 0.1, 0.1, 0.5])) == (2, 3, 3, 1)


def test_identical_evaluators_give_no_reversal_or_change():
    rng = np.random.default_rng(0)
    S = {m: rng.random(24) * s for m, s in zip("abcd", (0.9, 0.6, 0.3, 0.1))}
    res = IA.compare_evaluators(S, S, list("abcd"), n_boot=200, n_flips=2000)
    assert res["n_weak_reversals"] == 0 and res["n_decisive_reversals"] == 0
    assert res["n_nominal_significance_changes"] == 0
    assert res["ranking"]["kendall_tau"] == 1.0 and res["ranking"]["P_paired_order_agreement"] == 1.0


def test_true_decisive_reversal_is_detected():
    W = 24
    SA = {"a": np.full(W, 0.8), "b": np.full(W, 0.2)}
    SB = {"a": np.full(W, 0.2), "b": np.full(W, 0.8)}
    res = IA.compare_evaluators(SA, SB, ["a", "b"], n_boot=200, n_flips=2000)
    # constant gaps have zero-width CIs that exclude 0, so this is decisive
    assert res["pairs"][0]["decisive_reversal"] and res["ranking"]["kendall_tau"] == -1.0


def test_noise_level_sign_flip_is_weak_not_decisive():
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 0.05, 24)  # per-world gap noise, mean ~0
    SA = {"a": noise + 0.001, "b": np.zeros(24)}
    SB = {"a": -noise - 0.001 + 0.002, "b": np.zeros(24)}  # opposite sign of the mean gap, same noise scale
    res = IA.compare_evaluators(SA, SB, ["a", "b"], n_boot=500, n_flips=2000)
    row = res["pairs"][0]
    assert row["weak_reversal"] and not row["decisive_reversal"]


def test_definitions_hash_is_stable_text_hash():
    import hashlib
    assert IA.DEFINITIONS_SHA256 == hashlib.sha256(IA.DEFINITIONS.encode()).hexdigest()
