"""
Concurrency transition system: threads with mutexes, counting semaphores and
shared-variable writes. Enumerates, counts and samples complete interleavings.

Problem: {"threads": {"T1": [["lock","m"], ["write","x"], ["unlock","m"]], ...},
          "semaphores": {"s": 0}}

Rules: per-thread program order; lock(m) needs m free (mutexes are NOT
re-entrant -- AGY's version let the owner re-acquire); unlock(m) needs the
caller to own m; wait(s) needs s > 0 and decrements; signal(s) increments;
write(x) is always enabled. Paths that deadlock are not members of V(P).

Two interleavings that differ only in the order of independent operations
are Mazurkiewicz-equivalent ("superficial reordering"). `trace_class` gives
the class key, so the benchmark can insist that the alternative reference R2
differs from R1 in the order of at least one dependent pair.
"""

import random
from functools import lru_cache
from typing import Dict, Iterator, List, Sequence, Tuple

from research.simulator.traces import Event


class Interleaver:
    def __init__(self, problem: Dict):
        self.threads = list(problem["threads"].keys())
        self.prog = {t: [tuple(op) for op in ops] for t, ops in problem["threads"].items()}
        self.sem_names = sorted(problem.get("semaphores", {}))
        self.sem_init = tuple(problem.get("semaphores", {})[s] for s in self.sem_names)
        self._count = lru_cache(maxsize=None)(self._count_impl)

    def initial_state(self):
        return (tuple(0 for _ in self.threads), (), self.sem_init)

    def successors(self, state) -> List[Tuple[Event, tuple]]:
        ptrs, locks, sems = state
        owners = dict(locks)
        out = []
        for i, t in enumerate(self.threads):
            if ptrs[i] >= len(self.prog[t]):
                continue
            op, arg = self.prog[t][ptrs[i]]
            new_owners, new_sems = dict(owners), list(sems)
            if op == "lock":
                if arg in owners:
                    continue
                new_owners[arg] = t
            elif op == "unlock":
                if owners.get(arg) != t:
                    continue
                del new_owners[arg]
            elif op == "wait":
                k = self.sem_names.index(arg)
                if sems[k] <= 0:
                    continue
                new_sems[k] -= 1
            elif op == "signal":
                new_sems[self.sem_names.index(arg)] += 1
            elif op != "write":
                raise ValueError(op)
            new_ptrs = list(ptrs)
            new_ptrs[i] += 1
            out.append(((t, op, arg), (tuple(new_ptrs), tuple(sorted(new_owners.items())), tuple(new_sems))))
        return out

    def _finished(self, state) -> bool:
        return all(p >= len(self.prog[t]) for p, t in zip(state[0], self.threads))

    def _count_impl(self, state) -> int:
        succ = self.successors(state)
        if not succ:
            return 1 if self._finished(state) else 0
        return sum(self._count(nxt) for _, nxt in succ)

    def count_paths(self) -> int:
        return self._count(self.initial_state())

    def canonical(self) -> Tuple[Event, ...]:
        """Lowest-index enabled thread first, avoiding deadlocking choices."""
        state, trace = self.initial_state(), []
        while True:
            succ = [(e, s) for e, s in self.successors(state) if self._count(s) > 0]
            if not succ:
                return tuple(trace)
            e, state = succ[0]
            trace.append(e)

    def sample(self, rng: random.Random) -> Tuple[Event, ...]:
        state, trace = self.initial_state(), []
        while True:
            succ = [(e, s) for e, s in self.successors(state) if self._count(s) > 0]
            if not succ:
                return tuple(trace)
            e, state = rng.choices(succ, weights=[self._count(s) for _, s in succ])[0]
            trace.append(e)

    def accepts(self, trace: Sequence[Event]) -> bool:
        """Membership in V(P) by following this module's successor relation."""
        state = self.initial_state()
        for ev in trace:
            nxt = [s for e, s in self.successors(state) if e == tuple(ev)]
            if not nxt:
                return False
            state = nxt[0]
        return self._finished(state)

    def enumerate(self, limit: int = 200_000) -> Iterator[Tuple[Event, ...]]:
        n = 0
        stack = [(self.initial_state(), ())]
        while stack:
            state, trace = stack.pop()
            succ = self.successors(state)
            if not succ:
                if self._finished(state):
                    n += 1
                    if n > limit:
                        raise RuntimeError(f"|V(P)| exceeds enumeration limit {limit}")
                    yield trace
                continue
            for e, nxt in reversed(succ):
                stack.append((nxt, trace + (e,)))

    def random_interleaving(self, rng: random.Random) -> Tuple[Event, ...]:
        """Program-order-preserving merge that ignores synchronisation.
        Used to build invalid traces whose per-thread projections are correct."""
        ptrs = {t: 0 for t in self.threads}
        out = []
        while True:
            live = [t for t in self.threads if ptrs[t] < len(self.prog[t])]
            if not live:
                return tuple(out)
            weights = [len(self.prog[t]) - ptrs[t] for t in live]
            t = rng.choices(live, weights=weights)[0]
            op, arg = self.prog[t][ptrs[t]]
            out.append((t, op, arg))
            ptrs[t] += 1


def trace_class(trace: Sequence[Event]) -> Tuple:
    """Mazurkiewicz class key: for every shared object, the order of threads
    touching it. Program order is fixed, so this determines the class."""
    per_obj: Dict[str, List[str]] = {}
    for t, _, arg in trace:
        per_obj.setdefault(arg, []).append(t)
    return tuple(sorted((k, tuple(v)) for k, v in per_obj.items()))


def last_writer(trace: Sequence[Event]) -> Dict[str, str]:
    out = {}
    for t, op, arg in trace:
        if op == "write":
            out[arg] = t
    return out
