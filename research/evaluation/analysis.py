"""
Preregistered analysis (docs/PREREGISTRATION_V2.md §5-7), recomputed from raw
JSONL predictions only. Writes research/results/analysis_v2[_mock].json and
research/tables/*.md.

    python -m research.evaluation.analysis                 # real models in results/raw/
    python -m research.evaluation.analysis --mock          # sanity baselines (dry run)
    python -m research.evaluation.analysis --run-e3b       # choose judge by frozen rule, run E3b, re-analyse
"""

import argparse
import glob
import json
import os
from collections import defaultdict
from typing import Dict, List

import numpy as np

from research.benchmark.generator import load
from research.evaluation import metrics as M
from research.evaluation.experiments import (BENCH, MOCK_DIR, RAW_DIR, e3b_cells, parse_generation, parse_judge,
                                             run as run_cells)
from research.evaluation.provenance import stamp
from research.simulator.traces import normalize_schedule
from research.simulator.validators import validate

PARSE_FAIL_EXCLUDE = 0.20  # frozen (PREREGISTRATION_V2 §4)


def load_raw(log_dir: str) -> Dict[str, List[Dict]]:
    out = {}
    for path in sorted(glob.glob(f"{log_dir}/*.jsonl")):
        recs = [json.loads(l) for l in open(path) if l.strip()]
        if recs:
            out[recs[0]["model"]] = recs
    return out


def _same(inst, a, b) -> bool:
    if inst["domain"] == "scheduling":
        return normalize_schedule(a) == normalize_schedule(b)
    return tuple(map(tuple, a)) == tuple(map(tuple, b))


# ------------------------------------------------------------------ E1

def e1_scores(recs, inst_by_id) -> Dict[str, Dict]:
    out = {}
    for r in recs:
        if r["exp"] != "E1":
            continue
        inst = inst_by_id[r["instance_id"]]
        tr = parse_generation(inst, r["response"])
        ok = tr is not None and validate(inst["problem"], tr)[0]
        out[inst["id"]] = {
            "parsed": tr is not None, "trace": tr,
            "acc_ref": bool(tr is not None and _same(inst, tr, inst["R1"])),
            "acc_multi": bool(tr is not None and any(_same(inst, tr, inst[k]) for k in ["R1", "R2", "R3"])),
            "acc_sem": bool(ok),
        }
    return out


def summarize_e1(scores, inst_by_id) -> Dict:
    ids = sorted(scores)
    res = {"overall": _e1_block(ids, scores), "by_split": {}}
    for split in sorted({inst_by_id[i]["split"] for i in ids}):
        res["by_split"][split] = _e1_block([i for i in ids if inst_by_id[i]["split"] == split], scores)
    return res


def _e1_block(ids, scores) -> Dict:
    ref = [scores[i]["acc_ref"] for i in ids]
    sem = [scores[i]["acc_sem"] for i in ids]
    valid_ids = [i for i in ids if scores[i]["acc_sem"]]
    return {
        "n": len(ids),
        "parse_rate": float(np.mean([scores[i]["parsed"] for i in ids])) if ids else float("nan"),
        "acc_ref": M.cluster_bootstrap_ci(ref, ids),
        "acc_multi": M.cluster_bootstrap_ci([scores[i]["acc_multi"] for i in ids], ids),
        "acc_sem": M.cluster_bootstrap_ci(sem, ids),
        "rsg": M.cluster_bootstrap_ci(np.array(sem, float) - np.array(ref, float), ids),
        "canonical_rate_among_valid": float(np.mean([scores[i]["acc_ref"] for i in valid_ids])) if valid_ids else None,
        "mcnemar_sem_vs_ref": M.mcnemar_exact(sem, ref, "greater"),
    }


# ------------------------------------------------------------------ E2

def e2_table(recs) -> Dict:
    """(exp, instance, cand, ref) -> verdict (True/False/None); noise replicates kept separately."""
    main, noise = {}, {}
    for r in recs:
        if r["exp"] in ("E2", "E2M"):
            main[(r["exp"], r["instance_id"], r["cand"], r["ref"])] = parse_judge(r["response"])
        elif r["exp"] == "NOISE":
            noise[("E2", r["instance_id"], r["cand"], r["ref"])] = parse_judge(r["response"])
    return {"main": main, "noise": noise}


def _paired(table, ids, a, b, exp_a="E2", exp_b="E2"):
    xs, ys, keep = [], [], []
    for i in ids:
        va, vb = table.get((exp_a, i, *a)), table.get((exp_b, i, *b))
        if va is None or vb is None:
            continue
        xs.append(va)
        ys.append(vb)
        keep.append(i)
    return xs, ys, keep


