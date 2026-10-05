"""
Preregistered statistical significance testing and decision stability across valid reference choices.

Statistical unit: World (N=24).
Variants and seeds (3 x 4 = 12 generations per world) are nested within worlds and averaged to form world-level scores.
Inference: Paired sign-flip permutation test (20,000 sign flips) on 24 paired world-level differences.
Multiplicity: Holm-Bonferroni correction across all 6 model pairs at alpha = 0.05.
"""

from typing import Dict, List, Sequence, Tuple
import numpy as np
from research.ssr_pilot.core.schema import EvaluatorVerdict


def compute_world_level_sign_flip_pvalue(
    diffs_by_world: np.ndarray,
    n_flips: int = 20000,
    seed: int = 20261005
) -> float:
    """
    Computes Monte Carlo paired sign-flip permutation p-value on 24 world-level differences.
    """
    assert len(diffs_by_world) == 24, "Preregistered sign-flip test requires exactly N=24 worlds"
    obs_stat = float(np.abs(np.mean(diffs_by_world)))
    if obs_stat == 0.0:
        return 1.0

    rng = np.random.RandomState(seed)
    # Draw 20,000 random sign matrices of shape (n_flips, 24)
    signs = rng.choice([-1.0, 1.0], size=(n_flips, 24))
    permuted_means = np.abs(np.mean(signs * diffs_by_world, axis=1))
    
    # Monte Carlo p-value with +1 continuity correction
    p_val = float((np.sum(permuted_means >= obs_stat) + 1) / (n_flips + 1))
    return p_val


def compute_world_level_pairwise_significance(
    verdicts_a: Sequence[EvaluatorVerdict],
    verdicts_b: Sequence[EvaluatorVerdict],
    n_flips: int = 20000,
    seed: int = 20261005
) -> Tuple[float, float]:
    """
    Computes paired world-level difference mean and uncorrected Monte Carlo sign-flip p-value.
    """
    by_world_a: Dict[str, List[bool]] = {}
    by_world_b: Dict[str, List[bool]] = {}
    for v in verdicts_a:
        by_world_a.setdefault(v.world_id, []).append(v.evaluator_pass)
    for v in verdicts_b:
        by_world_b.setdefault(v.world_id, []).append(v.evaluator_pass)
        
    common_worlds = sorted(list(set(by_world_a.keys()).intersection(set(by_world_b.keys()))))
    assert len(common_worlds) == 24, "Must evaluate across all 24 worlds"
    
    mean_a = np.array([np.mean(by_world_a[w]) for w in common_worlds])
    mean_b = np.array([np.mean(by_world_b[w]) for w in common_worlds])
    diffs = mean_a - mean_b
    mean_diff = float(np.mean(diffs))
    
    raw_p = compute_world_level_sign_flip_pvalue(diffs, n_flips=n_flips, seed=seed)
    return mean_diff, raw_p


