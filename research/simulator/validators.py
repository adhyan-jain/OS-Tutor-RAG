"""
Independent trace validators V(P, T) -> (valid, reason).

Written separately from the enumerators in cpu_scheduler.py and
concurrency_interleaver.py and deliberately imports neither: each validator
consumes the candidate trace and checks the textbook rules directly. The test
suite requires the two implementations to agree on every enumerated trace,
every mutant and every random candidate, which is what makes the benchmark
labels trustworthy (AGY's labels were 76% wrong and nothing checked them).
"""

import itertools
from typing import Dict, Sequence, Tuple

from research.simulator.traces import IDLE, as_events, has_overlap, normalize_schedule

Result = Tuple[bool, str]


# ---------------------------------------------------------------- scheduling

def validate_schedule(problem: Dict, trace: Sequence) -> Result:
    procs = {p["pid"]: p for p in problem["processes"]}
    if has_overlap(trace):
        return False, "overlapping_segments"
    tr = normalize_schedule(trace)
    for pid, _, _ in tr:
        if pid != IDLE and pid not in procs:
            return False, f"unknown_process:{pid}"
    if problem["policy"] == "RR":
        return _validate_rr(procs, problem.get("quantum", 2), tr)
    return _validate_nonpreemptive(procs, problem["policy"], tr)


def _policy_key(p: Dict, policy: str) -> int:
    if policy == "FCFS":
        return p["arrival"]
    if policy == "SJF":
        return p["burst"]
    if policy == "PRIORITY":
        return p["priority"]
    raise ValueError(policy)


def _validate_nonpreemptive(procs, policy, tr) -> Result:
    done = set()
    t = 0
    for pid, start, end in tr:
        if start != t:
            return False, "time_discontinuity"
        pending = [q for q in procs.values() if q["pid"] not in done]
        ready = [q for q in pending if q["arrival"] <= t]
        if pid == IDLE:
            if ready:
                return False, "idle_while_ready"
            if not pending:  # nothing left to wait for: trailing idle time is not part of any valid schedule
                return False, "idle_after_completion"
            if end != min(q["arrival"] for q in pending):
                return False, "idle_wrong_length"
        else:
            p = procs[pid]
            if pid in done:
                return False, "preemption_or_rerun"
            if p["arrival"] > start:
                return False, "started_before_arrival"
            if end - start < p["burst"]:
                return False, "preempted_partial_burst"
            if end - start > p["burst"]:
                return False, "wrong_burst_length"
            if _policy_key(p, policy) > min(_policy_key(q, policy) for q in ready):
                return False, "policy_violation"
            done.add(pid)
        t = end
    if len(done) != len(procs):
        return False, "incomplete"
    return True, "ok"


def _validate_rr(procs, q, tr) -> Result:
    """Nondeterministic forward simulation: the set of queue configurations
    consistent with the prefix consumed so far."""
    def order(pids):
        return sorted(pids)

    rem0 = tuple(sorted((pid, p["burst"]) for pid, p in procs.items()))
    first = order([pid for pid, p in procs.items() if p["arrival"] == 0])
    configs = {(0, perm, rem0) for perm in itertools.permutations(first)}
    reason = "ok"

    def arrivals_between(lo, hi, rem, inclusive_hi):
        out = {}
        for pid, r in rem:
            a = procs[pid]["arrival"]
            if r > 0 and lo < a and (a <= hi if inclusive_hi else a < hi):
                out.setdefault(a, []).append(pid)
        return out

    for pid, start, end in tr:
        nxt = set()
        for (t, queue, rem) in configs:
            if t != start:
                reason = "time_discontinuity"
                continue
            if pid == IDLE:
                if queue:
                    reason = "idle_while_ready"
                    continue
                arr = arrivals_between(t, end, rem, inclusive_hi=True)
                if not arr or min(arr) != end or len(arr) != 1:
                    reason = "idle_wrong_length"
                    continue
                for perm in itertools.permutations(order(arr[end])):
                    nxt.add((end, perm, rem))
                continue
            # A merged segment may be several consecutive dispatches of pid.
            frontier = {(t, queue, rem)}
            while frontier:
                cur = frontier.pop()
                ct, cq, crem = cur
                if ct == end:
                    nxt.add(cur)
                    continue
                if not cq or cq[0] != pid:
                    reason = "queue_order_violation"
                    continue
                remd = dict(crem)
                run = min(q, remd[pid])
                if ct + run > end:
                    reason = "ran_past_quantum_or_burst"
                    continue
                cend = ct + run
                remd[pid] -= run
                during = arrivals_between(ct, cend, crem, inclusive_hi=False)
                at_end = order(arrivals_between(cend - 1, cend, crem, inclusive_hi=True).get(cend, []))
                pre = (pid,) if remd[pid] > 0 else ()
                groups = [list(itertools.permutations(order(during[a]))) for a in sorted(during)]
                new_rem = tuple(sorted(remd.items()))
                for combo in itertools.product(*groups):
                    mid = tuple(x for g in combo for x in g)
                    for e in itertools.permutations(at_end):
                        tails = {e + pre, pre + e}
                        for tail in tails:
                            frontier.add((cend, cq[1:] + mid + tail, new_rem))
        configs = nxt
        if not configs:
            return False, reason
    if not any(all(r == 0 for _, r in rem) for _, _, rem in configs):
        return False, "incomplete"
    return True, "ok"


# ---------------------------------------------------------------- concurrency

def validate_events(problem: Dict, trace: Sequence) -> Result:
    prog = {t: [tuple(op) for op in ops] for t, ops in problem["threads"].items()}
    sems = dict(problem.get("semaphores", {}))
    pc = {t: 0 for t in prog}
    owner: Dict[str, str] = {}
    for t, op, arg in as_events(trace):
        if t not in prog:
            return False, f"unknown_thread:{t}"
        if pc[t] >= len(prog[t]) or prog[t][pc[t]] != (op, arg):
            return False, "program_order_violation"
        if op == "lock":
            if arg in owner:
                return False, "mutual_exclusion_violation"
            owner[arg] = t
        elif op == "unlock":
            if owner.get(arg) != t:
                return False, "unlock_not_owner"
            del owner[arg]
        elif op == "wait":
            if sems[arg] <= 0:
                return False, "wait_on_zero_semaphore"
            sems[arg] -= 1
        elif op == "signal":
            sems[arg] += 1
        pc[t] += 1
    if any(pc[t] < len(prog[t]) for t in prog):
        return False, "incomplete"
    return True, "ok"


def validate(problem: Dict, trace: Sequence) -> Result:
    domain = problem.get("domain") or problem.get("family")
    if domain == "scheduling":
        return validate_schedule(problem, trace)
    if domain == "concurrency" or domain == "sync":
        return validate_events(problem, trace)
    if domain == "banker":
        return validate_banker(problem, trace)
    raise ValueError(f"Unknown domain/family: {domain}")


# ---------------------------------------------------------------- banker

def validate_banker(problem: Dict, trace: Sequence) -> Result:
    procs = {p["pid"]: p for p in problem["processes"]}
    work, done = list(problem["available"]), set()
    for p in trace:
        if p not in procs:
            return False, f"unknown_process:{p}"
        if p in done:
            return False, "repeated_process"
        need = [m - a for m, a in zip(procs[p]["max"], procs[p]["alloc"])]
        if any(n > w for n, w in zip(need, work)):
            return False, "need_exceeds_work"
        work = [w + a for w, a in zip(work, procs[p]["alloc"])]
        done.add(p)
    if len(done) != len(procs):
        return False, "incomplete"
    return True, "ok"