def accept_rate(table, ids, cand, ref, exp="E2"):
    vals = [(i, table[(exp, i, cand, ref)]) for i in ids if table.get((exp, i, cand, ref)) is not None]
    return M.cluster_bootstrap_ci([v for _, v in vals], [i for i, _ in vals])


def _diff_ci(x, y, keep):
    return M.cluster_bootstrap_ci(np.array(x, float) - np.array(y, float), keep) if keep else None


def summarize_e2(tab, inst_by_id) -> Dict:
    main, noise = tab["main"], tab["noise"]
    all_ids = sorted({k[1] for k in main})
    splits = sorted({inst_by_id[i]["split"] for i in all_ids})
    id_ids = [i for i in all_ids if inst_by_id[i]["split"] == "id"]
    n_cells = len(main)
    res = {"parse_failure_rate": sum(v is None for v in main.values()) / n_cells if n_cells else float("nan"),
           "n_cells": n_cells}

    conds = sorted({(k[0], k[2], k[3]) for k in main})
    res["accept_rates"] = {"all": {}, "by_split": defaultdict(dict)}
    for exp, cand, ref in conds:
        res["accept_rates"]["all"][f"{exp}|{cand}|{ref}"] = accept_rate(main, all_ids, cand, ref, exp)
        for split in splits:
            r = accept_rate(main, [i for i in all_ids if inst_by_id[i]["split"] == split], cand, ref, exp)
            if r["n"]:
                res["accept_rates"]["by_split"][split][f"{exp}|{cand}|{ref}"] = r

    # H2: anchoring index on the valid alternative, all splits
    a, b, keep = _paired(main, all_ids, ("R2", "self"), ("R2", "R1"))
    res["H2_anchoring"] = {**M.mcnemar_exact(a, b, "greater"), "AI": _diff_ci(a, b, keep)}
    res["H2_by_split"] = {}
    for split in splits:
        a, b, keep = _paired(main, [i for i in all_ids if inst_by_id[i]["split"] == split],
                             ("R2", "self"), ("R2", "R1"))
        res["H2_by_split"][split] = _diff_ci(a, b, keep)

    # H2b: is the penalty specific to a valid-but-different reference? (id only)
    h2b = {}
    for ctrl in ["irrelevant", "none", "R1_reworded", "I2"]:
        x, y, keep = _paired(main, id_ids, ("R2", ctrl), ("R2", "R1"))
        h2b[ctrl] = {**M.mcnemar_exact(x, y, "two-sided"), "diff_ctrl_minus_R1": _diff_ci(x, y, keep)}
    res["H2b_context_controls_id"] = h2b

    # H3: does WHICH valid reference matter? flips R1 vs R3 for the same (P, R2), vs noise floor
    x, y, keep = _paired(main, all_ids, ("R2", "R1"), ("R2", "R3"))
    flips = [p != q for p, q in zip(x, y)]
    noise_flips = [main.get(k) != v for k, v in noise.items() if v is not None and main.get(k) is not None]
    res["H3_reference_choice"] = M.flip_rate_vs_noise(flips, noise_flips)
    res["noise_floor"] = {"n": len(noise_flips), "flip_rate": float(np.mean(noise_flips)) if noise_flips else None}

    # can the judge separate valid from invalid at all? (balanced accuracy, R2 vs I)
    disc = {}
    for ref in ["none", "R1"]:
        x, y, keep = _paired(main, all_ids, ("R2", ref), ("I", ref))
        disc[ref] = M.cluster_bootstrap_ci([(p + (1 - q)) / 2 for p, q in zip(x, y)], keep) if keep else None
    res["balanced_accuracy_R2_vs_I"] = disc
    # Prereg D2: the concurrency splits failed the leakage audit, so discrimination
    # claims use scheduling only; the pooled figure above is descriptive.
    sched_ids = [i for i in all_ids if inst_by_id[i]["domain"] == "scheduling"]
    disc_s = {}
    for ref in ["none", "R1"]:
        x, y, keep = _paired(main, sched_ids, ("R2", ref), ("I", ref))
        disc_s[ref] = M.cluster_bootstrap_ci([(p + (1 - q)) / 2 for p, q in zip(x, y)], keep) if keep else None
    res["balanced_accuracy_R2_vs_I_scheduling_only"] = disc_s
    res["concurrency_discrimination_status"] = "audit-failed (PREREGISTRATION_V2 D2/D3): not used for claims"
    x, y, keep = _paired(main, id_ids, ("R2", "none"), ("I", "none"))
    res["balanced_accuracy_none_id"] = float(np.mean([(p + (1 - q)) / 2 for p, q in zip(x, y)])) if keep else None

    # mitigation arm (id): does "other valid executions may exist" change verdicts?
    mit = {}
    for cand in ["R2", "I"]:
        x, y, keep = _paired(main, id_ids, (cand, "R1"), (cand, "R1"), "E2M", "E2")
        mit[cand] = {**M.mcnemar_exact(x, y, "two-sided"),
                     "accept_with_note": float(np.mean(x)) if x else None,
                     "accept_without_note": float(np.mean(y)) if y else None}
    res["mitigation_id"] = mit
    return res


