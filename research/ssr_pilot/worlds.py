"""
The 24 pilot worlds: 8 scheduling, 8 synchronisation, 8 Banker's.

Each world is a declarative spec (initial state, rules, constraints, goal
implied by the family). Worlds are specified FIRST; every trace in the pilot is
derived afterwards from their semantics (bank.py). Textbook cases sit at
index 0 of each family (plus a textbook RR at scheduling index 6); the rest are
drawn from seeded generators. Every second world carries one task constraint
that excludes part of the rule-valid set, chosen by search so that it bites.
"""

import hashlib
import json
import math
import os
import random
from typing import Dict, List

from research.ssr_pilot import families as F

SEED = 20261003
WORLD_DIR = "research/ssr_pilot/worlds"

SCHED_PLAN = ["fcfs", "fcfs", "sjf", "sjf", "priority", "priority", "rr", "rr"]
SYNC_PLAN = ["mutex", "mutex", "mutex", "mutex", "semaphore", "semaphore", "semaphore", "semaphore"]
CONSTRAINED = {1, 3, 5, 7}  # zero-based index within the family


# ---------------------------------------------------------------- scheduling

def _sched_textbook(structure: str) -> Dict:
    procs = [{"pid": "P1", "arrival": 0, "burst": 24, "priority": 3},
             {"pid": "P2", "arrival": 0, "burst": 3, "priority": 3},
             {"pid": "P3", "arrival": 0, "burst": 3, "priority": 3}]
    w = {"family": "scheduling", "structure": structure, "policy": structure.upper(), "processes": procs,
         "constraints": [], "textbook": "Silberschatz & Galvin: P1=24, P2=3, P3=3, all arrive at 0"}
    if structure == "rr":
        w["quantum"] = 4
    return w


def _rand_sched(rng: random.Random, structure: str) -> Dict:
    rr = structure == "rr"
    for _ in range(2000):
        n = rng.randint(3, 4) if rr else rng.randint(3, 5)
        procs = [{"pid": f"P{i + 1}", "arrival": rng.choice([0, 0, 1, 2]),
                  "burst": rng.randint(1, 3 if rr else 4), "priority": rng.randint(1, 3)} for i in range(n)]
        w = {"family": "scheduling", "structure": structure, "policy": structure.upper(), "processes": procs,
             "constraints": []}
        if rr:
            w["quantum"] = rng.choice([1, 2])
        if 3 <= len(F.enumerate_rules(w)) <= 400:
            return w
    raise RuntimeError("no scheduling world found")


# ---------------------------------------------------------------- synchronisation

def _mutex_textbook() -> Dict:
    sec = [["lock", "m"], ["write", "x"], ["unlock", "m"]]
    return {"family": "sync", "structure": "mutex", "threads": {"T1": sec, "T2": sec, "T3": sec},
            "semaphores": {}, "constraints": [], "textbook": "three threads, one mutex, one shared counter"}


def _rand_mutex(rng: random.Random) -> Dict:
    for _ in range(2000):
        threads = {}
        for i in range(rng.randint(2, 3)):
            ops = []
            for _ in range(rng.randint(1, 2)):
                if rng.random() < 0.7:
                    m = rng.choice(["m1", "m2"])
                    ops += [["lock", m], ["write", rng.choice(["x", "y"])], ["unlock", m]]
                else:
                    ops.append(["write", rng.choice(["x", "y", "z"])])
            threads[f"T{i + 1}"] = ops
        w = {"family": "sync", "structure": "mutex", "threads": threads, "semaphores": {}, "constraints": []}
        users = {}  # mutex -> threads that lock it; it must be contended or the lock is decorative
        for t, ops in threads.items():
            for o in ops:
                if o[0] == "lock":
                    users.setdefault(o[1], set()).add(t)
        if any(len(v) >= 2 for v in users.values()) and 3 <= len(F.enumerate_rules(w)) <= 3000:
            return w
    raise RuntimeError("no mutex world found")


def _rand_semaphore(rng: random.Random) -> Dict:
    var = lambda: rng.choice(["x", "y", "buf", "out"])
    for _ in range(2000):
        shape = rng.choice(["prodcons", "chain", "pool"])
        if shape == "prodcons":
            k = rng.randint(1, 2)
            threads = {"T1": [o for _ in range(k) for o in (["write", var()], ["signal", "full"])],
                       "T2": [o for _ in range(k) for o in (["wait", "full"], ["write", var()])]}
            sems = {"full": 0}
        elif shape == "chain":
            n = rng.randint(2, 3)
            threads = {}
            for i in range(n):
                ops = [["write", var()]] if rng.random() < 0.6 else []
                if i > 0:
                    ops.append(["wait", f"s{i}"])
                ops.append(["write", var()])
                if i < n - 1:
                    ops.append(["signal", f"s{i + 1}"])
                threads[f"T{i + 1}"] = ops
            threads[f"T{n + 1}"] = [["write", var()]]
            sems = {f"s{i}": 0 for i in range(1, n)}
        else:
            n = rng.randint(2, 3)
            threads = {f"T{i + 1}": [["wait", "slots"], ["write", var()], ["signal", "slots"]] for i in range(n)}
            sems = {"slots": rng.randint(1, n - 1)}
        w = {"family": "sync", "structure": "semaphore", "threads": threads, "semaphores": sems, "constraints": []}
        if 3 <= len(F.enumerate_rules(w)) <= 3000:
            return w
    raise RuntimeError("no semaphore world found")


