"""
Independent semantic oracle for RCR framework.

The semantic oracle evaluates candidate model output y on task x purely by
parsing y, replaying y through the state transition system of x, and checking
task constraints.

Interface:
    oracle(y, x) -> TRUE / FALSE / UNVERIFIABLE

Notice: oracle NEVER takes reference R as an argument.
"""

import inspect
from typing import Dict, Optional, Sequence, Tuple
from research.ssr_pilot.oracle import Verdict, evaluate_candidate, compare_to_reference, TRUE, FALSE, UNVERIFIABLE


def evaluate_oracle(world: Dict, raw_text: str, truncated: bool = False,
                    shown2canon: Optional[Dict[str, str]] = None) -> Verdict:
    """
    Evaluates candidate text y strictly against world x's rules and constraints.
    Reference R is never passed or accessed.
    """
    return evaluate_candidate(world=world, raw_text=raw_text, truncated=truncated, shown2canon=shown2canon)


def assert_oracle_has_no_reference_parameter() -> bool:
    """
    Architectural check: `evaluate_candidate`'s signature has no reference/R
    parameter, so `semantic_valid` is invariant to reference choice BY
    CONSTRUCTION, not because it was measured to vary correctly with R. This
    is a structural guard against someone later adding a reference argument
    to the oracle, not an empirical demonstration.
    """
    params = set(inspect.signature(evaluate_candidate).parameters)
    forbidden = {"reference", "reference_text", "r", "ref"}
    return params.isdisjoint(forbidden)


def verify_oracle_reference_invariance(world: Dict, raw_text: str,
                                       valid_references: Sequence[Tuple]) -> bool:
    """
    Empirical no-leakage / no-side-effect check (NOT an empirical test of
    "oracle output varies correctly with different references" -- that
    framing is incoherent here, since `evaluate_oracle` never receives a
    reference argument at all; invariance in that sense holds by
    construction, see `assert_oracle_has_no_reference_parameter`).

    What this DOES test empirically: computing reference-relative fields via
    `compare_to_reference` for every candidate reference R in V(x) has no
    side effect that corrupts a subsequent independent oracle call on the
    same (world, raw_text) -- i.e. there is no shared mutable state or
    caching path through which a reference could leak into the semantic
    verdict. If `compare_to_reference` ever starts memoizing/mutating
    world-level state keyed on the reference, this test will catch it.
    """
    if not assert_oracle_has_no_reference_parameter():
        return False

    verdict1 = evaluate_oracle(world, raw_text)
    steps = verdict1.steps

    for r in valid_references:
        # Exercise the reference-relative comparison path with a varying R ...
        compare_to_reference(world, steps, raw_text, r)
        # ... then confirm the reference-free oracle verdict is unaffected.
        v_temp = evaluate_oracle(world, raw_text)
        if v_temp.semantic_valid != verdict1.semantic_valid or v_temp.reason != verdict1.reason:
            return False

    return True
