"""
Oracle tests for the SSR pilot (docs/research/SSR_PILOT_PREREG.md §6).

  * reference independence: no reference argument; verdict unchanged by any reference field
  * agreement with exhaustive enumeration (sched, sync) and an independent
    brute force (Banker's)
  * textbook cases
  * UNVERIFIABLE is never reported as FALSE, and vice versa
"""

import copy
import inspect
import itertools
import random
from collections import Counter

import pytest

from research.simulator.traces import normalize_schedule
from research.ssr_pilot import families as F
from research.ssr_pilot import oracle
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.worlds import load_worlds

WORLDS = load_worlds()
BY_ID = {w["id"]: w for w in WORLDS}


def text(world, steps):
    return "TRACE: " + F.format_steps(world, steps)


# ---------------------------------------------------------------- reference independence

def test_no_reference_parameter():
    params = inspect.signature(oracle.evaluate_candidate).parameters
    assert set(params) == {"world", "raw_text", "truncated", "shown2canon"}


@pytest.mark.parametrize("world", WORLDS, ids=lambda w: w["id"])
def test_verdict_unchanged_by_reference_fields(world):
    bank = load_bank(world)
    scrambled = copy.deepcopy(world)
    scrambled["reference"] = list(reversed(bank["reference"]))
    scrambled["R"] = "garbage"
    for t in [bank["reference"], *bank["valid"][:3], *[r["steps"] for r in bank["invalid_rule"][:3]]]:
        a = oracle.evaluate_candidate(world, text(world, t))
        b = oracle.evaluate_candidate(scrambled, text(world, t))
        assert a.to_dict() == b.to_dict()


# ---------------------------------------------------------------- agreement with enumeration

def _perturb(world, steps, rng):
    f = world["family"]
    if f == "scheduling":
        segs = [(p, e - s) for p, s, e in steps]
        i, j = rng.randrange(len(segs)), rng.randrange(len(segs))
        segs[i], segs[j] = segs[j], segs[i]
        out, t = [], 0
        for p, d in segs:
            out.append((p, t, t + d))
            t += d
        return normalize_schedule(out)
    if f == "sync":
        ev = list(steps)
        i, j = rng.randrange(len(ev)), rng.randrange(len(ev))
        ev[i], ev[j] = ev[j], ev[i]
        return tuple(ev)
    names = list(steps)
    rng.shuffle(names)
    return tuple(names)


@pytest.mark.parametrize("world", WORLDS, ids=lambda w: w["id"])
def test_oracle_agrees_with_enumeration(world):
    rng = random.Random(7)
    V = set(F.enumerate_rules(world))
    vlist = sorted(V)
    for t in vlist[:200]:
        assert F.rules_check(world, t)[0], t
    for _ in range(150):
        cand = _perturb(world, rng.choice(vlist), rng)
        assert F.rules_check(world, cand)[0] == (cand in V), (world["id"], cand)
        if world["family"] != "banker":
            assert F.system(world).accepts(cand) == (cand in V)


def _banker_bruteforce(world):
    """Independent safe-sequence enumeration: a different formulation of the same textbook rule."""
    mx = {p["pid"]: p["max"] for p in world["processes"]}
    al = {p["pid"]: p["alloc"] for p in world["processes"]}
    out = set()
    for perm in itertools.permutations(mx):
        work, ok = list(world["available"]), True
        for p in perm:
            if any(mx[p][j] - al[p][j] > work[j] for j in range(len(work))):
                ok = False
                break
            for j in range(len(work)):
                work[j] += al[p][j]
        if ok:
            out.add(perm)
    return out


@pytest.mark.parametrize("wid", [w["id"] for w in WORLDS if w["family"] == "banker"])
def test_banker_matches_bruteforce(wid):
    world = BY_ID[wid]
    assert set(F.enumerate_rules(world)) == _banker_bruteforce(world)


@pytest.mark.parametrize("world", WORLDS, ids=lambda w: w["id"])
def test_bank_labels(world):
    bank = load_bank(world)
    assert oracle.evaluate_candidate(world, text(world, bank["reference"])).semantic_valid == oracle.TRUE
    for t in bank["valid"]:
        assert oracle.evaluate_candidate(world, text(world, t)).semantic_valid == oracle.TRUE
    for r in bank["invalid_rule"]:
        v = oracle.evaluate_candidate(world, text(world, r["steps"]))
        assert v.semantic_valid == oracle.FALSE and v.valid_transitions is False
    for t in bank["invalid_constraint"]:
        v = oracle.evaluate_candidate(world, text(world, t))
        assert v.semantic_valid == oracle.FALSE and v.valid_transitions is True and v.constraints_ok is False
    assert bank["reference"] not in bank["valid"]
    assert len(bank["valid"]) >= 1
    assert len(bank["pairs"]) >= 1
    for p in bank["pairs"]:  # every matched pair is (valid alternative, invalid)
        assert oracle.evaluate_candidate(world, text(world, p["valid"])).semantic_valid == oracle.TRUE
        assert oracle.evaluate_candidate(world, text(world, p["invalid"])).semantic_valid == oracle.FALSE


def test_every_world_has_nonvacuous_semantics():
    """Each world must contain valid alternatives AND invalid traces, else it cannot discriminate."""
    for w in WORLDS:
        b = load_bank(w)
        assert b["n_task"] >= 2, w["id"]
        assert b["n_invalid_rule_pool"] >= 1, w["id"]
        assert b["pairs"], w["id"]


