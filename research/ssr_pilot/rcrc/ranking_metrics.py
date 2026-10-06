"""
Benchmark-level ranking and pairwise model stability across valid reference choices.
Includes tie-aware ranking mechanics (fractional ranks and Kendall tau-b) without artificial string tie-breaking.
"""

from typing import Dict, List, Sequence, Tuple
import numpy as np
from scipy import stats
from research.ssr_pilot.core.schema import EvaluatorVerdict


def compute_model_scores(verdicts: Sequence[EvaluatorVerdict]) -> Dict[str, float]:
    """
    Computes accuracy / pass rate for each model under a specific reference evaluation.
    """
    by_model: Dict[str, List[bool]] = {}
    for v in verdicts:
        by_model.setdefault(v.model, []).append(v.evaluator_pass)
    
    return {m: float(np.mean(passes)) for m, passes in by_model.items()}


def get_model_ranking(scores: Dict[str, float]) -> List[str]:
    """
    Returns sorted model names from highest score to lowest score.
    Ties are grouped into tied rank sets (alphabetical ordering retained only for list output presentation,
    while statistical Kendall tau computations use exact score vectors with tie handling).
    """
    return sorted(scores.keys(), key=lambda m: (-scores[m], m))


def compute_kendall_tau_scores(scores1: Dict[str, float], scores2: Dict[str, float]) -> float:
    """
    Computes Kendall's tau-b correlation directly from model score vectors.

    Degenerate-vector handling policy (predeclared; see deviation log D4):
    - Both vectors constant (all models score identically): return 1.0.
      Justification: both ranking vectors rank all models tied #1 — the ranking
      structure is identical, making 1.0 the most defensible finite value.
      This holds regardless of whether the two constant values are equal.
    - Exactly one vector constant: return float('nan').
      Justification: tau-b denominator = 0 in one factor; the metric is genuinely
      undefined. Callers must track and exclude these draws from aggregate statistics.
    - scipy returns NaN for non-constant input: return float('nan').
      Should not occur for tau-b with n=4 non-constant vectors; tracked if seen.
    """
    models = sorted(list(scores1.keys()))
    assert set(models) == set(scores2.keys()), "Score dicts must contain identical model sets"

    vec1 = np.array([scores1[m] for m in models])
    vec2 = np.array([scores2[m] for m in models])

    is_const1 = bool(np.all(vec1 == vec1[0]))
    is_const2 = bool(np.all(vec2 == vec2[0]))

    if is_const1 and is_const2:
        # Both rankings are fully tied — identical ranking structure.
        return 1.0
    if is_const1 or is_const2:
        # One ranking is fully tied, the other is not — tau-b is undefined.
        return float('nan')

    tau, _ = stats.kendalltau(vec1, vec2, variant='b')
    if np.isnan(tau):
        return float('nan')
    return float(tau)


def rankings_are_identical_tie_aware(scores1: Dict[str, float], scores2: Dict[str, float]) -> bool:
    """
    Tie-aware ranking identity check: two score dicts have identical rankings iff
    for every model pair (A, B): sign(s1_A - s1_B) == sign(s2_A - s2_B).

    Ties are preserved: if A and B tie under scores1 they must also tie under scores2.
    This is the correct criterion for oracle-recovery matching — a bare tau==1.0
    check is equivalent only when no ties exist in either score vector.
    """
    models = sorted(scores1.keys())
    for i, m1 in enumerate(models):
        for m2 in models[i + 1:]:
            sgn1 = np.sign(scores1[m1] - scores1[m2])
            sgn2 = np.sign(scores2[m1] - scores2[m2])
            if sgn1 != sgn2:
                return False
    return True


def compute_kendall_tau(ranking1: List[str], ranking2: List[str]) -> float:
    """
    Legacy wrapper for rank lists. Computes Kendall's tau correlation between two model rank lists.
    """
    assert set(ranking1) == set(ranking2), "Rankings must contain identical model sets"
    m_list = sorted(list(ranking1))
    r1_pos = [ranking1.index(m) for m in m_list]
    r2_pos = [ranking2.index(m) for m in m_list]
    tau, _ = stats.kendalltau(r1_pos, r2_pos, variant='b')
    return float(tau) if not np.isnan(tau) else float('nan')


def compute_pairwise_win_matrix(scores_by_ref: Dict[int, Dict[str, float]]) -> Dict:
    """
    Computes pairwise win probabilities and reversal probabilities across all evaluated reference choices.
    Ties are explicitly counted.
    Strict reversal probability: fraction of reference pairs (R1, R2) where pairwise winner strictly flips
    (i.e., score(A) > score(B) under R1 and score(B) > score(A) under R2).
    """
    models = sorted(list(next(iter(scores_by_ref.values())).keys()))
    win_counts: Dict[str, Dict[str, int]] = {m1: {m2: 0 for m2 in models} for m1 in models}
    tie_counts: Dict[str, Dict[str, int]] = {m1: {m2: 0 for m2 in models} for m1 in models}
    n_refs = len(scores_by_ref)

    for ref_idx, scores in scores_by_ref.items():
        for i, m1 in enumerate(models):
            for m2 in models[i + 1:]:
                s1, s2 = scores[m1], scores[m2]
                if s1 > s2:
                    win_counts[m1][m2] += 1
                elif s2 > s1:
                    win_counts[m2][m1] += 1
                else:
                    tie_counts[m1][m2] += 1
                    tie_counts[m2][m1] += 1

    pairwise_prob: Dict[str, Dict[str, float]] = {m1: {} for m1 in models}
    for m1 in models:
        for m2 in models:
            if m1 == m2:
                pairwise_prob[m1][m2] = 0.0
            else:
                pairwise_prob[m1][m2] = win_counts[m1][m2] / n_refs

    # Reversal probability calculation across reference draws
    # To handle 50,000 reference draws efficiently without O(N^2) loops over 50k draws,
    # for each model pair (A, B), we count how many draws have A > B (n_win_A), B > A (n_win_B), and A == B (n_tie).
    # Total reference pairs for pair (A, B) is N * (N - 1) / 2.
    # A strict reversal occurs when drawing one reference where A > B and another where B > A.
    # So number of reversing pairs for (A, B) is n_win_A * n_win_B.
    
    total_pair_comparisons = 0
    total_reversals = 0
    
    n_model_pairs = len(models) * (len(models) - 1) // 2
    
    for i, m1 in enumerate(models):
        for m2 in models[i + 1:]:
            n_win_1 = win_counts[m1][m2]
            n_win_2 = win_counts[m2][m1]
            n_reversals_pair = n_win_1 * n_win_2
            n_total_ref_pairs = n_refs * (n_refs - 1) // 2
            
            total_reversals += n_reversals_pair
            total_pair_comparisons += n_total_ref_pairs

    reversal_prob = (total_reversals / total_pair_comparisons) if total_pair_comparisons > 0 else 0.0

    return {
        "models": models,
        "n_references": n_refs,
        "pairwise_win_probabilities": pairwise_prob,
        "pairwise_reversal_probability": float(reversal_prob),
    }

