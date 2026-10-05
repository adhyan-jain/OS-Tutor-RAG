"""
Analysis for the SSR pilot (docs/research/SSR_PILOT_PREREG.md §3-5).

    python -m research.ssr_pilot.analyze --tag llm            # real models in runs/
    python -m research.ssr_pilot.analyze --tag dry --dry      # pseudo-models in runs_dry/ (plumbing check)

Every number is recomputed from raw JSONL. The world is the statistical unit:
bootstraps resample whole worlds; variants and seeds are nested inside worlds.
The decision rule is applied mechanically; judgement goes in the decision doc.
"""

import argparse
import glob
import itertools
import json
import os
from collections import Counter, defaultdict
from typing import Dict, List

import numpy as np

from research.evaluation import metrics as M
from research.ssr_pilot import attackers as A
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.render import VARIANTS, render_variant
from research.ssr_pilot.run_pilot import PREREG, RUNS, RUNS_DRY, sha256_file
from research.ssr_pilot.scoring import score_record
from research.ssr_pilot.worlds import WORLD_DIR, load_worlds

RESULTS = "research/ssr_pilot/results"
N_BOOT = 2000
K4_BOOT = 500
STABLE = 0.70


def _j(o):
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


# ---------------------------------------------------------------- loading

def load_scored(run_dir: str) -> List[Dict]:
    worlds = {w["id"]: w for w in load_worlds()}
    banks = {i: load_bank(w) for i, w in worlds.items()}
    rendered = {(i, v): render_variant(w, v) for i, w in worlds.items() for v in VARIANTS}
    out = []
    for path in sorted(glob.glob(f"{run_dir}/*.jsonl")):
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                out.append(score_record(worlds[r["world"]], rendered[(r["world"], r["variant"])],
                                        banks[r["world"]], r))
    return out


def ci(values, groups):
    return M.cluster_bootstrap_ci(values, groups, n_boot=N_BOOT, seed=0)


def passes_k1(c) -> bool:
    return bool(c and c["n"] and c["mean"] >= 0.10 and c["ci95"][0] > 0.05)


# ---------------------------------------------------------------- per-model summaries

def frr(records: List[Dict], key: str = "A_norm", valid_key: str = "B"):
    valid = [r for r in records if r[valid_key]]
    if not valid:
        return None
    return ci([float(not r[key]) for r in valid], [r["world"] for r in valid])


def _category(r: Dict) -> str:
    if r["A_norm"]:
        return "valid_canonical"
    if r["B"]:
        return "valid_noncanonical"
    return r["reason"]


def summarize(records: List[Dict]) -> Dict:
    g = [r["world"] for r in records]
    out = {"n": len(records)}
    for k in ["B", "B_ub", "A_strict", "A_norm", "C", "obs_equiv"]:
        out[k] = ci([float(r[k]) for r in records], g)
    out["unverifiable_rate"] = float(np.mean([r["semantic"] == "UNVERIFIABLE" for r in records]))
    out["FRR_norm"], out["FRR_strict"] = frr(records), frr(records, "A_strict")
    out["FRR_norm_ub"] = frr(records, "A_norm", "B_ub")  # sensitivity: UNVERIFIABLE counted as valid
    out["n_valid"] = sum(r["B"] for r in records)
    valid = [r for r in records if r["B"]]
    out["floor_FRR_random_valid"] = float(np.mean([1 - 1 / r["n_task"] for r in valid])) if valid else None
    out["disagree_A_norm_vs_B"] = float(np.mean([r["A_norm"] != r["B"] for r in records]))
    out["false_reject"] = float(np.mean([r["B"] and not r["A_norm"] for r in records]))
    out["false_accept"] = float(np.mean([r["A_norm"] and not r["B"] for r in records]))
    wrong = [r for r in records if not r["A_norm"]]
    out["share_valid_among_A_wrong"] = float(np.mean([r["B"] for r in wrong])) if wrong else None
    tax = Counter(_category(r) for r in records)
    out["taxonomy"] = {k: v / len(records) for k, v in sorted(tax.items())}
    return out


# ---------------------------------------------------------------- proxies (K3)

def fit_tau(points):
    """points: (nd or None, B). tau maximising balanced accuracy of 'nd <= tau' against the oracle."""
    cands = sorted({nd for nd, _ in points if nd is not None})
    pos = [nd for nd, b in points if b]
    neg = [nd for nd, b in points if not b]
    best, best_ba = 0.0, -1.0
    for t in cands:
        tp = np.mean([nd is not None and nd <= t for nd in pos]) if pos else 0.0
        tn = np.mean([nd is None or nd > t for nd in neg]) if neg else 0.0
        if (tp + tn) / 2 > best_ba:
            best, best_ba = t, (tp + tn) / 2
    return best


