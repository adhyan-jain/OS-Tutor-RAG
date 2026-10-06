"""
Tests for formal valid solution space V(x) enumeration and validation.
"""

from research.ssr_pilot import families as F
from research.ssr_pilot.core.valid_space import build_valid_space
from research.ssr_pilot.oracle import evaluate_candidate, TRUE, FALSE
from research.ssr_pilot.worlds import load_worlds


def test_valid_space_enumeration_and_integrity():
    worlds = load_worlds()
    assert len(worlds) == 24

    for w in worlds:
        v_space = build_valid_space(w)
        assert v_space.n_valid_task >= 1
        assert len(v_space.valid_solutions) == v_space.n_valid_task
        assert v_space.canonical_reference in v_space.valid_solutions

        # Every solution in V(x) must pass rules and task constraints via the oracle.
        # format_steps → text → parse+replay exercises the full pipeline independently
        # of how the valid_solutions list was constructed.
        for ref in v_space.valid_solutions:
            text = F.format_steps(w, ref)
            verdict = evaluate_candidate(w, text)
            assert verdict.semantic_valid == TRUE, (
                f"World {w['id']}: valid solution {ref!r} failed oracle: "
                f"semantic_valid={verdict.semantic_valid}, reason={verdict.reason}"
            )


def test_oracle_rejects_mutated_valid_solution():
    """Metamorphic test: appending a duplicate step to a valid trace must cause a rule violation."""
    worlds = load_worlds()
    for w in worlds:
        v_space = build_valid_space(w)
        ref = v_space.canonical_reference
        # Duplicate the first step — creates an invalid sequence for all three families.
        bad_steps = ref + (ref[0],)
        text = F.format_steps(w, bad_steps)
        verdict = evaluate_candidate(w, text)
        assert verdict.semantic_valid == FALSE, (
            f"World {w['id']}: expected oracle to reject duplicate-step trace, "
            f"got semantic_valid={verdict.semantic_valid}, reason={verdict.reason}"
        )