# ---------------------------------------------------------------- Banker's

def _banker_textbook() -> Dict:
    mx = {"P0": [7, 5, 3], "P1": [3, 2, 2], "P2": [9, 0, 2], "P3": [2, 2, 2], "P4": [4, 3, 3]}
    al = {"P0": [0, 1, 0], "P1": [2, 0, 0], "P2": [3, 0, 2], "P3": [2, 1, 1], "P4": [0, 0, 2]}
    return {"family": "banker", "structure": "banker", "resources": ["A", "B", "C"], "available": [3, 3, 2],
            "processes": [{"pid": p, "max": mx[p], "alloc": al[p]} for p in mx], "constraints": [],
            "textbook": "Silberschatz & Galvin Banker's example (5 processes, 3 resource types)"}


def _rand_banker(rng: random.Random) -> Dict:
    for _ in range(5000):
        n = rng.choice([4, 5, 5, 6])
        procs = []
        for i in range(n):
            alloc = [rng.randint(0, 3) for _ in range(3)]
            procs.append({"pid": f"P{i}", "alloc": alloc, "max": [a + rng.randint(0, 3) for a in alloc]})
        w = {"family": "banker", "structure": "banker", "resources": ["A", "B", "C"],
             "available": [rng.randint(0, 3) for _ in range(3)], "processes": procs, "constraints": []}
        if 3 <= len(F.enumerate_rules(w)) <= min(120, math.factorial(n) - 1):  # some orderings must be unsafe
            return w
    raise RuntimeError("no banker world found")


# ---------------------------------------------------------------- constraints

def _candidates(world: Dict, V: List) -> List[Dict]:
    f = world["family"]
    if f == "scheduling":
        pids = [p["pid"] for p in world["processes"]]
        out = [{"type": "precedence", "first": a, "second": b} for a in pids for b in pids if a != b]
        for p in pids:
            for by in sorted({max(e for q, s, e in t if q == p) for t in V}):
                out.append({"type": "deadline", "pid": p, "by": by})
        return out
    if f == "sync":
        counts = {}
        for t, ops in world["threads"].items():
            for op, a in ops:
                counts[(t, op, a)] = counts.get((t, op, a), 0) + 1
        ev = [list(e) for e, c in counts.items() if c == 1 and e[1] in ("write", "lock")]
        return [{"type": "before", "a": a, "b": b} for a in ev for b in ev if a[0] != b[0]]
    pids = [p["pid"] for p in world["processes"]]
    return [{"type": "before", "a": a, "b": b} for a in pids for b in pids if a != b]


def add_constraint(world: Dict, rng: random.Random) -> bool:
    V = F.enumerate_rules(world)
    keep = []
    for c in _candidates(world, V):
        sat = sum(F._holds(world, c, t) for t in V)
        if sat >= 2 and 0.2 <= sat / len(V) <= 0.8:
            keep.append(c)
    if not keep:
        return False
    world["constraints"] = [rng.choice(keep)]
    return True


# ---------------------------------------------------------------- build / io

def _regen(w: Dict, rng: random.Random) -> Dict:
    f, s = w["family"], w["structure"]
    if f == "scheduling":
        return _rand_sched(rng, s)
    if f == "sync":
        return _rand_mutex(rng) if s == "mutex" else _rand_semaphore(rng)
    return _rand_banker(rng)


def build_worlds(seed: int = SEED) -> List[Dict]:
    rng = random.Random(seed)
    worlds: List[Dict] = []

    def finish(w: Dict, prefix: str, i: int) -> Dict:
        if i in CONSTRAINED:
            while not add_constraint(w, rng):
                w = _regen(w, rng)
        w["id"] = f"{prefix}_{i + 1:02d}"
        return w

    for i, s in enumerate(SCHED_PLAN):
        w = _sched_textbook("fcfs") if i == 0 else _sched_textbook("rr") if i == 6 else _rand_sched(rng, s)
        worlds.append(finish(w, "sched", i))
    for i, s in enumerate(SYNC_PLAN):
        w = _mutex_textbook() if i == 0 else _rand_mutex(rng) if s == "mutex" else _rand_semaphore(rng)
        worlds.append(finish(w, "sync", i))
    for i in range(8):
        worlds.append(finish(_banker_textbook() if i == 0 else _rand_banker(rng), "bank", i))
    return worlds


def save_worlds(worlds: List[Dict], directory: str = WORLD_DIR) -> str:
    os.makedirs(directory, exist_ok=True)
    for w in worlds:
        with open(f"{directory}/{w['id']}.json", "w") as f:
            json.dump(w, f, indent=1, sort_keys=True)
    digest = hashlib.sha256(json.dumps(worlds, sort_keys=True).encode()).hexdigest()
    with open(f"{directory}/_index.json", "w") as f:
        json.dump({"seed": SEED, "n": len(worlds), "ids": [w["id"] for w in worlds], "sha256": digest}, f, indent=1)
    return digest


def load_worlds(directory: str = WORLD_DIR) -> List[Dict]:
    ids = json.load(open(f"{directory}/_index.json"))["ids"]
    return [json.load(open(f"{directory}/{i}.json")) for i in ids]


if __name__ == "__main__":
    ws = build_worlds()
    print(save_worlds(ws))
    for w in ws:
        V = F.enumerate_rules(w)
        task = [t for t in V if not F.violated_constraints(w, t)]
        print(w["id"], w["structure"], "|V_rules|", len(V), "|V_task|", len(task), w["constraints"])