def balanced_agreement(pred: np.ndarray, truth: np.ndarray) -> float:
    pos, neg = truth, ~truth
    tp = pred[pos].mean() if pos.any() else np.nan
    tn = (~pred[neg]).mean() if neg.any() else np.nan
    return float(np.nanmean([tp, tn]))


def proxy_analysis(records: List[Dict]) -> Dict:
    taus = {}
    for fam in {r["family"] for r in records}:  # strongest cheap proxy: threshold fitted to the oracle on OTHER families
        taus[fam] = fit_tau([(r["nd"], r["B"]) for r in records if r["family"] != fam])
    truth = np.array([r["B"] for r in records])
    preds = {"distance": np.array([r["nd"] is not None and r["nd"] <= taus[r["family"]] for r in records]),
             "final_state_only": np.array([r["fs"] for r in records])}
    worlds = sorted({r["world"] for r in records})
    widx = {w: np.array([i for i, r in enumerate(records) if r["world"] == w]) for w in worlds}
    rng = np.random.default_rng(0)
    out = {"tau_by_held_out_family": taus}
    for name, p in preds.items():
        boots = []
        for _ in range(500):
            idx = np.concatenate([widx[worlds[k]] for k in rng.integers(0, len(worlds), len(worlds))])
            boots.append(balanced_agreement(p[idx], truth[idx]))
        out[name] = {"balanced_agreement": balanced_agreement(p, truth),
                     "ci95": [float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))],
                     "accepts_when_oracle_rejects": float(p[~truth].mean()) if (~truth).any() else None,
                     "accepts_when_oracle_accepts": float(p[truth].mean()) if truth.any() else None,
                     "raw_agreement": float((p == truth).mean())}
    out["pass_K3"] = bool(all(out[n]["balanced_agreement"] < 0.95 for n in preds))
    return out


# ---------------------------------------------------------------- K4: do conclusions change?

def world_scores(records: List[Dict], models: List[str], key: str, worlds: List[str]):
    acc = defaultdict(list)
    for r in records:
        acc[(r["model"], r["world"])].append(float(r[key]))
    return {m: np.array([np.mean(acc[(m, w)]) for w in worlds]) for m in models}


def signflip_p(d: np.ndarray, n_flips: int = 20000, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_flips, len(d)))
    stat = np.abs((signs * d).mean(1))
    return float((1 + (stat >= abs(d.mean()) - 1e-12).sum()) / (n_flips + 1))


def _sig(d: np.ndarray) -> bool:
    se = d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else 0.0
    return bool(abs(d.mean()) > 2.0 * se) if se > 0 else bool(d.mean() != 0)


