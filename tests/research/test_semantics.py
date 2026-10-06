"""
Label-validity tests for the v2 benchmark (docs/CLAUDE_FINAL_RESEARCH_AUDIT.md §C).

The benchmark is only as good as V(P). These tests require the generator-side
enumerators and the independent validators to agree everywhere, pin textbook
cases, and re-verify every stored label in benchmark_v2.json.
"""

import json
import os
import random
from collections import Counter

import pytest

from research.benchmark.generator import _system, load
from research.simulator.concurrency_interleaver import Interleaver
from research.simulator.cpu_scheduler import Scheduler, make_process
from research.simulator.traces import format_events, format_schedule, normalize_schedule, parse_events, parse_schedule
from research.simulator.validators import validate

BENCH = "research/benchmark/benchmark_v2.json"


def sched(policy, procs, q=2):
    return {"domain": "scheduling", "policy": policy, "processes": procs, "quantum": q}


# ---------------------------------------------------------------- textbook cases

def test_fcfs_textbook_ties_and_no_preemption():
    procs = [make_process("P1", 0, 24), make_process("P2", 0, 3), make_process("P3", 0, 3)]
    s = Scheduler(procs, "FCFS")
    assert s.count_paths() == 6  # three simultaneous arrivals, any order
    assert s.canonical() == (("P1", 0, 24), ("P2", 24, 27), ("P3", 27, 30))
    assert validate(sched("FCFS", procs), [("P2", 0, 3), ("P3", 3, 6), ("P1", 6, 30)])[0]
    # AGY's simulator accepted preemptive FCFS traces like this one
    ok, why = validate(sched("FCFS", procs), [("P1", 0, 2), ("P2", 2, 5), ("P1", 5, 27), ("P3", 27, 30)])
    assert not ok and why == "preempted_partial_burst"


def test_sjf_textbook_unique():
    procs = [make_process("P1", 0, 6), make_process("P2", 0, 8), make_process("P3", 0, 7), make_process("P4", 0, 3)]
    s = Scheduler(procs, "SJF")
    assert s.count_paths() == 1
    assert [p for p, _, _ in s.canonical()] == ["P4", "P1", "P3", "P2"]


def test_rr_textbook_q4():
    procs = [make_process("P1", 0, 24), make_process("P2", 0, 3), make_process("P3", 0, 3)]
    prob = sched("RR", procs, 4)
    textbook = [("P1", 0, 4), ("P2", 4, 7), ("P3", 7, 10), ("P1", 10, 30)]
    assert validate(prob, textbook)[0]
    assert Scheduler(procs, "RR", 4).accepts(textbook)
    assert not validate(prob, [("P1", 0, 5), ("P2", 5, 8), ("P3", 8, 11), ("P1", 11, 30)])[0]


def test_rr_arrival_vs_requeue_ambiguity_admits_both_orders():
    # P1 preempted at t=2 exactly when P2 arrives: both queue orders are valid
    procs = [make_process("P1", 0, 4), make_process("P2", 2, 2)]
    prob = sched("RR", procs, 2)
    a = [("P1", 0, 2), ("P2", 2, 4), ("P1", 4, 6)]
    b = [("P1", 0, 4), ("P2", 4, 6)]
    assert validate(prob, a)[0] and validate(prob, b)[0]
    assert set(Scheduler(procs, "RR", 2).enumerate()) == {normalize_schedule(a), normalize_schedule(b)}


def test_mutex_not_reentrant_and_mutual_exclusion():
    prob = {"domain": "concurrency", "semaphores": {},
            "threads": {"T1": [["lock", "m"], ["write", "x"], ["unlock", "m"]],
                        "T2": [["lock", "m"], ["write", "x"], ["unlock", "m"]]}}
    il = Interleaver(prob)
    assert il.count_paths() == 2
    bad = [("T1", "lock", "m"), ("T2", "lock", "m"), ("T1", "write", "x"), ("T1", "unlock", "m"),
           ("T2", "write", "x"), ("T2", "unlock", "m")]
    assert validate(prob, bad) == (False, "mutual_exclusion_violation")
    assert not il.accepts(bad)


