"""
Prompt rendering for the SSR pilot: three surface variants per world.

  v0  plain narration, original names, one-line arrow output
  v1  entities renamed, paraphrased narration, one-line arrow output
  v2  rows/threads listed in reverse, rules stated after the data,
      markdown-table output

The world is the statistical unit; variants are matched renderings of the same
world and are never counted as independent observations. The prompt never
states the reference convention. It says any valid trace is acceptable.
"""

import hashlib
import random
from typing import Dict, List

from research.ssr_pilot import families as F

VARIANTS = {
    "v0": {"rename": False, "para": 0, "reorder": False, "style": "arrow"},
    "v1": {"rename": True, "para": 1, "reorder": False, "style": "arrow"},
    "v2": {"rename": False, "para": 0, "reorder": True, "style": "table"},
}

PROC_NAMES = ["httpd", "cron", "backup", "kswapd", "nginx", "sshd", "logger", "indexer", "mailer", "syncd"]
THREAD_NAMES = ["worker_a", "worker_b", "worker_c", "worker_d"]
MUTEX_NAMES = ["lockA", "lockB", "lockC"]
SEM_NAMES = ["gate", "tokens", "ready", "slots_free"]
VAR_NAMES = ["counter", "cache", "flag", "journal", "queue"]

POLICY_TEXT = {
    "FCFS": "non-preemptive First-Come-First-Served. Whenever the CPU is free it runs, to completion, a ready "
            "process with the earliest arrival time.",
    "SJF": "non-preemptive Shortest-Job-First. Whenever the CPU is free it runs, to completion, a ready process "
           "with the smallest burst time.",
    "PRIORITY": "non-preemptive Priority scheduling (a smaller number means higher priority). Whenever the CPU is "
                "free it runs, to completion, a ready process with the smallest priority number.",
}
SCHED_TIES = ("A process is ready once the current time is at or after its arrival time. If several ready "
              "processes tie on the selection criterion, any one of them may be chosen. If nothing is ready, the "
              "CPU idles until the next arrival.")
RR_TEXT = ("Round Robin with time quantum {q}. Arriving processes join the tail of a FIFO ready queue. The process "
           "at the head runs for min(quantum, remaining burst); if it is not finished it rejoins the tail. "
           "Processes that arrive at the same time may join the queue in any order, and a process arriving at "
           "exactly the moment another is preempted may join before or after the preempted process. If the queue "
           "is empty the CPU idles until the next arrival.")
CONC_TEXT = ("The threads run concurrently and their operations may interleave in any order, subject to these "
             "rules: each thread performs its own operations in the listed order; lock(m) can only happen when "
             "mutex m is free (mutexes are not re-entrant) and unlock(m) releases it; wait(s) can only happen when "
             "semaphore s is greater than 0 and decreases it by 1; signal(s) increases s by 1; write(v) is "
             "unrestricted. The trace must contain every operation of every thread exactly once.")
BANKER_TEXT = ("A process can run to completion only if its remaining need (Max - Allocation) is at most the "
               "currently available (Work) amount of every resource type. When it completes it releases its whole "
               "allocation, which is added to Work. Work starts equal to Available. A trace is the order in which "
               "all processes complete; every process must complete exactly once.")

PARA_INTRO = {
    "scheduling": ["Here is a CPU scheduling exercise.", "Consider the following scheduling scenario."],
    "sync": ["Here is a concurrency exercise.", "Consider the following multithreaded program."],
    "banker": ["Here is a deadlock-avoidance exercise.", "Consider the following Banker's algorithm scenario."],
}
FORMAT = {
    ("scheduling", "arrow"): "Write the whole trace on one line that starts with 'TRACE:', as comma-separated "
                             "entries NAME START-END in time order, using IDLE for idle CPU time "
                             "(for example: TRACE: A 0-3, IDLE 3-4, B 4-6).",
    ("scheduling", "table"): "Write 'TRACE:' and then a markdown table with columns Run | Start | End, one row "
                             "per entry in time order, using IDLE for idle CPU time.",
    ("sync", "arrow"): "Write the whole trace on one line that starts with 'TRACE:', as operations separated by "
                       "semicolons, each written THREAD op(arg) (for example: TRACE: T1 lock(m); T2 write(x)).",
    ("sync", "table"): "Write 'TRACE:' and then a markdown table with columns Step | Thread | Operation, one row "
                       "per operation in execution order, written like lock(m).",
    ("banker", "arrow"): "Write the order on one line that starts with 'TRACE:', process names separated by "
                         "commas (for example: TRACE: A, B, C).",
    ("banker", "table"): "Write 'TRACE:' and then a markdown table with columns Order | Process, one row per "
                         "process in completion order.",
}
TAIL = ("If several choices are allowed at some point, any of them may be chosen; more than one valid answer can "
        "exist, and any valid answer is accepted. Reply with the trace only, with no explanation.")


