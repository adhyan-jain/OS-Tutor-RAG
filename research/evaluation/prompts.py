"""
Prompt templates for E1 (generation) and E2 (judging). FROZEN with
docs/PREREGISTRATION_V2.md: the SHA-256 of this file is stamped into every
results file. Any change after the first model call is a protocol deviation.

The problem statement always spells out the rules *including* the source of
nondeterminism, so that every valid trace is derivable from the prompt alone.
A judge that rejects a valid alternative therefore errs on information it was
given, not on an under-specified task.
"""

from typing import Dict, Optional

from research.simulator.traces import format_events, format_schedule

POLICY_RULES = {
    "FCFS": ("non-preemptive First-Come-First-Served: whenever the CPU is free it runs, to completion, "
             "a ready process with the earliest arrival time"),
    "SJF": ("non-preemptive Shortest-Job-First: whenever the CPU is free it runs, to completion, "
            "a ready process with the smallest burst time"),
    "PRIORITY": ("non-preemptive Priority scheduling (a smaller number means higher priority): whenever the CPU "
                 "is free it runs, to completion, a ready process with the smallest priority number"),
}

SCHED_COMMON = ("A process is ready once the current time is at or after its arrival time. If several ready "
                "processes tie on the selection criterion, any one of them may be chosen. If no process is "
                "ready, the CPU is IDLE until the next arrival.")

RR_RULES = ("Round Robin with time quantum {q}. Arriving processes join the tail of a FIFO ready queue. The CPU "
            "runs the process at the head of the queue for min(quantum, remaining burst) time units; if it is "
            "not finished it rejoins the tail of the queue. Processes that arrive at the same time may join the "
            "queue in any order, and a process that arrives at exactly the moment another process is preempted "
            "may join the queue either before or after the preempted process. If the queue is empty, the CPU is "
            "IDLE until the next arrival.")

CONC_RULES = ("The threads run concurrently and their operations may interleave in any order, subject to: "
              "each thread performs its own operations in the order listed; lock(m) can only happen when mutex m "
              "is not held by any thread (mutexes are not re-entrant) and unlock(m) releases it; wait(s) can only "
              "happen when semaphore s is greater than 0 and decreases it by 1; signal(s) increases s by 1; "
              "write(v) has no constraint. An execution trace lists every operation of every thread exactly once.")

SCHED_FORMAT = ("A trace is a list of entries NAME START-END in time order, separated by commas, "
                "using IDLE as the name for idle CPU time, e.g. 'A 0-3, IDLE 3-4, B 4-6'.")
CONC_FORMAT = ("A trace is the sequence of operations in execution order, separated by semicolons, each written "
               "as THREAD op(arg), e.g. 'T1 lock(m); T2 write(x); T1 unlock(m)'.")

JUDGE_QUESTION = ("Question: Is the candidate trace a valid execution of this problem under the rules above? "
                  "Reply with exactly one word: VALID or INVALID.")
REFERENCE_HEADER = "Reference solution (a correct execution trace):"
MITIGATION_NOTE = "Note: the reference is one valid execution; other valid executions may exist."


def render_problem(inst: Dict) -> str:
    p = inst["problem"]
    if p["domain"] == "scheduling":
        if p["policy"] == "RR":
            head = "CPU scheduling problem. Policy: " + RR_RULES.format(q=p["quantum"])
        else:
            head = f"CPU scheduling problem. Policy: {POLICY_RULES[p['policy']]}. {SCHED_COMMON}"
        rows = ["| Process | Arrival | Burst | Priority |", "|---|---|---|---|"]
        rows += [f"| {q['pid']} | {q['arrival']} | {q['burst']} | {q['priority']} |" for q in p["processes"]]
        return f"{head}\n\nProcesses:\n" + "\n".join(rows) + f"\n\n{SCHED_FORMAT}"
    lines = [f"{t}: " + "; ".join(f"{op}({a})" for op, a in ops) for t, ops in p["threads"].items()]
    sems = ", ".join(f"{k} = {v}" for k, v in p["semaphores"].items()) or "none"
    return (f"Concurrency problem. {CONC_RULES}\n\nInitial semaphore values: {sems}\n"
            f"Thread programs:\n" + "\n".join(lines) + f"\n\n{CONC_FORMAT}")


def render_trace(inst: Dict, trace, style: Optional[str] = None) -> str:
    style = style or inst["format"]
    fmt = format_schedule if inst["domain"] == "scheduling" else format_events
    return fmt(trace, style)


def generation_prompt(inst: Dict) -> str:
    return (render_problem(inst) + "\n\nWrite one valid execution trace for this problem. "
            "Give the whole trace on a single line that starts with 'TRACE:' and write nothing after it.")


def judge_prompt(inst: Dict, candidate, reference=None, reference_style: Optional[str] = None,
                 mitigation: bool = False) -> str:
    parts = [render_problem(inst)]
    if reference is not None:
        parts.append(REFERENCE_HEADER + "\n" + render_trace(inst, reference, reference_style))
        if mitigation:
            parts.append(MITIGATION_NOTE)
    parts.append("Candidate execution trace:\n" + render_trace(inst, candidate))
    parts.append(JUDGE_QUESTION)
    return "\n\n".join(parts)