# ------------------------------------------------------------------ E3 / E4

def ranking(e1_by_model, ids) -> Dict:
    ref = {m: np.array([s[i]["acc_ref"] for i in ids], float) for m, s in e1_by_model.items()}
    sem = {m: np.array([s[i]["acc_sem"] for i in ids], float) for m, s in e1_by_model.items()}
    multi = {m: np.array([s[i]["acc_multi"] for i in ids], float) for m, s in e1_by_model.items()}
    return {"ref_vs_sem": M.ranking_bootstrap(ref, sem), "multi_vs_sem": M.ranking_bootstrap(multi, sem)}


FEATURES = ["log2_n_valid", "trace_len", "n_entities", "dist_R1_R2", "is_concurrency"]


def _feat(inst):
    return [inst["log2_n_valid"], inst["trace_len"], inst["n_entities"], inst["dist_R1_R2"],
            float(inst["domain"] == "concurrency")]


def scaling(tab, e1, inst_by_id) -> Dict:
    rows = [(i, v) for (exp, i, c, r), v in tab["main"].items()
            if exp == "E2" and c == "R2" and r == "R1" and v is not None]
    out = {}
    if rows:
        X = np.array([_feat(inst_by_id[i]) for i, _ in rows])
        y = np.array([v for _, v in rows], int)
        out["accept_R2_given_R1"] = {
            "logit": M.logistic_cluster_bootstrap(X, y, [i for i, _ in rows], FEATURES),
            "by_log2V_quartile": M.spearman_bins(X[:, 0], y),
            "by_trace_len_quartile": M.spearman_bins(X[:, 1], y),
        }
    ids = sorted(e1)
    if ids:
        X = np.array([_feat(inst_by_id[i]) for i in ids])
        gap = np.array([e1[i]["acc_sem"] and not e1[i]["acc_ref"] for i in ids], int)
        out["e1_gap_valid_but_not_R1"] = {
            "logit": M.logistic_cluster_bootstrap(X, gap, ids, FEATURES),
            "by_log2V_quartile": M.spearman_bins(X[:, 0], gap),
            "by_trace_len_quartile": M.spearman_bins(X[:, 1], gap),
        }
    return out


# ------------------------------------------------------------------ decision rules

def decide(per_model: Dict, included: List[str], rank: Dict) -> Dict:
    pvals = {}
    for m in included:
        pvals[f"H2|{m}"] = per_model[m]["E2"]["H2_anchoring"]["p"]
        pvals[f"H3|{m}"] = per_model[m]["E2"]["H3_reference_choice"]["p"]
    adj = M.holm(pvals)
    maj = len(included) // 2 + 1
    h2_sig = [m for m in included if adj[f"H2|{m}"]["reject"]]
    h3_sig = [m for m in included if adj[f"H3|{m}"]["reject"]]
    h2b_pass = []
    for m in included:
        c = per_model[m]["E2"]["H2b_context_controls_id"]
        if all(c[k]["diff_ctrl_minus_R1"] and c[k]["diff_ctrl_minus_R1"]["ci95"][0] > 0 for k in ["irrelevant", "none"]):
            h2b_pass.append(m)
    ood_disappears = {}
    for m in included:
        by = per_model[m]["E2"]["H2_by_split"]
        id_ci = by.get("id")
        if id_ci and id_ci["ci95"][0] > 0:
            ood_disappears[m] = [s for s, ci in by.items() if s != "id" and ci and ci["ci95"][0] <= 0]
    rr = rank.get("ref_vs_sem", {})
    h2_maj, h3_maj, h2b_maj = len(h2_sig) >= maj, len(h3_sig) >= maj, len(h2b_pass) >= maj
    if not h2_maj and not h3_maj:
        verdict = "KILL"
    elif h2_maj and not h2b_maj:
        verdict = "MODIFY (context-sensitivity only)"
    elif h2_maj:
        verdict = "anchoring supported (see limitations)"
    else:
        verdict = "MODIFY (H3 only)"
    return {
        "holm": adj,
        "H2_significant_models": h2_sig, "H2_majority": h2_maj,
        "H2b_pass_models": h2b_pass, "H2b_majority": h2b_maj,
        "H3_significant_models": h3_sig, "H3_majority": h3_maj,
        "H4_rankings_change": bool(rr and rr.get("p_tau_lt_1", 0) >= 0.95),
        "H4_tau_observed": rr.get("tau_observed"),
        "ood_splits_where_anchoring_ci_includes_0": ood_disappears,
        "verdict_rule": verdict,
    }


