"""
Trace-level metrics and sensitivity analysis across valid reference choices.
"""

from typing import Dict, List, Sequence
import numpy as np
from research.ssr_pilot.core.schema import EvaluatorVerdict


def compute_trace_metrics(verdicts: Sequence[EvaluatorVerdict]) -> Dict:
    """
    Computes trace-level metrics for a set of EvaluatorVerdict objects evaluated against a reference R.
    """
    if not verdicts:
        return {}

    total = len(verdicts)
    sem_valid_count = sum(1 for v in verdicts if v.semantic_valid == "TRUE")
    sem_invalid_count = sum(1 for v in verdicts if v.semantic_valid == "FALSE")
    
    eval_pass_count = sum(1 for v in verdicts if v.evaluator_pass)
    
    # FRR: semantically valid outputs rejected by evaluator
    frr = (sum(1 for v in verdicts if v.semantic_valid == "TRUE" and not v.evaluator_pass) / sem_valid_count) if sem_valid_count > 0 else 0.0
    
    # FAR: semantically invalid outputs accepted by evaluator
    far = (sum(1 for v in verdicts if v.semantic_valid == "FALSE" and v.evaluator_pass) / sem_invalid_count) if sem_invalid_count > 0 else 0.0

    strict_match_rate = sum(1 for v in verdicts if v.ref_match_strict) / total
    norm_match_rate = sum(1 for v in verdicts if v.ref_match_norm) / total
    obs_equiv_rate = sum(1 for v in verdicts if v.obs_equiv) / total

    return {
        "n_total": total,
        "n_semantic_valid": sem_valid_count,
        "n_semantic_invalid": sem_invalid_count,
        "evaluator_pass_rate": eval_pass_count / total,
        "frr": frr,
        "far": far,
        "strict_match_rate": strict_match_rate,
        "norm_match_rate": norm_match_rate,
        "obs_equiv_rate": obs_equiv_rate,
    }


def compute_reference_distribution(verdicts_by_ref: Dict[int, List[EvaluatorVerdict]]) -> Dict:
    """
    Summarizes the distribution of trace-level metrics across all valid references R in V(x).
    """
    frrs = []
    pass_rates = []
    norm_matches = []
    
    for ref_idx, v_list in verdicts_by_ref.items():
        m = compute_trace_metrics(v_list)
        frrs.append(m["frr"])
        pass_rates.append(m["evaluator_pass_rate"])
        norm_matches.append(m["norm_match_rate"])

    return {
        "n_references": len(verdicts_by_ref),
        "frr_mean": float(np.mean(frrs)),
        "frr_std": float(np.std(frrs)),
        "frr_min": float(np.min(frrs)),
        "frr_max": float(np.max(frrs)),
        "frr_quantiles": [float(q) for q in np.quantile(frrs, [0.0, 0.25, 0.5, 0.75, 1.0])],
        "pass_rate_mean": float(np.mean(pass_rates)),
        "pass_rate_std": float(np.std(pass_rates)),
        "norm_match_mean": float(np.mean(norm_matches)),
    }
