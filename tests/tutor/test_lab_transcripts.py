"""Messages real students sent an earlier course tutor, rewritten for OS content.

The shape of the traffic is what matters: about a third of messages are three words
or fewer ("done", "yes", "next", "hi bro"), many are not questions at all ("I am not
satisfied", "give me a video", "in simple words"), and a tutor that answers each with
a wall of text, or the same canned line twice, feels broken. These tests pin the
behaviour for those messages, with no model and no retrieval.
"""

import pytest

from src.tutor import conversation as conv
from src.tutor import engine
from src.tutor.conversation import Intent
from src.tutor.engine import RagPlan, Reply
from src.tutor.os_course import KNOWLEDGE as K

MAX_AUTHORED = 450  # characters; the path reply is the longest authored text


def say(state, msg):
    return engine.plan_turn(state, msg)


def after_answer(topic_msg="what is a page table?"):
    """A state that has just been explained a topic (question pending)."""
    s = conv.TutorState()
    plan = say(s, topic_msg)
    assert isinstance(plan, RagPlan)
    engine.finish_rag(s, plan, message=topic_msg, sources=[])
    return s


@pytest.mark.parametrize("msg,intent", [
    ("done", Intent.ACK), ("Yes", Intent.ACK), ("ok", Intent.ACK), ("okay", Intent.ACK),
    ("yes please", Intent.ACK), ("got it", Intent.ACK), ("ok done", Intent.ACK),
    ("next", Intent.SKIP), ("next step", Intent.SKIP), ("ok next", Intent.SKIP), ("Next topic", Intent.SKIP),
    ("hi", Intent.GREETING), ("hi bro", Intent.GREETING), ("hello there", Intent.GREETING), ("hii", Intent.GREETING),
    ("let's start", Intent.PATH), ("just tell me", Intent.TELL_ME), ("give me a hint", Intent.HINT),
    ("I am not satisfied with your answer", Intent.DISSATISFIED), ("that didn't help", Intent.DISSATISFIED),
    ("Give me the video", Intent.CAPABILITY), ("Atleast provide me ppt or pdf", Intent.CAPABILITY),
    ("Can u generate any images", Intent.CAPABILITY),
    ("Give me in simple words", Intent.STRUGGLE), ("in simple words please", Intent.STRUGGLE),
    ("explain that more simply", Intent.STRUGGLE),
    ("step by step in bullet points", Intent.FORMAT), ("as a list please", Intent.FORMAT),
    ("Give that as short bullet points", Intent.FORMAT),
    ("what is a page table", Intent.QUESTION), ("why do this step?", Intent.QUESTION),
])
def test_short_real_messages_resolve_to_the_right_intent(msg, intent):
    assert conv.classify(msg) is intent


def test_starter_chip_in_simple_words_is_still_a_normal_explain():
    # "Explain X in simple words" is a chip text; it must not read as the student being confused.
    assert conv.classify("Explain paging in simple words") is Intent.QUESTION


def test_done_with_a_question_open_asks_for_a_real_attempt_and_keeps_it_open():
    s = after_answer()
    assert s.pending
    q_id = s.pending["question_id"]
    r = say(s, "done")
    assert isinstance(r, Reply) and r.events["verdict"] == "ack_nudge"
    assert s.pending["question_id"] == q_id
    assert "Hint" in r.text and r.ui["chips"]


def test_done_with_nothing_open_moves_to_the_next_idea():
    s = after_answer()
    say(s, "skip")  # drop the question
    assert not s.pending
    plan = say(s, "ok")
    assert isinstance(plan, RagPlan) and plan.events["verdict"] == "advance"
    assert plan.lead.startswith("Next up:") and plan.concept_id != s.topic


def test_done_at_the_very_start_shows_the_path_not_a_random_topic():
    r = say(conv.TutorState(), "yes")
    assert isinstance(r, Reply) and r.ui["kind"] == "path"


def test_hi_bro_and_thanks_and_how_are_you_get_a_warm_short_reply_with_chips():
    for msg in ("hi bro", "how are you", "thanks", "who are you", "bye"):
        s = conv.TutorState()
        r = say(s, msg)
        assert isinstance(r, Reply) and 0 < len(r.text) <= MAX_AUTHORED
        assert r.ui["chips"], msg


def test_the_same_canned_reply_is_never_sent_twice_in_a_row():
    s = conv.TutorState()
    first = say(s, "how are you")
    second = say(s, "how are you")
    assert first.text != second.text and second.events.get("repeat_guard")
    third = say(s, "hi")
    assert third.text != second.text


