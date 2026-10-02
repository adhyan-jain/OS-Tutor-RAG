"""
CPU scheduling transition system: enumerate, count and sample V(P).

Policies
--------
FCFS, SJF, PRIORITY are NON-preemptive: once dispatched, a process runs its
whole burst. The only nondeterminism is the tie among ready processes with the
same key (arrival / burst / priority; lower priority number = more urgent).

RR(q): preemptive with quantum q. The nondeterminism is the textbook
ambiguity about queue order at a single instant: processes arriving at the
same time may enqueue in any order, and a process preempted at time t may be
re-queued before or after the processes that arrive at exactly t.

AGY's version re-scheduled every time unit, which made "FCFS" preemptive and
inflated |V(P)| to 25,200 on four processes. This module works on whole bursts
(Gantt segments) and is the *generator* side; `validators.py` is an
independent checker that never calls into this file.

State spaces are small enough to memoise counts, which gives exact |V(P)| and
uniform sampling from V(P) without materialising it.
"""

import itertools
import random
from functools import lru_cache
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from research.simulator.traces import IDLE, Segment, normalize_schedule

POLICIES = ("FCFS", "SJF", "PRIORITY", "RR")


def make_process(pid: str, arrival: int, burst: int, priority: int = 0) -> Dict:
    return {"pid": pid, "arrival": arrival, "burst": burst, "priority": priority}