def holm_bonferroni_correction(raw_p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Applies Holm-Bonferroni step-down correction to raw p-values across model pairs.
    """
    sorted_pairs = sorted(raw_p_values.keys(), key=lambda k: raw_p_values[k])
    m = len(sorted_pairs)
    corrected_p = {}
    cum_max = 0.0
    
    for i, pair in enumerate(sorted_pairs):
        p_val = raw_p_values[pair]
        adjusted = min(1.0, p_val * (m - i))
        cum_max = max(cum_max, adjusted)
        corrected_p[pair] = cum_max
        
    return corrected_p


def compute_significance_stability(
    verdicts_by_ref_and_model: Dict[int, Dict[str, List[EvaluatorVerdict]]],
    alpha: float = 0.05,
    n_flips: int = 20000,
    seed: int = 20261005
) -> Dict:
    """
    Computes statistical significance decision stability across reference choices using
    preregistered world-level paired sign-flip permutation tests with Holm-Bonferroni correction.
    """
    models = sorted(list(next(iter(verdicts_by_ref_and_model.values())).keys()))
    n_refs = len(verdicts_by_ref_and_model)
    
    pair_decisions: Dict[str, List[str]] = {}
    pair_raw_p_values: Dict[str, List[float]] = {}
    pair_adj_p_values: Dict[str, List[float]] = {}
    
    for ref_idx, model_dict in verdicts_by_ref_and_model.items():
        ref_raw_p = {}
        ref_diffs = {}
        
        for i, m1 in enumerate(models):
            for m2 in models[i + 1:]:
                pair_key = f"{m1}_vs_{m2}"
                mean_diff, raw_p = compute_world_level_pairwise_significance(
                    model_dict[m1], model_dict[m2], n_flips=n_flips, seed=seed + ref_idx
                )
                ref_diffs[pair_key] = mean_diff
                ref_raw_p[pair_key] = raw_p
                
        # Holm correction over the 6 pairs for this reference draw
        ref_adj_p = holm_bonferroni_correction(ref_raw_p)
        
        for pair_key in ref_raw_p:
            raw_p = ref_raw_p[pair_key]
            adj_p = ref_adj_p[pair_key]
            diff = ref_diffs[pair_key]
            
            if adj_p < alpha:
                dec = "SIGNIFICANT_A_WINS" if diff > 0 else "SIGNIFICANT_B_WINS"
            else:
                dec = "NON_SIGNIFICANT"
                
            pair_decisions.setdefault(pair_key, []).append(dec)
            pair_raw_p_values.setdefault(pair_key, []).append(raw_p)
            pair_adj_p_values.setdefault(pair_key, []).append(adj_p)
                
    stability_summary = {}
    for pair_key, dec_list in pair_decisions.items():
        counts = {d: dec_list.count(d) for d in set(dec_list)}
        probs = {d: counts[d] / n_refs for d in counts}
        adj_p_vals = pair_adj_p_values[pair_key]
        raw_p_vals = pair_raw_p_values[pair_key]
        stability_summary[pair_key] = {
            "decision_distribution": probs,
            "mean_adj_p_value": float(np.mean(adj_p_vals)),
            "std_adj_p_value": float(np.std(adj_p_vals)),
            "min_adj_p_value": float(np.min(adj_p_vals)),
            "max_adj_p_value": float(np.max(adj_p_vals)),
            "mean_raw_p_value": float(np.mean(raw_p_vals)),
            "is_decision_constant": len(set(dec_list)) == 1,
        }
        
    return {
        "n_references": n_refs,
        "n_sign_flips": n_flips,
        "pairwise_significance_summary": stability_summary,
    }


def compute_significance_stability_fast(
    world_ref_model_scores: Dict[str, Dict[int, Dict[str, float]]],
    ref_vectors: List[Dict[str, int]],
    alpha: float = 0.05,
    n_flips: int = 20000,
    seed: int = 20261005
) -> Dict:
    """
    Ultra-fast pre-vectorized significance stability calculator across sampled reference vectors.
    """
    worlds = sorted(list(world_ref_model_scores.keys()))
    models = sorted(list(next(iter(next(iter(world_ref_model_scores.values())).values())).keys()))
    n_refs = len(ref_vectors)
    
    pair_decisions: Dict[str, List[str]] = {}
    pair_raw_p_values: Dict[str, List[float]] = {}
    pair_adj_p_values: Dict[str, List[float]] = {}
    
    for ref_idx, ref_vec in enumerate(ref_vectors):
        ref_raw_p = {}
        ref_diffs = {}
        for i, m1 in enumerate(models):
            for m2 in models[i + 1:]:
                pair_key = f"{m1}_vs_{m2}"
                diffs = np.array([world_ref_model_scores[w][ref_vec[w]][m1] - world_ref_model_scores[w][ref_vec[w]][m2] for w in worlds])
                mean_diff = float(np.mean(diffs))
                raw_p = compute_world_level_sign_flip_pvalue(diffs, n_flips=n_flips, seed=seed + ref_idx)
                ref_diffs[pair_key] = mean_diff
                ref_raw_p[pair_key] = raw_p
                
        ref_adj_p = holm_bonferroni_correction(ref_raw_p)
        
        for pair_key in ref_raw_p:
            raw_p = ref_raw_p[pair_key]
            adj_p = ref_adj_p[pair_key]
            diff = ref_diffs[pair_key]
            if adj_p < alpha:
                dec = "SIGNIFICANT_A_WINS" if diff > 0 else "SIGNIFICANT_B_WINS"
            else:
                dec = "NON_SIGNIFICANT"
            pair_decisions.setdefault(pair_key, []).append(dec)
            pair_raw_p_values.setdefault(pair_key, []).append(raw_p)
            pair_adj_p_values.setdefault(pair_key, []).append(adj_p)
            
    stability_summary = {}
    for pair_key, dec_list in pair_decisions.items():
        counts = {d: dec_list.count(d) for d in set(dec_list)}
        probs = {d: counts[d] / n_refs for d in counts}
        adj_p_vals = pair_adj_p_values[pair_key]
        raw_p_vals = pair_raw_p_values[pair_key]
        stability_summary[pair_key] = {
            "decision_distribution": probs,
            "mean_adj_p_value": float(np.mean(adj_p_vals)),
            "std_adj_p_value": float(np.std(adj_p_vals)),
            "min_adj_p_value": float(np.min(adj_p_vals)),
            "max_adj_p_value": float(np.max(adj_p_vals)),
            "mean_raw_p_value": float(np.mean(raw_p_vals)),
            "is_decision_constant": len(set(dec_list)) == 1,
        }
        
    return {
        "n_references": n_refs,
        "n_sign_flips": n_flips,
        "pairwise_significance_summary": stability_summary,
    }