def test_semaphore_wait_on_zero():
    prob = {"domain": "concurrency", "semaphores": {"s": 0},
            "threads": {"T1": [["write", "x"], ["signal", "s"]], "T2": [["wait", "s"], ["write", "y"]]}}
    assert validate(prob, [("T2", "wait", "s"), ("T1", "write", "x"), ("T1", "signal", "s"), ("T2", "write", "y")]) \
        == (False, "wait_on_zero_semaphore")


# ---------------------------------------------------------------- two-oracle agreement

def _random_sched(rng):
    policy = rng.choice(["FCFS", "SJF", "PRIORITY", "RR"])
    procs = [make_process(f"P{i + 1}", rng.choice([0, 0, 1, 2, 3]), rng.randint(1, 4), rng.randint(1, 3))
             for i in range(rng.randint(2, 4))]
    return sched(policy, procs, rng.choice([1, 2, 3]))


def _perturb(trace, rng):
    segs = [(p, e - s) for p, s, e in trace]
    i, j = rng.randrange(len(segs)), rng.randrange(len(segs))
    segs[i], segs[j] = segs[j], segs[i]
    out, t = [], 0
    for p, d in segs:
        out.append((p, t, t + d))
        t += d
    return normalize_schedule(out)


@pytest.mark.parametrize("seed", range(4))
def test_scheduling_enumerator_and_validator_agree(seed):
    rng = random.Random(seed)
    for _ in range(80):
        prob = _random_sched(rng)
        s = _system(prob)
        V = set(s.enumerate())
        assert s.count_paths() == len(V)  # path/trace bijection, incl. RR
        for tr in V:
            assert validate(prob, tr)[0], (prob, tr)
        for _ in range(25):
            cand = _perturb(rng.choice(sorted(V)), rng)
            assert validate(prob, cand)[0] == (cand in V) == s.accepts(cand), (prob, cand)


@pytest.mark.parametrize("seed", range(4))
def test_concurrency_enumerator_and_validator_agree(seed):
    rng = random.Random(100 + seed)
    for _ in range(80):
        threads = {}
        for i in range(rng.randint(2, 3)):
            ops = []
            for _ in range(rng.randint(1, 2)):
                k = rng.random()
                if k < 0.5:
                    m = rng.choice(["m1", "m2"])
                    ops += [["lock", m], ["write", "x"], ["unlock", m]]
                elif k < 0.75:
                    ops += [["write", rng.choice("xy")]]
                else:
                    ops += [[rng.choice(["wait", "signal"]), "s"]]
            threads[f"T{i + 1}"] = ops
        prob = {"domain": "concurrency", "threads": threads, "semaphores": {"s": rng.choice([0, 1])}}
        il = Interleaver(prob)
        V = set(il.enumerate())
        assert il.count_paths() == len(V)
        for tr in V:
            assert validate(prob, tr)[0]
        for _ in range(25):
            cand = il.random_interleaving(rng)
            assert validate(prob, cand)[0] == (cand in V) == il.accepts(cand)


# ---------------------------------------------------------------- representation

def test_json_lists_validate_like_tuples():
    """Regression for AGY's oracle, which compared JSON lists with tuples and rejected everything."""
    procs = [make_process("P1", 0, 2), make_process("P2", 0, 1)]
    assert validate(sched("FCFS", procs), [["P1", 0, 2], ["P2", 2, 3]])[0]


def test_parse_roundtrip_odd_names_and_table():
    tr = (("Job-7", 0, 3), ("IDLE", 3, 4), ("cron_2", 4, 6))
    for style in ["arrow", "table"]:
        assert parse_schedule("TRACE: " + format_schedule(tr, style), ["Job-7", "cron_2"]) == tr
    ev = (("T1", "lock", "m1"), ("T2", "write", "x"), ("T1", "unlock", "m1"))
    for style in ["arrow", "table"]:
        assert parse_events(format_events(ev, style), ["T1", "T2"]) == ev