class Scheduler:
    def __init__(self, processes: Sequence[Dict], policy: str, quantum: int = 2):
        if policy not in POLICIES:
            raise ValueError(policy)
        self.procs = {p["pid"]: p for p in processes}
        self.order = [p["pid"] for p in processes]  # canonical tie-break order
        self.idx = {pid: i for i, pid in enumerate(self.order)}
        self.policy = policy
        self.q = quantum
        self._count = lru_cache(maxsize=None)(self._count_impl)

    # ---------- successor relation ----------

    def initial_states(self) -> List[Tuple[Tuple[Segment, ...], tuple]]:
        if self.policy != "RR":
            return [((), (0, frozenset(self.order)))]
        rem = tuple(sorted((pid, self.procs[pid]["burst"]) for pid in self.order))
        at0 = self._sorted([pid for pid in self.order if self.procs[pid]["arrival"] == 0])
        return [((), (0, perm, rem)) for perm in itertools.permutations(at0)]

    def successors(self, state) -> List[Tuple[Tuple[Segment, ...], tuple]]:
        """(segments emitted, next state) pairs, canonical choice first."""
        return self._succ_np(state) if self.policy != "RR" else self._succ_rr(state)

    def _sorted(self, pids):
        return sorted(pids, key=lambda p: self.idx[p])

    def _key(self, pid):
        p = self.procs[pid]
        return {"FCFS": p["arrival"], "SJF": p["burst"], "PRIORITY": p["priority"]}[self.policy]

    def _succ_np(self, state):
        t, remaining = state
        if not remaining:
            return []
        ready = [pid for pid in remaining if self.procs[pid]["arrival"] <= t]
        if not ready:
            nxt = min(self.procs[pid]["arrival"] for pid in remaining)
            return [(((IDLE, t, nxt),), (nxt, remaining))]
        best = min(self._key(pid) for pid in ready)
        out = []
        for pid in self._sorted([p for p in ready if self._key(p) == best]):
            end = t + self.procs[pid]["burst"]
            out.append((((pid, t, end),), (end, remaining - {pid})))
        return out

    def _succ_rr(self, state):
        t, queue, rem = state
        remd = dict(rem)
        unfinished = [pid for pid, r in remd.items() if r > 0]
        if not unfinished:
            return []
        if not queue:
            waiting = [pid for pid in unfinished if self.procs[pid]["arrival"] > t]
            nxt = min(self.procs[pid]["arrival"] for pid in waiting)
            arrivals = self._sorted([p for p in waiting if self.procs[p]["arrival"] == nxt])
            return [(((IDLE, t, nxt),), (nxt, perm, rem)) for perm in itertools.permutations(arrivals)]
        head = queue[0]
        run = min(self.q, remd[head])
        end = t + run
        remd[head] -= run
        new_rem = tuple(sorted(remd.items()))
        during_times = sorted({self.procs[p]["arrival"] for p in unfinished
                               if t < self.procs[p]["arrival"] < end})
        during_groups = [self._sorted([p for p in unfinished if self.procs[p]["arrival"] == a])
                         for a in during_times]
        at_end = self._sorted([p for p in unfinished if self.procs[p]["arrival"] == end])
        preempted = [head] if remd[head] > 0 else []
        seg = ((head, t, end),)
        out = []
        for during in itertools.product(*[list(itertools.permutations(g)) for g in during_groups]):
            during_flat = tuple(p for grp in during for p in grp)
            for e_perm in itertools.permutations(at_end):
                tails = [e_perm + tuple(preempted)]  # canonical: arrivals before re-queued process
                if preempted and e_perm:
                    tails.append(tuple(preempted) + e_perm)
                for tail in tails:
                    out.append((seg, (end, queue[1:] + during_flat + tail, new_rem)))
        return out

    # ---------- counting, sampling, enumeration ----------

    def _count_impl(self, state) -> int:
        succ = self.successors(state)
        if not succ:
            return 1
        return sum(self._count(nxt) for _, nxt in succ)

    def count_paths(self) -> int:
        return sum(self._count(s) for _, s in self.initial_states())

    def canonical(self) -> Tuple[Segment, ...]:
        segs, state = self.initial_states()[0]
        segs = list(segs)
        while True:
            succ = self.successors(state)
            if not succ:
                return normalize_schedule(segs)
            emitted, state = succ[0]
            segs.extend(emitted)

    def sample(self, rng: random.Random) -> Tuple[Segment, ...]:
        """Uniform over execution *paths*. For FCFS/SJF/PRIORITY paths and traces
        are in bijection; for RR the test suite checks the bijection on every
        generated instance before the instance is admitted."""
        inits = self.initial_states()
        _, state = rng.choices(inits, weights=[self._count(s) for _, s in inits])[0]
        segs: List[Segment] = []
        while True:
            succ = self.successors(state)
            if not succ:
                return normalize_schedule(segs)
            weights = [self._count(nxt) for _, nxt in succ]
            emitted, state = rng.choices(succ, weights=weights)[0]
            segs.extend(emitted)

    def accepts(self, trace: Sequence[Segment]) -> bool:
        """Membership in V(P) using only this module's successor relation:
        depth-first search pruned to paths whose normalised prefix fits `trace`."""
        target = normalize_schedule(trace)

        def fits(segs) -> bool:
            norm = normalize_schedule(segs)
            if len(norm) > len(target):
                return False
            if norm[:-1] != target[:len(norm) - 1]:
                return False
            if not norm:
                return True
            last, want = norm[-1], target[len(norm) - 1]
            return last[0] == want[0] and last[1] == want[1] and last[2] <= want[2]

        def walk(state, segs) -> bool:
            succ = self.successors(state)
            if not succ:
                return normalize_schedule(segs) == target
            for emitted, nxt in succ:
                ext = segs + list(emitted)
                if fits(ext) and walk(nxt, ext):
                    return True
            return False

        return any(walk(s, list(e)) for e, s in self.initial_states())

    def enumerate(self, limit: int = 200_000) -> Iterator[Tuple[Segment, ...]]:
        """Distinct traces of V(P), deduplicated after normalisation."""
        seen = set()

        def walk(state, segs):
            succ = self.successors(state)
            if not succ:
                tr = normalize_schedule(segs)
                if tr not in seen:
                    seen.add(tr)
                    yield tr
                return
            for emitted, nxt in succ:
                yield from walk(nxt, segs + list(emitted))

        n = 0
        for emitted, s in self.initial_states():
            for tr in walk(s, list(emitted)):
                n += 1
                if n > limit:
                    raise RuntimeError(f"|V(P)| exceeds enumeration limit {limit}")
                yield tr


def waiting_times(processes: Sequence[Dict], trace: Sequence[Segment]) -> Dict[str, int]:
    """Completion - arrival - burst per process (standard textbook definition)."""
    finish = {}
    for pid, _, end in trace:
        if pid != IDLE:
            finish[pid] = end
    return {p["pid"]: finish.get(p["pid"], -1) - p["arrival"] - p["burst"] for p in processes}
