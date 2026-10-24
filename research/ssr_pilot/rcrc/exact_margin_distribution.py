"""
Exact pairwise score-margin distribution via dynamic programming convolution.

For N tasks and models A, B:
  D_i(r_i) = (c_{Ai}(r_i) - c_{Bi}(r_i)) / K
  M_{AB}(R) = (1/N) * sum_i D_i(r_i)

Under independent per-world reference draws q_i, the DP convolves per-task
discrete distributions of D_i. Returns the exact margin distribution.

This uses floating-point arithmetic. For rational input probabilities, the
result is exact up to floating-point rounding error (~1e-15 for N=24).

COMPLEXITY: O(N * |D_support|^2) where |D_support| is the number of distinct
difference values per task (at most min(K+1, |V_i|) per task).

Mathematical note:
  E[S_m] identity: E[S_m] = (1/NK) sum_i sum_r q_i(r) c_{mi}(r)
  Under uniform q: E[S_m] = (1/N) sum_i (a_{mi} / |V_i|) / K * K = (1/N) sum_i a_{mi}/|V_i|
  where a_{mi} = number of valid outputs of m for task i (matching any valid ref).
  This weights tasks inversely by valid-space size. When |V_i| varies, this gives
  a different ranking than an unweighted E3 pass rate.

Winner reversal probability: 2 * p_positive * p_negative.
Derivation: P(reversal) = P(M_1 > 0 and M_2 < 0) + P(M_1 < 0 and M_2 > 0)
  = p_+ * p_- + p_- * p_+ = 2*p_+*p_- (under independence of the two draws).
"""

from collections import defaultdict
from fractions import Fraction
import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np


def per_task_diff_distribution(
    c_A: Union[List[int], np.ndarray],
    c_B: Union[List[int], np.ndarray],
    K: int,
    q: Union[List[float], np.ndarray],
) -> Dict[float, float]:
    """
    Computes discrete difference distribution for a single task i.

    Args:
        c_A: 1D array of length |V_i|, match counts in [0, K] for model A.
        c_B: 1D array of length |V_i|, match counts in [0, K] for model B.
        K: Number of generations per task.
        q: 1D probability array over reference space summing to 1.

    Returns:
        Dict mapping difference value (c_A[r] - c_B[r]) / K to aggregated probability.
    """
    c_A_arr = np.asarray(c_A)
    c_B_arr = np.asarray(c_B)
    q_arr = np.asarray(q, dtype=float)

    n_refs = len(q_arr)
    if len(c_A_arr) != n_refs or len(c_B_arr) != n_refs:
        raise ValueError(f"Length mismatch: len(c_A)={len(c_A_arr)}, len(c_B)={len(c_B_arr)}, len(q)={n_refs}")
    if not np.isclose(np.sum(q_arr), 1.0, atol=1e-7):
        raise ValueError(f"Probabilities must sum to 1, got {np.sum(q_arr)}")

    diff_counts = defaultdict(float)
    for r in range(n_refs):
        # Difference in [-K, K]
        diff_int = int(round(c_A_arr[r] - c_B_arr[r]))
        diff_counts[diff_int] += float(q_arr[r])

    # Convert integer difference to float scaled by K
    dist: Dict[float, float] = {}
    for diff_int, prob in diff_counts.items():
        if prob > 0.0:
            diff_val = float(diff_int) / float(K)
            dist[diff_val] = prob

    return dist


