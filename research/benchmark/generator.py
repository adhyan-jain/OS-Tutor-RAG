"""
Benchmark generator for reference sensitivity in nondeterministic execution
judging (replaces AGY's generator; see docs/CLAUDE_FINAL_RESEARCH_AUDIT.md).

Every instance carries
  R1  canonical valid trace (textbook tie-break: listed order / arrivals before
      re-queued process / lowest-index enabled thread),
  R2  valid trace sampled uniformly from V(P) \\ {R1} -- for concurrency it must
      also lie in a different Mazurkiewicz class (not a commuting reshuffle),
  R3  a third valid trace, distinct from R1 and R2,
  I   an invalid trace with the SAME multiset of segments/events, the same
      length and the same per-process totals as the valid traces, chosen so its
      edit distance to R1 matches R2's. Shallow features therefore cannot
      separate R2 from I; only the order -- i.e. the semantics -- can.
  I2  a second invalid trace (used as an "invalid reference").
All labels are confirmed by two independent implementations (enumerator and
validator); instances where they disagree are rejected and counted.
"""

import hashlib
import json
import math
import os
import random
from typing import Dict, List, Optional, Tuple

import numpy as np

from research.simulator.concurrency_interleaver import Interleaver, last_writer, trace_class
from research.simulator.cpu_scheduler import Scheduler, make_process, waiting_times
from research.simulator.traces import IDLE, first_divergence, levenshtein, normalize_schedule
from research.simulator.validators import validate

SPLITS = {
    # name: (n_instances, domain)
    "id": (150, "scheduling"),
    "lexical_ood": (80, "scheduling"),
    "long_trace": (80, "scheduling"),
    "high_branching": (80, "scheduling"),
    "rr_primitive": (80, "scheduling"),
    "struct_mutex": (80, "concurrency"),
    "struct_semaphore": (80, "concurrency"),
}

ODD_NAMES = ["httpd", "cron_2", "Xq9", "backup", "kswapd", "nginx_w", "Job-7", "zeta", "init_rd", "sshd"]
MAX_TRIES = 400


# ------------------------------------------------------------- problem makers

def _sched_problem(rng, n_lo, n_hi, policies, arrivals, bursts, names=None, quantum=None):
    policy = rng.choice(policies)
    n = rng.randint(n_lo, n_hi)
    names = names or [f"P{i + 1}" for i in range(n)]
    procs = [make_process(names[i], rng.choice(arrivals), rng.choice(bursts), rng.randint(1, 3))
             for i in range(n)]
    prob = {"domain": "scheduling", "policy": policy, "processes": procs}
    if policy == "RR":
        prob["quantum"] = quantum or rng.choice([1, 2, 3])
    return prob


def make_problem(split: str, rng: random.Random) -> Dict:
    if split == "id":
        return _sched_problem(rng, 3, 5, ["FCFS", "SJF", "PRIORITY"], [0, 0, 1, 2, 3, 4], range(1, 7))
    if split == "lexical_ood":
        n = rng.randint(3, 5)
        names = rng.sample(ODD_NAMES, n)
        return _sched_problem(rng, n, n, ["FCFS", "SJF", "PRIORITY"], [0, 0, 1, 2, 3, 4], range(1, 7), names)
    if split == "long_trace":
        return _sched_problem(rng, 7, 10, ["FCFS", "SJF", "PRIORITY"], [0, 0, 2, 4, 6, 8], range(1, 7))
    if split == "high_branching":
        # many simultaneous arrivals and equal keys -> |V| in the hundreds to tens of thousands
        return _sched_problem(rng, 6, 8, ["FCFS", "SJF"], [0, 0, 0, 0, 1], [2, 2, 2, 3])
    if split == "rr_primitive":
        return _sched_problem(rng, 3, 4, ["RR"], [0, 0, 1, 2, 3, 4], range(1, 6))
    if split == "struct_mutex":
        return _mutex_problem(rng)
    if split == "struct_semaphore":
        return _semaphore_problem(rng)
    raise ValueError(split)


def _mutex_problem(rng):
    threads = {}
    for i in range(rng.randint(2, 3)):
        ops = []
        for _ in range(rng.randint(1, 2)):
            if rng.random() < 0.7:
                m = rng.choice(["m1", "m2"])
                ops += [["lock", m], ["write", rng.choice(["x", "y"])], ["unlock", m]]
            else:
                ops += [["write", rng.choice(["x", "y", "z"])]]
        threads[f"T{i + 1}"] = ops
    return {"domain": "concurrency", "threads": threads, "semaphores": {}}