def conclusions(records: List[Dict], models: List[str]) -> Dict:
    worlds = sorted(set.intersection(*[{r["world"] for r in records if r["model"] == m} for m in models]))
    keep = set(worlds)
    sub = [r for r in records if r["world"] in keep]
    SA, SB = (world_scores(sub, models, k, worlds) for k in ("A_norm", "B"))
    pairs = list(itertools.combinations(models, 2))
    pa = {f"{a}|{b}": signflip_p(SA[a] - SA[b]) for a, b in pairs}
    pb = {f"{a}|{b}": signflip_p(SB[a] - SB[b]) for a, b in pairs}
    ha, hb = M.holm(pa), M.holm(pb)
    rng = np.random.default_rng(1)
    n = len(worlds)
    boots = [rng.integers(0, n, n) for _ in range(K4_BOOT)]

    pair_rows, rev_ok, sig_ok = [], False, False
    for a, b in pairs:
        key = f"{a}|{b}"
        dA, dB = SA[a] - SA[b], SB[a] - SB[b]
        sA, sB = np.sign(dA.mean()), np.sign(dB.mean())
        reversed_ = bool(sA * sB < 0)
        stab_rev = float(np.mean([np.sign(dA[i].mean()) == sA and np.sign(dB[i].mean()) == sB for i in boots]))
        sig_change = bool(ha[key]["reject"] != hb[key]["reject"])
        stab_sig = float(np.mean([_sig(dA[i]) == ha[key]["reject"] and _sig(dB[i]) == hb[key]["reject"]
                                  for i in boots]))
        delta = np.array([(dA[i] - dB[i]).mean() for i in boots])
        pair_rows.append({"pair": key, "mean_diff_A_norm": dA.mean(), "mean_diff_B": dB.mean(),
                          "p_A_holm": ha[key]["p_holm"], "p_B_holm": hb[key]["p_holm"],
                          "reversed": reversed_, "reversal_stability": stab_rev,
                          "significance_changes": sig_change, "significance_stability": stab_sig,
                          "delta_ci95": [float(np.percentile(delta, 2.5)), float(np.percentile(delta, 97.5))]})
        rev_ok |= reversed_ and stab_rev >= STABLE
        sig_ok |= sig_change and stab_sig >= STABLE

    prof, prof_ok = {}, False
    for m in models:
        mr = [r for r in sub if r["model"] == m]
        n0 = np.array([sum(not r["A_norm"] for r in mr if r["world"] == w) for w in worlds], float)
        n01 = np.array([sum((not r["A_norm"]) and r["B"] for r in mr if r["world"] == w) for w in worlds], float)
        share = float(n01.sum() / n0.sum()) if n0.sum() else float("nan")
        stab = float(np.mean([(n01[i].sum() / n0[i].sum() >= 0.5) if n0[i].sum() else False for i in boots]))
        prof[m] = {"share_valid_among_A_wrong": share, "majority": bool(share >= 0.5), "stability": stab}
        prof_ok |= bool(share >= 0.5) and stab >= STABLE
    precise = all(r["delta_ci95"][0] >= -0.05 and r["delta_ci95"][1] <= 0.05 for r in pair_rows)
    rank = M.ranking_bootstrap(SA, SB, n_boot=500, seed=0) if len(models) >= 3 else None
    return {"n_worlds": n, "pairs": pair_rows, "failure_profile": prof, "ranking": rank,
            "K4_i_reversal": bool(rev_ok), "K4_ii_significance_change": bool(sig_ok),
            "K4_iii_failure_profile": bool(prof_ok), "pass_K4": bool(rev_ok or sig_ok or prof_ok),
            "adequate_precision_no_change": bool(precise)}


# ---------------------------------------------------------------- whole analysis

def decide(k: Dict, res: Dict) -> Dict:
    c = res["conclusions"]
    if not (k["K0"] and k["K1"] and k["K2"] and k["K3"]):
        return {"mechanical_verdict": "KILL", "reason": "K0, K1, K2 or K3 failed"}
    if k["K4"] and k["K5"]:
        return {"mechanical_verdict": "GREENLIGHT", "reason": "all of K0-K5 passed"}
    if not k["K4"] and c and c["adequate_precision_no_change"]:
        return {"mechanical_verdict": "KILL",
                "reason": "K4 failed with adequate precision (evaluator choice moves no pairwise gap by > 0.05)"}
    return {"mechanical_verdict": "CONDITIONAL",
            "reason": "K0-K3 passed; K4 and/or K5 inconclusive at this sample size"}


def analyze(records: List[Dict], k0: Dict, models: List[str]) -> Dict:
    R = [r for r in records if r["model"] in models]
    res = {"models": models, "n_records": len(R), "K0": k0}
    res["per_model"] = {m: summarize([r for r in R if r["model"] == m]) for m in models}
    res["pooled"] = summarize(R)
    res["by_family"] = {f: frr([r for r in R if r["family"] == f]) for f in sorted({r["family"] for r in R})}
    res["by_variant"] = {v: frr([r for r in R if r["variant"] == v]) for v in VARIANTS}
    res["by_family_model"] = {f: {m: frr([r for r in R if r["family"] == f and r["model"] == m]) for m in models}
                              for f in res["by_family"]}
    res["family_model_rates"] = {
        f: {m: {"B": float(np.mean([r["B"] for r in R if r["family"] == f and r["model"] == m])),
                "n_valid": sum(r["B"] for r in R if r["family"] == f and r["model"] == m),
                "n": sum(1 for r in R if r["family"] == f and r["model"] == m)} for m in models}
        for f in res["by_family"]}
    res["proxies"] = proxy_analysis(R)
    res["conclusions"] = conclusions(R, models) if len(models) >= 2 else None
    k = {"K0": bool(k0["pass"]), "K1": passes_k1(res["pooled"]["FRR_norm"]),
         "K2": all(passes_k1(c) for c in res["by_variant"].values()),
         "K3": res["proxies"]["pass_K3"], "K4": bool(res["conclusions"] and res["conclusions"]["pass_K4"]),
         "K5": sum(passes_k1(c) for c in res["by_family"].values()) >= 2}
    res["criteria"] = k
    res["decision"] = decide(k, res)
    return res


