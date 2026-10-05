"""
Per-family semantics for the SSR pilot: parsing, rule replay, task constraints,
observations, enumeration, and relaxed-rule samplers.

Families
  scheduling  non-preemptive FCFS/SJF/PRIORITY and RR(q); steps are (pid, start, end)
  sync        mutex / semaphore interleavings; steps are (thread, op, arg)
  banker      Banker's safe sequences; steps are process ids in completion order

Nothing here reads a reference trace. Scheduling and sync replay delegate to
research/simulator/validators.py (written separately from the enumerators);
Banker's replay is new. See docs/research/SSR_PILOT_PREREG.md §7.3.
"""

import itertools
import random
import re
from typing import Dict, List, Optional, Sequence, Tuple

from research.simulator.concurrency_interleaver import Interleaver
from research.simulator.cpu_scheduler import Scheduler, waiting_times
from research.simulator.traces import IDLE, format_events, format_schedule, levenshtein, normalize_schedule
from research.simulator.validators import validate_events, validate_schedule

ENUM_CAP = 20000

_SEG = re.compile(r"([A-Za-z_][\w\-]*)\s*[:(\[]?\s*(\d+)\s*(?:-|–|to|,)\s*(\d+)\s*[)\]]?")
_ROW3 = re.compile(r"\|\s*([A-Za-z_][\w\-]*)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|")
_EVT = re.compile(r"([A-Za-z_][\w\-]*)[\s:|]+(lock|unlock|wait|signal|write)\s*\(\s*([\w\-]+)\s*\)", re.I)
_TOK = re.compile(r"[A-Za-z_][\w\-]*")
_STOP = {"trace", "then", "and", "order", "process", "processes", "step", "completion", "safe", "sequence"}


# ------------------------------------------------------------------ world access

def problem(world: Dict) -> Dict:
    if world["family"] == "scheduling":
        return {"domain": "scheduling", "policy": world["policy"], "processes": world["processes"],
                "quantum": world.get("quantum", 2)}
    if world["family"] == "sync":
        return {"domain": "concurrency", "threads": world["threads"], "semaphores": world.get("semaphores", {})}
    raise ValueError(world["family"])


def entity_names(world: Dict) -> List[str]:
    """Every name that can appear in a prompt or trace (renamed in variant v1)."""
    f = world["family"]
    if f in ("scheduling", "banker"):
        return [p["pid"] for p in world["processes"]]
    objs = []
    for ops in world["threads"].values():
        for _, arg in ops:
            if arg not in objs:
                objs.append(arg)
    for s in world.get("semaphores", {}):
        if s not in objs:
            objs.append(s)
    return list(world["threads"]) + objs


def identity_map(world: Dict) -> Dict[str, str]:
    return {n: n for n in entity_names(world)}


def system(world: Dict):
    if world["family"] == "scheduling":
        return Scheduler(world["processes"], world["policy"], world.get("quantum", 2))
    if world["family"] == "sync":
        return Interleaver(problem(world))
    raise ValueError(world["family"])


# ------------------------------------------------------------------ parsing

def _region(text: str) -> Tuple[str, bool]:
    ends = [m.end() for m in re.finditer(r"TRACE\s*:", text, re.I)]
    return (text[ends[-1]:], True) if ends else (text, False)


def parse(world: Dict, text: str, shown2canon: Optional[Dict[str, str]] = None):
    """-> (steps | None, info). `shown2canon` maps names as shown in the prompt back to the world's names."""
    s2c = shown2canon or identity_map(world)
    region, marker = _region(text)
    unknown: List[str] = []
    f = world["family"]
    if f == "scheduling":
        found = _ROW3.findall(region) or _SEG.findall(region)
        steps = []
        for name, a, b in found:
            nm = IDLE if name.upper() == IDLE else s2c.get(name)
            if nm is None:
                unknown.append(name)
            else:
                steps.append((nm, int(a), int(b)))
    elif f == "sync":
        steps = []
        for t, op, a in _EVT.findall(region):
            ct, ca = s2c.get(t), s2c.get(a)
            if ct is None or ca is None:
                unknown.append(f"{t}/{a}")
            else:
                steps.append((ct, op.lower(), ca))
    else:
        steps = []
        for tk in _TOK.findall(region):
            if tk in s2c:
                steps.append(s2c[tk])
            elif tk.lower() not in _STOP:
                unknown.append(tk)
    return (tuple(steps) if steps else None), {"unknown": unknown, "marker": marker}


# ------------------------------------------------------------------ rules, constraints