def _semaphore_problem(rng):
    """Semaphore-only shapes (producer/consumer, signal chains, counting
    resource pools) never seen in struct_mutex; randomised so problems are
    unique rather than a handful of fixed templates."""
    var = lambda: rng.choice(["x", "y", "buf", "out", "log"])
    shape = rng.choice(["prodcons", "signal_chain", "pool"])
    if shape == "prodcons":
        n_prod = rng.randint(1, 2)
        items = [rng.randint(1, 2) for _ in range(n_prod)]
        threads = {}
        for i, k in enumerate(items):
            threads[f"T{i + 1}"] = [op for _ in range(k) for op in (["write", var()], ["signal", "full"])]
        cons = []
        for _ in range(sum(items)):
            cons += [["wait", "full"], ["write", var()]]
        threads[f"T{n_prod + 1}"] = cons
        return {"domain": "concurrency", "threads": threads, "semaphores": {"full": 0}}
    if shape == "signal_chain":
        n = rng.randint(2, 4)
        threads = {}
        for i in range(n):
            ops = [["write", var()]] if rng.random() < 0.6 else []
            if i > 0:
                ops.append(["wait", f"s{i}"])
            ops.append(["write", var()])
            if i < n - 1:
                ops.append(["signal", f"s{i + 1}"])
            threads[f"T{i + 1}"] = ops
        threads[f"T{n + 1}"] = [["write", var()] for _ in range(rng.randint(1, 2))]
        return {"domain": "concurrency", "threads": threads, "semaphores": {f"s{i}": 0 for i in range(1, n)}}
    n = rng.randint(2, 3)
    threads = {}
    for i in range(n):
        ops = []
        for _ in range(rng.randint(1, 2)):
            ops += [["wait", "slots"], ["write", var()], ["signal", "slots"]]
        threads[f"T{i + 1}"] = ops
    return {"domain": "concurrency", "threads": threads, "semaphores": {"slots": rng.randint(1, n - 1)}}


# ------------------------------------------------------------- helpers

def _system(prob):
    if prob["domain"] == "scheduling":
        return Scheduler(prob["processes"], prob["policy"], prob.get("quantum", 2))
    return Interleaver(prob)


def _tokens(prob, trace) -> List:
    """Sequence used for edit distance: dispatch order (scheduling) or events."""
    if prob["domain"] == "scheduling":
        return [p for p, _, _ in trace]
    return list(trace)


def _busy_period_permutation(trace, rng, swaps) -> Tuple:
    segs = list(trace)
    periods, cur = [], []
    for i, s in enumerate(segs):
        if s[0] == IDLE:
            if cur:
                periods.append(cur)
            cur = []
        else:
            cur.append(i)
    if cur:
        periods.append(cur)
    periods = [p for p in periods if len(p) >= 2]
    if not periods:
        return tuple(trace)
    for _ in range(swaps):
        p = rng.choice(periods)
        i, j = rng.sample(p, 2)
        segs[i], segs[j] = segs[j], segs[i]
    out, t = [], 0
    for pid, s, e in segs:
        out.append((pid, t, t + (e - s)))
        t += e - s
    return normalize_schedule(out)


def _adjacent_swaps(trace, rng, swaps) -> Tuple:
    ev = list(trace)
    for _ in range(swaps):
        cands = [i for i in range(len(ev) - 1) if ev[i][0] != ev[i + 1][0]]
        if not cands:
            break
        i = rng.choice(cands)
        ev[i], ev[i + 1] = ev[i + 1], ev[i]
    return tuple(ev)


def _pairs(prob, trace):
    t = _tokens(prob, trace)
    return set(zip(t, t[1:]))


def _profile(prob, trace, r1) -> Tuple[int, int, int]:
    """Similarity of a trace to the reference R1: first/last divergence and edit distance."""
    a, b = _tokens(prob, trace), _tokens(prob, r1)
    return first_divergence(a, b), first_divergence(a[::-1], b[::-1]), levenshtein(a, b)


def _invalid_pool(prob, system, valid_bases, rng, n=600) -> List[Tuple]:
    pool = set()
    for k in range(n):
        # half the candidates mutate R2 itself so they keep R2's similarity profile to R1
        base = valid_bases[1] if k % 2 == 0 else rng.choice(valid_bases)
        if prob["domain"] == "scheduling":
            cand = _busy_period_permutation(base, rng, rng.randint(1, 3))
            if len(cand) != len(base):  # RR merges can shorten -- keep length identical
                continue
        else:
            cand = (_adjacent_swaps(base, rng, rng.randint(1, 3)) if rng.random() < 0.6
                    else system.random_interleaving(rng))
        if not validate(prob, cand)[0]:
            pool.add(cand)
    return sorted(pool)


