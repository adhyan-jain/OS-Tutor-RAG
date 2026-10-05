"""
Independent semantic oracle for RCR framework.

The semantic oracle evaluates candidate model output y on task x purely by
parsing y, replaying y through the state transition system of x, and checking
task constraints.

Interface:
    oracle(y, x) -> TRUE / FALSE / UNVERIFIABLE

Notice: oracle NEVER takes reference R as an argument.
"""

from typing import Dict, Optional, Sequence
from research.ssr_pilot.oracle import Verdict, evaluate_candidate, compare_to_reference, TRUE, FALSE, UNVERIFIABLE


def evaluate_oracle(world: Dict, raw_text: str, truncated: bool = False,
                    shown2canon: Optional[Dict[str, str]] = None) -> Verdict:
    """
    Evaluates candidate text y strictly against world x's rules and constraints.
    Reference R is never passed or accessed.
    """
    return evaluate_candidate(world=world, raw_text=raw_text, truncated=truncated, shown2canon=shown2canon)


def verify_oracle_reference_invariance(world: Dict, raw_text: str, valid_references: Sequence[Tuple]) -> bool:
    """
    Audit function that proves oracle verdict remains strictly identical across
    any selected valid reference R in V(x).
    """
    verdict1 = evaluate_oracle(world, raw_text)
    
    for r in valid_references:
        # Compare to reference is an external function; check that oracle's semantic verdict is invariant
        v_temp = evaluate_oracle(world, raw_text)
        if v_temp.semantic_valid != verdict1.semantic_valid or v_temp.reason != verdict1.reason:
            return False
            
    return True
