"""
Statistics for the preregistered analysis (docs/PREREGISTRATION_V2.md §5-6).

Replaces AGY's metrics.py, which claimed McNemar and BH-FDR but implemented
neither, used an unseeded bootstrap, and computed Spearman over three
hand-coded "models" (NaN). Every function here is seeded and works on
per-instance paired data so that clustering by problem is respected.
"""

from typing import Dict, List, Sequence

import numpy as np
from scipy import stats

N_BOOT = 2000


def _rng(seed=0):
    return np.random.default_rng(seed)


def cluster_bootstrap_ci(values: Sequence[float], groups: Sequence, n_boot: int = N_BOOT, seed: int = 0) -> Dict:
    """Mean with a 95% CI from resampling whole groups (problems)."""
    values = np.asarray(values, float)
    if len(values) == 0:
        return {"mean": float("nan"), "ci95": [float("nan")] * 2, "n": 0, "n_groups": 0}
    uniq, inv = np.unique(np.asarray(groups), return_inverse=True)
    sums = np.bincount(inv, weights=values)
    cnts = np.bincount(inv).astype(float)
    rng = _rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(uniq), len(uniq))
        boots.append(sums[idx].sum() / cnts[idx].sum())
    return {"mean": float(values.mean()),
            "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "n": int(len(values)), "n_groups": int(len(uniq))}


def mcnemar_exact(a: Sequence[bool], b: Sequence[bool], alternative: str = "two-sided") -> Dict:
    """Exact McNemar on paired binary outcomes. alternative='greater' tests
    P(a=1,b=0) > P(a=0,b=1), i.e. mean(a) > mean(b)."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    n10 = int((a & ~b).sum())
    n01 = int((~a & b).sum())
    n = n10 + n01
    p = 1.0 if n == 0 else float(stats.binomtest(n10, n, 0.5, alternative=alternative).pvalue)
    return {"n10": n10, "n01": n01, "n_pairs": int(len(a)), "p": p,
            "diff": float(a.mean() - b.mean()) if len(a) else 0.0}


def flip_rate_vs_noise(flips: Sequence[bool], noise_flips: Sequence[bool]) -> Dict:
    """One-sided Fisher exact: is the flip rate above the noise-floor flip rate?"""
    f, nf = np.asarray(flips, bool), np.asarray(noise_flips, bool)
    table = [[int(f.sum()), int((~f).sum())], [int(nf.sum()), int((~nf).sum())]]
    p = float(stats.fisher_exact(table, alternative="greater").pvalue) if len(f) and len(nf) else 1.0
    return {"flip_rate": float(f.mean()) if len(f) else float("nan"),
            "noise_flip_rate": float(nf.mean()) if len(nf) else float("nan"),
            "n": int(len(f)), "n_noise": int(len(nf)), "p": p}


def holm(pvals: Dict[str, float], alpha: float = 0.05) -> Dict[str, Dict]:
    keys = sorted(pvals, key=lambda k: pvals[k])
    m = len(keys)
    out, running, stop = {}, 0.0, False
    for i, k in enumerate(keys):
        adj = min(1.0, (m - i) * pvals[k])
        running = max(running, adj)
        reject = (not stop) and running <= alpha
        if not reject:
            stop = True
        out[k] = {"p": pvals[k], "p_holm": running, "reject": reject}
    return out


def kendall_tau(x: Sequence[float], y: Sequence[float]) -> float:
    if len(set(x)) < 2 or len(set(y)) < 2:
        return float("nan")
    return float(stats.kendalltau(x, y).statistic)


def ranking_bootstrap(per_model_a: Dict[str, np.ndarray], per_model_b: Dict[str, np.ndarray],
                      n_boot: int = N_BOOT, seed: int = 0) -> Dict:
    """Instance-level scores for the same instances under two scorers.
    Returns observed tau, P(tau < 1) over bootstrap, and rank tables."""
    models = sorted(per_model_a)
    A = np.stack([np.asarray(per_model_a[m], float) for m in models])
    B = np.stack([np.asarray(per_model_b[m], float) for m in models])
    obs_a, obs_b = A.mean(1), B.mean(1)
    rng = _rng(seed)
    taus, inversions = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, A.shape[1], A.shape[1])
        ma, mb = A[:, idx].mean(1), B[:, idx].mean(1)
        taus.append(kendall_tau(ma, mb))
        inversions.append(_n_inversions(ma, mb))
    taus = np.asarray(taus)
    valid = taus[~np.isnan(taus)]
    return {
        "models": models,
        "score_a": dict(zip(models, map(float, obs_a))),
        "score_b": dict(zip(models, map(float, obs_b))),
        "rank_a": _ranks(models, obs_a), "rank_b": _ranks(models, obs_b),
        "tau_observed": kendall_tau(obs_a, obs_b),
        "inversions_observed": _n_inversions(obs_a, obs_b),
        "p_tau_lt_1": float((valid < 1 - 1e-9).mean()) if len(valid) else float("nan"),
        "p_any_inversion": float((np.asarray(inversions) > 0).mean()),
        "tau_ci95": [float(np.percentile(valid, 2.5)), float(np.percentile(valid, 97.5))] if len(valid) else None,
    }


def _ranks(models, scores) -> Dict[str, int]:
    order = np.argsort(-np.asarray(scores), kind="stable")
    return {models[i]: int(r + 1) for r, i in enumerate(order)}


def _n_inversions(a, b) -> int:
    n = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if (a[i] - a[j]) * (b[i] - b[j]) < 0:
                n += 1
    return n


def logistic_cluster_bootstrap(X: np.ndarray, y: np.ndarray, groups: Sequence, names: List[str],
                               n_boot: int = 1000, seed: int = 0) -> Dict:
    """Standardised-coefficient logistic regression with group-bootstrap CIs.
    (statsmodels is not installed; sklearn + bootstrap is the preregistered fallback.)"""
    from sklearn.linear_model import LogisticRegression
    X = np.asarray(X, float)
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    y = np.asarray(y, int)
    if len(set(y)) < 2:
        return {"degenerate": True, "positive_rate": float(y.mean())}
    fit = lambda Zs, ys: LogisticRegression(C=1e4, max_iter=5000).fit(Zs, ys).coef_[0]
    coef = fit(Z, y)
    uniq, inv = np.unique(np.asarray(groups), return_inverse=True)
    members = [np.where(inv == g)[0] for g in range(len(uniq))]
    rng = _rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = np.concatenate([members[g] for g in rng.integers(0, len(uniq), len(uniq))])
        if len(set(y[idx])) < 2:
            continue
        boots.append(fit(Z[idx], y[idx]))
    boots = np.asarray(boots)
    return {name: {"coef_std": float(c),
                   "ci95": [float(np.percentile(boots[:, k], 2.5)), float(np.percentile(boots[:, k], 97.5))],
                   "excludes_zero": bool(np.percentile(boots[:, k], 2.5) > 0 or np.percentile(boots[:, k], 97.5) < 0)}
            for k, (name, c) in enumerate(zip(names, coef))}


def spearman_bins(x: Sequence[float], y: Sequence[float], n_bins: int = 4) -> Dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    edges = np.unique(np.quantile(x, np.linspace(0, 1, n_bins + 1)))
    b = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
    means = [float(y[b == k].mean()) for k in range(len(edges) - 1) if (b == k).any()]
    rho = stats.spearmanr(range(len(means)), means).statistic if len(means) > 2 else float("nan")
    return {"bin_edges": [float(e) for e in edges], "bin_means": means,
            "bin_n": [int((b == k).sum()) for k in range(len(edges) - 1)], "spearman_rho_bins": float(rho)}
