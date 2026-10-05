"""
Oracle recovery rate and canonical reference diagnostic.
"""

from typing import Dict, List, Tuple
import numpy as np
from research.ssr_pilot.core.schema import EvaluatorVerdict
from research.ssr_pilot.rcrc.ranking_metrics import compute_model_scores, get_model_ranking


def compute_oracle_recovery(
    evaluator_conclusions_by_ref: Dict[int, List[str]],
    oracle_conclusion: List[str]
) -> Dict:
    """
    Computes RCR(E) = P_R[ Ranking(E, R) == Ranking(Oracle) ]
    """
    n_refs = len(evaluator_conclusions_by_ref)
    exact_matches = sum(1 for rank in evaluator_conclusions_by_ref.values() if rank == oracle_conclusion)
    
    return {
        "n_references": n_refs,
        "oracle_ranking": oracle_conclusion,
        "oracle_recovery_rate": exact_matches / n_refs if n_refs > 0 else 0.0,
        "rankings_matching_oracle": exact_matches,
    }


def diagnose_canonical_reference(
    valid_solutions: List[Tuple],
    canonical_reference: Tuple,
    verdicts_by_ref: Dict[int, List[EvaluatorVerdict]]
) -> Dict:
    """
    Determines whether the benchmark's actual canonical reference is typical or atypical within V(x).
    """
    # 0 is always canonical reference
    if 0 not in verdicts_by_ref:
        return {}

    pass_rates = [sum(1 for v in v_list if v.evaluator_pass) / len(v_list) for v_list in verdicts_by_ref.values()]
    canon_pass_rate = sum(1 for v in verdicts_by_ref[0] if v.evaluator_pass) / len(verdicts_by_ref[0])
    
    # Percentile rank of canonical reference pass rate in V(x)
    smaller_count = sum(1 for pr in pass_rates if pr < canon_pass_rate)
    percentile = (smaller_count / len(pass_rates)) * 100.0 if pass_rates else 50.0

    return {
        "canonical_pass_rate": canon_pass_rate,
        "mean_pass_rate_in_valid_space": float(np.mean(pass_rates)),
        "std_pass_rate_in_valid_space": float(np.std(pass_rates)),
        "canonical_percentile_in_valid_space": float(percentile),
        "is_canonical_atypical": (percentile < 10.0 or percentile > 90.0),
    }
