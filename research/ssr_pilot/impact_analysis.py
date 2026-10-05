"""
Conclusion-impact analysis of the frozen SSR data (no new generation).

    python -m research.ssr_pilot.impact_analysis

Reads the already-scored records of the two arms and writes ONLY to
research/ssr_pilot/results/impact_analysis/. The frozen result folders are never written.

The distortion metrics are defined in DEFINITIONS below. The text is hashed and the hash is
stored in analysis.json, so the definitions cannot change after the numbers are seen.
World = statistical unit (24 worlds); bootstraps resample whole worlds.
"""

import hashlib
import itertools
import json
import os
from collections import Counter
from typing import Dict, List, Optional

import numpy as np

from research.evaluation import metrics as M
from research.ssr_pilot.analyze import proxy_analysis, signflip_p

ARMS = {"original": "research/ssr_pilot/results/llm/records.jsonl",
        "stated": "research/ssr_pilot/results/stated_convention/records.jsonl"}
OUT = "research/ssr_pilot/results/impact_analysis"
EVALS = ("B", "C", "A_norm", "A_strict")
N_BOOT = 2000
SEED = 0
ALPHA = 0.05
MIN_GAP_FOR_RATIO = 0.02

DEFINITIONS = """\
Unit: world. s[m,w] = mean over the 12 generations (3 variants x 4 seeds) of model m in world w.
Evaluators: B (oracle, UNVERIFIABLE = invalid), C (B and outcome-equivalent to R), A_norm, A_strict.
Pairwise gap d_E(a,b) = mean over worlds of s_E[a] - s_E[b]; CI = 95% percentile, 2,000 world bootstraps (seed 0).
1. Weak ranking reversal (pair): sign(d_B) and sign(d_A) are both nonzero and opposite. NOT called a reversal on its own.
2. Decisive ranking reversal (pair): weak reversal AND both 95% CIs (d_B and d_A) exclude 0.
3. Ranking stability: per evaluator, P(bootstrap rank order == point-estimate rank order); paired agreement
   P(rank order under A_norm == rank order under B within the same bootstrap sample); Kendall tau between the evaluators
   (point estimate and bootstrap CI); rank-probability matrix.
4. Pairwise decision reversal: for a pair, the decision "a better than b" (sign of the gap, only counted when the
   evaluator's CI excludes 0) differs between evaluators, including "decided" vs "undecided".
5. Nominal significance change (pair): Holm-adjusted paired sign-flip decisions (alpha 0.05, 6 pairs, 20,000 flips)
   differ between A_norm and B.  Supported significance change: nominal AND the 95% CI of the evaluator effect on the
   gap (d_A - d_B) excludes 0 (so a difference between 'significant' and 'not significant' is not itself taken as evidence).
6. Relative distortion: gap ratio d_B/d_A, reported only when |d_A| >= 0.02 (otherwise undefined); spread ratio =
   (max-min model score under B) / (same under A_norm).
7. Absolute distortion: per model B - A_norm and A_norm / B with world-bootstrap CI.
8. Taxonomy distortion: per model share of A_norm-'wrong' outputs that are oracle-valid (ratio of sums over worlds, CI),
   and the shares valid-noncanonical / invalid (FALSE) / UNVERIFIABLE among all outputs.
A pair is labelled 'reversal' ONLY under definition 2; 'significance change' ONLY under definition 5 (supported).
"""
DEFINITIONS_SHA256 = hashlib.sha256(DEFINITIONS.encode()).hexdigest()


# ---------------------------------------------------------------- pure helpers (unit-tested)

def sign0(x: float) -> int:
    return 0 if x == 0 else (1 if x > 0 else -1)


def ci_excludes_zero(ci) -> bool:
    return bool(ci[0] > 0 or ci[1] < 0)


def weak_reversal(dA: float, dB: float) -> bool:
    return sign0(dA) * sign0(dB) < 0


def decisive_reversal(dA: float, dB: float, ciA, ciB) -> bool:
    return weak_reversal(dA, dB) and ci_excludes_zero(ciA) and ci_excludes_zero(ciB)