def dp_convolve_margin_distributions(
    per_task_dists: List[Dict[float, float]],
    N: int,
    K: Optional[int] = None,
) -> Dict[float, float]:
    """
    Convolves N per-task distributions to get distribution of M_AB = (1/N) * sum_i D_i.

    First convolves raw sums as integer multiples of 1/K, then scales to margin by dividing by N.

    Args:
        per_task_dists: List of N per-task difference distributions.
        N: Number of tasks.
        K: Optional int scale factor. If None, detected from rational keys.

    Returns:
        Dict mapping margin value to probability.
    """
    if N == 0 or len(per_task_dists) == 0:
        return {0.0: 1.0}

    # Detect common denominator K if not provided
    if K is None:
        denoms = []
        for d in per_task_dists:
            for val in d:
                if abs(val) > 1e-12:
                    denoms.append(Fraction(val).limit_denominator(1000).denominator)
        K = math.lcm(*denoms) if denoms else 1

    # Convolve raw integer sums (each task diff is diff_int / K)
    raw_dist: Dict[int, float] = {0: 1.0}

    for task_dist in per_task_dists:
        next_dist: Dict[int, float] = defaultdict(float)
        for cur_sum, cur_p in raw_dist.items():
            if cur_p == 0.0:
                continue
            for diff_val, prob in task_dist.items():
                if prob == 0.0:
                    continue
                diff_int = int(round(diff_val * K))
                next_dist[cur_sum + diff_int] += cur_p * prob
        raw_dist = dict(next_dist)

    # Scale raw sum to margin: margin = (raw_sum / K) / N = raw_sum / (N * K)
    margin_dist: Dict[float, float] = {}
    total_scale = float(N * K)
    for raw_sum in sorted(raw_dist.keys()):
        prob = raw_dist[raw_sum]
        margin_val = float(raw_sum) / total_scale
        if abs(margin_val) < 1e-15:
            margin_val = 0.0
        margin_dist[margin_val] = float(prob)

    return margin_dist


def compute_exact_pairwise_margin(
    task_data: List[Dict],
    K: int,
    q_type: Union[str, List[np.ndarray], Tuple[np.ndarray, ...]] = "uniform",
) -> Dict:
    """
    Computes exact pairwise margin distribution and related statistics for models A and B.

    Args:
        task_data: List of N dicts, each with keys 'c_A' (array), 'c_B' (array), 'n_refs' (int).
        K: Number of generations per task.
        q_type: 'uniform' (use 1/n_refs for each) or list/tuple of N probability arrays.

    Returns:
        Dict containing:
          - margin_distribution: Dict[float, float]
          - expected_margin: float
          - variance_margin: float
          - std_margin: float
          - p_positive: float
          - p_negative: float
          - p_zero: float
          - winner_reversal_probability: float (2 * p_+ * p_-)
          - pairwise_reversal_probability: float
          - n_tasks: int
          - K: int
    """
    N = len(task_data)
    per_task_dists: List[Dict[float, float]] = []

    for i, t in enumerate(task_data):
        n_refs = t.get("n_refs", len(t["c_A"]))
        c_A = np.asarray(t["c_A"])[:n_refs]
        c_B = np.asarray(t["c_B"])[:n_refs]

        if q_type == "uniform":
            q = np.full(n_refs, 1.0 / n_refs)
        elif isinstance(q_type, (list, tuple, np.ndarray)):
            q = np.asarray(q_type[i])[:n_refs]
        else:
            raise ValueError(f"Unknown q_type: {q_type}")

        dist_i = per_task_diff_distribution(c_A, c_B, K, q)
        per_task_dists.append(dist_i)

    margin_dist = dp_convolve_margin_distributions(per_task_dists, N=N, K=K)

    # Compute statistics
    p_positive = sum(p for m, p in margin_dist.items() if m > 1e-12)
    p_negative = sum(p for m, p in margin_dist.items() if m < -1e-12)
    p_zero = sum(p for m, p in margin_dist.items() if abs(m) <= 1e-12)

    expected_margin = sum(m * p for m, p in margin_dist.items())
    variance_margin = sum(((m - expected_margin) ** 2) * p for m, p in margin_dist.items())
    std_margin = float(np.sqrt(max(0.0, variance_margin)))

    # Exact winner reversal probability under independent draws: 2 * p_+ * p_-
    reversal_prob = 2.0 * p_positive * p_negative

    return {
        "margin_distribution": margin_dist,
        "expected_margin": float(expected_margin),
        "variance_margin": float(variance_margin),
        "std_margin": std_margin,
        "p_positive": float(p_positive),
        "p_negative": float(p_negative),
        "p_zero": float(p_zero),
        "winner_reversal_probability": float(reversal_prob),
        "pairwise_reversal_probability": float(reversal_prob),
        "n_tasks": N,
        "K": K,
    }
