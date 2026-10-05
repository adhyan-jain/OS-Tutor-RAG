"""
Tests for semantic oracle reference-invariance.
"""

from research.ssr_pilot.core.oracle import evaluate_oracle, verify_oracle_reference_invariance
from research.ssr_pilot.core.valid_space import build_valid_space
from research.ssr_pilot.worlds import load_worlds


def test_oracle_reference_invariance():
    worlds = load_worlds()
    
    test_outputs = [
        "TRACE: P1 0-24, P2 24-27, P3 27-30",
        "INVALID TRACE: P1 0-10",
        "SOME UNPARSEABLE JUNK"
    ]

    for w in worlds:
        v_space = build_valid_space(w)
        for text in test_outputs:
            is_invariant = verify_oracle_reference_invariance(w, text, v_space.valid_solutions)
            assert is_invariant, f"Oracle verdict was not reference-invariant on world {w['id']} for text: {text}"