def decision(d: float, ci) -> int:
    """+1 / -1 if the gap is decided (CI excludes 0), else 0."""
    return sign0(d) if ci_excludes_zero(ci) else 0


def decision_reversal(dA: float, ciA, dB: float, ciB) -> bool:
    return decision(dA, ciA) != decision(dB, ciB)


def supported_significance_change(nominal: bool, ci_effect) -> bool:
    return bool(nominal and ci_excludes_zero(ci_effect))


def gap_ratio(dA: float, dB: float) -> Optional[float]:
    return None if abs(dA) < MIN_GAP_FOR_RATIO else dB / dA


def rank_vector(scores: np.ndarray) -> tuple:
    """Competition ranks (1 = best); ties share the best rank."""
    scores = np.asarray(scores, float)
    return tuple(int(1 + (scores > s).sum()) for s in scores)


def pct(v, lo=2.5, hi=97.5):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    return [float(np.percentile(v, lo)), float(np.percentile(v, hi))] if len(v) else [float("nan")] * 2


def ratio_of_sums(num: np.ndarray, den: np.ndarray, boots: np.ndarray) -> Dict:
    point = float(num.sum() / den.sum()) if den.sum() else float("nan")
    bs = [num[i].sum() / den[i].sum() if den[i].sum() else np.nan for i in boots]
    return {"point": point, "ci95": pct(bs)}


def world_matrix(records: List[Dict], models: List[str], key: str, worlds: List[str]) -> Dict[str, np.ndarray]:
    acc: Dict = {}
    for r in records:
        acc.setdefault((r["model"], r["world"]), []).append(float(r[key]))
    return {m: np.array([np.mean(acc[(m, w)]) for w in worlds]) for m in models}


# ---------------------------------------------------------------- core comparison

def compare_evaluators(SA: Dict[str, np.ndarray], SB: Dict[str, np.ndarray], models: List[str],
                       n_boot: int = N_BOOT, seed: int = SEED, n_flips: int = 20000) -> Dict:
    """SA = reference-style evaluator world scores, SB = oracle-style world scores (model -> (W,) array)."""
    W = len(next(iter(SA.values())))
    rng = np.random.default_rng(seed)
    boots = rng.integers(0, W, (n_boot, W))
    pairs = list(itertools.combinations(models, 2))
    pa = {f"{a}|{b}": signflip_p(SA[a] - SA[b], n_flips) for a, b in pairs}
    pb = {f"{a}|{b}": signflip_p(SB[a] - SB[b], n_flips) for a, b in pairs}
    ha, hb = M.holm(pa, ALPHA), M.holm(pb, ALPHA)
    rows = []
    for a, b in pairs:
        k = f"{a}|{b}"
        dA, dB = SA[a] - SA[b], SB[a] - SB[b]
        mA, mB = float(dA.mean()), float(dB.mean())
        ciA = pct([dA[i].mean() for i in boots])
        ciB = pct([dB[i].mean() for i in boots])
        effect = pct([(dA[i] - dB[i]).mean() for i in boots])
        nominal = bool(ha[k]["reject"] != hb[k]["reject"])
        rows.append({
            "pair": k, "d_A": mA, "d_B": mB, "ci_A": ciA, "ci_B": ciB,
            "p_holm_A": ha[k]["p_holm"], "p_holm_B": hb[k]["p_holm"],
            "holm_reject_A": bool(ha[k]["reject"]), "holm_reject_B": bool(hb[k]["reject"]),
            "weak_reversal": weak_reversal(mA, mB),
            "decisive_reversal": decisive_reversal(mA, mB, ciA, ciB),
            "decision_reversal": decision_reversal(mA, ciA, mB, ciB),
            "nominal_significance_change": nominal,
            "effect_ci_dA_minus_dB": effect,
            "supported_significance_change": supported_significance_change(nominal, effect),
            "gap_ratio_B_over_A": gap_ratio(mA, mB),
        })
    point = {e: rank_vector(np.array([S[m].mean() for m in models])) for e, S in (("A", SA), ("B", SB))}
    rv = {"A": [], "B": []}
    tau_bs, agree = [], []
    probs = {e: np.zeros((len(models), len(models))) for e in rv}
    for i in boots:
        sa = np.array([SA[m][i].mean() for m in models])
        sb = np.array([SB[m][i].mean() for m in models])
        ra, rb = rank_vector(sa), rank_vector(sb)
        rv["A"].append(ra)
        rv["B"].append(rb)
        agree.append(ra == rb)
        tau_bs.append(M.kendall_tau(sa, sb))
        for e, r in (("A", ra), ("B", rb)):
            for j, rk in enumerate(r):
                probs[e][j, rk - 1] += 1
    tau_point = M.kendall_tau([SA[m].mean() for m in models], [SB[m].mean() for m in models])
    ranking = {
        "models": models,
        "point_rank_A": point["A"], "point_rank_B": point["B"],
        "same_point_order": bool(point["A"] == point["B"]),
        "P_boot_order_equals_point_A": float(np.mean([r == point["A"] for r in rv["A"]])),
        "P_boot_order_equals_point_B": float(np.mean([r == point["B"] for r in rv["B"]])),
        "P_paired_order_agreement": float(np.mean(agree)),
        "kendall_tau": float(tau_point), "kendall_tau_ci95": pct(tau_bs),
        "rank_probability_A": (probs["A"] / n_boot).round(3).tolist(),
        "rank_probability_B": (probs["B"] / n_boot).round(3).tolist(),
    }
    spread = {e: float(max(S[m].mean() for m in models) - min(S[m].mean() for m in models))
              for e, S in (("A", SA), ("B", SB))}
    return {"n_worlds": W, "pairs": rows, "ranking": ranking, "spread": spread,
            "spread_ratio_B_over_A": spread["B"] / spread["A"] if spread["A"] else None,
            "n_decisive_reversals": sum(r["decisive_reversal"] for r in rows),
            "n_weak_reversals": sum(r["weak_reversal"] for r in rows),
            "n_supported_significance_changes": sum(r["supported_significance_change"] for r in rows),
            "n_nominal_significance_changes": sum(r["nominal_significance_change"] for r in rows),
            "n_decision_reversals": sum(r["decision_reversal"] for r in rows)}


