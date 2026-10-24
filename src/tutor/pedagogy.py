"""Per-student concept state and the deterministic pedagogical policy.

State changes only through ``apply_classification`` (every change is appended to
a history row naming its source), so a state can always be traced to the
evidence that produced it. A model's suggestion is ``advisory`` and clamped: it
can lift a concept at most one level and never to UNDERSTOOD, never lower it.

There is no clock. "Recency" is a turn counter, so cooldowns are reproducible.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from .knowledge import ConceptQuestion, CourseKnowledge, Misconception

STATES: tuple[str, ...] = (
    "UNKNOWN", "INTRODUCED", "ATTEMPTED", "PARTIALLY_UNDERSTOOD", "UNDERSTOOD", "MASTERED",
)
RANK = {s: i for i, s in enumerate(STATES)}
UNDERSTOOD_OR_BETTER = ("UNDERSTOOD", "MASTERED")
CLASSIFICATIONS = ("CORRECT", "PARTIAL", "MISCONCEPTION", "UNCLEAR")
ADVISORY_CEILING = "PARTIALLY_UNDERSTOOD"

# A concept is not re-raised for this many turns after an intervention.
CONCEPT_COOLDOWN_TURNS = 4
# After this many non-correct answers on one question the tutor explains and
# moves on instead of asking again.
EXPLAIN_AFTER_MISSES = 2


@dataclass
class ConceptRecord:
    state: str = "UNKNOWN"
    attempts: int = 0
    misconceptions: list[str] = field(default_factory=list)
    asked: list[str] = field(default_factory=list)
    misses: dict[str, int] = field(default_factory=dict)
    last_seq: int | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ConceptStates:
    seq: int = 0
    records: dict[str, ConceptRecord] = field(default_factory=dict)

    def get(self, concept_id: str) -> ConceptRecord:
        rec = self.records.get(concept_id)
        if rec is None:
            rec = self.records[concept_id] = ConceptRecord()
        return rec

    def tick(self) -> int:
        self.seq += 1
        return self.seq

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ConceptStates":
        out = cls()
        if not data:
            return out
        out.seq = int(data.get("seq", 0))
        for cid, raw in (data.get("records") or {}).items():
            rec = ConceptRecord()
            for key, value in (raw or {}).items():
                if hasattr(rec, key):
                    setattr(rec, key, copy.deepcopy(value))
            if rec.state not in RANK:
                rec.state = "UNKNOWN"
            out.records[cid] = rec
        return out

    def summary(self) -> dict[str, str]:
        return {cid: r.state for cid, r in self.records.items() if RANK[r.state] > 0}


def _next_state(current: str, classification: str) -> str:
    """Never regresses understanding on PARTIAL/UNCLEAR; a stated
    misconception drops UNDERSTOOD one step."""
    if classification == "CORRECT":
        return current if current == "MASTERED" else "UNDERSTOOD"
    if classification == "PARTIAL":
        return current if RANK[current] >= RANK["PARTIALLY_UNDERSTOOD"] else "PARTIALLY_UNDERSTOOD"
    if classification == "MISCONCEPTION":
        if RANK[current] >= RANK["UNDERSTOOD"]:
            return "PARTIALLY_UNDERSTOOD"
        return current if RANK[current] >= RANK["ATTEMPTED"] else "ATTEMPTED"
    return current if RANK[current] >= RANK["ATTEMPTED"] else "ATTEMPTED"  # UNCLEAR


def _record(rec: ConceptRecord, before: str, after: str, source: str, reason: str, seq: int) -> None:
    rec.history.append({"from": before, "to": after, "source": source, "reason": reason, "seq": seq})


def introduce(states: ConceptStates, concept_id: str) -> bool:
    """Mark a concept as shown (answered or asked about)."""
    rec = states.get(concept_id)
    if rec.state != "UNKNOWN":
        return False
    rec.state = "INTRODUCED"
    _record(rec, "UNKNOWN", "INTRODUCED", "deterministic", "introduced", states.seq)
    return True


def apply_classification(
    states: ConceptStates,
    concept_id: str,
    classification: str,
    *,
    question_id: str = "",
    misconception_id: str | None = None,
    reason: str = "",
) -> ConceptRecord:
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unknown classification {classification!r}")
    rec = states.get(concept_id)
    before = rec.state
    rec.attempts += 1
    if question_id and question_id not in rec.asked:
        rec.asked.append(question_id)
    if classification != "CORRECT" and question_id:
        rec.misses[question_id] = rec.misses.get(question_id, 0) + 1
    if misconception_id and misconception_id not in rec.misconceptions:
        rec.misconceptions.append(misconception_id)
    rec.state = _next_state(before, classification)
    rec.last_seq = states.seq
    _record(rec, before, rec.state, "deterministic", reason or classification.lower(), states.seq)
    return rec


def mark_mastered(states: ConceptStates, concept_id: str) -> None:
    """MASTERED is reachable only from UNDERSTOOD, via a correct TRANSFER answer."""
    rec = states.get(concept_id)
    if rec.state == "UNDERSTOOD":
        _record(rec, "UNDERSTOOD", "MASTERED", "deterministic", "transfer_correct", states.seq)
        rec.state = "MASTERED"


def apply_advisory(states: ConceptStates, concept_id: str, suggested: str) -> ConceptRecord:
    """Fold in a model's suggested classification for an answer the grader could
    not classify. Clamped: at most one level up, never past
    PARTIALLY_UNDERSTOOD, never down. The model advises; it does not decide."""
    rec = states.get(concept_id)
    if suggested not in CLASSIFICATIONS or suggested == "UNCLEAR":
        return rec
    before = rec.state
    target = _next_state(before, "PARTIAL" if suggested == "CORRECT" else suggested)
    ceiling = min(max(RANK[before] + 1, RANK["ATTEMPTED"]), RANK[ADVISORY_CEILING])
    after = STATES[min(RANK[target], ceiling)] if RANK[target] > RANK[before] else before
    if after != before:
        rec.state = after
        _record(rec, before, after, "llm_advisory", "llm_suggestion", states.seq)
    return rec


# ------------------------------------------------------------------ grading

_NEGATION = re.compile(r"\b(not|n't|never|rather\s+than|instead\s+of)\b[^.;,!?]*$|n't\b[^.;,!?]*$", re.I)
_DONT_KNOW = re.compile(
    r"^\s*(i\s+)?(don'?t|do\s+not|dunno|no\s+idea|not\s+sure|idk|\?+|no)\b|\b(no\s+idea|not\s+sure|idk)\b",
    re.I,
)


@dataclass(frozen=True)
class Classification:
    label: str  # CORRECT | PARTIAL | MISCONCEPTION | UNCLEAR
    misconception_id: str | None = None
    matched_groups: int = 0
    dont_know: bool = False


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def misconception_hit(m: Misconception, text: str) -> bool:
    """A pattern counts only when the student is not negating it ("threads do
    not share memory" must not read as a misconception about sharing)."""
    t = _normalise(text)
    for pat in m.patterns:
        for hit in re.finditer(pat, t, re.I):
            if not _NEGATION.search(t[: hit.start()][-40:]):
                return True
    return False


def classify_answer(question: ConceptQuestion, text: str, knowledge: CourseKnowledge) -> Classification:
    """Classify a free-text answer against the authored keys. Deterministic."""
    t = _normalise(text)
    if not t:
        return Classification("UNCLEAR", dont_know=True)
    for m in knowledge.misconceptions:
        if m.concept_id == question.concept_id and misconception_hit(m, t):
            return Classification("MISCONCEPTION", misconception_id=m.id)
    matched = sum(1 for group in question.groups if any(re.search(p, t, re.I) for p in group))
    if matched >= question.need and question.groups:
        return Classification("CORRECT", matched_groups=matched)
    if matched >= 1:
        return Classification("PARTIAL", matched_groups=matched)
    return Classification("UNCLEAR", dont_know=bool(_DONT_KNOW.search(t)))


def is_parroted_hint(question: ConceptQuestion, text: str, threshold: float = 0.6) -> bool:
    """The student just repeated the hint back. Hints share vocabulary with the
    answer key by design, so an echo would otherwise be graded CORRECT; ask for
    it in their own words instead (not counted as an attempt)."""
    a = set(re.findall(r"[a-z0-9']+", (text or "").lower()))
    b = set(re.findall(r"[a-z0-9']+", (question.scaffold or "").lower()))
    if len(a) < 4 or not b:
        return False
    return len(a & b) / len(a | b) >= threshold


def find_misconception(knowledge: CourseKnowledge, text: str) -> Misconception | None:
    """A misconception embedded in a student's *question* (not an answer), so
    the answer can address it. Replaces a per-message model call."""
    for m in knowledge.misconceptions:
        if misconception_hit(m, text):
            return m
    return None


# ------------------------------------------------------------------- policy

#: recall -> understanding -> application -> analysis
LEVEL: dict[str, int] = {
    "OBSERVATION": 1, "WHY": 2, "PREDICTION": 3, "CONSEQUENCE": 3, "INTERPRETATION": 4, "TRANSFER": 4,
}
LEVEL_NAMES = {1: "recall", 2: "understanding", 3: "application", 4: "analysis"}


def choose_question(
    knowledge: CourseKnowledge,
    concept_id: str,
    rec: ConceptRecord,
    exclude: frozenset[str] = frozenset(),
    after_explanation: bool = False,
) -> ConceptQuestion | None:
    """Pick a question type from the concept's state, then an unasked question
    of that type. Cheap, deterministic, never repeats an asked question.

    ``after_explanation``: the student has just been *told* the idea, so a
    recall question would only echo the answer above it. Ask them to apply it
    (predict / consequence) first; a quiz keeps the easy recall-first ramp."""
    pool = [q for q in knowledge.questions if q.concept_id == concept_id and q.id not in exclude]
    if rec.state in ("UNKNOWN", "INTRODUCED"):
        order = ("PREDICTION", "CONSEQUENCE", "WHY", "OBSERVATION") if after_explanation else ("OBSERVATION", "WHY", "PREDICTION")
    elif rec.state == "ATTEMPTED":
        order = ("WHY", "PREDICTION", "OBSERVATION")
    elif rec.state == "PARTIALLY_UNDERSTOOD":
        order = ("INTERPRETATION", "CONSEQUENCE", "WHY", "PREDICTION")
    elif rec.state == "UNDERSTOOD":
        order = ("TRANSFER", "INTERPRETATION")
    else:
        order = ("TRANSFER",)
    for qtype in order:
        for q in pool:
            if q.qtype == qtype and q.id not in rec.asked:
                return q
    for q in pool:  # any other unasked question rather than leaving a core idea unraised
        if q.id not in rec.asked and (rec.state != "MASTERED" or q.qtype == "TRANSFER"):
            return q
    return None


def deeper_question(
    knowledge: CourseKnowledge, question: ConceptQuestion, rec: ConceptRecord
) -> ConceptQuestion | None:
    """After a CORRECT answer, the next unasked question on the same concept one
    level up, lowest level first; None when nothing harder is authored."""
    level = LEVEL.get(question.qtype, 1)
    cands = [
        q for q in knowledge.questions
        if q.concept_id == question.concept_id and q.id != question.id
        and q.id not in rec.asked and LEVEL.get(q.qtype, 1) > level
    ]
    cands.sort(key=lambda q: LEVEL.get(q.qtype, 1))
    return cands[0] if cands else None


def may_open_followup(states: ConceptStates, concept_id: str) -> bool:
    """Whether a Socratic question about this concept is allowed right now: not
    already understood, not asked about inside the cooldown window."""
    rec = states.records.get(concept_id)
    if rec is None:
        return True
    if rec.state in UNDERSTOOD_OR_BETTER:
        return False
    return rec.last_seq is None or states.seq - rec.last_seq >= CONCEPT_COOLDOWN_TURNS


@dataclass(frozen=True)
class Followup:
    kind: str  # advance | probe | scaffold | explain
    text: str = ""
    misconception_id: str | None = None


def next_after_answer(
    knowledge: CourseKnowledge, question: ConceptQuestion, cls: Classification, rec: ConceptRecord
) -> Followup:
    """What the tutor does with a classified answer. State must already be
    updated so ``rec.misses`` includes this answer."""
    if cls.label == "CORRECT":
        return Followup("advance")
    misses = rec.misses.get(question.id, 0)
    if cls.label == "MISCONCEPTION" and cls.misconception_id:
        m = knowledge.misconception_by_id[cls.misconception_id]
        if misses >= EXPLAIN_AFTER_MISSES:
            return Followup("explain", m.correction, m.id)
        return Followup("probe", m.probe, m.id)
    if misses >= EXPLAIN_AFTER_MISSES:
        return Followup("explain", question.expected_reasoning)
    return Followup("scaffold", question.scaffold)


def prerequisite_gap(knowledge: CourseKnowledge, states: ConceptStates, concept_id: str) -> str | None:
    """A prerequisite the student has not touched yet (candidate "start here
    first" suggestion for someone who knows nothing)."""
    for pid in knowledge.concept_by_id[concept_id].prerequisites:
        rec = states.records.get(pid)
        if rec is None or RANK[rec.state] < RANK["INTRODUCED"]:
            return pid
    return None