def _substantive(prob, a, b) -> bool:
    if prob["domain"] == "scheduling":
        return waiting_times(prob["processes"], a) != waiting_times(prob["processes"], b)
    return trace_class(a) != trace_class(b)


def _hash_v(system) -> Optional[str]:
    try:
        traces = sorted(system.enumerate(limit=20_000))
    except RuntimeError:
        return None
    return hashlib.sha256(json.dumps(traces).encode()).hexdigest()[:16]


# ------------------------------------------------------------- instance builder

def build_instance(split: str, rng: random.Random, stats: Dict, scorer=None) -> Optional[Dict]:
    prob = make_problem(split, rng)
    system = _system(prob)
    n_valid = system.count_paths()
    if n_valid < 3:
        stats["rejected_lt3_valid"] += 1
        return None
    r1 = system.canonical()
    r2 = r3 = None
    for _ in range(60):
        cand = system.sample(rng)
        if cand != r1 and _substantive(prob, r1, cand):
            r2 = cand
            break
    if r2 is None:
        stats["rejected_no_substantive_alt"] += 1
        return None
    for _ in range(60):
        cand = system.sample(rng)
        if cand not in (r1, r2):
            r3 = cand
            break
    if r3 is None:
        stats["rejected_no_r3"] += 1
        return None

    bases = [r1, r2, r3] + [system.sample(rng) for _ in range(5)]
    # Leakage defence (PREREGISTRATION_V2 §9 D2): the first v2 audit showed that
    # similarity to R1 and locally implausible adjacent pairs (e.g. lock(m)
    # immediately followed by another thread's lock(m)) separated I from R2.
    # I is therefore restricted to traces whose every adjacent pair occurs in
    # some valid trace, and matched to R2 on its similarity profile to R1.
    valid_pairs = set()
    for _ in range(300):
        valid_pairs |= _pairs(prob, system.sample(rng))
    for b in bases:
        valid_pairs |= _pairs(prob, b)
    n_cand = 1500 if prob["domain"] == "concurrency" else 600
    pool = [c for c in _invalid_pool(prob, system, bases, rng, n_cand) if _pairs(prob, c) <= valid_pairs]
    if len(pool) < 2:
        stats["rejected_no_invalid"] += 1
        return None
    t1, t2 = _tokens(prob, r1), _tokens(prob, r2)
    d12 = levenshtein(t1, t2)
    target = _profile(prob, r2, r1)

    def mismatch(c):
        p = _profile(prob, c, r1)
        return (len(c) != len(r2), sum(abs(x - y) for x, y in zip(p, target)), rng.random())

    scored = sorted(pool, key=mismatch)
    if mismatch(scored[0])[:2] != (False, 0):
        stats["rejected_profile_unmatched"] += 1
        return None
    matched = [c for c in scored if mismatch(c)[:2] == (False, 0)]
    if scorer is not None and len(matched) > 1:
        # adversarial filtering: the matched candidate attackers find most R2-like
        inst_view = {"domain": prob["domain"], "format": "table" if split == "lexical_ood" else "arrow", "R1": r1}
        s = scorer(inst_view, [r2] + matched)
        gap = np.abs(s[:, 1:] - s[:, :1]).sum(0)
        matched = [matched[k] for k in np.argsort(gap, kind="stable")]
    inv = matched[0]
    inv2 = matched[1] if len(matched) > 1 else next(c for c in scored if c != inv)

    # Two-oracle label check. Membership side uses enumeration when feasible.
    labels = {k: validate(prob, tr) for k, tr in [("R1", r1), ("R2", r2), ("R3", r3), ("I", inv), ("I2", inv2)]}
    expected = {"R1": True, "R2": True, "R3": True, "I": False, "I2": False}
    if any(labels[k][0] != v for k, v in expected.items()):
        stats["rejected_oracle_disagreement"] += 1
        return None
    if not (all(system.accepts(t) for t in (r1, r2, r3)) and not system.accepts(inv) and not system.accepts(inv2)):
        stats["rejected_oracle_disagreement"] += 1
        return None
    enum_checked = False
    if n_valid <= 20_000:
        vset = set(system.enumerate(limit=20_000))
        if len(vset) != n_valid or not (r1 in vset and r2 in vset and r3 in vset
                                        and inv not in vset and inv2 not in vset):
            stats["rejected_oracle_disagreement"] += 1
            return None
        enum_checked = True

    entities = prob["processes"] if prob["domain"] == "scheduling" else prob["threads"]
    return {
        "split": split,
        "domain": prob["domain"],
        "problem": prob,
        "format": "table" if split == "lexical_ood" else "arrow",
        "n_valid": n_valid,
        "log2_n_valid": math.log2(n_valid),
        "trace_len": len(r1),
        "n_entities": len(entities),
        "R1": r1, "R2": r2, "R3": r3, "I": inv, "I2": inv2,
        "I_violation": labels["I"][1],
        "I2_violation": labels["I2"][1],
        "dist_R1_R2": d12,
        "dist_R1_I": levenshtein(t1, _tokens(prob, inv)),
        "dist_R1_R3": levenshtein(t1, _tokens(prob, r3)),
        "firstdiv_R1_R2": first_divergence(t1, t2),
        "firstdiv_R1_I": first_divergence(t1, _tokens(prob, inv)),
        "R2_substantive": True,
        "R2_same_outcome": (last_writer(r1) == last_writer(r2)) if prob["domain"] == "concurrency"
        else sum(waiting_times(prob["processes"], r1).values()) == sum(waiting_times(prob["processes"], r2).values()),
        "labels_verified": {"validator": True, "enumerator_membership": True, "full_enumeration": enum_checked},
        "V_hash": _hash_v(system) if enum_checked else None,
    }