# ---------------------------------------------------------------- names

def name_maps(world: Dict, variant: str) -> Dict[str, str]:
    """canonical -> shown."""
    names = F.entity_names(world)
    if not VARIANTS[variant]["rename"]:
        return {n: n for n in names}
    rng = random.Random(f"{world['id']}-{variant}")
    f = world["family"]
    if f in ("scheduling", "banker"):
        return dict(zip(names, rng.sample(PROC_NAMES, len(names))))
    threads = list(world["threads"])
    mutexes = sorted({a for ops in world["threads"].values() for op, a in ops if op in ("lock", "unlock")})
    sems = sorted(world.get("semaphores", {}))
    vs = sorted({a for ops in world["threads"].values() for op, a in ops if op == "write"})
    out = dict(zip(threads, rng.sample(THREAD_NAMES, len(threads))))
    out.update(dict(zip(mutexes, rng.sample(MUTEX_NAMES, len(mutexes)))))
    out.update(dict(zip(sems, rng.sample(SEM_NAMES, len(sems)))))
    out.update(dict(zip(vs, rng.sample(VAR_NAMES, len(vs)))))
    return out


# ---------------------------------------------------------------- constraint text

def constraint_text(world: Dict, c: Dict, m: Dict[str, str]) -> str:
    t = c["type"]
    if t == "deadline":
        return f"Constraint: {m[c['pid']]} must complete no later than time {c['by']}."
    if t == "precedence":
        return f"Constraint: {m[c['first']]} must finish before {m[c['second']]} first starts running."
    if world["family"] == "sync":
        a, b = c["a"], c["b"]
        return (f"Constraint: the operation {m[a[0]]} {a[1]}({m[a[2]]}) must occur before the operation "
                f"{m[b[0]]} {b[1]}({m[b[2]]}) in the trace.")
    return f"Constraint: {m[c['a']]} must complete before {m[c['b']]}."


# ---------------------------------------------------------------- rendering

def _data_block(world: Dict, m: Dict[str, str], reverse: bool) -> str:
    f = world["family"]
    if f == "scheduling":
        procs = list(world["processes"])[::-1] if reverse else list(world["processes"])
        rows = ["| Process | Arrival | Burst | Priority |", "|---|---|---|---|"]
        rows += [f"| {m[p['pid']]} | {p['arrival']} | {p['burst']} | {p['priority']} |" for p in procs]
        return "Processes:\n" + "\n".join(rows)
    if f == "sync":
        items = list(world["threads"].items())[::-1] if reverse else list(world["threads"].items())
        lines = [f"{m[t]}: " + "; ".join(f"{op}({m[a]})" for op, a in ops) for t, ops in items]
        sems = ", ".join(f"{m[s]} = {v}" for s, v in world.get("semaphores", {}).items()) or "none"
        return "Initial semaphore values: " + sems + "\nThread programs:\n" + "\n".join(lines)
    procs = list(world["processes"])[::-1] if reverse else list(world["processes"])
    res = world["resources"]
    head = "| Process | " + " | ".join(f"Alloc {r}" for r in res) + " | " + " | ".join(f"Max {r}" for r in res) + " |"
    rows = [head, "|" + "---|" * (1 + 2 * len(res))]
    for p in procs:
        rows.append(f"| {m[p['pid']]} | " + " | ".join(map(str, p["alloc"])) + " | "
                    + " | ".join(map(str, p["max"])) + " |")
    avail = ", ".join(f"{r} = {v}" for r, v in zip(res, world["available"]))
    return "Available: " + avail + "\n" + "\n".join(rows)


