"""
Trace representation shared by the scheduling and concurrency domains.

Scheduling trace: tuple of segments (pid, start, end); "IDLE" is a pid.
Concurrency trace: tuple of events (thread, op, arg).

All traces are tuples of tuples so they hash and compare reliably. AGY's
original oracle compared JSON lists to tuples and so rejected every trace;
`as_schedule` / `as_events` exist to make that impossible.
"""

import re
from typing import Iterable, List, Optional, Sequence, Tuple

Segment = Tuple[str, int, int]
Event = Tuple[str, str, str]

IDLE = "IDLE"


def as_schedule(trace: Iterable[Sequence]) -> Tuple[Segment, ...]:
    return tuple((str(s[0]), int(s[1]), int(s[2])) for s in trace)


def as_events(trace: Iterable[Sequence]) -> Tuple[Event, ...]:
    return tuple((str(e[0]), str(e[1]), str(e[2])) for e in trace)


def normalize_schedule(trace: Iterable[Sequence]) -> Tuple[Segment, ...]:
    """Fill gaps with IDLE, drop empty segments, merge adjacent same-pid segments.

    A Gantt chart that writes "P1 0-2, P1 2-4" describes the same schedule as
    "P1 0-4", and an unmarked gap is idle time. Both sides of every comparison
    go through this, so representation choices never decide correctness.
    """
    segs = sorted(as_schedule(trace), key=lambda s: (s[1], s[2]))
    out: List[Segment] = []
    t = 0
    for pid, start, end in segs:
        if end <= start:
            continue
        if start > t:
            out.append((IDLE, t, start))
        out.append((pid, start, end))
        t = max(t, end)
    merged: List[Segment] = []
    for seg in out:
        if merged and merged[-1][0] == seg[0] and merged[-1][2] == seg[1]:
            merged[-1] = (seg[0], merged[-1][1], seg[2])
        else:
            merged.append(seg)
    return tuple(merged)


def has_overlap(trace: Iterable[Sequence]) -> bool:
    segs = sorted(as_schedule(trace), key=lambda s: (s[1], s[2]))
    return any(b[1] < a[2] for a, b in zip(segs, segs[1:]))


# ---------- formatting ----------

def format_schedule(trace: Sequence[Segment], style: str = "arrow") -> str:
    trace = as_schedule(trace)
    if style == "arrow":
        return ", ".join(f"{p} {s}-{e}" for p, s, e in trace)
    if style == "table":
        rows = ["| Run | Start | End |", "|---|---|---|"]
        rows += [f"| {p} | {s} | {e} |" for p, s, e in trace]
        return "\n".join(rows)
    raise ValueError(style)


def format_events(trace: Sequence[Event], style: str = "arrow") -> str:
    trace = as_events(trace)
    if style == "arrow":
        return "; ".join(f"{t} {op}({a})" for t, op, a in trace)
    if style == "table":
        rows = ["| Step | Thread | Operation |", "|---|---|---|"]
        rows += [f"| {i + 1} | {t} | {op}({a}) |" for i, (t, op, a) in enumerate(trace)]
        return "\n".join(rows)
    raise ValueError(style)


# ---------- parsing model output ----------

_SEG_RE = re.compile(r"([A-Za-z_][\w\-]*)\s*[:(\[]?\s*(\d+)\s*(?:-|–|to|,)\s*(\d+)\s*[)\]]?")
_ROW_RE = re.compile(r"\|\s*([A-Za-z_][\w\-]*)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|")
_EVT_RE = re.compile(r"([A-Za-z_][\w\-]*)[\s:|]+(lock|unlock|wait|signal|read|write)\s*\(\s*([\w\-]+)\s*\)", re.I)


def _answer_region(text: str) -> str:
    m = re.search(r"TRACE\s*:(.*)", text, re.S | re.I)
    return m.group(1) if m else text


def parse_schedule(text: str, valid_names: Iterable[str]) -> Optional[Tuple[Segment, ...]]:
    """Parse a model's schedule. Returns None when nothing parseable is found."""
    names = set(valid_names) | {IDLE}
    region = _answer_region(text)
    rows = _ROW_RE.findall(region)
    found = rows if rows else _SEG_RE.findall(region)
    segs = []
    for name, s, e in found:
        canon = IDLE if name.upper() == IDLE else name
        if canon in names:
            segs.append((canon, int(s), int(e)))
    return tuple(segs) if segs else None


def parse_events(text: str, valid_threads: Iterable[str]) -> Optional[Tuple[Event, ...]]:
    threads = set(valid_threads)
    evs = [(t, op.lower(), a) for t, op, a in _EVT_RE.findall(_answer_region(text)) if t in threads]
    return tuple(evs) if evs else None


# ---------- distances ----------

def levenshtein(a: Sequence, b: Sequence) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def first_divergence(a: Sequence, b: Sequence) -> int:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))
