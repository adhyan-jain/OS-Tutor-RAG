"""
Tests for statistical significance decision stability and tie/indeterminate handling.
"""

from research.ssr_pilot.core.schema import EvaluatorVerdict
from research.ssr_pilot.rcrc.significance_metrics import compute_pairwise_significance


def test_pairwise_significance_decisions():
    # Synthetic mock verdicts for Model A and Model B
    v_a = [
        EvaluatorVerdict("E2", "w1", "g1", "mA", "v0", 0, 0, (), "TRUE", True, True, True, True),
        EvaluatorVerdict("E2", "w1", "g2", "mA", "v0", 1, 0, (), "TRUE", True, True, True, True),
    ]
    v_b = [
        EvaluatorVerdict("E2", "w1", "g1", "mB", "v0", 0, 0, (), "TRUE", False, False, False, False),
        EvaluatorVerdict("E2", "w1", "g2", "mB", "v0", 1, 0, (), "TRUE", False, False, False, False),
    ]

    # Insufficient samples should yield INDETERMINATE
    state, p_val = compute_pairwise_significance(v_a, v_b)
    assert state == "INDETERMINATE"
    assert p_val == 1.0