def test_video_request_is_honest_and_offers_something_useful():
    s = after_answer()
    r = say(s, "show me with the help of video step by step")
    assert isinstance(r, Reply) and r.events["verdict"] == "capability"
    assert "text" in r.text and any("bullet" in c.lower() for c in r.ui["chips"])
    assert s.pending  # a side request does not drop the open question
    assert "back to my question" in r.text


def test_not_satisfied_offers_three_ways_to_fix_it():
    s = after_answer()
    r = say(s, "I am not satisfied with your answer")
    assert r.events["verdict"] == "dissatisfied" and len(r.ui["chips"]) == 3


def test_bullet_request_reshapes_the_last_answer_without_a_new_quiz_question():
    s = after_answer()
    plan = say(s, "Can't u provide me step by step like a bullet in points")
    assert isinstance(plan, RagPlan) and plan.events["verdict"] == "format" and plan.continuation
    assert "bullet" in plan.query.lower()
    fin = engine.finish_rag(s, plan, message="x", sources=[])
    assert "Think about this" not in fin.text


def test_bullets_for_a_named_topic_is_just_a_normal_question():
    s = after_answer()
    plan = say(s, "explain deadlock step by step")
    assert isinstance(plan, RagPlan) and plan.events["verdict"] != "format"


def test_answer_chips_are_three_complete_distinct_messages():
    s = conv.TutorState()
    plan = say(s, "what is a page table?")
    s.pending = None  # look at the chip layer, not the question
    fin = engine.finish_rag(s, plan, message="x", sources=[], socratic=False)
    chips = fin.ui["chips"]
    assert len(chips) == 3 and len({c.lower() for c in chips}) == 3
    assert all(len(c.split()) >= 3 for c in chips)
    # each chip names its topic, so it makes sense when tapped on its own
    assert all(conv.classify(c) is not Intent.ANSWER for c in chips)


def test_every_authored_reply_stays_small():
    """Walk each authored branch for several concepts and bound the length."""
    worst = 0
    for cid in [c.id for c in K.concepts][:12]:
        questions = [q for q in K.questions if q.concept_id == cid]
        if not questions:
            continue
        for flow in (["hint", "just tell me"], ["no idea", "i give up"], ["skip"], ["done", "i don't understand"]):
            s = conv.TutorState()
            plan = say(s, f"Explain {K.concept_by_id[cid].name}")
            engine.finish_rag(s, plan, message="x", sources=[])
            for msg in flow:
                r = say(s, msg)
                if isinstance(r, Reply):
                    worst = max(worst, len(r.text))
                    assert len(r.text) <= MAX_AUTHORED, (cid, msg, len(r.text), r.text)
    assert worst > 0


def test_path_reply_is_a_short_list():
    r = say(conv.TutorState(), "I'm new to operating systems")
    assert len(r.text) <= MAX_AUTHORED and r.text.count("\n- ") == 3


def test_a_whole_session_in_one_chat():
    """New student -> path -> learn -> asked a question -> hint -> told -> bullets ->
    thanks -> next idea -> quiz -> summary. One state throughout, nothing dropped."""
    s = conv.TutorState()
    r = say(s, "I'm new to operating systems")
    assert r.ui["kind"] == "path"

    plan = say(s, r.ui["chips"][0])
    fin = engine.finish_rag(s, plan, message=r.ui["chips"][0], sources=[])
    assert s.pending and "Think about this" in fin.text

    hint = say(s, "give me a hint")
    assert hint.text.startswith("**Hint:**") and s.pending
    told = say(s, "just tell me")
    assert "short version" in told.text and not s.pending and len(told.ui["chips"]) == 3

    bullets = say(s, "in bullet points")
    assert isinstance(bullets, RagPlan) and bullets.no_question

    hello = say(s, "thanks")
    assert isinstance(hello, Reply) and hello.ui["chips"]

    nxt = say(s, "next")
    assert isinstance(nxt, RagPlan) and nxt.events["verdict"] == "advance"
    engine.finish_rag(s, nxt, message="next", sources=[])

    quiz = say(s, "test my understanding")
    assert isinstance(quiz, Reply) and quiz.ui["kind"] == "question"
    for _ in range(6):
        if not s.quiz:
            break
        say(s, "skip")
    assert not s.quiz
    assert engine.progress(s)["total"] == len(K.concepts)
