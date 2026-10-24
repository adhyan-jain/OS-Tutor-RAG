"""
Tests for the extended RCR analysis (full-draw significance, detection, near-tie decomposition).

Unit tests check the vectorised statistics against the scalar reference implementations
in rcrc/significance_metrics.py. Artifact tests check structural and cross-consistency
properties of results/rcrc/extended_analysis.json.
"""

import json
import os

import numpy as np
import pytest

from research.ssr_pilot.rcr_extended_analysis import holm_rows, sign_flip_pvalues
from research.ssr_pilot.rcrc.significance_metrics import (
    compute_world_level_sign_flip_pvalue,
    holm_bonferroni_correction,
)

ARTIFACT = "research/ssr_pilot/results/rcrc/extended_analysis.json"
E1, E2, E3 = "E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"


def _signs(n_flips=20000, seed=7):
    return np.random.default_rng(seed).choice(np.array([-1.0, 1.0], dtype=np.float32), size=(n_flips, 24))


def test_holm_rows_matches_scalar_implementation():
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, size=(200, 6))
    vec = holm_rows(p)
    for r in range(len(p)):
        scalar = holm_bonferroni_correction({str(k): float(p[r, k]) for k in range(6)})
        assert np.allclose(vec[r], [scalar[str(k)] for k in range(6)])


def test_holm_rows_monotone_and_bounded():
    p = np.array([[0.001, 0.01, 0.02, 0.5, 0.6, 0.9]])
    adj = holm_rows(p)[0]
    assert np.all(adj <= 1.0) and np.all(adj >= p[0])
    assert np.all(np.diff(adj) >= -1e-12)


def test_sign_flip_zero_difference_is_one():
    assert sign_flip_pvalues(np.zeros((1, 24)), _signs())[0] == 1.0


def test_sign_flip_consistent_shift_is_significant():
    diffs = np.full((1, 24), 1 / 12)
    assert sign_flip_pvalues(diffs, _signs())[0] < 0.001


def test_sign_flip_agrees_with_scalar_reference():
    rng = np.random.default_rng(3)
    diffs = rng.integers(-3, 6, size=24) / 12.0  # multiples of 1/12 as in the real data
    vec_p = sign_flip_pvalues(diffs[None, :], _signs(20000, 11))[0]
    ref_p = compute_world_level_sign_flip_pvalue(diffs, n_flips=20000, seed=5)
    assert abs(vec_p - ref_p) < 0.02


@pytest.fixture(scope="module")
def result():
    assert os.path.exists(ARTIFACT), "Run: python -m research.ssr_pilot.rcr_extended_analysis"
    with open(ARTIFACT) as f:
        return json.load(f)


def test_artifact_uses_all_draws_not_a_subsample(result):
    prov = result["provenance"]
    assert prov["n_draws"] == 50000
    assert prov["n_sign_flips"] == 20000
    assert "ALL" in prov["sign_flip_scope"]


def test_oracle_decision_is_reference_invariant(result):
    for pair, stats in result["significance_all_draws"][E3].items():
        assert stats["decision_is_constant"] is True, pair
        assert stats["min_adj_p"] == stats["max_adj_p"], f"E3 p-value varies with reference for {pair}"


def test_oracle_separates_exactly_the_qwen3_pairs(result):
    det = result["detection_vs_oracle"][E3]
    separated = {p for p, d in det.items() if d["oracle_decision"] != "NON_SIGNIFICANT"}
    assert separated == {"llama3.1:8b_vs_qwen3:8b", "mistral:7b-instruct_vs_qwen3:8b"}
    for p in separated:
        assert det[p]["oracle_decision"] == "SIGNIFICANT_B_WINS"  # qwen3 is B in both pairs


