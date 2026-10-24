"""Authored knowledge model: what the tutor knows about the OS course.

Pure data, no behaviour and no model calls. The pedagogy engine is generic; only
the instances of these types (``os_course.py``) are specific to the course.
Misconceptions carry their own detection regexes, so nothing here ever asks a
model whether a student's answer is right.
"""

from __future__ import annotations

from dataclasses import dataclass, field

QUESTION_TYPES: tuple[str, ...] = (
    "PREDICTION", "WHY", "CONSEQUENCE", "OBSERVATION", "INTERPRETATION", "TRANSFER",
)


@dataclass(frozen=True)
class Concept:
    id: str
    name: str
    description: str  # one or two sentences, safe to show as a concept card
    prerequisites: tuple[str, ...] = ()
    importance: int = 2  # 1 background .. 3 core
    # Regexes matched against a lower-cased student message: "this message is
    # about this concept". Longer matches win, so specific beats generic.
    aliases: tuple[str, ...] = ()
    topic: str = ""  # course unit, used to group starters and the learning path


@dataclass(frozen=True)
class Misconception:
    id: str
    concept_id: str
    statement: str  # the wrong belief in a student's likely words
    patterns: tuple[str, ...]  # regex alternatives; any match flags it
    probe: str  # Socratic question that targets it without revealing the answer
    correction: str  # concise correction, used after repeated difficulty


@dataclass(frozen=True)
class ConceptQuestion:
    """One authored question with deterministic answer keys."""

    id: str
    concept_id: str
    qtype: str
    ask: str
    # Each group is a set of regex alternatives; `need` groups must match for
    # CORRECT. Fewer (but >=1) matched is PARTIAL.
    groups: tuple[tuple[str, ...], ...] = ()
    need: int = 1
    expected_reasoning: str = ""  # what a good answer contains
    scaffold: str = ""  # hint used on PARTIAL / after misses


@dataclass(frozen=True)
class CourseKnowledge:
    concepts: tuple[Concept, ...]
    misconceptions: tuple[Misconception, ...]
    questions: tuple[ConceptQuestion, ...]
    starters: tuple[str, ...] = ()
    #: Ordered concept ids: a sensible first-pass route through the course for a
    #: student who knows nothing and does not know what to ask.
    learning_path: tuple[str, ...] = ()
    concept_by_id: dict[str, Concept] = field(default_factory=dict, compare=False)
    misconception_by_id: dict[str, Misconception] = field(default_factory=dict, compare=False)
    question_by_id: dict[str, ConceptQuestion] = field(default_factory=dict, compare=False)

    def validate(self) -> list[str]:
        """Structural problems (empty list means consistent)."""
        problems: list[str] = []
        cids = set(self.concept_by_id)
        for c in self.concepts:
            for p in c.prerequisites:
                if p not in cids:
                    problems.append(f"concept {c.id}: unknown prerequisite {p}")
        state: dict[str, int] = {}

        def cyclic(cid: str) -> bool:
            if state.get(cid) == 1:
                return True
            if state.get(cid) == 2:
                return False
            state[cid] = 1
            if any(p in self.concept_by_id and cyclic(p) for p in self.concept_by_id[cid].prerequisites):
                return True
            state[cid] = 2
            return False

        if any(cyclic(cid) for cid in cids):
            problems.append("prerequisite cycle")
        for m in self.misconceptions:
            if m.concept_id not in cids:
                problems.append(f"misconception {m.id}: unknown concept {m.concept_id}")
        for q in self.questions:
            if q.concept_id not in cids:
                problems.append(f"question {q.id}: unknown concept {q.concept_id}")
            if q.qtype not in QUESTION_TYPES:
                problems.append(f"question {q.id}: bad type {q.qtype}")
            if not q.groups:
                problems.append(f"question {q.id}: no answer key")
        for cid in self.learning_path:
            if cid not in cids:
                problems.append(f"learning path: unknown concept {cid}")
        return problems

    def dependents(self, concept_id: str) -> list[Concept]:
        """Concepts that build directly on this one ("what comes next")."""
        return [c for c in self.concepts if concept_id in c.prerequisites]


def build(
    concepts: tuple[Concept, ...],
    misconceptions: tuple[Misconception, ...],
    questions: tuple[ConceptQuestion, ...],
    starters: tuple[str, ...] = (),
    learning_path: tuple[str, ...] = (),
) -> CourseKnowledge:
    return CourseKnowledge(
        concepts=concepts,
        misconceptions=misconceptions,
        questions=questions,
        starters=starters,
        learning_path=learning_path,
        concept_by_id={c.id: c for c in concepts},
        misconception_by_id={m.id: m for m in misconceptions},
        question_by_id={q.id: q for q in questions},
    )
