"""
SUPPLEMENTARY (post-hoc, non-confirmatory) analysis of the Blocks World runs.

Nothing here changes a confirmatory verdict. It answers the questions the locked plan does not:
  * what the models actually got wrong (failure taxonomy; copy-of-prompt-example rate),
  * which unit is independent (tasks, not the 12 generations inside a cell),
  * how much uncertainty each variance source contributes to the headline numbers:
        generation variability  -> resample the 12 generations inside each (model, task) cell
        task variability        -> resample the 24 tasks with replacement
        reference-choice var.   -> already integrated out exactly by the DP (uniform q)
  * an EXPLORATORY detection analysis over all 50,000 reference vectors x 20,000 sign flips
    (the locked H4 is undefined because no pair is E3-separated).
"""

import itertools
import json
import os
from typing import Dict, List

import numpy as np

from research.pilot_second_domain.analyze_blocks_world_confirmatory import (
    MODELS,
    N_DRAWS,
    load_model_runs,
)
from research.pilot_second_domain.blocks_world_tasks import (
    BlocksWorld,
    evaluate_plan_semantic,
    extract_plan,
    format_plan_as_string,
    get_all_tasks,
    plan_to_tuple,
)
from research.ssr_pilot.rcr_extended_analysis import holm_rows, sign_flip_pvalues
from research.ssr_pilot.rcrc.exact_margin_distribution import compute_exact_pairwise_margin

RESULTS_PATH = "research/pilot_second_domain/results/blocks_world_supplementary.json"
PROMPT_EXAMPLE = "move_to_table(A), move(A, B)"  # fixed demonstration string in every prompt
N_BOOT = 2000
N_FLIPS = 20000
SEED = 20261029
K = 12


def build_cells(tasks, model_runs):
    """Per (model, task): per-generation E3 bool, per-generation ref-match matrix (12, |V|), taxonomy."""
    V = {}
    for t in tasks:
        bw = BlocksWorld(t["blocks"])
        clear = set(t["blocks"]) - set(t["init_on"].values())
        V[t["id"]] = [
            plan_to_tuple(p)
            for p in bw.enumerate_all_minimal_plans(
                t["init_on"], set(t["init_table"]), clear, t["goal_on"], set(t["goal_table"])
            )
        ]
    cells = {m: {} for m in MODELS}
    tax = {m: {} for m in MODELS}
    for m in MODELS:
        for t in tasks:
            recs = sorted(model_runs[m][t["id"]], key=lambda r: (r["variant"], r["seed"]))
            e3, match = [], np.zeros((K, len(V[t["id"]])), dtype=bool)
            for g, r in enumerate(recs):
                plan = extract_plan(r["response"])
                ok = evaluate_plan_semantic(t, plan)
                e3.append(ok)
                tup = plan_to_tuple(plan)
                for ri, ref in enumerate(V[t["id"]]):
                    match[g, ri] = tup == ref
                cat = classify(t, plan, ok, tup in set(V[t["id"]]))
                tax[m][cat] = tax[m].get(cat, 0) + 1
            cells[m][t["id"]] = {
                "e3": np.array(e3, dtype=bool),
                "match": match,
                "variants": [r["variant"] for r in recs],
            }
    return V, cells, tax


def classify(task, plan, ok, in_v) -> str:
    if format_plan_as_string(plan) == PROMPT_EXAMPLE and not ok:
        return "copied_prompt_example_invalid"
    if ok and in_v:
        return "valid_shortest"
    if ok:
        return "valid_not_shortest"
    bw = BlocksWorld(task["blocks"])
    on, tb = dict(task["init_on"]), set(task["init_table"])
    cl = set(task["blocks"]) - set(on.values())
    for i, a in enumerate(plan):
        if a not in bw.get_applicable_actions(on, tb, cl):
            return "illegal_first_step" if i == 0 else "illegal_later_step"
        on, tb, cl = bw.apply_action(on, tb, cl, a)
    return "legal_but_goal_not_reached"


def pair_reversal(c_by_task_A, c_by_task_B, n_refs) -> Dict:
    data = [{"c_A": a, "c_B": b, "n_refs": n} for a, b, n in zip(c_by_task_A, c_by_task_B, n_refs)]
    return compute_exact_pairwise_margin(data, K=K, q_type="uniform")


