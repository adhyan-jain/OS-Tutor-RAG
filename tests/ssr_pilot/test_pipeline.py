"""Pipeline identities: attackers scored by the full evaluator stack must behave exactly as the design predicts."""

import numpy as np
import pytest

from research.ssr_pilot import analyze, render
from research.ssr_pilot import attackers as A
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.scoring import score_record
from research.ssr_pilot.worlds import load_worlds

WORLDS = load_worlds()
BANKS = {w["id"]: load_bank(w) for w in WORLDS}


def score(name, w, variant, seed=0):
    text = A.generate(name, w, BANKS[w["id"]], variant, seed)
    rec = {"model": f"attacker:{name}", "variant": variant, "seed": seed, "response": text, "done_reason": "stop"}
    return score_record(w, render.render_variant(w, variant), BANKS[w["id"]], rec)


@pytest.mark.parametrize("w", WORLDS, ids=lambda w: w["id"])
@pytest.mark.parametrize("variant", list(render.VARIANTS))
def test_attacker_identities(w, variant):
    ref = score("always_reference", w, variant)
    assert ref["B"] and ref["A_norm"] and ref["A_strict"] and ref["C"] and ref["nd"] == 0
    alt = score("symbolic_alt", w, variant)
    assert alt["B"] and not alt["A_norm"] and not alt["A_strict"]  # a perfect solver, rejected by reference matching
    inv = score("random_invalid", w, variant)
    assert not inv["B"] and not inv["A_norm"] and inv["semantic"] == "FALSE"
    val = score("random_valid", w, variant)
    assert val["B"] and val["semantic"] == "TRUE"


def test_exact_match_rejects_extra_unknown_entities():
    """Regression (found after the first LLM run): 'reference + a token outside the world' must not be an exact match."""
    w = next(x for x in WORLDS if x["id"] == "sched_01")
    ref = BANKS["sched_01"]["reference"]
    text = "TRACE: " + render.reference_text(w, ref, render.render_variant(w, "v0")) + ", P9 30-31"
    rec = {"model": "m", "variant": "v0", "seed": 0, "response": text, "done_reason": "stop"}
    r = score_record(w, render.render_variant(w, "v0"), BANKS["sched_01"], rec)
    assert r["semantic"] == "UNVERIFIABLE" and not r["B"] and not r["A_norm"]


def test_a_norm_true_implies_b_true():
    """The reference is task-valid, so matching it can never be a false accept."""
    for w in WORLDS:
        for variant in render.VARIANTS:
            for name in A.GENERATORS:
                r = score(name, w, variant)
                assert not (r["A_norm"] and not r["B"])


def test_strict_never_looser_than_norm():
    for w in WORLDS:
        for variant in render.VARIANTS:
            for name in A.GENERATORS:
                r = score(name, w, variant)
                assert not (r["A_strict"] and not r["A_norm"])


def test_floor_is_the_mechanical_disagreement_of_a_random_valid_generator():
    """E[FRR] of uniform-over-V_task equals 1 - 1/|V_task| per world."""
    for w in WORLDS:
        n = BANKS[w["id"]]["n_task"]
        tv = A.task_valid(w)
        assert len(tv) == n
        assert sum(t != BANKS[w["id"]]["reference"] for t in tv) / n == pytest.approx(1 - 1 / n)


def test_statistics_helpers():
    d = np.array([0.1] * 24)
    assert analyze.signflip_p(d, n_flips=2000) < 0.01  # consistently positive -> significant
    assert analyze.signflip_p(np.array([0.1, -0.1] * 12), n_flips=2000) > 0.9
    assert analyze.balanced_agreement(np.array([1, 1, 0, 0], bool), np.array([1, 0, 1, 0], bool)) == 0.5
    assert analyze.passes_k1({"n": 10, "mean": 0.2, "ci95": [0.1, 0.3]})
    assert not analyze.passes_k1({"n": 10, "mean": 0.2, "ci95": [0.04, 0.3]})
    assert not analyze.passes_k1({"n": 10, "mean": 0.09, "ci95": [0.06, 0.3]})


def test_decision_rule_is_mechanical():
    base = {"K0": True, "K1": True, "K2": True, "K3": True, "K4": True, "K5": True}
    c = {"adequate_precision_no_change": False}
    assert analyze.decide(base, {"conclusions": c})["mechanical_verdict"] == "GREENLIGHT"
    assert analyze.decide({**base, "K1": False}, {"conclusions": c})["mechanical_verdict"] == "KILL"
    assert analyze.decide({**base, "K3": False}, {"conclusions": c})["mechanical_verdict"] == "KILL"
    assert analyze.decide({**base, "K5": False}, {"conclusions": c})["mechanical_verdict"] == "CONDITIONAL"
    assert analyze.decide({**base, "K4": False}, {"conclusions": c})["mechanical_verdict"] == "CONDITIONAL"
    precise = {"adequate_precision_no_change": True}
    assert analyze.decide({**base, "K4": False}, {"conclusions": precise})["mechanical_verdict"] == "KILL"
