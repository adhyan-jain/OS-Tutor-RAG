import pytest

from src.tutor import pedagogy as ped
from src.tutor.os_course import KNOWLEDGE as K


def test_state_never_regresses_on_partial_or_unclear():
    cs = ped.ConceptStates()
    ped.apply_classification(cs, "locks", "CORRECT", question_id="q_lock_guarantee")
    assert cs.get("locks").state == "UNDERSTOOD"
    ped.apply_classification(cs, "locks", "PARTIAL", question_id="q_flag_lock")
    ped.apply_classification(cs, "locks", "UNCLEAR", question_id="q_flag_lock")
    assert cs.get("locks").state == "UNDERSTOOD"


def test_misconception_drops_understood_one_step():
    cs = ped.ConceptStates()
    ped.apply_classification(cs, "locks", "CORRECT")
    ped.apply_classification(cs, "locks", "MISCONCEPTION", misconception_id="x")
    assert cs.get("locks").state == "PARTIALLY_UNDERSTOOD"


def test_mastery_only_from_understood_via_transfer():
    cs = ped.ConceptStates()
    ped.mark_mastered(cs, "locks")
    assert cs.get("locks").state == "UNKNOWN"
    ped.apply_classification(cs, "locks", "CORRECT")
    ped.mark_mastered(cs, "locks")
    assert cs.get("locks").state == "MASTERED"


def test_advisory_is_clamped():
    cs = ped.ConceptStates()
    ped.apply_advisory(cs, "locks", "CORRECT")
    assert cs.get("locks").state == "ATTEMPTED"  # at most one level up from UNKNOWN
    ped.apply_advisory(cs, "locks", "CORRECT")
    assert cs.get("locks").state == "PARTIALLY_UNDERSTOOD"
    ped.apply_advisory(cs, "locks", "CORRECT")
    assert cs.get("locks").state == "PARTIALLY_UNDERSTOOD"  # never UNDERSTOOD
    ped.apply_advisory(cs, "locks", "UNCLEAR")
    ped.apply_advisory(cs, "locks", "BOGUS")
    assert cs.get("locks").state == "PARTIALLY_UNDERSTOOD"


def test_advisory_history_names_its_source():
    cs = ped.ConceptStates()
    ped.apply_advisory(cs, "locks", "PARTIAL")
    assert cs.get("locks").history[-1]["source"] == "llm_advisory"


def test_roundtrip():
    cs = ped.ConceptStates()
    cs.tick()
    ped.apply_classification(cs, "paging", "PARTIAL", question_id="q_pages_frames")
    back = ped.ConceptStates.from_dict(cs.to_dict())
    assert back.get("paging").state == "PARTIALLY_UNDERSTOOD" and back.seq == 1


def test_question_choice_follows_state_and_never_repeats():
    cs = ped.ConceptStates()
    seen = set()
    for _ in range(10):
        q = ped.choose_question(K, "deadlock", cs.get("deadlock"))
        if q is None:
            break
        assert q.id not in seen
        seen.add(q.id)
        cs.get("deadlock").asked.append(q.id)
    assert len(seen) == len([q for q in K.questions if q.concept_id == "deadlock"])


def test_first_question_is_recall():
    q = ped.choose_question(K, "paging", ped.ConceptRecord())
    assert q.qtype == "OBSERVATION"


def test_next_after_answer_ladder():
    q = K.question_by_id["q_three_states"]
    cs = ped.ConceptStates()
    cls = ped.classify_answer(q, "ready", K)
    assert cls.label == "PARTIAL"
    rec = ped.apply_classification(cs, q.concept_id, cls.label, question_id=q.id)
    assert ped.next_after_answer(K, q, cls, rec).kind == "scaffold"
    rec = ped.apply_classification(cs, q.concept_id, cls.label, question_id=q.id)
    f = ped.next_after_answer(K, q, cls, rec)
    assert f.kind == "explain" and f.text == q.expected_reasoning


def test_misconception_gets_probe_then_correction():
    q = K.question_by_id["q_thread_share"]
    cs = ped.ConceptStates()
    cls = ped.classify_answer(q, "threads each have their own address space", K)
    assert cls.label == "MISCONCEPTION" and cls.misconception_id == "threads_own_memory"
    rec = ped.apply_classification(cs, q.concept_id, cls.label, question_id=q.id, misconception_id=cls.misconception_id)
    assert ped.next_after_answer(K, q, cls, rec).kind == "probe"
    rec = ped.apply_classification(cs, q.concept_id, cls.label, question_id=q.id, misconception_id=cls.misconception_id)
    assert ped.next_after_answer(K, q, cls, rec).kind == "explain"


def test_deeper_question_goes_up_a_level():
    q = K.question_by_id["q_three_states"]
    nxt = ped.deeper_question(K, q, ped.ConceptRecord())
    assert nxt is not None and ped.LEVEL[nxt.qtype] > ped.LEVEL[q.qtype]


def test_cooldown_and_understood_block_followups():
    cs = ped.ConceptStates()
    assert ped.may_open_followup(cs, "locks")
    cs.tick()
    ped.apply_classification(cs, "locks", "PARTIAL")
    assert not ped.may_open_followup(cs, "locks")  # inside cooldown
    for _ in range(ped.CONCEPT_COOLDOWN_TURNS):
        cs.tick()
    assert ped.may_open_followup(cs, "locks")
    ped.apply_classification(cs, "locks", "CORRECT")
    for _ in range(10):
        cs.tick()
    assert not ped.may_open_followup(cs, "locks")  # understood


def test_parroted_hint_detected():
    q = K.question_by_id["q_three_states"]
    assert ped.is_parroted_hint(q, q.scaffold)
    assert not ped.is_parroted_hint(q, "running ready and blocked")
