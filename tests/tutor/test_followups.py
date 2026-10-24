import pytest

from src.tutor import followups as fu
from src.tutor.os_course import KNOWLEDGE as K


@pytest.mark.parametrize("text,cid", [
    ("what is a page table", "page_table"),
    ("How does paging work, in simple terms?", "paging"),
    ("explain fork and exec", "fork_exec_wait"),
    ("what is a deadlock", "deadlock"),
    ("what happens on a TLB miss", "tlb"),
    ("difference between a mutex and a semaphore", "semaphores"),
    ("what is a context switch", "context_switch"),
    ("round robin vs FCFS", "scheduling"),
    ("how do I use grep", "linux_commands"),
])
def test_concept_detection(text, cid):
    assert fu.concept_for_text(text) == cid


def test_specific_beats_generic():
    assert fu.concept_for_text("what is a process control block") == "pcb"


def test_unknown_topic_is_none():
    assert fu.concept_for_text("what is the capital of france") is None


def test_chips_name_the_concept_and_dedupe():
    chips = fu.concept_chips("tlb", [], has_questions=True, understood=False, prereq_gap=None)
    assert all("TLB" in c for c in chips)
    again = fu.concept_chips("tlb", chips, has_questions=True, understood=False, prereq_gap=None)
    assert not set(c.lower() for c in again) & set(c.lower() for c in chips)


def test_prereq_chip_when_gap():
    chips = fu.concept_chips("tlb", [], has_questions=True, understood=False, prereq_gap="page_table")
    assert any("before learning" in c for c in chips)


def test_source_chips_from_titles():
    srcs = [{"metadata": {"slide_title": "Memory\nPaging / What is a page table?"}},
            {"metadata": {"slide_title": "x"}},
            {"metadata": {"slide_title": "Memory\nPaging / What is a page table?"}}]
    assert fu.source_chips(srcs, []) == ["Tell me more about: What is a page table"]


def test_clean_title_rejects_junk():
    assert fu.clean_title("x") is None
    assert fu.clean_title("") is None
    assert fu.clean_title("a" * 90) is None


def test_starter_chips_skip_touched_topics():
    chips = fu.starter_chips({"records": {"os_role": {}}})
    assert all("operating system" not in c.lower() or "user mode" in c.lower() for c in chips)


GOOD = '{"socratic":"Why does the OS save registers during a context switch?","follow_ups":["What is a PCB used for?","How does a timer interrupt help the scheduler?"]}'


def test_parse_followups_happy_path():
    s, chips = fu.parse_followups(GOOD, asked_question="what is a context switch")
    assert s.endswith("?") and len(chips) == 2


def test_parse_followups_filters_bad_items():
    raw = ('{"socratic":"ok","follow_ups":["what is it?","What is a context switch exactly right now?",'
           '"See https://x.com for more info please?","How does the timer interrupt help the scheduler regain the CPU?"]}')
    s, chips = fu.parse_followups(raw, asked_question="what is a context switch exactly right now")
    assert s is None  # "ok" is not a valid question
    assert chips == ["How does the timer interrupt help the scheduler regain the CPU?"]


def test_parse_followups_drops_repeats_of_history():
    s, chips = fu.parse_followups(GOOD, asked_question="x", avoid=["What is a PCB used for?"])
    assert chips == ["How does a timer interrupt help the scheduler?"]


@pytest.mark.parametrize("raw", ["", "not json", "[1,2]", '{"socratic": 5}', "```json\n{broken"])
def test_parse_followups_never_raises(raw):
    assert fu.parse_followups(raw, asked_question="q") == (None, [])


def test_parse_followups_strips_code_fence():
    s, chips = fu.parse_followups("```json\n" + GOOD + "\n```", asked_question="x")
    assert s and chips
