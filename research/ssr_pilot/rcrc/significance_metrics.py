"""
Statistical significance decision stability across valid reference choices.
"""

from typing import Dict, List, Sequence, Tuple
import numpy as np
from scipy import stats
from research.ssr_pilot.core.schema import EvaluatorVerdict


def compute_pairwise_significance(
    verdicts_a: Sequence[EvaluatorVerdict],
    verdicts_b: Sequence[EvaluatorVerdict],
    alpha: float = 0.05
) -> Tuple[str, float]:
    """
    Performs paired McNemar / Paired T-test on matched task generations for models A and B under reference R.
    Returns (decision_state, p_value).
    
    Decision states:
    - "SIGNIFICANT_A_WINS"
    - "SIGNIFICANT_B_WINS"
    - "NON_SIGNIFICANT"
    - "INDETERMINATE"
    """
    # Group by (world_id, variant, seed)
    map_a = {(v.world_id, v.variant, v.seed): v.evaluator_pass for v in verdicts_a}
    map_b = {(v.world_id, v.variant, v.seed): v.evaluator_pass for v in verdicts_b}
    
    common_keys = sorted(list(set(map_a.keys()).intersection(set(map_b.keys()))))
    if len(common_keys) < 10:
        return "INDETERMINATE", 1.0
        
    y_a = np.array([map_a[k] for k in common_keys], dtype=int)
    y_b = np.array([map_b[k] for k in common_keys], dtype=int)
    
    # McNemar's test contingency table
    b_wins = np.sum((y_a == 0) & (y_b == 1))
    a_wins = np.sum((y_a == 1) & (y_b == 0))
    
    n_diff = a_wins + b_wins
    if n_diff == 0:
        return "NON_SIGNIFICANT", 1.0
        
    # Exact binomial test for McNemar
    res = stats.binomtest(a_wins, n_diff, 0.5)
    p_val = float(res.pvalue)
    
    if p_val < alpha:
        if a_wins > b_wins:
            return "SIGNIFICANT_A_WINS", p_val
        else:
            return "SIGNIFICANT_B_WINS", p_val
    else:
        return "NON_SIGNIFICANT", p_val


def compute_significance_stability(
    verdicts_by_ref_and_model: Dict[int, Dict[str, List[EvaluatorVerdict]]],
    alpha: float = 0.05
) -> Dict:
    """
    Computes statistical significance decision stability across reference choices.
    """
    models = sorted(list(next(iter(verdicts_by_ref_and_model.values())).keys()))
    n_refs = len(verdicts_by_ref_and_model)
    
    pair_decisions: Dict[str, List[str]] = {}
    pair_p_values: Dict[str, List[float]] = {}
    
    for ref_idx, model_dict in verdicts_by_ref_and_model.items():
        for i, m1 in enumerate(models):
            for m2 in models[i + 1:]:
                pair_key = f"{m1}_vs_{m2}"
                dec, p_val = compute_pairwise_significance(model_dict[m1], model_dict[m2], alpha=alpha)
                pair_decisions.setdefault(pair_key, []).append(dec)
                pair_p_values.setdefault(pair_key, []).append(p_val)
                
    stability_summary = {}
    for pair_key, dec_list in pair_decisions.items():
        counts = {d: dec_list.count(d) for d in set(dec_list)}
        probs = {d: counts[d] / n_refs for d in counts}
        p_vals = pair_p_values[pair_key]
        stability_summary[pair_key] = {
            "decision_distribution": probs,
            "mean_p_value": float(np.mean(p_vals)),
            "std_p_value": float(np.std(p_vals)),
            "min_p_value": float(np.min(p_vals)),
            "max_p_value": float(np.max(p_vals)),
            "is_decision_constant": len(set(dec_list)) == 1,
        }
        
    return {
        "n_references": n_refs,
        "pairwise_significance_summary": stability_summary,
    }
