"""
Leakage audit for benchmark_v2 (thresholds frozen in docs/PREREGISTRATION_V2.md §3).

Question: can a model that never reasons about the problem tell the valid
alternative R2 from the invalid trace I using surface features alone --
length, tokens, n-grams, divergence position, similarity to the reference R1,
local adjacency, or sentence embeddings? If yes, a judge could score well (or
badly) for reasons unrelated to execution semantics.

AGY's audit ran one TF-IDF attacker on a dataset whose "invalid" traces were
mostly valid, with a threshold equal to the observed accuracy. This replaces it.
"""

import argparse
import difflib
import json
import os
from typing import Dict, List

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from research.benchmark.generator import load
from research.evaluation.provenance import stamp
from research.simulator.traces import first_divergence, format_events, format_schedule, levenshtein

CHANCE = {"binary": 0.5, "threeway": 1 / 3}
MARGIN = 0.05  # frozen
SEEDS = [0, 1, 2, 3, 4]
N_BOOT = 2000


def render(inst, trace) -> str:
    fmt = format_schedule if inst["domain"] == "scheduling" else format_events
    return fmt(trace, inst["format"])


def toks(inst, trace) -> List[str]:
    if inst["domain"] == "scheduling":
        return [p for p, _, _ in trace]
    return [f"{t}:{op}({a})" for t, op, a in trace]


def build_rows(instances, target: str):
    labels = {"binary": [("R2", 1), ("I", 0)], "threeway": [("R1", 0), ("R2", 1), ("I", 2)]}[target]
    rows = []
    for inst in instances:
        for key, y in labels:
            tr = inst[key]
            rows.append({"group": inst["id"], "domain": inst["domain"], "y": y,
                         "text": render(inst, tr), "ref_text": render(inst, inst["R1"]),
                         "toks": toks(inst, tr), "ref_toks": toks(inst, inst["R1"]),
                         "problem": json.dumps(inst["problem"])})
    return rows


# ------------------------------------------------------------------ features

def f_length(rows):
    return np.array([[len(r["toks"]), len(r["text"]), len(r["text"].split())] for r in rows], float)


def f_divergence(rows):
    out = []
    for r in rows:
        a, b = r["toks"], r["ref_toks"]
        fd = first_divergence(a, b)
        ld = first_divergence(a[::-1], b[::-1])
        out.append([fd, fd / max(len(a), 1), ld, ld / max(len(a), 1)])
    return np.array(out, float)


def f_refsim(rows):
    out = []
    for r in rows:
        a, b = r["toks"], r["ref_toks"]
        bg = lambda s: {(x, y) for x, y in zip(s, s[1:])}
        ja = len(bg(a) & bg(b)) / max(len(bg(a) | bg(b)), 1)
        out.append([levenshtein(a, b), difflib.SequenceMatcher(None, r["text"], r["ref_text"]).ratio(), ja,
                    first_divergence(a, b), float(a[:1] == b[:1]), float(a[-1:] == b[-1:])])
    return np.array(out, float)


def adjacent_pairs(rows):
    return [" ".join(f"{x}>{y}" for x, y in zip(r["toks"], r["toks"][1:])) for r in rows]


_EMB_CACHE: Dict[str, np.ndarray] = {}


def f_embedding(rows):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-large-en-v1.5", device="cpu")
    texts = sorted({r["text"] for r in rows} | {r["ref_text"] for r in rows})
    missing = [t for t in texts if t not in _EMB_CACHE]
    if missing:
        vecs = model.encode(missing, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        _EMB_CACHE.update(zip(missing, vecs))
    e = np.stack([_EMB_CACHE[r["text"]] for r in rows])
    er = np.stack([_EMB_CACHE[r["ref_text"]] for r in rows])
    return np.hstack([e, e - er, (e * er).sum(1, keepdims=True)])


def attackers():
    lr = lambda: LogisticRegression(max_iter=2000, C=1.0)
    gb = lambda: HistGradientBoostingClassifier(max_iter=200, random_state=0)
    return {
        "length_counts": ("dense", f_length, lambda: make_pipeline(StandardScaler(), lr())),
        "divergence_position": ("dense", f_divergence, gb),
        "reference_similarity": ("dense", f_refsim, gb),
        "char_ngram_2_5": ("text", lambda rows: [r["text"] for r in rows],
                           lambda: make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5)), lr())),
        "bag_of_words": ("text", lambda rows: [r["text"] for r in rows],
                         lambda: make_pipeline(CountVectorizer(token_pattern=r"[^\s,;|]+", ngram_range=(1, 2)), lr())),
        "local_plausibility": ("text", adjacent_pairs,
                               lambda: make_pipeline(CountVectorizer(token_pattern=r"\S+"), lr())),
        "bge_embedding": ("dense", f_embedding, lambda: make_pipeline(StandardScaler(), lr())),
    }


