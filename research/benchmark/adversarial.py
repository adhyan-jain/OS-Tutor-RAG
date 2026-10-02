"""
Adversarial filtering for invalid traces (PREREGISTRATION_V2 §9, deviation D2).

The first v2 leakage audit failed: reference-similarity, bag-of-words and
adjacent-pair attackers separated the valid alternative R2 from the invalid
trace I above the frozen threshold. Following adversarial filtering
(Zellers et al., 2018, SWAG; Le Bras et al., 2020, AFLite), shallow attackers
are trained on an AUXILIARY benchmark generated from a different seed
(disjoint problems), and the generator then picks, among the profile-matched,
locally plausible invalid candidates, the one whose attacker score is closest
to R2's. The final audit retrains all attackers from scratch under grouped CV
on the real benchmark, so it measures residual leakage, not the filter's fit.
"""

from typing import Callable, Dict, List

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

AUX_SEED = 99173


def _rows_for(inst: Dict, traces: List) -> List[Dict]:
    from research.benchmark.audit_leakage import render, toks
    return [{"text": render(inst, t), "ref_text": render(inst, inst["R1"]), "toks": toks(inst, t),
             "ref_toks": toks(inst, inst["R1"])} for t in traces]


def train_scorer(aux_instances: List[Dict]) -> Callable[[Dict, List], np.ndarray]:
    """Returns score(inst, traces) -> attackers x traces matrix of P(valid), per domain."""
    from research.benchmark.audit_leakage import adjacent_pairs, f_refsim
    models = {}
    for dom in ["scheduling", "concurrency"]:
        rows, y = [], []
        for inst in (i for i in aux_instances if i["domain"] == dom):
            rows += _rows_for(inst, [inst["R2"], inst["I"]])
            y += [1, 0]
        y = np.array(y)
        bow = make_pipeline(CountVectorizer(token_pattern=r"[^\s,;|]+", ngram_range=(1, 2)),
                            LogisticRegression(max_iter=3000)).fit([r["text"] for r in rows], y)
        pairs = make_pipeline(CountVectorizer(token_pattern=r"\S+"),
                              LogisticRegression(max_iter=3000)).fit(adjacent_pairs(rows), y)
        refsim = HistGradientBoostingClassifier(max_iter=200, random_state=0).fit(f_refsim(rows), y)
        models[dom] = (bow, pairs, refsim)

    def score(inst: Dict, traces: List) -> np.ndarray:
        rows = _rows_for(inst, traces)
        bow, pairs, refsim = models[inst["domain"]]
        return np.vstack([bow.predict_proba([r["text"] for r in rows])[:, 1],
                          pairs.predict_proba(adjacent_pairs(rows))[:, 1],
                          refsim.predict_proba(f_refsim(rows))[:, 1]])

    return score
