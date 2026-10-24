"""
Total-variation distance robustness certificate for expected pairwise margins.

PROPOSITION (TV Lipschitz bound for bounded functions, standard result):
Let D_i: V_i -> [-1, 1]. For distributions q and q^0 over V_i:
  |E_{q_i}[D_i] - E_{q^0_i}[D_i]| <= 2 * TV(q_i, q^0_i)
Thus:
  |mu_{AB}(q) - mu_{AB}(q^0)| 
    = |(1/N) sum_i (E_{q_i}[D_i] - E_{q^0_i}[D_i])|
    <= (1/N) sum_i |E_{q_i}[D_i] - E_{q^0_i}[D_i]|
    <= (2/N) sum_i TV(q_i, q^0_i)

PROOF: The first two inequalities are triangle inequality. The last holds because
|E_q[f] - E_{q^0}[f]| = |sum_r f(r)(q(r) - q^0(r))| 
<= sup|f| * sum_r |q(r) - q^0(r)| = sup|f| * 2*TV(q,q^0).
For D_i in [-1,1], sup|D_i| <= 1, giving the factor of 2.

Note: This bound is NOT novel. It is a standard consequence of the TV metric
being the largest coupling. Its application to RCR is new in context, but
the mathematics is textbook (e.g., Levin & Peres, Markov Chains and Mixing
Times, 2017, Lemma 4.2).

IMPORTANT - SUFFICIENT VS. NECESSARY CONDITION:
The condition |mu_{AB}(q^0)| > (2/N) * sum_i TV(q_i, q^0_i) is a SUFFICIENT condition
for sign invariance under worst-case distribution shift. It is NOT a necessary condition.
Failure of the certificate (|mu| <= bound) means the sufficient condition cannot guarantee
invariance; it does NOT prove that the expected margin sign flips or is unstable.
For instance, if D_i(r) > 0 for all r in V_i, the expected margin sign is strictly positive
under ALL probability distributions, yet a loose TV bound may fail to certify this.

Note: This bound is on the EXPECTED margin. It does not guarantee that every
sampled reference vector gives the same sign.
"""

from typing import Dict, List, Optional, Union
import numpy as np


def tv_distance(q1: Union[List[float], np.ndarray], q2: Union[List[float], np.ndarray]) -> float:
    """
    Computes total variation distance between two discrete distributions:
      TV(q1, q2) = 0.5 * sum |q1 - q2|

    Validates that both sum to 1 within 1e-9.
    """
    arr1 = np.asarray(q1, dtype=float)
    arr2 = np.asarray(q2, dtype=float)

    if len(arr1) != len(arr2):
        raise ValueError(f"Support size mismatch: len(q1)={len(arr1)}, len(q2)={len(arr2)}")
    if not np.isclose(np.sum(arr1), 1.0, atol=1e-9):
        raise ValueError(f"q1 does not sum to 1: sum={np.sum(arr1)}")
    if not np.isclose(np.sum(arr2), 1.0, atol=1e-9):
        raise ValueError(f"q2 does not sum to 1: sum={np.sum(arr2)}")

    return float(0.5 * np.sum(np.abs(arr1 - arr2)))


def tv_bound_on_expected_margin_change(tv_distances_per_world: List[float], N: int) -> float:
    """
    Computes upper bound on change in expected pairwise margin:
      bound = (2 / N) * sum_i TV(q_i, q^0_i)
    """
    return float((2.0 / float(N)) * float(np.sum(tv_distances_per_world)))


def certify_margin_sign(expected_margin: float, tv_budget: float) -> Dict:
    """
    Evaluates whether the sign of the expected margin is certified robust under a given TV budget.

    Args:
        expected_margin: mu_{AB}(q^0), expected margin under baseline distribution.
        tv_budget: Upper bound on margin change induced by TV perturbation.

    Returns:
        Dict containing:
          - certified: bool (|expected_margin| > tv_budget)
          - expected_margin: float
          - tv_bound: float
          - certified_sign: int (+1, -1) or None
          - certifying_condition: str
    """
    margin_mag = abs(expected_margin)
    is_certified = bool(margin_mag > tv_budget)

    if is_certified:
        sign = 1 if expected_margin > 0 else -1
        condition = f"|expected_margin| ({margin_mag:.6f}) > tv_bound ({tv_budget:.6f}): sign is invariant under any distribution within TV budget"
    else:
        sign = None
        condition = f"|expected_margin| ({margin_mag:.6f}) <= tv_bound ({tv_budget:.6f}): sufficient bound cannot certify sign invariance (certificate failure; does not prove sign will flip)"

    return {
        "certified": is_certified,
        "expected_margin": float(expected_margin),
        "tv_bound": float(tv_budget),
        "certified_sign": sign,
        "certifying_condition": condition,
    }


def tv_budget_for_canonical_bias(p: float, n_refs: int) -> float:
    """
    Calculates TV distance between canonical-bias distribution and uniform distribution.

    Canonical bias distribution:
      q^0 = uniform (1/n_refs each)
      q = [p, (1-p)/(n_refs-1), ..., (1-p)/(n_refs-1)] for n_refs > 1.

    Formula:
      TV = 0.5 * (|p - 1/n_refs| + (n_refs - 1)*|(1-p)/(n_refs-1) - 1/n_refs|)
         = |p - 1/n_refs|
    """
    if n_refs <= 1:
        return 0.0
    return float(abs(p - (1.0 / float(n_refs))))