# ------------------------------------------------------------------ main

def analyse(log_dir: str, out_path: str) -> Dict:
    data = load(BENCH)
    inst_by_id = {i["id"]: i for i in data["instances"]}
    raw = load_raw(log_dir)
    per_model, e1_by_model, included = {}, {}, []
    for model, recs in raw.items():
        e1 = e1_scores(recs, inst_by_id)
        tab = e2_table(recs)
        e2 = summarize_e2(tab, inst_by_id) if tab["main"] else None
        per_model[model] = {"E1": summarize_e1(e1, inst_by_id) if e1 else None, "E2": e2,
                            "E4_scaling": scaling(tab, e1, inst_by_id),
                            "E3B_records": sum(r["exp"] == "E3B" for r in recs)}
        if e1:
            e1_by_model[model] = e1
        if e2 and e2["parse_failure_rate"] <= PARSE_FAIL_EXCLUDE:
            included.append(model)
        per_model[model]["included"] = model in included
    common = sorted(set.intersection(*[set(s) for s in e1_by_model.values()])) if e1_by_model else []
    rank = ranking(e1_by_model, common) if len(e1_by_model) >= 2 and common else {}
    report = {"provenance": stamp(), "log_dir": log_dir, "models": sorted(raw), "included_models": included,
              "per_model": per_model, "E3_ranking": rank,
              "E3B_secondary": e3b_summary(raw, e1_by_model),
              "decision": decide(per_model, included, rank) if included else None}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=1, default=str)
    write_tables(report, out_path.replace("results/", "tables/").replace(".json", ".md"))
    return report


def e3b_summary(raw, e1_by_model) -> Dict:
    for judge, recs in raw.items():
        e3 = [r for r in recs if r["exp"] == "E3B"]
        if not e3 or not e1_by_model:
            continue
        verdict = defaultdict(dict)
        for r in e3:
            verdict[r["gen_model"]][r["instance_id"]] = parse_judge(r["response"]) is True
        ids = sorted(set.intersection(*[set(s) for s in e1_by_model.values()]))
        judge_scores = {m: np.array([verdict[m].get(i, False) for i in ids], float) for m in e1_by_model}
        sem = {m: np.array([e1_by_model[m][i]["acc_sem"] for i in ids], float) for m in e1_by_model}
        return {"judge": judge, "llm_judge_with_R1_vs_sem": M.ranking_bootstrap(judge_scores, sem)}
    return {}


def choose_e3b_judge(report) -> str:
    """Frozen rule: highest no-reference balanced accuracy on id in E2."""
    return max(report["included_models"],
               key=lambda m: report["per_model"][m]["E2"]["balanced_accuracy_none_id"] or -1)


def run_e3b(log_dir: str, backend_prefix: str, report) -> None:
    data = load(BENCH)
    inst_by_id = {i["id"]: i for i in data["instances"]}
    raw = load_raw(log_dir)
    e1_outputs = {m: {iid: s["trace"] for iid, s in e1_scores(recs, inst_by_id).items()} for m, recs in raw.items()}
    judge = choose_e3b_judge(report)
    print(f"E3b judge chosen by frozen rule: {judge}")
    run_cells(f"{backend_prefix}:{judge}", e3b_cells(inst_by_id, e1_outputs), log_dir)


def _fmt(ci):
    if not ci or ci.get("n", 0) == 0:
        return "—"
    return f"{ci['mean']:.3f} [{ci['ci95'][0]:.3f}, {ci['ci95'][1]:.3f}]"