def diagnostic():
    """Non-gating: problem + trace text. Measures learnability of the task."""
    return ("text", lambda rows: [r["problem"] + " || " + r["text"] for r in rows],
            lambda: make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5)),
                                  LogisticRegression(max_iter=2000)))


# ------------------------------------------------------------------ CV + CI

def cv_accuracy(rows, spec) -> Dict:
    kind, featurize, make_model = spec
    X = featurize(rows)
    y = np.array([r["y"] for r in rows])
    groups = np.array([r["group"] for r in rows])
    correct = np.zeros((len(SEEDS), len(rows)))
    for si, seed in enumerate(SEEDS):
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        for tr, te in cv.split(np.zeros(len(y)), y, groups):
            m = make_model()
            if kind == "text":
                m.fit([X[i] for i in tr], y[tr])
                pred = m.predict([X[i] for i in te])
            else:
                m.fit(X[tr], y[tr])
                pred = m.predict(X[te])
            correct[si, te] = pred == y[te]
    per_row = correct.mean(0)
    uniq, inv = np.unique(groups, return_inverse=True)
    per_group = np.bincount(inv, weights=per_row) / np.bincount(inv)
    rng = np.random.default_rng(0)
    boots = [per_group[rng.integers(0, len(uniq), len(uniq))].mean() for _ in range(N_BOOT)]
    return {"accuracy": float(per_row.mean()), "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "per_seed": [float(c.mean()) for c in correct], "n_rows": len(rows), "n_instances": len(uniq)}


def run(path: str, out_path: str, include_embeddings: bool = True) -> Dict:
    data = load(path)
    inst = data["instances"]
    report = {"provenance": stamp(), "margin": MARGIN, "chance": CHANCE, "results": {}, "failures": []}
    subsets = {"pooled": inst,
               "scheduling": [i for i in inst if i["domain"] == "scheduling"],
               "concurrency": [i for i in inst if i["domain"] == "concurrency"]}
    specs = attackers()
    if not include_embeddings:
        specs.pop("bge_embedding")
    for target in ["binary", "threeway"]:
        for sub, items in subsets.items():
            rows = build_rows(items, target)
            for name, spec in list(specs.items()) + [("DIAGNOSTIC_problem_plus_trace", diagnostic())]:
                res = cv_accuracy(rows, spec)
                gating = target == "binary" and not name.startswith("DIAGNOSTIC")
                res["threshold"] = CHANCE[target] + MARGIN
                res["exceeds"] = res["ci95"][0] > CHANCE[target] + MARGIN
                res["gating"] = gating
                report["results"][f"{target}/{sub}/{name}"] = res
                if gating and res["exceeds"]:
                    report["failures"].append(f"{target}/{sub}/{name}")
                print(f"{target:8} {sub:11} {name:32} acc={res['accuracy']:.3f} "
                      f"CI=[{res['ci95'][0]:.3f},{res['ci95'][1]:.3f}] {'FAIL' if gating and res['exceeds'] else ''}")
    report["passed"] = not report["failures"]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=1)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="research/benchmark/benchmark_v2.json")
    ap.add_argument("--out", default="research/results/leakage_audit_v2.json")
    ap.add_argument("--no-embeddings", action="store_true")
    a = ap.parse_args()
    r = run(a.data, a.out, include_embeddings=not a.no_embeddings)
    print("PASSED" if r["passed"] else f"FAILED: {r['failures']}")
