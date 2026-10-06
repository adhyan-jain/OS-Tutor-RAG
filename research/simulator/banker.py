"""
Independent Banker's Algorithm safe-sequence solver and transition system.

Provides:
  BankerSolver   Transition-system representation of Banker's deadlock avoidance
                 with memoized path counting, canonical solving, uniform path
                 sampling, safe-sequence enumeration, and membership acceptance.
"""

from functools import lru_cache
import random
from typing import Dict, List, Optional, Sequence, Tuple


class BankerSolver:
    """
    Transition system for Banker's Algorithm.

    State: (available_tuple, remaining_pids_tuple)
    Transitions: At any state, any process whose Need <= Work can finish and release its Allocation.
    """

    def __init__(self, processes: Sequence[Dict], available: Sequence[int]):
        self.raw_processes = list(processes)
        self.pids: Tuple[str, ...] = tuple(p["pid"] for p in processes)
        self.procs: Dict[str, Dict] = {p["pid"]: p for p in processes}
        self.available: Tuple[int, ...] = tuple(int(x) for x in available)
        self.n_resources = len(self.available)

        # Precompute need and alloc per process for fast checking
        self.needs: Dict[str, Tuple[int, ...]] = {
            p["pid"]: tuple(int(m) - int(a) for m, a in zip(p["max"], p["alloc"]))
            for p in processes
        }
        self.allocs: Dict[str, Tuple[int, ...]] = {
            p["pid"]: tuple(int(a) for a in p["alloc"])
            for p in processes
        }

    def _enabled(self, work: Tuple[int, ...], remaining: Tuple[str, ...]) -> List[str]:
        """Return list of enabled processes in canonical order (initial problem process order)."""
        enabled = []
        for p in remaining:
            need = self.needs[p]
            if all(n <= w for n, w in zip(need, work)):
                enabled.append(p)
        return enabled

    @lru_cache(maxsize=16384)
    def _count_paths(self, work: Tuple[int, ...], remaining: Tuple[str, ...]) -> int:
        if not remaining:
            return 1
        total = 0
        for p in self._enabled(work, remaining):
            alloc = self.allocs[p]
            next_work = tuple(w + a for w, a in zip(work, alloc))
            next_remaining = tuple(x for x in remaining if x != p)
            total += self._count_paths(next_work, next_remaining)
        return total

    def count_paths(self) -> int:
        """Count the total number of safe sequences from the initial state."""
        return self._count_paths(self.available, self.pids)

    def canonical(self) -> Optional[Tuple[str, ...]]:
        """
        Produce the canonical safe sequence (greedy DFS choosing lowest-index process first).
        Returns None if no safe sequence exists.
        """
        def _dfs(work: Tuple[int, ...], remaining: Tuple[str, ...]) -> Optional[List[str]]:
            if not remaining:
                return []
            for p in self._enabled(work, remaining):
                alloc = self.allocs[p]
                next_work = tuple(w + a for w, a in zip(work, alloc))
                next_remaining = tuple(x for x in remaining if x != p)
                res = _dfs(next_work, next_remaining)
                if res is not None:
                    return [p] + res
            return None

        res = _dfs(self.available, self.pids)
        return tuple(res) if res is not None else None

    def sample(self, rng: random.Random) -> Optional[Tuple[str, ...]]:
        """Sample a safe sequence uniformly at random from all valid safe sequences."""
        work = self.available
        remaining = self.pids
        seq: List[str] = []

        while remaining:
            enabled = self._enabled(work, remaining)
            if not enabled:
                return None
            
            # Weight choice by forward paths to achieve exact uniform distribution over paths
            weights = []
            for p in enabled:
                alloc = self.allocs[p]
                next_work = tuple(w + a for w, a in zip(work, alloc))
                next_remaining = tuple(x for x in remaining if x != p)
                weights.append(self._count_paths(next_work, next_remaining))
            
            total_weight = sum(weights)
            if total_weight == 0:
                return None

            # Weighted selection
            r = rng.randint(1, total_weight)
            cum = 0
            chosen = enabled[0]
            for p, w in zip(enabled, weights):
                cum += w
                if r <= cum:
                    chosen = p
                    break
            
            seq.append(chosen)
            alloc = self.allocs[chosen]
            work = tuple(w + a for w, a in zip(work, alloc))
            remaining = tuple(x for x in remaining if x != chosen)

        return tuple(seq)

    def enumerate(self, limit: Optional[int] = None) -> List[Tuple[str, ...]]:
        """Enumerate all valid safe sequences in canonical lexicographical order."""
        results: List[Tuple[str, ...]] = []

        def _dfs(work: Tuple[int, ...], remaining: Tuple[str, ...], prefix: List[str]):
            if limit is not None and len(results) >= limit:
                return
            if not remaining:
                results.append(tuple(prefix))
                return
            for p in self._enabled(work, remaining):
                alloc = self.allocs[p]
                next_work = tuple(w + a for w, a in zip(work, alloc))
                next_remaining = tuple(x for x in remaining if x != p)
                _dfs(next_work, next_remaining, prefix + [p])

        _dfs(self.available, self.pids, [])
        return results

    def accepts(self, trace: Sequence[str]) -> bool:
        """Test whether a candidate sequence is a valid, complete safe sequence."""
        if len(trace) != len(self.pids):
            return False
        if set(trace) != set(self.pids):
            return False

        work = list(self.available)
        for p in trace:
            if p not in self.procs:
                return False
            need = self.needs[p]
            if any(n > w for n, w in zip(need, work)):
                return False
            alloc = self.allocs[p]
            work = [w + a for w, a in zip(work, alloc)]

        return True
