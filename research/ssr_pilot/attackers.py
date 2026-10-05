"""
Attackers for the SSR pilot.

1. Generators ("pseudo-models") whose outputs are scored by every evaluator:
     always_reference   prints the canonical trace for every world
     random_valid       uniform over the task-valid set V_task (gives the
                        mechanical disagreement floor 1 - E[1/|V_task|])
     random_invalid     samples the bank's invalid traces
     symbolic_alt       a perfect solver with a different tie-break (the LAST
                        task-valid trace in enumeration order)
2. Cheap evaluator proxies scored against the oracle on model outputs:
     distance proxy     accept if normalised distance to R <= tau (tau fitted in
                        analyze.py to the oracle's verdicts on OTHER mechanism
                        families: leave-one-family-out, the strongest cheap proxy)
     final-state-only   accept if the observed outcome equals R's outcome
3. Surface classifiers for the K0 integrity gate (valid alternative vs
   invalid): length/token counts, character n-grams, listing-order,
   distance-to-R. Protocols: grouped CV by world, and leave-one-structure-out.
"""

import random
from typing import Dict, List, Sequence, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from research.evaluation.metrics import cluster_bootstrap_ci
from research.ssr_pilot import families as F
from research.ssr_pilot import render

GENERATORS = ["always_reference", "random_valid", "random_invalid", "symbolic_alt"]
SEEDS = (0, 1, 2, 3)


# ---------------------------------------------------------------- generators

def task_valid(world: Dict) -> List[Tuple]:
    return [t for t in F.enumerate_rules(world) if not F.violated_constraints(world, t)]


def generate(name: str, world: Dict, bank: Dict, variant: str, seed: int) -> str:
    rendered = render.render_variant(world, variant)
    rng = random.Random(f"{name}-{world['id']}-{variant}-{seed}")
    if name == "always_reference":
        steps = bank["reference"]
    elif name == "random_valid":
        steps = rng.choice(task_valid(world))
    elif name == "symbolic_alt":
        steps = task_valid(world)[-1]
    elif name == "random_invalid":
        pools = [p for p in ([r["steps"] for r in bank["invalid_rule"]], bank["invalid_constraint"]) if p]
        steps = rng.choice(rng.choice(pools))
    else:
        raise ValueError(name)
    return "TRACE: " + F.format_steps(world, steps, rendered["style"], rendered["c2s"])


# ---------------------------------------------------------------- evaluator proxies

def norm_distance(world: Dict, steps: Sequence, ref: Sequence) -> float:
    d = F.distance(world, steps, ref)
    return d / max(len(F.tokens(world, steps)), len(F.tokens(world, ref)), 1)


def proxy_final_state(world: Dict, steps, ref) -> bool:
    return steps is not None and F.observe(world, steps) == F.observe(world, ref)


# ---------------------------------------------------------------- surface classifiers (K0)

def build_rows(worlds: List[Dict], banks: Dict[str, Dict], seed: int = 0) -> List[Dict]:
    """Valid ALTERNATIVES (reference excluded) vs invalid, balanced within each world."""
    rows = []
    for w in worlds:
        b = banks[w["id"]]
        for p in b["pairs"]:  # one profile-matched (valid, invalid) pair at a time: balanced by construction
            for y, t in ((1, p["valid"]), (0, p["invalid"])):
                rows.append({"world": w["id"], "structure": w["structure"], "family": w["family"], "y": y,
                             "steps": t, "ref": b["reference"], "w": w})
    return rows


def _listing_index(world: Dict) -> Dict[str, int]:
    names = [p["pid"] for p in world["processes"]] if world["family"] != "sync" else list(world["threads"])
    return {n: i for i, n in enumerate(names)}


def _entities(world: Dict, steps: Sequence) -> List[int]:
    idx = _listing_index(world)
    seq = [s[0] for s in steps] if world["family"] in ("scheduling", "sync") else list(steps)
    return [idx[e] for e in seq if e in idx]


def f_length(rows):
    return np.array([[len(F.tokens(r["w"], r["steps"])), len(F.format_steps(r["w"], r["steps"])),
                      len(set(map(str, F.tokens(r["w"], r["steps"]))))] for r in rows], float)


def f_listing(rows):
    out = []
    for r in rows:
        e = _entities(r["w"], r["steps"])
        pairs = list(zip(e, e[1:]))
        frac = sum(1 for a, b in pairs if b >= a) / max(1, len(pairs))
        rho = float(np.corrcoef(range(len(e)), e)[0, 1]) if len(e) > 2 and len(set(e)) > 1 else 0.0
        out.append([frac, rho])
    return np.array(out, float)


def f_dist(rows):
    out = []
    for r in rows:
        a, b = F.tokens(r["w"], r["steps"]), F.tokens(r["w"], r["ref"])
        fd = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        out.append([norm_distance(r["w"], r["steps"], r["ref"]), fd / max(len(a), 1), float(a[:1] == b[:1]),
                    float(a[-1:] == b[-1:])])
    return np.array(out, float)


def f_text(rows):
    return [F.format_steps(r["w"], r["steps"]) for r in rows]


CLASSIFIERS = {
    "length_counts": ("dense", f_length, lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))),
    "char_ngrams": ("text", f_text, lambda: make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)),
                                                          LogisticRegression(max_iter=2000))),
    "listing_order": ("dense", f_listing, lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))),
    "distance_to_R": ("dense", f_dist, lambda: GradientBoostingClassifier(n_estimators=60, max_depth=2,
                                                                          random_state=0)),
}


def _fit_predict(kind, make_model, X, y, tr, te):
    m = make_model()
    if kind == "text":
        m.fit([X[i] for i in tr], y[tr])
        return m.predict([X[i] for i in te])
    m.fit(X[tr], y[tr])
    return m.predict(X[te])


def eval_classifier(rows: List[Dict], name: str, protocol: str, repeats: int = 5) -> Dict:
    kind, featurize, make_model = CLASSIFIERS[name]
    X = featurize(rows)
    if kind == "dense":
        X = np.asarray(X)
    y = np.array([r["y"] for r in rows])
    worlds = np.array([r["world"] for r in rows])
    correct = np.zeros((repeats if protocol == "grouped_cv" else 1, len(rows)))
    if protocol == "grouped_cv":
        for k in range(repeats):
            cv = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=k)
            for tr, te in cv.split(np.zeros(len(y)), y, worlds):
                correct[k, te] = _fit_predict(kind, make_model, X, y, tr, te) == y[te]
    else:  # leave one mechanism structure out
        structs = np.array([r["structure"] for r in rows])
        for tr, te in LeaveOneGroupOut().split(np.zeros(len(y)), y, structs):
            correct[0, te] = _fit_predict(kind, make_model, X, y, tr, te) == y[te]
    ci = cluster_bootstrap_ci(correct.mean(0), worlds)
    return {"accuracy": ci["mean"], "ci95": ci["ci95"], "n_rows": len(rows), "n_worlds": ci["n_groups"]}


def k0_gate(rows: List[Dict]) -> Dict:
    out, ok = {}, True
    for name in CLASSIFIERS:
        for protocol in ("grouped_cv", "loso"):
            r = eval_classifier(rows, name, protocol)
            r["pass"] = bool(r["ci95"][0] <= 0.55 and r["accuracy"] <= 0.65)
            ok = ok and r["pass"]
            out[f"{name}/{protocol}"] = r
    return {"pass": bool(ok), "results": out}