def write_tables(report, path) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    prov = report["provenance"]
    L = [f"# Results tables ({os.path.basename(path)})", "",
         f"Provenance: prereg sha256 `{prov['sha256'].get('docs/PREREGISTRATION_V2.md')}`, "
         f"git `{prov['git_head'][:10]}`, generated {prov['generated_at']}", ""]
    L += ["## E1 generation (all splits)", "",
          "| model | parse | Acc_ref | Acc_multi | Acc_sem | RSG | canonical among valid |",
          "|---|---|---|---|---|---|---|"]
    for m, d in sorted(report["per_model"].items()):
        if d["E1"]:
            o = d["E1"]["overall"]
            L.append(f"| {m} | {o['parse_rate']:.3f} | {_fmt(o['acc_ref'])} | {_fmt(o['acc_multi'])} | "
                     f"{_fmt(o['acc_sem'])} | {_fmt(o['rsg'])} | {o['canonical_rate_among_valid']} |")
    conds = ["E2|R2|none", "E2|R2|R1", "E2|R2|R3", "E2|R2|self", "E2|I|none", "E2|I|R1"]
    L += ["", "## E2 judging: acceptance rate by condition (all splits)", "",
          "| model | parse fail | " + " | ".join(conds) + " |", "|---|---|" + "---|" * len(conds)]
    for m, d in sorted(report["per_model"].items()):
        if d["E2"]:
            e = d["E2"]
            L.append(f"| {m} | {e['parse_failure_rate']:.3f} | " +
                     " | ".join(_fmt(e["accept_rates"]["all"].get(c)) for c in conds) + " |")
    L += ["", "## Primary tests", "",
          "Balanced accuracy (R2 vs I) uses scheduling only; concurrency failed the leakage audit (prereg D2).", "",
          "| model | AI (self − R1) | H2 p | R1↔R3 flip | noise flip | H3 p | bal.acc none | bal.acc ref=R1 |",
          "|---|---|---|---|---|---|---|---|"]
    for m, d in sorted(report["per_model"].items()):
        if d["E2"]:
            e = d["E2"]
            h2, h3 = e["H2_anchoring"], e["H3_reference_choice"]
            L.append(f"| {m} | {_fmt(h2['AI'])} | {h2['p']:.2g} | {h3['flip_rate']:.3f} | {h3['noise_flip_rate']} | "
                     f"{h3['p']:.2g} | {_fmt(e['balanced_accuracy_R2_vs_I_scheduling_only']['none'])} | "
                     f"{_fmt(e['balanced_accuracy_R2_vs_I_scheduling_only']['R1'])} |")
    L += ["", "## H2b context controls (id): accept(R2|ctrl) − accept(R2|R1)", "",
          "| model | none | irrelevant | R1 reworded | invalid ref |", "|---|---|---|---|---|"]
    for m, d in sorted(report["per_model"].items()):
        if d["E2"]:
            c = d["E2"]["H2b_context_controls_id"]
            L.append(f"| {m} | " + " | ".join(_fmt(c[k]["diff_ctrl_minus_R1"])
                                              for k in ["none", "irrelevant", "R1_reworded", "I2"]) + " |")
    splits = sorted({s for d in report["per_model"].values() if d["E2"] for s in d["E2"]["H2_by_split"]})
    L += ["", "## Anchoring index by split", "",
          "| model | " + " | ".join(splits) + " |", "|---|" + "---|" * len(splits)]
    for m, d in sorted(report["per_model"].items()):
        if d["E2"]:
            L.append(f"| {m} | " + " | ".join(_fmt(d["E2"]["H2_by_split"].get(s)) for s in splits) + " |")
    r = report.get("E3_ranking", {}).get("ref_vs_sem")
    if r:
        L += ["", "## E3 ranking: Acc_ref vs Acc_sem", "",
              f"Kendall τ = {r['tau_observed']}, P(τ<1) under bootstrap = {r['p_tau_lt_1']}, "
              f"inversions = {r['inversions_observed']}", "",
              "| model | Acc_ref | rank | Acc_sem | rank |", "|---|---|---|---|---|"]
        for m in r["models"]:
            L.append(f"| {m} | {r['score_a'][m]:.3f} | {r['rank_a'][m]} | {r['score_b'][m]:.3f} | {r['rank_b'][m]} |")
    if report.get("decision"):
        d = {k: v for k, v in report["decision"].items() if k != "holm"}
        L += ["", "## Preregistered decision rules", "", "```", json.dumps(d, indent=1), "```"]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--run-e3b", action="store_true")
    a = ap.parse_args()
    log_dir = MOCK_DIR if a.mock else RAW_DIR
    out = "research/results/analysis_v2_mock.json" if a.mock else "research/results/analysis_v2.json"
    rep = analyse(log_dir, out)
    if a.run_e3b:
        run_e3b(log_dir, "mock" if a.mock else "ollama", rep)
        rep = analyse(log_dir, out)
    print(json.dumps({k: v for k, v in rep["decision"].items() if k != "holm"}, indent=1, default=str)
          if rep["decision"] else "no included models")