def mean_reversal(counts: Dict[str, List[np.ndarray]], n_refs) -> float:
    vals = []
    for a, b in itertools.combinations(MODELS, 2):
        vals.append(pair_reversal(counts[a], counts[b], n_refs)["winner_reversal_probability"])
    return float(np.mean(vals))


def run() -> Dict:
    rng = np.random.default_rng(SEED)
    tasks = get_all_tasks()
    model_runs = load_model_runs()
    V, cells, tax = build_cells(tasks, model_runs)
    tids = [t["id"] for t in tasks]
    n_refs = [len(V[i]) for i in tids]

    # ---- pass rates with the TASK as the independent unit -----------------------------------
    task_rate = {m: np.array([cells[m][i]["e3"].mean() for i in tids]) for m in MODELS}
    pass_ci = {}
    for m in MODELS:
        boots = [task_rate[m][rng.integers(0, 24, 24)].mean() for _ in range(N_BOOT)]
        pass_ci[m] = {
            "pass_rate": float(task_rate[m].mean()),
            "task_cluster_bootstrap_95ci": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "n_valid_generations": int(sum(cells[m][i]["e3"].sum() for i in tids)),
            "n_generations": 288,
            "n_tasks_with_any_valid": int((task_rate[m] > 0).sum()),
        }

    # ---- variance components for the generation-level E3 outcome ----------------------------
    var_comp = {}
    for m in MODELS:
        y = np.concatenate([cells[m][i]["e3"].astype(float) for i in tids])
        grand = y.mean()
        ss_tot = ((y - grand) ** 2).sum()
        ss_task = sum(12 * (cells[m][i]["e3"].mean() - grand) ** 2 for i in tids)
        by_variant = {}
        for v in ("v0", "v1", "v2"):
            vals = [cells[m][i]["e3"][[x == v for x in cells[m][i]["variants"]]] for i in tids]
            by_variant[v] = float(np.mean(np.concatenate(vals)))
        var_comp[m] = {
            "share_of_variance_between_tasks": float(ss_task / ss_tot) if ss_tot > 0 else None,
            "pass_rate_by_prompt_variant": by_variant,
        }

    # ---- reversal-probability uncertainty ----------------------------------------------------
    counts = {m: [cells[m][i]["match"].sum(axis=0) for i in tids] for m in MODELS}
    pairs = list(itertools.combinations(MODELS, 2))
    point = {f"{a}_vs_{b}": pair_reversal(counts[a], counts[b], n_refs)["winner_reversal_probability"] for a, b in pairs}
    point_mean = float(np.mean(list(point.values())))

    gen_boot, task_boot = [], []
    for _ in range(N_BOOT):
        # generation bootstrap: resample the 12 generations within every cell, independently per model
        gc = {}
        for m in MODELS:
            gc[m] = []
            for i in tids:
                g = rng.integers(0, K, K)
                gc[m].append(cells[m][i]["match"][g].sum(axis=0))
        gen_boot.append(mean_reversal(gc, n_refs))
        # task bootstrap: resample the 24 tasks with replacement
        ti = rng.integers(0, 24, 24)
        tc = {m: [counts[m][j] for j in ti] for m in MODELS}
        task_boot.append(mean_reversal(tc, [n_refs[j] for j in ti]))

    def summ(x):
        x = np.array(x)
        return {
            "mean": float(x.mean()),
            "ci95": [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))],
            "share_ge_0.08": float((x >= 0.08).mean()),
        }

    reversal_unc = {
        "point_exact_dp_mean": point_mean,
        "per_pair_exact_dp": point,
        "generation_bootstrap": summ(gen_boot),
        "task_bootstrap": summ(task_boot),
        "note": "Reference-choice variability is integrated out exactly by the DP (uniform q); "
                "the bootstrap intervals therefore isolate generation vs task variability.",
    }

    # ---- exact sensitivity to a non-uniform (canonical-biased) reference distribution ---------
    # q puts extra mass p on the canonical (first BFS) reference of every task; p=0 is uniform.
    def biased_q(n, p):
        q = np.full(n, (1.0 - p) / n)
        q[0] += p
        return q

    sensitivity = {}
    for p in (0.0, 0.25, 0.5, 0.8, 0.95):
        qs = [biased_q(n, p) for n in n_refs]
        per_pair = {}
        for a, b in pairs:
            data = [{"c_A": counts[a][k], "c_B": counts[b][k], "n_refs": n_refs[k]} for k in range(len(tids))]
            per_pair[f"{a}_vs_{b}"] = compute_exact_pairwise_margin(data, K=K, q_type=qs)["winner_reversal_probability"]
        sensitivity[str(p)] = {"mean_reversal": float(np.mean(list(per_pair.values()))), "per_pair": per_pair}

    # ---- E1 (strict string) vs E2 (action tuple) agreement ------------------------------------
    e1_e2_disagree = 0
    for m in MODELS:
        for t in tasks:
            vs = [format_plan_as_string(list(p)) for p in V[t["id"]]]
            for r in model_runs[m][t["id"]]:
                plan = extract_plan(r["response"])
                tup_hit = plan_to_tuple(plan) in set(V[t["id"]])
                str_hit = "".join(format_plan_as_string(plan).split()).lower() in {"".join(s.split()).lower() for s in vs}
                e1_e2_disagree += int(tup_hit != str_hit)

    # ---- EXPLORATORY detection analysis (locked H4 is undefined) ------------------------------
    n_tasks = len(tids)
    idx = np.stack([rng.integers(0, n, size=N_DRAWS) for n in n_refs], axis=1)
    scores = np.zeros((N_DRAWS, n_tasks, len(MODELS)), dtype=np.float32)
    for mi, m in enumerate(MODELS):
        for ti_, i in enumerate(tids):
            scores[:, ti_, mi] = counts[m][ti_][idx[:, ti_]] / float(K)
    signs = np.random.default_rng(SEED + 1).choice(np.array([-1.0, 1.0], dtype=np.float32), size=(N_FLIPS, n_tasks))
    raw = np.zeros((N_DRAWS, len(pairs)))
    for k, (a, b) in enumerate(pairs):
        d = scores[:, :, MODELS.index(a)] - scores[:, :, MODELS.index(b)]
        raw[:, k] = sign_flip_pvalues(d, signs)
    adj = holm_rows(raw)
    flips_e3 = np.random.default_rng(SEED + 2).choice(np.array([-1.0, 1.0], dtype=np.float32), size=(N_FLIPS, n_tasks))
    e3_d = np.stack([(task_rate[a] - task_rate[b]) for a, b in pairs])  # (6, 24)
    e3_p = sign_flip_pvalues(e3_d.astype(np.float64), flips_e3)
    e3_adj = holm_rows(e3_p[None, :])[0]
    exploratory = {}
    for k, (a, b) in enumerate(pairs):
        exploratory[f"{a}_vs_{b}"] = {
            "e3_raw_p": float(e3_p[k]),
            "e3_holm_p": float(e3_adj[k]),
            "e2_detects_rate_holm_lt_0.05": float((adj[:, k] < 0.05).mean()),
            "e2_n_draws_detecting": int((adj[:, k] < 0.05).sum()),
            "e2_median_holm_p": float(np.median(adj[:, k])),
        }

    out = {
        "status": "SUPPLEMENTARY_POST_HOC_NOT_CONFIRMATORY",
        "failure_taxonomy": tax,
        "pass_rate_ci": pass_ci,
        "variance_components": var_comp,
        "reversal_uncertainty": reversal_unc,
        "canonical_bias_sensitivity_exact_dp": sensitivity,
        "e1_vs_e2_generation_level_disagreements": e1_e2_disagree,
        "exploratory_detection": {
            "n_draws": N_DRAWS,
            "n_sign_flips": N_FLIPS,
            "note": "No pair is E3-separated at Holm alpha=0.05, so the locked H4 is untestable. "
                    "Rates below are descriptive only.",
            "per_pair": exploratory,
        },
        "seed": SEED,
    }
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("failure_taxonomy", "pass_rate_ci", "variance_components")}, indent=1))
    print(json.dumps(r["reversal_uncertainty"], indent=1))
    print(json.dumps(r["exploratory_detection"], indent=1))