# ---------------------------------------------------------------- per-arm analysis

def per_model_effects(records, models, worlds, boots) -> Dict:
    out = {}
    for m in models:
        mr = [r for r in records if r["model"] == m]

        def per_world(f):
            return np.array([sum(f(r) for r in mr if r["world"] == w) for w in worlds], float)

        n = per_world(lambda r: 1.0)
        nB, nA = per_world(lambda r: r["B"]), per_world(lambda r: r["A_norm"])
        wrong = per_world(lambda r: not r["A_norm"])
        wrong_valid = per_world(lambda r: (not r["A_norm"]) and r["B"])
        fr = per_world(lambda r: r["B"] and not r["A_norm"])
        fa = per_world(lambda r: r["A_norm"] and not r["B"])
        sem = Counter(r["semantic"] for r in mr)
        out[m] = {
            "n": len(mr),
            "rates": {e: ratio_of_sums(per_world(lambda r, e=e: r[e]), n, boots) for e in EVALS + ("B_ub",)},
            "abs_distortion_B_minus_A_norm": ratio_of_sums(nB - nA, n, boots),
            "A_norm_over_B": ratio_of_sums(nA, nB, boots) if nB.sum() else None,
            "FRR_norm": ratio_of_sums(fr, nB, boots) if nB.sum() else None,
            "n_valid": int(nB.sum()),
            "valid_noncanonical_rate": ratio_of_sums(fr, n, boots),
            "invalid_acceptance_rate": ratio_of_sums(fa, n, boots),
            "share_valid_among_A_wrong": ratio_of_sums(wrong_valid, wrong, boots) if wrong.sum() else None,
            "semantic_shares": {k: v / len(mr) for k, v in sorted(sem.items())},
            "top_invalid_reasons": Counter(r["reason"] for r in mr if r["semantic"] == "FALSE").most_common(4),
        }
    return out