def test_reference_matching_misses_oracle_differences(result):
    for ev in (E1, E2):
        for pair in ("llama3.1:8b_vs_qwen3:8b", "mistral:7b-instruct_vs_qwen3:8b"):
            d = result["detection_vs_oracle"][ev][pair]
            assert d["miss_true_difference"] >= 0.999
            assert d["wrong_direction_significant"] == 0.0


def test_legacy_crosscheck_within_monte_carlo_error(result):
    """Cross-check extended analysis legacy metrics against the primary analysis.
    Values reflect post-D9 canonical reference alignment (deviation D9).
    Post-D9: E2 reversal ~0.1718, tau-b ~0.6163, E2 oracle recovery ~0.1350, E1 oracle recovery ~0.0285.
    """
    cc = result["legacy_crosscheck"]
    assert abs(cc[E2]["pairwise_reversal_probability"] - 0.1718) < 0.01
    assert abs(cc[E2]["kendall_tau_b_mean"] - 0.6163) < 0.01
    assert abs(cc[E2]["oracle_recovery_rate"] - 0.1350) < 0.01
    assert abs(cc[E1]["oracle_recovery_rate"] - 0.0285) < 0.01
    assert cc[E3]["pairwise_reversal_probability"] == 0.0
    assert cc[E3]["kendall_tau_b_mean"] == 1.0


def test_near_tie_shares_sum_to_one(result):
    for ev in (E1, E2):
        nt = result["near_tie_decomposition"][ev]
        total = nt["reversal_mass_share_in_oracle_nonseparated_pairs"] + nt["reversal_mass_share_in_oracle_separated_pairs"]
        assert total == pytest.approx(1.0)


def test_family_breakdown_covers_all_families(result):
    fams = result["by_family"]
    assert set(fams) == {"scheduling", "sync", "banker"}
    assert all(f["n_worlds"] == 8 for f in fams.values())
    assert fams["scheduling"][E2]["pairwise_reversal_probability"] == 0.0


def test_canonical_reference_reproduces_oracle_ordering():
    """After D9 the canonical-reference E2 ranking equals the E3 ranking (as in the pilot report)."""
    with open("research/ssr_pilot/results/rcrc/rcr_summary.json") as f:
        ev = json.load(f)["evaluators"]
    assert ev[E2]["canonical_model_ranking"] == ev[E3]["oracle_model_ranking"]


KREF = "research/ssr_pilot/results/rcrc/kref_attenuation.json"


def test_attenuation_law_holds_exactly():
    with open(KREF) as f:
        k = json.load(f)
    a = k["attenuation_law"]
    assert a["pearson_r_observed_vs_predicted"] > 0.999
    assert a["valid_generations_matching_no_reference"] == 0
    assert a["valid_generations_matching_more_than_one_reference"] == 0
    assert a["invalid_generations_matching_a_reference"] == 0  # D3(b) rule applied


def test_kref_detection_grows_with_k_and_reaches_oracle():
    with open(KREF) as f:
        k = json.load(f)["k_reference"]
    pair = "llama3.1:8b_vs_qwen3:8b"
    d = {key: v["detect_oracle_separated_pairs"][pair] for key, v in k.items()}
    assert d["1"] < 0.01 and d["25"] > 0.7 and d["all"] == 1.0
    assert k["all"]["mean_reversal_all_pairs"] == 0.0


def test_inverse_v_correction_is_unbiased_but_low_power():
    with open(KREF) as f:
        c = json.load(f)["inverse_V_correction"]
    pair = "llama3.1:8b_vs_qwen3:8b"
    assert abs(c["10"]["mean_estimated_gap_over_oracle_gap_separated"][pair] - 1.0) < 0.1
    assert c["10"]["detect_oracle_separated_pairs"][pair] < 0.6  # bias fixed, power not restored


def test_evaluator_effect_cis_are_ordered(result):
    for ev in (E1, E2):
        for pair, x in result["evaluator_effect_on_gap"][ev].items():
            assert x["ci95_low"] <= x["evaluator_effect_on_gap"] <= x["ci95_high"], pair
