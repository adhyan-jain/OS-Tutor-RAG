"""
Scores one raw model output under every evaluator.

  semantic     oracle verdict (TRUE / FALSE / UNVERIFIABLE), reference-independent
  B            semantic == TRUE            (UNVERIFIABLE counts as not valid)
  B_ub         semantic != FALSE           (sensitivity bound: UNVERIFIABLE counts as valid)
  A_strict     whitespace-collapsed exact string match to the reference
  A_norm       exact match of the parsed, normalised trajectory
  C            B and outcome-equivalent to the reference's outcome
  nd           normalised edit distance to the reference (input to the distance proxy)
  fs           final-state-only proxy verdict
"""

from typing import Dict

from research.ssr_pilot import attackers as A
from research.ssr_pilot import oracle, render


def score_record(world: Dict, rendered: Dict, bank: Dict, rec: Dict) -> Dict:
    truncated = rec.get("done_reason") == "length"
    v = oracle.evaluate_candidate(world, rec["response"], truncated=truncated, shown2canon=rendered["s2c"])
    ref = bank["reference"]
    cmp = oracle.compare_to_reference(world, v.steps, rec["response"], ref,
                                      render.reference_text(world, ref, rendered))
    B = v.semantic_valid == oracle.TRUE
    return {
        "model": rec["model"], "world": world["id"], "family": world["family"], "structure": world["structure"],
        "variant": rec["variant"], "seed": rec["seed"], "n_task": bank["n_task"],
        "semantic": v.semantic_valid, "reason": v.reason, "parseable": v.parseable, "truncated": truncated,
        "B": B, "B_ub": v.semantic_valid != oracle.FALSE,
        # An exact match must also reject output that mentions entities outside the world: the parser drops
        # such tokens, so without this check "reference + junk" would count as matching (prereg deviation D3).
        "A_strict": bool(cmp["ref_match_strict"]),
        "A_norm": bool(cmp["ref_match_norm"] and v.reason != "unknown_entity"),
        "obs_equiv": bool(cmp["obs_equiv"]), "C": bool(B and cmp["obs_equiv"]),
        "nd": None if v.steps is None else A.norm_distance(world, v.steps, ref),
        "fs": bool(A.proxy_final_state(world, v.steps, ref)),
        "quality": v.quality,
    }