# ---------------------------------------------------------------- textbook cases

def test_textbook_fcfs_and_rr():
    w = BY_ID["sched_01"]  # Silberschatz P1=24, P2=3, P3=3
    ok = oracle.evaluate_candidate(w, "TRACE: P2 0-3, P3 3-6, P1 6-30")
    assert ok.semantic_valid == oracle.TRUE and ok.quality == pytest.approx(3.0)  # (6+0+3)/3
    bad = oracle.evaluate_candidate(w, "TRACE: P1 0-2, P2 2-5, P1 5-27, P3 27-30")
    assert bad.semantic_valid == oracle.FALSE and bad.violated_rule == "preempted_partial_burst"
    rr = BY_ID["sched_07"]  # same processes, quantum 4
    assert oracle.evaluate_candidate(rr, "TRACE: P1 0-4, P2 4-7, P3 7-10, P1 10-30").semantic_valid == oracle.TRUE


def test_textbook_banker():
    w = BY_ID["bank_01"]
    assert oracle.evaluate_candidate(w, "TRACE: P1, P3, P4, P2, P0").semantic_valid == oracle.TRUE
    unsafe = oracle.evaluate_candidate(w, "TRACE: P0, P1, P2, P3, P4")
    assert unsafe.semantic_valid == oracle.FALSE and unsafe.violated_rule == "need_exceeds_work"


def test_textbook_mutex():
    w = BY_ID["sync_01"]
    good = "TRACE: " + "; ".join(f"{t} {o}({a})" for t, o, a in [
        ("T1", "lock", "m"), ("T1", "write", "x"), ("T1", "unlock", "m"),
        ("T2", "lock", "m"), ("T2", "write", "x"), ("T2", "unlock", "m"),
        ("T3", "lock", "m"), ("T3", "write", "x"), ("T3", "unlock", "m")])
    assert oracle.evaluate_candidate(w, good).semantic_valid == oracle.TRUE
    both = ("TRACE: T1 lock(m); T2 lock(m); T1 write(x); T1 unlock(m); T2 write(x); T2 unlock(m); "
            "T3 lock(m); T3 write(x); T3 unlock(m)")
    v = oracle.evaluate_candidate(w, both)
    assert v.semantic_valid == oracle.FALSE and v.violated_rule == "mutual_exclusion_violation"


# ---------------------------------------------------------------- UNVERIFIABLE vs FALSE

def test_unverifiable_cases():
    w = BY_ID["sched_01"]
    assert oracle.evaluate_candidate(w, "I cannot do this.").semantic_valid == oracle.UNVERIFIABLE
    assert oracle.evaluate_candidate(w, "").semantic_valid == oracle.UNVERIFIABLE
    unk = oracle.evaluate_candidate(w, "TRACE: P2 0-3, P9 3-6, P1 6-30")
    assert unk.semantic_valid == oracle.UNVERIFIABLE and unk.reason == "unknown_entity"
    trunc = oracle.evaluate_candidate(w, "TRACE: P2 0-3, P3 3-6", truncated=True)
    assert trunc.semantic_valid == oracle.UNVERIFIABLE and trunc.reason == "truncated"
    # the same prefix, not truncated, is a definite failure to finish the task
    done = oracle.evaluate_candidate(w, "TRACE: P2 0-3, P3 3-6")
    assert done.semantic_valid == oracle.FALSE and done.violated_rule == "incomplete"
    # a truncated output whose visible prefix already breaks a rule is still FALSE
    viol = oracle.evaluate_candidate(w, "TRACE: P2 0-2, P3 2-5", truncated=True)
    assert viol.semantic_valid == oracle.FALSE


def test_trailing_idle_after_completion_is_false_not_a_crash():
    """Regression: a model appended 'IDLE' after the last process; the validator used to raise ValueError."""
    w = BY_ID["sched_01"]
    v = oracle.evaluate_candidate(w, "TRACE: P2 0-3, P3 3-6, P1 6-30, IDLE 30-31")
    assert v.semantic_valid == oracle.FALSE and v.violated_rule == "idle_after_completion"


def test_constraint_violation_is_false_with_valid_transitions():
    w = BY_ID["bank_02"]  # constraint: P3 before P4
    bank = load_bank(w)
    v = oracle.evaluate_candidate(w, text(w, bank["invalid_constraint"][0]))
    assert (v.valid_transitions, v.constraints_ok, v.semantic_valid) == (True, False, oracle.FALSE)


def test_compare_to_reference_is_separate():
    w = BY_ID["sched_01"]
    bank = load_bank(w)
    alt = bank["valid"][0]
    v = oracle.evaluate_candidate(w, text(w, alt))
    c = oracle.compare_to_reference(w, v.steps, text(w, alt), bank["reference"], F.format_steps(w, bank["reference"]))
    assert v.semantic_valid == oracle.TRUE and c["ref_match_norm"] is False
    same = oracle.compare_to_reference(w, bank["reference"], text(w, bank["reference"]), bank["reference"],
                                       F.format_steps(w, bank["reference"]))
    assert same["ref_match_norm"] and same["ref_match_strict"] and same["obs_equiv"]