def _rules(world: Dict) -> str:
    f = world["family"]
    if f == "scheduling":
        if world["policy"] == "RR":
            return "Policy: " + RR_TEXT.format(q=world["quantum"])
        return "Policy: " + POLICY_TEXT[world["policy"]] + " " + SCHED_TIES
    return CONC_TEXT if f == "sync" else BANKER_TEXT


def convention_text(world: Dict, variant: str) -> str:
    f = world["family"]
    is_v1 = VARIANTS[variant]["rename"]
    is_v2 = VARIANTS[variant]["reorder"]
    if f == "scheduling":
        if world["policy"] == "RR":
            if is_v1:
                return ("Convention for tie-breaking: If multiple processes arrive at the same time, enqueue them in the order listed in the Processes table. "
                        "If a process is preempted at the exact moment another process arrives, enqueue the newly arriving process before the preempted process.")
            elif is_v2:
                return ("Convention for tie-breaking: If multiple processes arrive at the same time, enqueue them in process ID index order (P1 before P2 before P3). "
                        "If a process is preempted at the exact moment another process arrives, enqueue the newly arriving process before the preempted process.")
            else:
                return ("Convention for tie-breaking: If multiple processes arrive at the same time, enqueue them in the order listed in the Processes table (P1 before P2 before P3). "
                        "If a process is preempted at the exact moment another process arrives, enqueue the newly arriving process before the preempted process.")
        else:
            if is_v1:
                return "Convention for tie-breaking: If several ready processes tie on the selection criterion, choose the process listed earliest in the Processes table."
            elif is_v2:
                return "Convention for tie-breaking: If several ready processes tie on the selection criterion, choose the process with the lowest process index / ID (e.g. P1 before P2 before P3)."
            else:
                return "Convention for tie-breaking: If several ready processes tie on the selection criterion, choose the process listed earliest in the Processes table (e.g. P1 before P2 before P3)."
    elif f == "sync":
        if is_v1:
            return "Convention for tie-breaking: If multiple threads are simultaneously enabled to execute their next operation, choose the thread listed earliest in the Thread programs list."
        elif is_v2:
            return "Convention for tie-breaking: If multiple threads are simultaneously enabled to execute their next operation, choose the thread with the lowest thread index / ID (e.g. T1 before T2 before T3)."
        else:
            return "Convention for tie-breaking: If multiple threads are simultaneously enabled to execute their next operation, choose the thread listed earliest in the Thread programs list (e.g. T1 before T2 before T3)."
    elif f == "banker":
        if is_v1:
            return "Convention for tie-breaking: If multiple processes can safely run to completion at any step, select the process listed earliest in the Process table."
        elif is_v2:
            return "Convention for tie-breaking: If multiple processes can safely run to completion at any step, select the process with the lowest process index / ID (e.g. P0 before P1 before P2)."
        else:
            return "Convention for tie-breaking: If multiple processes can safely run to completion at any step, select the process listed earliest in the Process table (e.g. P0 before P1 before P2)."
    return ""


def render_variant(world: Dict, variant: str, stated_convention: bool = False) -> Dict:
    spec = VARIANTS[variant]
    m = name_maps(world, variant)
    f = world["family"]
    intro = PARA_INTRO[f][spec["para"]]
    rules = _rules(world)
    if stated_convention:
        rules = rules + "\n" + convention_text(world, variant)
    data = _data_block(world, m, spec["reorder"])
    cons = "\n".join(constraint_text(world, c, m) for c in world.get("constraints", []))
    fmt = FORMAT[(f, spec["style"])]
    parts = [intro, data, rules, cons, fmt, TAIL] if spec["reorder"] else [intro, rules, data, cons, fmt, TAIL]
    prompt = "\n\n".join(p for p in parts if p)
    return {"world": world["id"], "variant": variant, "prompt": prompt, "c2s": m,
            "s2c": {v: k for k, v in m.items()}, "style": spec["style"],
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "stated_convention": stated_convention}


def render_all(world: Dict, stated_convention: bool = False) -> List[Dict]:
    return [render_variant(world, v, stated_convention=stated_convention) for v in VARIANTS]


def reference_text(world: Dict, reference, rendered: Dict) -> str:
    """The reference as it would be printed in this variant (for the strict string match)."""
    return F.format_steps(world, reference, rendered["style"], rendered["c2s"])

