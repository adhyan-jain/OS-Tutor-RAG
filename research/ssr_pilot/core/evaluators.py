"""
Evaluator implementations for Reference-Choice Robustness (RCR).

Supported Evaluators:
- E1_CANONICAL_EXACT: Strict string / step match relative to reference R_i.
- E2_NORMALIZED_MATCH: Normalized schedule / event match relative to reference R_i.
- E3_SEMANTIC_ORACLE: Executable semantic validity verdict (reference-independent).
- E4_OBSERVATIONAL_EQUIV: Observational equivalence relative to reference R_i.
"""

import re
from typing import Dict, Optional, Sequence, Tuple
from research.ssr_pilot import families as F
from research.ssr_pilot.core.oracle import evaluate_oracle, Verdict
from research.ssr_pilot.core.schema import EvaluatorVerdict


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def evaluate_with_reference(
    evaluator_id: str,
    world: Dict,
    raw_text: str,
    reference_steps: Tuple,
    generation_id: str = "",
    model: str = "",
    variant: str = "",
    seed: int = 0,
    reference_idx: int = 0,
    truncated: bool = False,
    shown2canon: Optional[Dict[str, str]] = None
) -> EvaluatorVerdict:
    """
    Evaluates candidate raw_text y using specified evaluator_id relative to reference_steps R.
    """
    oracle_verdict = evaluate_oracle(world, raw_text, truncated=truncated, shown2canon=shown2canon)
    steps, _ = F.parse(world, raw_text, shown2canon)
    
    # Reference comparison
    if steps is None:
        ref_match_norm = False
        ref_match_strict = False
        obs_equiv = False
    else:
        norm_cand = F.normalize_schedule(steps) if world["family"] == "scheduling" else tuple(steps)
        norm_ref = F.normalize_schedule(reference_steps) if world["family"] == "scheduling" else tuple(reference_steps)
        ref_match_norm = (norm_cand == norm_ref)
        
        region, _ = F._region(raw_text)
        formatted_ref = F.format_steps(world, reference_steps)
        ref_match_strict = _squash(region) == _squash(formatted_ref)
        obs_equiv = (F.observe(world, steps) == F.observe(world, reference_steps))

    # Determine evaluator verdict (pass / fail)
    if evaluator_id == "E1_CANONICAL_EXACT":
        eval_pass = ref_match_strict
    elif evaluator_id == "E2_NORMALIZED_MATCH":
        eval_pass = ref_match_norm
    elif evaluator_id == "E3_SEMANTIC_ORACLE":
        eval_pass = (oracle_verdict.semantic_valid == "TRUE")
    elif evaluator_id == "E4_OBSERVATIONAL_EQUIV":
        eval_pass = obs_equiv
    else:
        raise ValueError(f"Unknown evaluator_id: {evaluator_id}")

    return EvaluatorVerdict(
        evaluator_id=evaluator_id,
        world_id=world["id"],
        generation_id=generation_id,
        model=model,
        variant=variant,
        seed=seed,
        reference_idx=reference_idx,
        reference_steps=reference_steps,
        semantic_valid=oracle_verdict.semantic_valid,
        ref_match_norm=ref_match_norm,
        ref_match_strict=ref_match_strict,
        obs_equiv=obs_equiv,
        evaluator_pass=eval_pass,
        reason=oracle_verdict.reason,
    )