def subset_robustness(records, models, key, values) -> Dict:
    out = {}
    for v in sorted(values):
        sub = [r for r in records if r[key] == v]
        ws = sorted({r["world"] for r in sub})
        SA = world_matrix(sub, models, "A_norm", ws)
        SB = world_matrix(sub, models, "B", ws)
        sa = [SA[m].mean() for m in models]
        sb = [SB[m].mean() for m in models]
        valid = [r for r in sub if r["B"]]
        out[v] = {"n_worlds": len(ws), "B": dict(zip(models, np.round(sb, 3).tolist())),
                  "A_norm": dict(zip(models, np.round(sa, 3).tolist())),
                  "rank_B": rank_vector(np.array(sb)), "rank_A_norm": rank_vector(np.array(sa)),
                  "tau": float(M.kendall_tau(sa, sb)),
                  "FRR_norm": float(np.mean([not r["A_norm"] for r in valid])) if valid else None,
                  "n_valid": len(valid)}
    return out


def family_comparisons(records: List[Dict], models: List[str]) -> Dict:
    """Same definitions applied inside each family (8 worlds each): is any family-level reversal decisive?"""
    out = {}
    for fam in sorted({r["family"] for r in records}):
        sub = [r for r in records if r["family"] == fam]
        ws = sorted({r["world"] for r in sub})
        out[fam] = compare_evaluators(world_matrix(sub, models, "A_norm", ws),
                                      world_matrix(sub, models, "B", ws), models)
    return out


def analyze_arm(records: List[Dict]) -> Dict:
    models = sorted({r["model"] for r in records})
    worlds = sorted({r["world"] for r in records})
    boots = np.random.default_rng(SEED).integers(0, len(worlds), (N_BOOT, len(worlds)))
    S = {e: world_matrix(records, models, e, worlds) for e in EVALS + ("B_ub",)}
    return {"models": models, "n_records": len(records), "n_worlds": len(worlds),
            "per_model": per_model_effects(records, models, worlds, boots),
            "A_norm_vs_B": compare_evaluators(S["A_norm"], S["B"], models),
            "A_norm_vs_B_ub": compare_evaluators(S["A_norm"], S["B_ub"], models),
            "A_strict_vs_B": compare_evaluators(S["A_strict"], S["B"], models),
            "A_norm_vs_C": compare_evaluators(S["A_norm"], S["C"], models),
            "by_family": subset_robustness(records, models, "family", {r["family"] for r in records}),
            "by_family_comparison": family_comparisons(records, models),
            "by_variant": subset_robustness(records, models, "variant", {r["variant"] for r in records}),
            "proxies": proxy_analysis(records)}


def paired_arm_effect(orig: List[Dict], stated: List[Dict], models: List[str]) -> Dict:
    worlds = sorted({r["world"] for r in orig})
    boots = np.random.default_rng(SEED).integers(0, len(worlds), (N_BOOT, len(worlds)))
    out = {}
    for m in models:
        o_, s_ = [r for r in orig if r["model"] == m], [r for r in stated if r["model"] == m]
        row = {}
        for key in ("B", "A_norm"):
            d = world_matrix(s_, [m], key, worlds)[m] - world_matrix(o_, [m], key, worlds)[m]
            row[f"{key}_stated_minus_original"] = {"point": float(d.mean()), "ci95": pct([d[i].mean() for i in boots])}
        out[m] = row
    return out


def load(path: str) -> List[Dict]:
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    arms = {k: load(p) for k, p in ARMS.items()}
    res = {"definitions_sha256": DEFINITIONS_SHA256, "n_boot": N_BOOT, "seed": SEED,
           "arms": {k: analyze_arm(v) for k, v in arms.items()}}
    res["convention_effect"] = paired_arm_effect(arms["original"], arms["stated"], res["arms"]["original"]["models"])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "analysis.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    with open(os.path.join(OUT, "definitions.txt"), "w") as fh:
        fh.write(DEFINITIONS)
    print("wrote", OUT, "definitions sha256", DEFINITIONS_SHA256)


if __name__ == "__main__":
    main()