def rules_check(world: Dict, steps: Sequence) -> Tuple[bool, str]:
    f = world["family"]
    if f == "scheduling":
        return validate_schedule(problem(world), steps)
    if f == "sync":
        return validate_events(problem(world), steps)
    procs = {p["pid"]: p for p in world["processes"]}
    work, done = list(world["available"]), set()
    for p in steps:
        if p in done:
            return False, "repeated_process"
        need = [m - a for m, a in zip(procs[p]["max"], procs[p]["alloc"])]
        if any(n > w for n, w in zip(need, work)):
            return False, "need_exceeds_work"
        work = [w + a for w, a in zip(work, procs[p]["alloc"])]
        done.add(p)
    return (True, "ok") if len(done) == len(procs) else (False, "incomplete")


def _holds(world: Dict, c: Dict, steps: Sequence) -> bool:
    try:
        t, f = c["type"], world["family"]
        if t == "deadline":
            return max(e for p, s, e in steps if p == c["pid"]) <= c["by"]
        if t == "precedence":
            return max(e for p, s, e in steps if p == c["first"]) <= min(s for p, s, e in steps if p == c["second"])
        if t == "before" and f == "sync":
            ev = [tuple(e) for e in steps]
            return ev.index(tuple(c["a"])) < ev.index(tuple(c["b"]))
        if t == "before" and f == "banker":
            return list(steps).index(c["a"]) < list(steps).index(c["b"])
    except ValueError:
        return False
    raise ValueError(c)


def violated_constraints(world: Dict, steps: Sequence) -> List[Dict]:
    return [c for c in world.get("constraints", []) if not _holds(world, c, steps)]


# ------------------------------------------------------------------ observation, quality, distance

def observe(world: Dict, steps: Sequence):
    """World-declared observable outcome (defined for any parsed steps, valid or not)."""
    f = world["family"]
    if f == "scheduling":
        pids = [p["pid"] for p in world["processes"]]
        return tuple((p, max([e for q, s, e in steps if q == p], default=-1)) for p in sorted(pids))
    if f == "sync":
        last = {}
        for t, op, a in steps:
            if op == "write":
                last[a] = t
        return tuple(sorted(last.items()))
    procs = {p["pid"]: p for p in world["processes"]}
    done = sorted(set(steps))
    work = [w + sum(procs[p]["alloc"][j] for p in done) for j, w in enumerate(world["available"])]
    return (tuple(done), tuple(work))


def quality(world: Dict, steps: Sequence) -> Optional[float]:
    """Mean waiting time for a complete valid schedule; undefined (None) elsewhere."""
    if world["family"] != "scheduling":
        return None
    w = waiting_times(world["processes"], steps)
    return sum(w.values()) / len(w)


def tokens(world: Dict, steps: Sequence) -> List:
    return [p for p, _, _ in steps] if world["family"] == "scheduling" else list(steps)


def distance(world: Dict, a: Sequence, b: Sequence) -> int:
    return levenshtein(tokens(world, a), tokens(world, b))


def profile(world: Dict, steps: Sequence, ref: Sequence) -> Tuple[float, float, float, float]:
    """Similarity of a trace to the reference: normalised edit distance, first-divergence position
    (fraction of length), and whether first / last step agree. Used to match invalid traces to valid ones."""
    a, b = tokens(world, steps), tokens(world, ref)
    fd = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return (levenshtein(a, b) / max(len(a), len(b), 1), fd / max(len(a), 1),
            float(a[:1] == b[:1]), float(a[-1:] == b[-1:]))


# ------------------------------------------------------------------ enumeration

def _banker_enum(world: Dict):
    procs = [p["pid"] for p in world["processes"]]
    for perm in itertools.permutations(procs):
        if rules_check(world, perm)[0]:
            yield perm


def enumerate_rules(world: Dict) -> List[Tuple]:
    """All rule-valid traces, canonical order first."""
    if world["family"] == "banker":
        return list(_banker_enum(world))
    return list(system(world).enumerate(limit=ENUM_CAP))


# ------------------------------------------------------------------ relaxed-rule samplers

def relaxations(world: Dict) -> List[str]:
    f = world["family"]
    if f == "scheduling":
        if world["policy"] == "RR":
            return ["ignore_head", "ignore_quantum"]
        return ["ignore_arrival", "ignore_policy", "wrong_burst"]
    if f == "sync":
        r = []
        if any(op == "lock" for ops in world["threads"].values() for op, _ in ops):
            r.append("ignore_mutex")
        if world.get("semaphores"):
            r.append("ignore_sem")
        return r
    return ["ignore_need", "skip_one_check"]


def relaxed_sample(world: Dict, relax: str, rng: random.Random):
    f = world["family"]
    if f == "scheduling":
        return _relaxed_rr(world, relax, rng) if world["policy"] == "RR" else _relaxed_np(world, relax, rng)
    if f == "sync":
        return _relaxed_sync(world, relax, rng)
    return _relaxed_banker(world, relax, rng)