def attacker_table(records: List[Dict]) -> Dict:
    out = {}
    for name in sorted({r["model"] for r in records if r["model"].startswith("attacker:")}):
        rs = [r for r in records if r["model"] == name]
        s = summarize(rs)
        out[name] = {"B": s["B"]["mean"], "A_norm": s["A_norm"]["mean"], "A_strict": s["A_strict"]["mean"],
                     "C": s["C"]["mean"], "FRR_norm": s["FRR_norm"]["mean"] if s["FRR_norm"] else None,
                     "floor_FRR": s["floor_FRR_random_valid"],
                     "final_state_only_accepts": float(np.mean([r["fs"] for r in rs])),
                     "unverifiable": s["unverifiable_rate"]}
    return out


# ---------------------------------------------------------------- tables

def _f(c):
    return "—" if not c or not c.get("n") else f"{c['mean']:.3f} [{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}]"


def _x(v):
    return "—" if v is None else f"{v:.3f}"


def write_tables(res: Dict, attackers: Dict, path: str) -> None:
    ks = ["K0", "K1", "K2", "K3", "K4", "K5"]
    L = [f"# SSR pilot results ({os.path.basename(os.path.dirname(path))})", "",
         "## Decision (mechanical)", "", f"**{res['decision']['mechanical_verdict']}** — {res['decision']['reason']}", "",
         "| " + " | ".join(ks) + " |", "|" + "---|" * len(ks),
         "| " + " | ".join("pass" if res["criteria"][k] else "FAIL" for k in ks) + " |", "",
         "## Per model (world-clustered 95% CI; UNVERIFIABLE counts as not valid)", "",
         "| model | B semantic | A_norm | A_strict | C | FRR_norm | FRR_strict | random-valid floor | UNVERIF |",
         "|---|---|---|---|---|---|---|---|---|"]
    for m, s in res["per_model"].items():
        L.append(f"| {m} | {_f(s['B'])} | {_f(s['A_norm'])} | {_f(s['A_strict'])} | {_f(s['C'])} | "
                 f"{_f(s['FRR_norm'])} | {_f(s['FRR_strict'])} | {_x(s['floor_FRR_random_valid'])} | "
                 f"{s['unverifiable_rate']:.3f} |")
    s = res["pooled"]
    L += [f"| **pooled** | {_f(s['B'])} | {_f(s['A_norm'])} | {_f(s['A_strict'])} | {_f(s['C'])} | "
          f"{_f(s['FRR_norm'])} | {_f(s['FRR_strict'])} | | {s['unverifiable_rate']:.3f} |", "",
          "## FRR_norm by family and by variant (pooled over models)", "", "| group | FRR_norm |", "|---|---|"]
    L += [f"| family: {k} | {_f(v)} |" for k, v in res["by_family"].items()]
    L += [f"| variant: {k} | {_f(v)} |" for k, v in res["by_variant"].items()]
    L += ["", "## FRR_norm by family × model", "", "| family | " + " | ".join(res["models"]) + " |",
          "|---|" + "---|" * len(res["models"])]
    for f, d in res["by_family_model"].items():
        L.append(f"| {f} | " + " | ".join(_f(d[m]) for m in res["models"]) + " |")
    L += ["", "## Semantic-validity rate B (and n valid outputs) by family × model", "",
          "| family | " + " | ".join(res["models"]) + " |", "|---|" + "---|" * len(res["models"])]
    for f, d in res["family_model_rates"].items():
        L.append(f"| {f} | " + " | ".join(f"{d[m]['B']:.3f} (n={d[m]['n_valid']}/{d[m]['n']})" for m in res["models"]) + " |")
    L += ["", "## Sensitivity: UNVERIFIABLE counted as valid", "", "| model | B_ub | FRR_norm_ub |", "|---|---|---|"]
    for m, s in res["per_model"].items():
        L.append(f"| {m} | {_f(s['B_ub'])} | {_f(s['FRR_norm_ub'])} |")
    L.append(f"| **pooled** | {_f(res['pooled']['B_ub'])} | {_f(res['pooled']['FRR_norm_ub'])} |")
    L += ["", "## Cheap proxies vs the oracle (K3; threshold fitted on other families)", "",
          "| proxy | balanced agreement [95% CI] | accepts when oracle rejects | accepts when oracle accepts |",
          "|---|---|---|---|"]
    for n in ("distance", "final_state_only"):
        p = res["proxies"][n]
        L.append(f"| {n} | {p['balanced_agreement']:.3f} [{p['ci95'][0]:.3f}, {p['ci95'][1]:.3f}] | "
                 f"{_x(p['accepts_when_oracle_rejects'])} | {_x(p['accepts_when_oracle_accepts'])} |")
    c = res.get("conclusions")
    if c:
        L += ["", f"## Do conclusions change? ({c['n_worlds']} worlds)", "",
              "| pair | Δ A_norm | Δ B | p(A) Holm | p(B) Holm | reversed | stab | sig changes | stab | "
              "CI of evaluator effect on the gap |", "|---|---|---|---|---|---|---|---|---|---|"]
        for r in c["pairs"]:
            L.append(f"| {r['pair']} | {r['mean_diff_A_norm']:+.3f} | {r['mean_diff_B']:+.3f} | {r['p_A_holm']:.3g} | "
                     f"{r['p_B_holm']:.3g} | {r['reversed']} | {r['reversal_stability']:.2f} | "
                     f"{r['significance_changes']} | {r['significance_stability']:.2f} | "
                     f"[{r['delta_ci95'][0]:+.3f}, {r['delta_ci95'][1]:+.3f}] |")
        L += ["", "| model | share of A_norm-wrong outputs that are semantically valid | majority | stability |",
              "|---|---|---|---|"]
        for m, p in c["failure_profile"].items():
            L.append(f"| {m} | {_x(p['share_valid_among_A_wrong'])} | {p['majority']} | {p['stability']:.2f} |")
        if c["ranking"]:
            r = c["ranking"]
            L += ["", f"Ranking by A_norm vs B: Kendall τ = {r['tau_observed']}, P(τ<1) = {r['p_tau_lt_1']}; "
                  f"A_norm ranks {r['rank_a']}, B ranks {r['rank_b']}"]
        L += ["", f"K4(i) reversal {c['K4_i_reversal']}; K4(ii) significance change {c['K4_ii_significance_change']}; "
              f"K4(iii) failure profile {c['K4_iii_failure_profile']}; adequate precision of 'no change': "
              f"{c['adequate_precision_no_change']}"]
    L += ["", "## Failure taxonomy (share of outputs)", ""]
    cats = sorted({k for s in res["per_model"].values() for k in s["taxonomy"]})
    L += ["| model | " + " | ".join(cats) + " |", "|---|" + "---|" * len(cats)]
    for m, s in res["per_model"].items():
        L.append(f"| {m} | " + " | ".join(f"{s['taxonomy'].get(k, 0):.3f}" for k in cats) + " |")
    if attackers:
        L += ["", "## Generators / attackers (not models)", "",
              "| attacker | B | A_norm | A_strict | C | FRR_norm | random-valid floor | final-state-only accepts |",
              "|---|---|---|---|---|---|---|---|"]
        for n, a in attackers.items():
            L.append(f"| {n} | {a['B']:.3f} | {a['A_norm']:.3f} | {a['A_strict']:.3f} | {a['C']:.3f} | "
                     f"{_x(a['FRR_norm'])} | {_x(a['floor_FRR'])} | {a['final_state_only_accepts']:.3f} |")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="llm")
    ap.add_argument("--dry", action="store_true", help="treat attackers in runs_dry/ as the models (plumbing check)")
    a = ap.parse_args(argv)
    worlds = load_worlds()
    banks = {w["id"]: load_bank(w) for w in worlds}
    k0 = A.k0_gate(A.build_rows(worlds, banks))
    records = load_scored(RUNS_DRY if a.dry else RUNS)
    attackers = attacker_table(load_scored(RUNS_DRY)) if os.path.isdir(RUNS_DRY) else {}
    models = sorted({r["model"] for r in records})
    res = analyze(records, k0, models)
    res["provenance"] = {"prereg_sha256": sha256_file(PREREG),
                         "worlds_index_sha256": sha256_file(f"{WORLD_DIR}/_index.json"),
                         "tag": a.tag, "dry_run": a.dry}
    out = f"{RESULTS}/{a.tag}"
    os.makedirs(out, exist_ok=True)
    json.dump({**res, "attackers": attackers}, open(f"{out}/analysis.json", "w"), indent=1, default=_j)
    with open(f"{out}/records.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    write_tables(res, attackers, f"{out}/tables.md")
    print(json.dumps({"criteria": res["criteria"], "decision": res["decision"]}, indent=1, default=_j))


if __name__ == "__main__":
    main()
