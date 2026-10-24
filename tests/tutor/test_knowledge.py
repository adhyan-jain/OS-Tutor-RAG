"""The authored knowledge must be self-consistent, and each question's own model
answer must pass its own key (otherwise a student giving exactly the right answer
could be marked wrong)."""

import pytest

from src.tutor import pedagogy as ped
from src.tutor import triage
from src.tutor.os_course import KNOWLEDGE as K


def test_structure_is_valid():
    assert K.validate() == []


def test_every_concept_has_a_question_and_alias():
    with_q = {q.concept_id for q in K.questions}
    assert set(K.concept_by_id) <= with_q
    assert all(c.aliases for c in K.concepts)


def test_learning_path_covers_every_concept_once():
    assert sorted(K.learning_path) == sorted(K.concept_by_id)


@pytest.mark.parametrize("q", K.questions, ids=lambda q: q.id)
def test_model_answer_passes_its_own_key(q):
    assert ped.classify_answer(q, q.expected_reasoning, K).label == "CORRECT"


@pytest.mark.parametrize("q", K.questions, ids=lambda q: q.id)
def test_keys_are_well_formed(q):
    assert all(isinstance(g, tuple) and g for g in q.groups)
    assert 1 <= q.need <= len(q.groups)


@pytest.mark.parametrize("q", K.questions, ids=lambda q: q.id)
@pytest.mark.parametrize("text", ["I don't know", "idk", "", "hmm"])
def test_no_answer_is_never_correct(q, text):
    assert ped.classify_answer(q, text, K).label == "UNCLEAR"


def test_dont_know_is_flagged():
    q = K.question_by_id["q_three_states"]
    assert ped.classify_answer(q, "I don't know", K).dont_know


@pytest.mark.parametrize("q", K.questions, ids=lambda q: q.id)
def test_course_questions_never_trip_triage(q):
    assert triage.classify(q.ask) is triage.Intent.COURSE


def test_starters_never_trip_triage():
    assert all(triage.classify(s) is triage.Intent.COURSE for s in K.starters)


@pytest.mark.parametrize("m", K.misconceptions, ids=lambda m: m.id)
def test_misconceptions_have_probe_and_correction(m):
    assert m.probe.endswith("?")
    assert len(m.correction) > 30


def test_misconception_detection_and_negation():
    m = K.misconception_by_id["threads_own_memory"]
    assert ped.misconception_hit(m, "threads each have their own address space")
    assert not ped.misconception_hit(m, "it is not true that threads have their own address space")
