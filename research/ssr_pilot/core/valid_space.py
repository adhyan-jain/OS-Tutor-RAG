"""
Formalization of the complete valid-solution space V(x) for each task/world.

V(x) is defined as the set of all executable trajectories y such that:
1. y obeys the formal transition system rules of world x.
2. y satisfies all task constraints of world x.
3. Each solution in V(x) is validated independently of any canonical trace.
"""

from typing import Dict, List, Tuple
from research.ssr_pilot import families as F
from research.ssr_pilot.core.schema import ValidSpaceSpec


def build_valid_space(world: Dict) -> ValidSpaceSpec:
    """
    Exhaustively enumerates and verifies all valid solutions V(x) for a world.
    """
    rules_valid = F.enumerate_rules(world)
    task_valid = [t for t in rules_valid if not F.violated_constraints(world, t)]
    
    # Audit verification: ensure every single enumerated trace in V(x) has no violated constraints
    for t in task_valid:
        ok, rule = F.rules_check(world, t)
        assert ok, f"Trace {t} failed rules check with rule {rule}"
        viol = F.violated_constraints(world, t)
        assert not viol, f"Trace {t} failed constraint check with violation {viol}"
    
    canonical_ref = task_valid[0]
    
    return ValidSpaceSpec(
        world_id=world["id"],
        family=world["family"],
        n_rules=len(rules_valid),
        n_valid_task=len(task_valid),
        valid_solutions=task_valid,
        canonical_reference=canonical_ref,
        exhaustive=True,
        enumeration_method="exact_replay_search",
    )


def build_all_valid_spaces(worlds: List[Dict]) -> Dict[str, ValidSpaceSpec]:
    """
    Builds ValidSpaceSpec for all loaded worlds.
    """
    return {w["id"]: build_valid_space(w) for w in worlds}