def test_gap_means_idle():
    assert normalize_schedule([("P1", 0, 2), ("P2", 3, 4)]) == (("P1", 0, 2), ("IDLE", 2, 3), ("P2", 3, 4))


# ---------------------------------------------------------------- stored benchmark

@pytest.fixture(scope="module")
def bench():
    if not os.path.exists(BENCH):
        pytest.skip("benchmark_v2.json not generated")
    return load(BENCH)


def test_every_stored_label_reverified(bench):
    for inst in bench["instances"]:
        p, s = inst["problem"], _system(inst["problem"])
        for k in ["R1", "R2", "R3"]:
            assert validate(p, inst[k])[0] and s.accepts(inst[k]), (inst["id"], k)
        for k in ["I", "I2"]:
            assert not validate(p, inst[k])[0] and not s.accepts(inst[k]), (inst["id"], k)
        assert len({inst["R1"], inst["R2"], inst["R3"]}) == 3
        assert inst["I"] != inst["I2"]
        assert s.canonical() == inst["R1"]
        assert s.count_paths() == inst["n_valid"]


def test_invalid_traces_share_surface_statistics(bench):
    """I must not be separable from R2 by length or by the multiset of segments/events."""
    def cpu_time(t):
        c = Counter()
        for p, s, e in t:
            c[p] += e - s
        return c

    for inst in bench["instances"]:
        if inst["domain"] == "scheduling":
            assert cpu_time(inst["I"]) == cpu_time(inst["R2"]), inst["id"]
            assert inst["I"][-1][2] == inst["R2"][-1][2], inst["id"]  # same makespan
            if inst["problem"]["policy"] != "RR":  # non-preemptive: identical segment multiset
                ms = Counter((p, e - s) for p, s, e in inst["I"]), Counter((p, e - s) for p, s, e in inst["R2"])
                assert ms[0] == ms[1], inst["id"]
        else:
            assert Counter(inst["I"]) == Counter(inst["R2"]), inst["id"]
            for t in inst["problem"]["threads"]:  # per-thread order preserved
                assert [e for e in inst["I"] if e[0] == t] == [e for e in inst["R2"] if e[0] == t]
    n_len_mismatch = sum(len(i["I"]) != len(i["R2"]) for i in bench["instances"])
    assert n_len_mismatch <= 0.02 * len(bench["instances"]), n_len_mismatch


def test_alternatives_are_substantive(bench):
    from research.simulator.concurrency_interleaver import trace_class
    from research.simulator.cpu_scheduler import waiting_times
    for inst in bench["instances"]:
        if inst["domain"] == "scheduling":
            procs = inst["problem"]["processes"]
            assert waiting_times(procs, inst["R1"]) != waiting_times(procs, inst["R2"])
        else:
            assert trace_class(inst["R1"]) != trace_class(inst["R2"])


def test_no_duplicate_problems(bench):
    keys = [json.dumps(i["problem"], sort_keys=True) for i in bench["instances"]]
    assert len(keys) == len(set(keys))


def test_banker_validator_standalone():
    from research.simulator.validators import validate_banker
    world = {
        "family": "banker",
        "available": [3, 3, 2],
        "processes": [
            {"pid": "P0", "max": [7, 5, 3], "alloc": [0, 1, 0]},
            {"pid": "P1", "max": [3, 2, 2], "alloc": [2, 0, 0]},
            {"pid": "P2", "max": [9, 0, 2], "alloc": [3, 0, 2]},
            {"pid": "P3", "max": [2, 2, 2], "alloc": [2, 1, 1]},
            {"pid": "P4", "max": [4, 3, 3], "alloc": [0, 0, 2]},
        ]
    }
    valid_seq = ("P1", "P3", "P4", "P0", "P2")
    ok, reason = validate_banker(world, valid_seq)
    assert ok and reason == "ok"

    invalid_seq = ("P0", "P1", "P2", "P3", "P4")
    ok, reason = validate_banker(world, invalid_seq)
    assert not ok and reason == "need_exceeds_work"