def generate(seed: int = 20261002, scorer=None, exclude_problems=(), sizes: Optional[Dict[str, int]] = None) -> Dict:
    rng = random.Random(seed)
    data = {"metadata": {"seed": seed, "generator": "research/benchmark/generator.py",
                         "adversarial_filtering": scorer is not None, "splits": {}},
            "instances": []}
    seen_problems = set(exclude_problems)  # no problem may appear twice (incl. the auxiliary set)
    for split, (n, _) in SPLITS.items():
        n = (sizes or {}).get(split, n)
        stats = {k: 0 for k in ["rejected_lt3_valid", "rejected_no_substantive_alt", "rejected_no_r3",
                                 "rejected_no_invalid", "rejected_profile_unmatched", "rejected_oracle_disagreement",
                                 "rejected_duplicate"]}
        got, tries = [], 0
        while len(got) < n:
            tries += 1
            if tries > n * MAX_TRIES:
                raise RuntimeError(f"split {split}: could not build {n} instances ({stats})")
            inst = build_instance(split, rng, stats, scorer)
            if inst is not None:
                key = json.dumps(inst["problem"], sort_keys=True)
                if key in seen_problems:
                    stats["rejected_duplicate"] += 1
                    continue
                seen_problems.add(key)
                inst["id"] = f"{split}_{len(got):03d}"
                got.append(inst)
        # irrelevant reference: a valid trace of a different problem in the same split
        for k, inst in enumerate(got):
            inst["irrelevant_ref"] = got[(k + 1) % len(got)]["R1"]
            inst["irrelevant_ref_from"] = got[(k + 1) % len(got)]["id"]
        stats["attempts"] = tries
        data["metadata"]["splits"][split] = {"n": len(got), **stats}
        data["instances"].extend(got)
    return data


def save(data: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


def load(path: str) -> Dict:
    from research.simulator.traces import as_events, as_schedule
    with open(path) as f:
        data = json.load(f)
    for inst in data["instances"]:
        conv = as_schedule if inst["domain"] == "scheduling" else as_events
        for k in ["R1", "R2", "R3", "I", "I2", "irrelevant_ref"]:
            inst[k] = conv(inst[k])
    return data


def generate_filtered(seed: int = 20261002) -> Dict:
    """Auxiliary set (different seed) -> train shallow attackers -> adversarially filtered benchmark."""
    from research.benchmark.adversarial import AUX_SEED, train_scorer
    # concurrency attackers need more training data than 160 instances to transfer
    aux = generate(AUX_SEED, sizes={"struct_mutex": 240, "struct_semaphore": 240})
    scorer = train_scorer(aux["instances"])
    aux_keys = {json.dumps(i["problem"], sort_keys=True) for i in aux["instances"]}
    data = generate(seed, scorer=scorer, exclude_problems=aux_keys)
    data["metadata"]["aux_seed"] = AUX_SEED
    return data


if __name__ == "__main__":
    d = generate_filtered()
    save(d, "research/benchmark/benchmark_v2.json")
    print(json.dumps(d["metadata"], indent=1))