def _relaxed_np(world, relax, rng):
    procs = {p["pid"]: p for p in world["processes"]}
    key = {"FCFS": "arrival", "SJF": "burst", "PRIORITY": "priority"}[world["policy"]]
    t, left, segs = 0, set(procs), []
    bad = rng.choice(sorted(procs))  # wrong_burst: this process runs for the wrong length
    while left:
        ready = [p for p in left if relax == "ignore_arrival" or procs[p]["arrival"] <= t]
        if not ready:
            nxt = min(procs[p]["arrival"] for p in left)
            segs.append((IDLE, t, nxt))
            t = nxt
            continue
        if relax == "ignore_policy":
            cand = ready
        else:
            best = min(procs[p][key] for p in ready)
            cand = [p for p in ready if procs[p][key] == best]
        pid = rng.choice(sorted(cand))
        run = procs[pid]["burst"]
        if relax == "wrong_burst" and pid == bad:
            run = run + rng.choice([-1, 1]) if run > 1 else run + 1
        segs.append((pid, t, t + run))
        t += run
        left.discard(pid)
    return normalize_schedule(segs)


def _relaxed_rr(world, relax, rng):
    procs = {p["pid"]: p for p in world["processes"]}
    q = world.get("quantum", 2)
    rem = {p: procs[p]["burst"] for p in procs}
    t, segs = 0, []
    while any(rem.values()):
        arrived = [p for p in procs if rem[p] > 0 and procs[p]["arrival"] <= t]
        if not arrived:
            nxt = min(procs[p]["arrival"] for p in procs if rem[p] > 0)
            segs.append((IDLE, t, nxt))
            t = nxt
            continue
        if relax == "ignore_head":
            pid = rng.choice(sorted(arrived))
            run = min(q, rem[pid])
        else:  # ignore_quantum: FIFO by arrival, run to completion
            pid = sorted(arrived, key=lambda p: (procs[p]["arrival"], p))[0]
            run = rem[pid]
        segs.append((pid, t, t + run))
        t += run
        rem[pid] -= run
    return normalize_schedule(segs)


def _relaxed_sync(world, relax, rng):
    prog = {t: [tuple(o) for o in ops] for t, ops in world["threads"].items()}
    pc = {t: 0 for t in prog}
    owner, sems, out = {}, dict(world.get("semaphores", {})), []
    while any(pc[t] < len(prog[t]) for t in prog):
        enabled = []
        for t in prog:
            if pc[t] >= len(prog[t]):
                continue
            op, a = prog[t][pc[t]]
            if op == "lock" and a in owner and relax != "ignore_mutex":
                continue
            if op == "unlock" and owner.get(a) != t and relax != "ignore_mutex":
                continue
            if op == "wait" and sems.get(a, 0) <= 0 and relax != "ignore_sem":
                continue
            enabled.append(t)
        if not enabled:
            return None
        t = rng.choice(enabled)
        op, a = prog[t][pc[t]]
        if op == "lock":
            owner[a] = t
        elif op == "unlock":
            owner.pop(a, None)
        elif op == "wait":
            sems[a] = sems.get(a, 0) - 1
        elif op == "signal":
            sems[a] = sems.get(a, 0) + 1
        pc[t] += 1
        out.append((t, op, a))
    return tuple(out)


def _relaxed_banker(world, relax, rng):
    procs = {p["pid"]: p for p in world["processes"]}
    names = list(procs)
    if relax == "ignore_need":
        rng.shuffle(names)
        return tuple(names)
    work, left, out = list(world["available"]), list(names), []
    skip_at = rng.randrange(len(names))
    while left:
        ok = [p for p in left if all(m - a <= w for m, a, w in zip(procs[p]["max"], procs[p]["alloc"], work))]
        pick = rng.choice(left) if (len(out) == skip_at or not ok) else rng.choice(ok)
        left.remove(pick)
        out.append(pick)
        work = [w + a for w, a in zip(work, procs[pick]["alloc"])]
    return tuple(out)


# ------------------------------------------------------------------ formatting

def _m(c2s: Optional[Dict[str, str]], x: str) -> str:
    return c2s.get(x, x) if c2s else x


def format_steps(world: Dict, steps: Sequence, style: str = "arrow", c2s: Optional[Dict[str, str]] = None) -> str:
    f = world["family"]
    if f == "scheduling":
        return format_schedule([(_m(c2s, p), s, e) for p, s, e in steps], style)
    if f == "sync":
        return format_events([(_m(c2s, t), op, _m(c2s, a)) for t, op, a in steps], style)
    names = [_m(c2s, p) for p in steps]
    if style == "table":
        return "\n".join(["| Order | Process |", "|---|---|"] + [f"| {i + 1} | {n} |" for i, n in enumerate(names)])
    return ", ".join(names)
