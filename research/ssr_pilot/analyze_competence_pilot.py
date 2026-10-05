"""
Analysis for the competence-filter mini-pilot (decision_rubric.md is the rule book).

    python -m research.ssr_pilot.analyze_competence_pilot

Reuses the SSR statistical framework unchanged (summarize / frr / world-clustered
bootstrap, 2,000 resamples, seed 0). The baseline is the four local 7-9B models of
the stated-convention arm, re-scored from raw outputs with the current scorer; it
must reproduce pooled FRR_norm 0.625 before any new number is trusted.

Writes records.jsonl, analysis.json and REPORT.md under results/competence_pilot/.
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional

import numpy as np

from research.ssr_pilot.analyze import _j, conclusions, frr, proxy_analysis, summarize
from research.ssr_pilot.analyze_stated_convention import RUNS_STATED, load_scored_stated
from research.ssr_pilot.render import VARIANTS
from research.ssr_pilot.run_competence_pilot import (MODELS, MODEL_GB, OUT, RESOURCE_LOG, RUBRIC, RUNS, SELECTION,
                                                     installed)
from research.ssr_pilot.run_pilot import sha256_file

BASELINE_FRR = 0.625  # pooled FRR_norm of the stated-convention arm
BASELINE_FRR_TOL = 0.0005
GATE_GAIN = 0.15
GATE_N_VALID = 100
STRATUM_U = ["sched_04", "sched_06", "sched_08", "sync_02", "sync_04", "bank_02", "bank_06", "bank_08"]
MIN_VALID_FOR_BREAKDOWN = 10
N_BOOT = 2000

LABELS = {"A": "A) DISCREPANCY SURVIVES COMPETENCE CHECK",
          "B": "B) DISCREPANCY SUBSTANTIALLY SHRINKS",
          "C": "C) INCONCLUSIVE DUE TO MODEL/POWER LIMITATIONS"}


# ---------------------------------------------------------------- rubric (decision_rubric.md)

def decide_competence(gain: float, n_valid: int, frr_mean: Optional[float], frr_lo: Optional[float],
                      frr_hi: Optional[float], baseline: float = BASELINE_FRR) -> Dict:
    """Mechanical decision exactly as frozen in decision_rubric.md."""
    gate = bool(gain >= GATE_GAIN and n_valid >= GATE_N_VALID)
    out = {"gate_passed": gate, "competence_gain": gain, "n_valid": n_valid, "baseline_frr": baseline}
    if frr_mean is None:
        return {**out, "decision": "C", "reason": "no semantically valid outputs, FRR undefined"}
    drop = baseline - frr_mean
    out["drop_vs_baseline"] = drop
    if not gate:
        return {**out, "decision": "C",
                "reason": f"competence gate failed (gain {gain:+.3f} vs required >= {GATE_GAIN}, "
                          f"n_valid {n_valid} vs required >= {GATE_N_VALID})"}
    if frr_mean >= 0.50 and drop <= 0.15 and frr_lo > 0.10:
        return {**out, "decision": "A",
                "reason": f"FRR {frr_mean:.3f} >= 0.50, drop {drop:+.3f} <= 0.15, CI lower bound {frr_lo:.3f} > 0.10"}
    if frr_hi < 0.50 and drop >= 0.15:
        return {**out, "decision": "B",
                "reason": f"FRR CI upper bound {frr_hi:.3f} < 0.50 and drop {drop:+.3f} >= 0.15"}
    return {**out, "decision": "C",
            "reason": f"FRR {frr_mean:.3f} [{frr_lo:.3f}, {frr_hi:.3f}] with drop {drop:+.3f} meets neither A nor B"}


# ---------------------------------------------------------------- statistics

def frr_diff_ci(new: List[Dict], base: List[Dict], n_boot: int = N_BOOT, seed: int = 0) -> Optional[Dict]:
    """FRR_norm(new) - FRR_norm(baseline), resampling whole worlds jointly."""
    worlds = sorted({r["world"] for r in new} & {r["world"] for r in base})
    if not worlds:
        return None

    def per_world(recs):
        v, nc = defaultdict(int), defaultdict(int)
        for r in recs:
            if r["B"]:
                v[r["world"]] += 1
                nc[r["world"]] += int(not r["A_norm"])
        return np.array([v[w] for w in worlds], float), np.array([nc[w] for w in worlds], float)

    (vn, cn), (vb, cb) = per_world(new), per_world(base)
    if vn.sum() == 0 or vb.sum() == 0:
        return None
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(worlds), len(worlds))
        if vn[idx].sum() and vb[idx].sum():
            diffs.append(cn[idx].sum() / vn[idx].sum() - cb[idx].sum() / vb[idx].sum())
    return {"diff": float(cn.sum() / vn.sum() - cb.sum() / vb.sum()),
            "ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))], "n_boot": len(diffs)}


def counts(records: List[Dict]) -> Dict:
    valid = [r for r in records if r["B"]]
    return {"n": len(records), "n_valid": len(valid), "n_canonical": sum(r["A_norm"] for r in records),
            "n_valid_noncanonical": sum(1 for r in valid if not r["A_norm"])}


def _block(rs: List[Dict]) -> Dict:
    return {"FRR_norm": frr(rs) if any(r["B"] for r in rs) else None, **counts(rs),
            "B": float(np.mean([r["B"] for r in rs])) if rs else None}


def strata(records: List[Dict]) -> Dict:
    u = set(STRATUM_U)
    return {"D (R is the literal reading)": _block([r for r in records if r["world"] not in u]),
            "U (R underdetermined)": _block([r for r in records if r["world"] in u])}


def breakdown(records: List[Dict], key: str, values: List[str]) -> Dict:
    return {v: _block([r for r in records if r[key] == v]) for v in values}


# ---------------------------------------------------------------- resource log

def resource_summary() -> Dict:
    if not os.path.exists(RESOURCE_LOG):
        return {"lines": [], "busy_polls": 0, "runtimes": {}}
    lines = open(RESOURCE_LOG).read().splitlines()
    key = re.compile(r"START|END|FAILED|NOT INSTALLED|gave up|STATUS|Ollama failure")
    runtimes = {}
    for l in lines:
        m = re.search(r"\[(.+?)\] END (smoke|full): (\d+) calls, ([\d.]+)s/call, (\d+) min", l)
        if m and m.group(2) == "full":
            runtimes[m.group(1)] = {"calls": int(m.group(3)), "s_per_call": float(m.group(4)),
                                    "minutes": int(m.group(5))}
    return {"lines": [l for l in lines if key.search(l)], "busy_polls": sum("gate BUSY" in l for l in lines),
            "runtimes": runtimes}


# ---------------------------------------------------------------- report

def _f(c):
    return "—" if not c or not c.get("n") else f"{c['mean']:.3f} [{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}]"


def _x(v):
    return "—" if v is None else f"{v:.3f}"


def build_report(res: Dict) -> str:
    base, new, dec = res["baseline"], res["new"], res["decision"]
    pooled, pb = new["pooled"], base["pooled"]
    models = new["models"]
    c, cb = new["counts_pooled"], base["counts_pooled"]
    L = ["# Competence-filter mini-pilot — REPORT", "",
         "Date: 2026-10-03. Stated-convention generation arm only; same 24 worlds, prompts, settings, oracle and "
         "statistics as the stated-convention arm. Rules: `decision_rubric.md` (frozen before any output).", "",
         "## A. Purpose", "",
         "The stated-convention arm kept the evaluator discrepancy high (pooled FRR_norm 0.625) but its four local "
         "models are weak (pooled semantic validity 0.153). This phase asks whether the discrepancy survives when "
         "clearly more capable models are used: *among semantically valid outputs, does a large share remain "
         "non-canonical under the stated convention?* It does not ask whether stronger models are better.", "",
         "## B. Selected models", "", "| model | family | size | installed | outputs scored | run status |",
         "|---|---|---|---|---|---|"]
    fam = {"gemma3:12b": "Google Gemma 3 (12B)", "olmo2:7b": "Allen Institute OLMo 2 (7B)", "qwen3:14b": "Alibaba Qwen 3 (14B)", "phi4:14b": "Microsoft Phi-4 (14B)"}
    for m in MODELS:
        L.append(f"| {m} | {fam[m]} | {MODEL_GB[m]} GB (Q4_K_M) | {'yes' if m in res['installed'] else 'no'} | "
                 f"{res['n_by_model'].get(m, 0)} / 288 | {res['run_status'].get(m, 'not run')} |")
    L += ["", "Full reasoning and hardware feasibility: `model_selection.md`.", "",
          "## C. Experimental design", "",
          "24 worlds × 3 surface variants (v0, v1, v2) × 4 seeds = 288 generations per model; stated-convention "
          "prompts; temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600; evaluators A_strict, A_norm, B, C "
          "unchanged; world-clustered bootstrap (2,000 resamples, seed 0). One model at a time. Baseline = the 4 local "
          f"models of the stated-convention arm (recomputed; pooled FRR_norm {pb['FRR_norm']['mean']:.3f}).", ""]
    rs = res["resources"]
    L += ["## D. Resource use", "",
          f"GPU-gate polls that found the GPU or RAM busy: **{rs['busy_polls']}** (every 5 minutes; see "
          "`resource_log.md`).", ""]
    if rs["runtimes"]:
        L += ["| model | calls | s/call | minutes |", "|---|---|---|---|"]
        L += [f"| {m} | {v['calls']} | {v['s_per_call']} | {v['minutes']} |" for m, v in rs["runtimes"].items()]
        L.append("")
    L += ["Key events:", ""] + [f"- {l[2:]}" for l in rs["lines"][:40]] + [""]
    L += ["## E. Overall validity (world-clustered 95% CI; UNVERIFIABLE counted as not valid)", "",
          "| model | n | B semantic | A_norm | A_strict | C | UNVERIF |", "|---|---|---|---|---|---|---|"]
    for m in models:
        s = new["per_model"][m]
        L.append(f"| {m} | {s['n']} | {_f(s['B'])} | {_f(s['A_norm'])} | {_f(s['A_strict'])} | {_f(s['C'])} | "
                 f"{s['unverifiable_rate']:.3f} |")
    L += [f"| **new models pooled** | {pooled['n']} | {_f(pooled['B'])} | {_f(pooled['A_norm'])} | "
          f"{_f(pooled['A_strict'])} | {_f(pooled['C'])} | {pooled['unverifiable_rate']:.3f} |",
          f"| *baseline (4 local) pooled* | {pb['n']} | {_f(pb['B'])} | {_f(pb['A_norm'])} | "
          f"{_f(pb['A_strict'])} | {_f(pb['C'])} | {pb['unverifiable_rate']:.3f} |", "",
          "## F. Competence-conditioned disagreement (among semantically valid outputs)", "",
          "| model | semantically valid | canonical accepted | canonical rejected | **FRR_norm** | FRR_strict | "
          "FRR_norm, UNVERIF as valid | valid-but-reference-wrong (share of all outputs) |",
          "|---|---|---|---|---|---|---|---|"]
    for m in models:
        s, cm = new["per_model"][m], new["counts"][m]
        L.append(f"| {m} | {cm['n_valid']} | {cm['n_valid'] - cm['n_valid_noncanonical']} | "
                 f"{cm['n_valid_noncanonical']} | {_f(s['FRR_norm'])} | {_f(s['FRR_strict'])} | "
                 f"{_f(s['FRR_norm_ub'])} | {s['false_reject']:.3f} |")
    L += [f"| **new models pooled** | {c['n_valid']} | {c['n_valid'] - c['n_valid_noncanonical']} | "
          f"{c['n_valid_noncanonical']} | **{_f(pooled['FRR_norm'])}** | {_f(pooled['FRR_strict'])} | "
          f"{_f(pooled['FRR_norm_ub'])} | {pooled['false_reject']:.3f} |",
          f"| *baseline pooled* | {cb['n_valid']} | {cb['n_valid'] - cb['n_valid_noncanonical']} | "
          f"{cb['n_valid_noncanonical']} | {_f(pb['FRR_norm'])} | {_f(pb['FRR_strict'])} | "
          f"{_f(pb['FRR_norm_ub'])} | {pb['false_reject']:.3f} |", "",
          f"Total canonical (A_norm) outputs, new models: {c['n_canonical']} of {c['n']}.", "",
          "## G. Comparison to the stated-convention baseline", ""]
    d = res["frr_difference"]
    L += [f"- Baseline pooled FRR_norm: **{_f(pb['FRR_norm'])}** (n valid {cb['n_valid']}).",
          f"- New-model pooled FRR_norm: **{_f(pooled['FRR_norm'])}** (n valid {c['n_valid']}).",
          f"- Competence gain (pooled B): **{dec['competence_gain']:+.3f}** "
          f"({pooled['B']['mean']:.3f} vs {pb['B']['mean']:.3f}).",
          "- Difference in FRR_norm (new − baseline), world-clustered: " +
          (f"**{d['diff']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]**" if d else "undefined"), "",
          "All models, ordered by semantic validity (descriptive; does validity rise together with non-canonical "
          "output?):", "", "| model | arm | B | A_norm | n valid | FRR_norm |", "|---|---|---|---|---|---|"]
    for row in res["seven_model_table"]:
        L.append(f"| {row['model']} | {row['arm']} | {row['B']:.3f} | {row['A_norm']:.3f} | {row['n_valid']} | "
                 f"{_x(row['FRR_norm'])} |")
    L += ["", f"Spearman correlation between B and FRR_norm across models with ≥ 1 valid output: "
          f"{_x(res['spearman_B_vs_FRR'])} (descriptive; {len(res['seven_model_table'])} models).", "",
          "**World strata (fixed in advance; see decision_rubric.md).** Stratum U is the 8 constrained worlds in "
          "which a literal reading of the stated tie-break violates the task constraint, so the prompt does not "
          "determine R there.", "",
          "| stratum | arm | n outputs | n valid | B | FRR_norm |", "|---|---|---|---|---|---|"]
    for name in new["strata"]:
        for arm, blk in (("new", new["strata"][name]), ("baseline", base["strata"][name])):
            L.append(f"| {name} | {arm} | {blk['n']} | {blk['n_valid']} | {_x(blk['B'])} | {_f(blk['FRR_norm'])} |")
    L += ["", "## H. Family and variant breakdown (new models pooled; baseline alongside)", "",
          f"Cells with fewer than {MIN_VALID_FOR_BREAKDOWN} valid outputs are marked *too few to interpret*.", "",
          "| group | n valid (new) | B (new) | FRR_norm (new) | FRR_norm (baseline) |", "|---|---|---|---|---|"]
    for grp in ("by_family", "by_variant"):
        for k, blk in new[grp].items():
            flag = "" if blk["n_valid"] >= MIN_VALID_FOR_BREAKDOWN else " *too few to interpret*"
            L.append(f"| {k} | {blk['n_valid']} | {_x(blk['B'])} | {_f(blk['FRR_norm'])}{flag} | "
                     f"{_f(base[grp][k]['FRR_norm'])} |")
    L += ["", "## I. Statistical results", "",
          "All intervals are world-clustered bootstrap 95% CIs (2,000 resamples, seed 0).", ""]
    cc = new.get("conclusions")
    if cc:
        L += ["Pairwise comparisons among the new models, A_norm vs B (descriptive; no competence-specific threshold):",
              "", "| pair | Δ A_norm | Δ B | p(A) Holm | p(B) Holm | reversed | evaluator effect on the gap [95% CI] |",
              "|---|---|---|---|---|---|---|"]
        for r in cc["pairs"]:
            L.append(f"| {r['pair']} | {r['mean_diff_A_norm']:+.3f} | {r['mean_diff_B']:+.3f} | {r['p_A_holm']:.3g} | "
                     f"{r['p_B_holm']:.3g} | {r['reversed']} | [{r['delta_ci95'][0]:+.3f}, {r['delta_ci95'][1]:+.3f}] |")
        if cc.get("ranking"):
            rk = cc["ranking"]
            L += ["", f"Ranking by A_norm {rk['rank_a']} vs by B {rk['rank_b']} (Kendall τ = {rk['tau_observed']})."]
    else:
        L.append("Pairwise comparisons need at least two completed models.")
    px = new.get("proxies")
    if px:
        L += ["", "Cheap proxies against the oracle on the new models' outputs (descriptive):", "",
              "| proxy | balanced agreement [95% CI] | accepts when oracle rejects |", "|---|---|---|"]
        for n in ("distance", "final_state_only"):
            p = px[n]
            L.append(f"| {n} | {p['balanced_agreement']:.3f} [{p['ci95'][0]:.3f}, {p['ci95'][1]:.3f}] | "
                     f"{_x(p['accepts_when_oracle_rejects'])} |")
    L += ["", "## J. Limitations", "",
          "- **24 worlds and at most 3 new models.** Intervals are wide; per-family and per-variant cells can have few "
          "valid outputs.",
          "- **Local, quantised 12–14B models only** (Q4_K_M, partial CPU offload on an 8 GB GPU). Nothing here speaks "
          "to frontier or reasoning models, and `think` was off where applicable.",
          "- **The stated convention does not determine R in 8 of the 12 constrained worlds** (stratum U): a literal "
          "reading violates the task constraint and the prompt does not say how to resolve it, so non-canonical valid "
          "output is partly expected there even from a perfect solver. Stratum D is the cleaner test.",
          "- **Hardware constraints:** the GPU is shared with another project; runs wait for a free GPU and enough RAM "
          "(see Section D).",
          "- The competence gate, the 0.50/0.15 survival thresholds and the strata were fixed before any output; no "
          "threshold was changed afterwards. The result describes these worlds and models only; no novelty, "
          "universality, frontier-model, or publication-readiness claim is made.", ""]
    miss = [m for m in MODELS if res["run_status"].get(m) != "done" or res["n_by_model"].get(m, 0) < 288]
    if miss:
        L += [f"- **Incomplete or skipped models:** {', '.join(miss)} (see Section B and `resource_log.md`).", ""]
    L += ["## K. Decision", "", f"**{LABELS[dec['decision']]}**", "", f"Rule application: {dec['reason']}.", "",
          f"- Competence gate: gain {dec['competence_gain']:+.3f} (need ≥ {GATE_GAIN}) and n_valid {dec['n_valid']} "
          f"(need ≥ {GATE_N_VALID}) → {'passed' if dec['gate_passed'] else 'FAILED'}.",
          f"- Pooled FRR_norm {_f(pooled['FRR_norm'])} against the 0.625 baseline.", ""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main

def main():
    base_recs = load_scored_stated(RUNS_STATED)
    base_models = sorted({r["model"] for r in base_recs})
    base_pooled = summarize(base_recs)
    got = base_pooled["FRR_norm"]["mean"]
    if abs(got - BASELINE_FRR) > BASELINE_FRR_TOL:
        sys.exit(f"baseline does not reproduce: pooled FRR_norm {got:.4f} != {BASELINE_FRR}")

    new_recs = load_scored_stated(RUNS) if os.path.isdir(RUNS) else []
    models = [m for m in MODELS if any(r["model"] == m for r in new_recs)]
    if not new_recs:
        sys.exit("no competence-pilot outputs yet")

    def block(recs, mods):
        return {"models": mods, "pooled": summarize(recs),
                "per_model": {m: summarize([r for r in recs if r["model"] == m]) for m in mods},
                "counts": {m: counts([r for r in recs if r["model"] == m]) for m in mods},
                "counts_pooled": counts(recs), "strata": strata(recs),
                "by_family": breakdown(recs, "family", sorted({r["family"] for r in recs})),
                "by_variant": breakdown(recs, "variant", list(VARIANTS))}

    base, new = block(base_recs, base_models), block(new_recs, models)
    new["conclusions"] = conclusions(new_recs, models) if len(models) >= 2 else None
    try:
        new["proxies"] = proxy_analysis(new_recs)
    except Exception as e:  # too few valid outputs for a proxy fit
        new["proxies"], new["proxies_error"] = None, str(e)

    pooled = new["pooled"]
    frr_ci = pooled["FRR_norm"]
    gain = pooled["B"]["mean"] - base["pooled"]["B"]["mean"]
    decision = decide_competence(gain, new["counts_pooled"]["n_valid"],
                                 frr_ci["mean"] if frr_ci else None, frr_ci["ci95"][0] if frr_ci else None,
                                 frr_ci["ci95"][1] if frr_ci else None)
    seven = []
    for arm, mods, blk in (("baseline", base_models, base), ("new", models, new)):
        for m in mods:
            s = blk["per_model"][m]
            seven.append({"model": m, "arm": arm, "B": s["B"]["mean"], "A_norm": s["A_norm"]["mean"],
                          "n_valid": blk["counts"][m]["n_valid"],
                          "FRR_norm": s["FRR_norm"]["mean"] if s["FRR_norm"] else None})
    seven.sort(key=lambda r: r["B"])
    pts = [(r["B"], r["FRR_norm"]) for r in seven if r["FRR_norm"] is not None]
    rho = None
    if len(pts) >= 3:
        from scipy import stats
        rho = float(stats.spearmanr([p[0] for p in pts], [p[1] for p in pts]).statistic)

    status_path = f"{OUT}/run_status.json"
    res = {"baseline": base, "new": new, "decision": decision, "seven_model_table": seven, "spearman_B_vs_FRR": rho,
           "frr_difference": frr_diff_ci(new_recs, base_recs),
           "installed": [m for m in MODELS if m in installed()],
           "n_by_model": dict(Counter(r["model"] for r in new_recs)),
           "run_status": json.load(open(status_path)) if os.path.exists(status_path) else {},
           "resources": resource_summary(),
           "provenance": {"decision_rubric_sha256": sha256_file(RUBRIC),
                          "model_selection_sha256": sha256_file(SELECTION), "baseline_reproduced_frr": got}}
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/records.jsonl", "w") as f:
        for r in new_recs:
            f.write(json.dumps(r) + "\n")
    json.dump(res, open(f"{OUT}/analysis.json", "w"), indent=1, default=_j)
    open(f"{OUT}/REPORT.md", "w").write(build_report(res))
    print(json.dumps({"models": models, "decision": decision, "pooled_FRR_norm": frr_ci,
                      "competence_gain": gain}, indent=1, default=_j))


if __name__ == "__main__":
    main()
