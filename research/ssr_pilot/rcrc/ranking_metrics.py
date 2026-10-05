"""
Benchmark-level ranking and pairwise model stability across valid reference choices.
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
    Ties broken alphabetically for stability.
    """
    return sorted(scores.keys(), key=lambda m: (-scores[m], m))


def compute_kendall_tau(ranking1: List[str], ranking2: List[str]) -> float:
    """
    Computes Kendall's tau correlation between two model rankings.
    """
    assert set(ranking1) == set(ranking2), "Rankings must contain identical model sets"
    m_list = sorted(list(ranking1))
    r1_pos = [ranking1.index(m) for m in m_list]
    r2_pos = [ranking2.index(m) for m in m_list]
    tau, _ = stats.kendalltau(r1_pos, r2_pos)
    return float(tau) if not np.isnan(tau) else 1.0


def compute_pairwise_win_matrix(scores_by_ref: Dict[int, Dict[str, float]]) -> Dict:
    """
    Computes pairwise win probabilities across all evaluated reference choices.
    For models A and B:
    P(A > B): fraction of references where score(A) > score(B).
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

    # Reversal probability: fraction of reference pairs (R1, R2) where pairwise winner flips
    reversal_counts = 0
    total_pairs = 0
    refs = list(scores_by_ref.keys())
    
    for i, r1 in enumerate(refs):
        for r2 in refs[i + 1:]:
            s_r1 = scores_by_ref[r1]
            s_r2 = scores_by_ref[r2]
            for m_i, m1 in enumerate(models):
                for m2 in models[m_i + 1:]:
                    w1 = np.sign(s_r1[m1] - s_r1[m2])
                    w2 = np.sign(s_r2[m1] - s_r2[m2])
                    if w1 != 0 and w2 != 0 and w1 != w2:
                        reversal_counts += 1
                    total_pairs += 1

    reversal_prob = (reversal_counts / total_pairs) if total_pairs > 0 else 0.0

    return {
        "models": models,
        "n_references": n_refs,
        "pairwise_win_probabilities": pairwise_prob,
        "pairwise_reversal_probability": reversal_prob,
    }
