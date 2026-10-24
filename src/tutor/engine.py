"""The tutoring engine: one pure function per half-turn.

``plan_turn`` runs BEFORE retrieval. It either fully handles the message with
authored text (``Reply``: triage, orientation, a graded answer to the pending
Socratic question, a hint, a quiz question...) or hands it on to the RAG
pipeline as a ``RagPlan``.

``finish_rag`` runs AFTER the grounded answer has been produced. It picks the
single Socratic question to append (if any) and the follow-up chips.

Neither calls a model. The only model involvement lives in the API route and is
advisory: a clamped classification of a free-text answer the authored keys could
not read (``realise``), and model-written follow-up questions that code
validates (``followups.parse_followups``). Policy is code; the model phrases.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from . import conversation as conv
from . import followups as fu
from . import pedagogy as ped
from . import triage
from .conversation import Intent, TutorState
from .knowledge import Concept, ConceptQuestion
from .os_course import KNOWLEDGE as K

QUIZ_LENGTH = 3

STATE_LABEL = {
    "UNKNOWN": "new", "INTRODUCED": "introduced", "ATTEMPTED": "attempted",
    "PARTIALLY_UNDERSTOOD": "getting there", "UNDERSTOOD": "understood", "MASTERED": "mastered",
}


@dataclass
class Reply:
    """A turn handled entirely by code."""

    text: str
    ui: dict[str, Any]
    events: dict[str, Any] = field(default_factory=dict)
    #: Context for the optional single advisory model call (free-text answer the
    #: authored keys could not classify). None for almost every turn.
    realise: dict[str, Any] | None = None


@dataclass
class RagPlan:
    """A turn that needs the retrieval pipeline."""

    query: str
    detail_override: str | None = None
    lead: str = ""  # authored opening line shown before the grounded answer
    resume_line: str = ""  # authored line pointing back to a pending question
    concept_id: str | None = None
    struggling: bool = False
    misconception_note: str = ""
    continuation: bool = False
    #: A re-shaping of the last answer ("as bullet points"): no new Socratic question after it.
    no_question: bool = False
    events: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------ helpers


def _short(text: str, limit: int = 90) -> str:
    """First sentence of ``text``, cut at a word boundary if still longer than ``limit``."""
    first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    if len(first) <= limit:
        return first
    cut = first[:limit].rsplit(" ", 1)[0].rstrip(",;:-")
    return cut + "…"


def _states(state: TutorState) -> ped.ConceptStates:
    return ped.ConceptStates.from_dict(state.concepts)


def _save(state: TutorState, cs: ped.ConceptStates) -> None:
    state.concepts = cs.to_dict()


def _concept_card(cid: str, cs: ped.ConceptStates) -> dict[str, Any]:
    c = K.concept_by_id[cid]
    st = cs.records.get(cid).state if cid in cs.records else "UNKNOWN"
    return {"id": c.id, "name": c.name, "text": c.description, "state": st, "state_label": STATE_LABEL[st]}


def _question_ui(q: ConceptQuestion, source: str) -> dict[str, Any]:
    return {
        "id": q.id, "type": q.qtype, "level": ped.LEVEL_NAMES[ped.LEVEL.get(q.qtype, 1)],
        "concept": K.concept_by_id[q.concept_id].name, "source": source,
    }


def _chips(state: TutorState, items: list[str], *, limit: int = 4) -> list[str]:
    """Dedupe against what was already offered or tapped; remember what is shown."""
    seen = set(state.asked_chips)
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key in seen or any(key == o.lower() for o in out):
            continue
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _remember(state: TutorState, chips: list[str]) -> None:
    for chip in chips:
        key = chip.strip().lower()
        if key not in state.asked_chips and not any(key == conv_text.lower() for conv_text in conv.ACTIONS.values()):
            state.asked_chips.append(key)
    state.asked_chips[:] = state.asked_chips[-40:]


def _reply(state: TutorState, text: str, kind: str, chips: list[str], *, cid: str | None = None,
           cs: ped.ConceptStates | None = None, question: dict | None = None,
           events: dict | None = None, realise: dict | None = None, remember: bool = True) -> Reply:
    ui: dict[str, Any] = {"kind": kind, "chips": chips}
    if cid and cs is not None:
        ui["concept"] = _concept_card(cid, cs)
    if question:
        ui["question"] = question
    if remember:
        _remember(state, chips)
    return Reply(text, ui, events or {}, realise)


def _next_step_chips(state: TutorState, cs: ped.ConceptStates, cid: str | None) -> list[str]:
    if cid is None:
        return _chips(state, fu.starter_chips(state.concepts), limit=3)
    rec = cs.records.get(cid)
    understood = bool(rec and rec.state in ped.UNDERSTOOD_OR_BETTER)
    has_q = any(q.concept_id == cid for q in K.questions)
    gap = ped.prerequisite_gap(K, cs, cid)
    return _chips(state, fu.concept_chips(cid, state.asked_chips, has_questions=has_q, understood=understood, prereq_gap=gap),
                  limit=3)


def _question_chips(q_hinted: bool, scaffold: str) -> list[str]:
    chips = []
    if scaffold and not q_hinted:
        chips.append(conv.ACTIONS["hint"])
    chips += [conv.ACTIONS["tell_me"], conv.ACTIONS["skip"]]
    return chips


def _ask(state: TutorState, cs: ped.ConceptStates, q: ConceptQuestion, source: str, lead: str = "") -> Reply:
    """Pose an authored question and remember it as pending."""
    ped.introduce(cs, q.concept_id)
    rec = cs.get(q.concept_id)
    rec.last_seq = cs.seq
    if q.id not in rec.asked:  # a skipped question is still asked: never repeat it
        rec.asked.append(q.id)
    state.pending = {
        "kind": "authored", "question_id": q.id, "concept_id": q.concept_id,
        "hinted": False, "simplified": 0, "source": source,
    }
    state.topic = q.concept_id
    _save(state, cs)
    label = "A quick question" if source == "quiz" else "Think about this"
    if source == "quiz" and state.quiz:
        label = f"Question {state.quiz['asked']} of {state.quiz['total']}"
    parts = [lead] if lead else []
    parts.append(f"**{label}:** {q.ask}")
    chips = _question_chips(False, q.scaffold)
    return _reply(state, "\n\n".join(parts), "question", chips, cid=q.concept_id, cs=cs,
                  question=_question_ui(q, source), events={"verdict": f"{source}_question", "question_id": q.id},
                  remember=False)


def _pending_question(state: TutorState) -> ConceptQuestion | None:
    p = state.pending
    if not p or p.get("kind") != "authored":
        return None
    return K.question_by_id.get(p.get("question_id", ""))


def resume_line(state: TutorState) -> str:
    p = state.pending
    if not p:
        return ""
    if p.get("kind") == "authored":
        q = _pending_question(state)
        return f"\n\nWhenever you're ready, back to my question: **{q.ask}**" if q else ""
    return f"\n\nWhenever you're ready, back to my question: **{p.get('question', '')}**"


# ------------------------------------------------------------- orientation


def _path_reply(state: TutorState, cs: ped.ConceptStates, lead: str = "") -> Reply:
    remaining = [cid for cid in K.learning_path
                 if cid not in cs.records or cs.records[cid].state not in ped.UNDERSTOOD_OR_BETTER]
    if not remaining:
        text = "You've worked through the whole path, nicely done. Pick any topic to go deeper, or ask me for a quiz."
        return _reply(state, text, "path", _chips(state, ["Test my understanding of deadlock", "Test my understanding of paging"]), cs=cs)
    nxt = remaining[:3]
    lines = [f"- **{K.concept_by_id[c].name}**: {_short(K.concept_by_id[c].description, 75)}" for c in nxt]
    touched = len(K.learning_path) - len(remaining)
    intro = lead or ("Let's build up from the foundations. I'd start here:" if touched == 0
                     else "Here is what I'd look at next:")
    text = (f"{intro}\n\n" + "\n".join(lines) +
            "\n\nTap one to begin, or ask in your own words. No silly questions here.")
    # Offered as-is, not de-duplicated: the orientation reply just before may have shown
    # the same three, and a path reply with no chips would leave the student stuck.
    chips = [f"Explain {fu.term(K.concept_by_id[c])} in simple words" for c in nxt]
    _remember(state, chips)
    state.topic = state.topic
    return _reply(state, text, "path", chips, cs=cs, events={"verdict": "path", "next": nxt})


def _orientation(state: TutorState, cs: ped.ConceptStates, kind: str) -> Reply:
    state.lost_count += 1
    openers = ("That's completely fine, plenty of people don't know where to begin. ",
               "No worries, you don't need a perfect question. ",
               "Not sure what to ask? That's okay. ")
    head = openers[(state.lost_count - 1) % len(openers)]
    if kind == "greeting":
        head = "Hi! I'm your OS tutor. "
    elif kind == "help":
        head = "Of course, I'm right here and happy to help. No question is too small. "
    text = (head + "I answer from your course slides and OSTEP chapters, and ask a small question now and then. "
            "We can start from the basics, or you can pick something below.")
    chips = _chips(state, [conv.ACTIONS["path"], *fu.starter_chips(state.concepts, 3)], limit=4)
    return _reply(state, text, "orientation", chips, cs=cs, events={"verdict": f"orientation_{kind}"})


def _advance(state: TutorState, cs: ped.ConceptStates) -> Reply | RagPlan:
    """"done" / "ok" / "next" with nothing pending: move on to the next idea in the
    path. Never-touched concepts come first, so the student does not circle back."""
    if state.topic is None:
        return _path_reply(state, cs)
    unseen = [c for c in K.learning_path if c not in cs.records or cs.records[c].state == "UNKNOWN"]
    later = [c for c in K.learning_path if c != state.topic and c in cs.records
             and cs.records[c].state not in ped.UNDERSTOOD_OR_BETTER]
    pool = [c for c in unseen if c != state.topic] or later
    if not pool:
        return _path_reply(state, cs)
    nxt = K.concept_by_id[pool[0]]
    return RagPlan(query=f"Explain {nxt.name} in simple words.", concept_id=nxt.id, lead=f"Next up: **{nxt.name}**.",
                   events={"verdict": "advance", "next": nxt.id})


def _capability(state: TutorState, cs: ped.ConceptStates) -> Reply:
    text = ("I can only reply in text here, so no video, audio, images or slides. What I can do is explain it "
            "step by step in short points, or give a tiny example.")
    if state.topic:
        chips = _chips(state, [conv.ACTIONS["bullets"], conv.ACTIONS["example"], conv.ACTIONS["next_topic"]], limit=3)
    else:
        chips = _chips(state, [conv.ACTIONS["path"], *fu.starter_chips(state.concepts, 2)], limit=3)
    return _reply(state, text + resume_line(state), "feedback", chips, cid=state.topic, cs=cs if state.topic else None,
                  events={"verdict": "capability"})


def _dissatisfied(state: TutorState, cs: ped.ConceptStates) -> Reply:
    text = "Sorry that didn't land. I can say it more simply, give an example, or list the steps. Which helps most?"
    if state.topic:
        chips = _chips(state, [conv.ACTIONS["simpler"], conv.ACTIONS["example"], conv.ACTIONS["bullets"]], limit=3)
    else:
        chips = _chips(state, [conv.ACTIONS["path"], *fu.starter_chips(state.concepts, 2)], limit=3)
    return _reply(state, text + resume_line(state), "feedback", chips, cid=state.topic, cs=cs if state.topic else None,
                  events={"verdict": "dissatisfied"})


def _format_plan(state: TutorState, message: str) -> RagPlan:
    c = K.concept_by_id[state.topic] if state.topic else None
    where = f" (Topic: {c.name}.)" if c else ""
    return RagPlan(query=f"{message}{where} Answer as 3 to 4 short bullet points.", concept_id=state.topic,
                   continuation=True, no_question=True, resume_line=resume_line(state), events={"verdict": "format"})


# -------------------------------------------------------------------- quiz


def _quiz_summary(state: TutorState, cs: ped.ConceptStates) -> Reply:
    quiz = state.quiz or {}
    cid = quiz.get("concept_id")
    state.quiz = None
    state.pending = None
    _save(state, cs)
    if not cid:
        return _reply(state, "No problem, we'll carry on.", "feedback", _next_step_chips(state, cs, state.topic), cs=cs)
    name = K.concept_by_id[cid].name
    rec = cs.get(cid)
    total, correct = quiz.get("asked", 0), quiz.get("correct", 0)
    if rec.state in ped.UNDERSTOOD_OR_BETTER:
        verdict = f"You've got a solid grip on **{name}** now."
    elif rec.state == "PARTIALLY_UNDERSTOOD":
        verdict = f"You're getting there with **{name}**; one more pass over the explanation should lock it in."
    else:
        verdict = f"**{name}** is still new to you, and that's fine. Let's go through it together first."
    text = f"That's the quiz: you answered {correct} of {total} fully. {verdict}"
    chips = _next_step_chips(state, cs, cid)
    if rec.state not in ped.UNDERSTOOD_OR_BETTER:
        chips = _chips(state, [f"Explain {fu.term(K.concept_by_id[cid])} more simply"] + chips)
    return _reply(state, text, "quiz_summary", chips, cid=cid, cs=cs, events={"verdict": "quiz_done", "correct": correct, "asked": total})


def _quiz_next(state: TutorState, cs: ped.ConceptStates, lead: str = "", prefer: ConceptQuestion | None = None) -> Reply:
    quiz = state.quiz
    if not quiz or quiz["asked"] >= quiz["total"]:
        r = _quiz_summary(state, cs)
        r.text = f"{lead}\n\n{r.text}".strip()
        return r
    rec = cs.get(quiz["concept_id"])
    q = prefer or ped.choose_question(K, quiz["concept_id"], rec)
    if q is None:
        r = _quiz_summary(state, cs)
        r.text = f"{lead}\n\n{r.text}".strip()
        return r
    quiz["asked"] += 1
    return _ask(state, cs, q, "quiz", lead)


def _start_quiz(state: TutorState, cs: ped.ConceptStates, message: str) -> Reply:
    cid = fu.concept_for_text(message) or state.topic
    if cid is None:
        # Nothing to quiz on yet: orient instead of guessing a topic.
        r = _orientation(state, cs, "lost")
        r.text = ("I'd love to quiz you, but I'm not sure on what yet. Pick a topic, or ask me to explain "
                  "something first and I'll test you on it afterwards.")
        return r
    if not any(q.concept_id == cid for q in K.questions):
        return _reply(state, "I don't have quiz questions for that topic yet, but I can explain it. Ask away.",
                      "feedback", _next_step_chips(state, cs, cid), cid=cid, cs=cs)
    # A fresh quiz re-opens a concept even if the cooldown or a prior pass would block a follow-up.
    state.quiz = {"concept_id": cid, "asked": 0, "total": QUIZ_LENGTH, "correct": 0}
    state.pending = None
    c = K.concept_by_id[cid]
    lead = f"Let's check your understanding of **{c.name}**: {QUIZ_LENGTH} short questions. Answer in your own words; there are hints if you want them."
    return _quiz_next(state, cs, lead)


# ------------------------------------------------------- pending question

_TENTATIVE_START = re.compile(r"^\s*(?:can|could|should|is|are|does|do|did|will|would|isn'?t|doesn'?t)\b", re.I)
_FIRM_QUESTION_START = re.compile(
    r"^\s*(?:what|why|how|when|where|which|who|explain|describe|compare|define|list|difference|tell me|give|show|"
    r"walk me through|derive|trace|calculate|write|draw|summari[sz]e)\b", re.I)


def _is_attempt(q: ConceptQuestion, message: str) -> bool:
    """Whether the message is an attempt at the pending question rather than a
    fresh question. A firm question ("Compare FCFS and SJF") is never graded,
    even if it names a keyword; a tentative one ("is it the kernel?") is graded
    first and only treated as a question if it matches nothing."""
    if _FIRM_QUESTION_START.match(message) and len(message.split()) >= 4:
        return False
    if _TENTATIVE_START.match(message):
        return ped.classify_answer(q, message, K).label != "UNCLEAR"
    return True


def _finish_question(state: TutorState, cs: ped.ConceptStates, q: ConceptQuestion, lead: str, *, correct: bool) -> Reply:
    """The pending question is done (answered, explained or skipped)."""
    cid = q.concept_id
    state.pending = None
    if state.quiz and state.quiz.get("concept_id") == cid:
        if correct:
            state.quiz["correct"] += 1
        prefer = ped.deeper_question(K, q, cs.get(cid)) if correct else None
        if prefer is not None and state.quiz["asked"] >= state.quiz["total"]:
            prefer = None
        return _quiz_next(state, cs, lead, prefer=prefer)
    _save(state, cs)
    chips = _next_step_chips(state, cs, cid)
    return _reply(state, lead, "feedback", chips, cid=cid, cs=cs)


def _handle_pending(state: TutorState, cs: ped.ConceptStates, message: str, intent: Intent) -> Reply | RagPlan | None:
    p = state.pending
    if not p:
        return None
    if p.get("kind") == "free":
        return _handle_free_pending(state, cs, message, intent)
    q = _pending_question(state)
    if q is None:
        state.pending = None
        return None
    cid = q.concept_id
    concept = K.concept_by_id[cid]
    rec = cs.get(cid)

    if intent in (Intent.PATH, Intent.LOST, Intent.QUIZ, Intent.PREREQS, Intent.NEXT_TOPIC, Intent.GREETING, Intent.HELP_OPENER):
        state.pending = None  # a change of direction drops the question
        return None
    if intent is Intent.ACK and ped.classify_answer(q, message, K).label == "UNCLEAR":
        # "yes" / "ok" / "done" answers nothing: nudge toward a real attempt, keep the question open.
        return _reply(state, "Take a shot in your own words, even a rough guess helps. Or tap Hint if you'd like a nudge.",
                      "question", _question_chips(bool(p.get("hinted")), q.scaffold), cid=cid, cs=cs,
                      question=_question_ui(q, p.get("source", "followup")), events={"verdict": "ack_nudge"}, remember=False)
    if intent is Intent.SKIP:
        rec.last_seq = cs.seq
        return _finish_question(state, cs, q, "No problem, we'll carry on.", correct=False)
    if intent is Intent.HINT:
        if q.scaffold and not p.get("hinted"):
            p["hinted"] = True
            _save(state, cs)
            return _reply(state, f"**Hint:** {q.scaffold}", "question", _question_chips(True, q.scaffold), cid=cid, cs=cs,
                          question=_question_ui(q, p.get("source", "followup")), events={"verdict": "hint"}, remember=False)
        return _reply(state, 'That is the only hint I have for this one. Have a go, or say "just tell me" and I will show the idea.',
                      "question", _question_chips(True, q.scaffold), cid=cid, cs=cs, events={"verdict": "hint_repeated"}, remember=False)
    if intent is Intent.TELL_ME:
        ped.apply_classification(cs, cid, "UNCLEAR", question_id=q.id, reason="asked_for_answer")
        return _finish_question(state, cs, q, f"Here is the short version: {q.expected_reasoning}", correct=False)
    if intent is Intent.STRUGGLE:
        kind = conv.difficulty_kind(message) or "confused"
        times = int(p.get("simplified", 0))
        p["simplified"] = times + 1
        if times == 0:
            opener = conv.STRUGGLE_OPENERS.get(kind, conv.STRUGGLE_OPENERS["confused"])
            text = (f"{opener}\n\n**{concept.name}**, in simple terms: {_short(concept.description, 150)}\n\n"
                    f"**An easier way in:** {q.scaffold or q.ask}")
            p["hinted"] = True  # "an easier way in" is the scaffold: a following "hint" must not repeat it
            _save(state, cs)
            return _reply(state, text, "question", _question_chips(True, q.scaffold), cid=cid, cs=cs,
                          question=_question_ui(q, p.get("source", "followup")), events={"verdict": "simplified"}, remember=False)
        ped.apply_classification(cs, cid, "UNCLEAR", question_id=q.id, reason="struggle_twice")
        return _finish_question(state, cs, q, f"No problem, let's walk through it together. Here is the short version: {q.expected_reasoning}", correct=False)
    if intent is Intent.EXAMPLE:
        plan = RagPlan(query=f"Give a simple example of {concept.name} from the course material.", concept_id=cid,
                       resume_line=resume_line(state), events={"verdict": "side_question"})
        return plan
    if not _is_attempt(q, message):
        reminded = bool(p.get("reminded"))
        p["reminded"] = True
        return RagPlan(query=message, concept_id=fu.concept_for_text(message) or cid,
                       resume_line="" if reminded else resume_line(state), events={"verdict": "side_question"})
    return _grade(state, cs, q, message)


def _grade(state: TutorState, cs: ped.ConceptStates, q: ConceptQuestion, message: str) -> Reply:
    cid = q.concept_id
    if (state.pending or {}).get("hinted") and ped.is_parroted_hint(q, message):
        return _reply(state, "That's the hint again. Try putting the idea in your own words, even if you're not sure: "
                      "a rough attempt is more useful than a perfect copy.", "question",
                      _question_chips(True, q.scaffold), cid=cid, cs=cs, question=_question_ui(q, (state.pending or {}).get("source", "followup")),
                      events={"verdict": "parroted_hint"}, remember=False)
    before = cs.get(cid).state
    cls = ped.classify_answer(q, message, K)
    rec = ped.apply_classification(cs, cid, cls.label, question_id=q.id, misconception_id=cls.misconception_id)
    if cls.label == "CORRECT" and q.qtype == "TRANSFER" and before == "UNDERSTOOD":
        ped.mark_mastered(cs, cid)
    follow = ped.next_after_answer(K, q, cls, rec)
    events = {"verdict": f"graded_{cls.label.lower()}", "question_id": q.id, "classification": cls.label,
              "followup": follow.kind, "state_before": before, "state_after": rec.state,
              "misconception_id": cls.misconception_id, "source": "deterministic"}
    seq = cs.seq
    if follow.kind == "advance":
        lead = f"{conv.pick(conv.CORRECT_OPENERS, seq)} {q.expected_reasoning}"
        r = _finish_question(state, cs, q, lead, correct=True)
        r.events.update(events)
        return r
    if follow.kind == "explain":
        lead = f"Let's walk through it together. Here is the short version: {follow.text or q.expected_reasoning}"
        r = _finish_question(state, cs, q, lead, correct=False)
        r.events.update(events)
        return r
    # probe / scaffold: the question stays pending
    if follow.kind == "probe":
        note = f"{conv.pick(conv.MISCONCEPTION_OPENERS, seq)} {follow.text}"
    elif cls.label == "PARTIAL":
        note = f"{conv.pick(conv.PARTIAL_OPENERS, seq)} {follow.text}"
    elif cls.dont_know:
        note = f"{conv.pick(conv.UNSURE_OPENERS, seq)} {follow.text}"
    else:
        note = f"Good attempt. {follow.text}"
    _save(state, cs)
    p = state.pending or {}
    realise = None
    earnest_partial = cls.label == "PARTIAL" and len(message.split()) >= 6
    if (cls.label == "UNCLEAR" and not cls.dont_know) or earnest_partial:
        # The authored keys could not fully read an earnest free-text answer: one
        # advisory model call phrases the feedback (and may lift the state by at
        # most one clamped level). The authored scaffold stays the fallback.
        realise = {
            "concept_id": cid, "concept_name": K.concept_by_id[cid].name,
            "concept_description": K.concept_by_id[cid].description, "question": q.ask,
            "expected_reasoning": q.expected_reasoning, "concept_state": rec.state,
            "misses": rec.misses.get(q.id, 0), "student_answer": message,
        }
    return _reply(state, note, "question", _question_chips(bool(p.get("hinted")), q.scaffold), cid=cid, cs=cs,
                  question=_question_ui(q, p.get("source", "followup")), events=events, realise=realise, remember=False)


def _handle_free_pending(state: TutorState, cs: ped.ConceptStates, message: str, intent: Intent) -> Reply | RagPlan | None:
    """A model-written Socratic question has no answer key, so nothing is graded
    and no concept state moves on its account. The student's attempt gets a
    grounded, encouraging reply (via the advisory call) or an authored fallback."""
    p = state.pending or {}
    cid = p.get("concept_id")
    if intent in (Intent.PATH, Intent.LOST, Intent.QUIZ, Intent.PREREQS, Intent.NEXT_TOPIC, Intent.GREETING, Intent.HELP_OPENER):
        state.pending = None
        return None
    if intent in (Intent.SKIP, Intent.PAUSE):
        state.pending = None
        return _reply(state, "No problem, we'll carry on.", "feedback", _next_step_chips(state, cs, cid), cid=cid, cs=cs if cid else None)
    if intent is Intent.ACK:
        return _reply(state, "Go on, give it a try in one sentence. A rough answer is fine.", "question",
                      [conv.ACTIONS["tell_me"], conv.ACTIONS["skip"]], cid=cid, cs=cs if cid else None, remember=False)
    if intent in (Intent.QUESTION, Intent.EXAMPLE) and conv.is_new_request(message) or intent is Intent.CONTINUE:
        reminded = bool(p.get("reminded"))
        p["reminded"] = True
        return RagPlan(query=message, concept_id=fu.concept_for_text(message) or cid,
                       resume_line="" if reminded else resume_line(state), events={"verdict": "side_question"})
    if intent in (Intent.HINT, Intent.TELL_ME, Intent.STRUGGLE):
        state.pending = None
        text = ("No problem. Here's the idea in short: " + p.get("answer_hint", "re-read the answer above, then try putting the key "
                "point in one sentence of your own.")) if intent is Intent.TELL_ME else (
            "Let's make it smaller: re-read the last answer and pick the one sentence that matters most. What does it say, in your own words?")
        if intent is Intent.HINT:
            text = "Re-read the answer above and look for the one key word that answers it, then try again."
            return _reply(state, text, "question", [conv.ACTIONS["tell_me"], conv.ACTIONS["skip"]], cid=cid, cs=cs if cid else None, remember=False)
        return _reply(state, text, "feedback", _next_step_chips(state, cs, cid), cid=cid, cs=cs if cid else None)
    # an attempt
    state.pending = None
    realise = {
        "concept_id": cid or "", "concept_name": K.concept_by_id[cid].name if cid else "this topic",
        "concept_description": p.get("context", "")[:600], "question": p.get("question", ""),
        "expected_reasoning": "The key point(s) from the course material shown in the description.",
        "concept_state": "", "misses": 0, "student_answer": message, "free": True,
    }
    fallback = ("Thanks for having a go; putting it in your own words is exactly how it sticks. Compare it with the "
                "explanation above: did you capture the main point? If you'd like, I can explain it a different way.")
    chips = _next_step_chips(state, cs, cid)
    return _reply(state, fallback, "feedback", chips, cid=cid, cs=cs if cid else None, realise=realise,
                  events={"verdict": "free_attempt"})


# -------------------------------------------------------------------- plan


_REPEAT_TEXT = "Still here! Pick one of these, or ask in your own words."


def plan_turn(state: TutorState, message: str, *, socratic: bool = True) -> Reply | RagPlan:
    """One half-turn. Wraps the planner with a never-repeat guard: the same authored
    reply is never sent twice in a row (a real tutor stuck on one canned line)."""
    out = _plan_turn(state, message, socratic=socratic)
    return _no_repeat(state, out) if isinstance(out, Reply) else out


def _no_repeat(state: TutorState, reply: Reply) -> Reply:
    if reply.text.strip() == state.last_text.strip():
        reply.text = _REPEAT_TEXT
        reply.events["repeat_guard"] = True
    state.last_text = reply.text
    return reply


def off_topic(state: TutorState) -> Reply:
    """A question retrieval found nothing in the course for ("what is fear"): one
    friendly line and course chips, instead of a model call that rambles."""
    chips = _chips(state, [conv.ACTIONS["path"], *fu.starter_chips(state.concepts, 2)], limit=3)
    reply = _reply(state, triage.fixed_response(triage.Intent.OFF_SCOPE) or "", "triage", chips,
                   events={"verdict": "off_topic"})
    return _no_repeat(state, reply)


def _plan_turn(state: TutorState, message: str, *, socratic: bool = True) -> Reply | RagPlan:
    state.turns += 1
    cs = _states(state)
    cs.tick()

    tri = triage.classify(message)
    if triage.short_circuits(tri):
        text = triage.fixed_response(tri, message) or ""
        chips = _chips(state, [conv.ACTIONS["path"], *fu.starter_chips(state.concepts, 2)], limit=3)
        _save(state, cs)
        return _reply(state, text, "triage", chips, events={"verdict": f"triage_{tri.value}", "needs_attention": tri is triage.Intent.DISTRESS})

    intent = conv.classify(message)

    # Side requests that never need the knowledge base. They leave a pending question open.
    if intent is Intent.CAPABILITY:
        r = _capability(state, cs)
        _save(state, cs)
        return r
    if intent is Intent.DISSATISFIED:
        r = _dissatisfied(state, cs)
        _save(state, cs)
        return r
    if intent is Intent.FORMAT:
        firm = bool(_FIRM_QUESTION_START.match(message)) and len(message.split()) >= 5
        if fu.concept_for_text(message) or firm or state.topic is None:
            intent = Intent.QUESTION  # it names its own topic: just answer it
        else:
            _save(state, cs)
            return _format_plan(state, message)

    if intent is Intent.PAUSE:
        had = bool(state.quiz or state.pending)
        state.quiz = None
        state.pending = None
        _save(state, cs)
        text = "Okay, paused. No pressure: ask me anything, or say \"test my understanding\" whenever you want to pick it back up." if had \
            else "Sure. What would you like to look at?"
        return _reply(state, text, "feedback", _next_step_chips(state, cs, state.topic), cid=state.topic, cs=cs if state.topic else None,
                      events={"verdict": "paused"})

    handled = _handle_pending(state, cs, message, intent)
    if handled is not None:
        _save(state, cs)
        return handled

    if intent in (Intent.ACK, Intent.SKIP):
        # Nothing pending: "done" / "ok" / "next" means go on to the next idea.
        r = _advance(state, cs)
        _save(state, cs)
        return r
    if intent is Intent.QUIZ:
        r = _start_quiz(state, cs, message)
        _save(state, cs)
        return r
    if intent is Intent.PATH:
        r = _path_reply(state, cs)
        _save(state, cs)
        return r
    if intent in (Intent.LOST, Intent.HELP_OPENER, Intent.GREETING):
        kind = {"lost": "lost", "help_opener": "help", "greeting": "greeting"}[intent.value]
        r = _orientation(state, cs, kind)
        _save(state, cs)
        return r
    if intent is Intent.PREREQS:
        cid = fu.concept_for_text(message) or state.topic
        if cid:
            c = K.concept_by_id[cid]
            pre = [K.concept_by_id[p] for p in c.prerequisites]
            if pre:
                names = ", ".join(f"**{p.name}**" for p in pre)
                text = f"Before **{c.name}**, it helps to be comfortable with {names}. {pre[0].description}"
                chips = _chips(state, [f"Explain {fu.term(p)} in simple words" for p in pre] + [f"Explain {fu.term(c)} in simple words"])
            else:
                text = f"**{c.name}** is a good place to start: it doesn't depend on anything else in this course. {c.description}"
                chips = _next_step_chips(state, cs, cid)
            state.topic = cid
            _save(state, cs)
            return _reply(state, text, "feedback", chips, cid=cid, cs=cs, events={"verdict": "prereqs"})
    if intent is Intent.NEXT_TOPIC:
        cid = fu.concept_for_text(message) or state.topic
        if cid:
            deps = K.dependents(cid)
            if deps:
                c = K.concept_by_id[cid]
                names = ", ".join(f"**{d.name}**" for d in deps[:3])
                text = f"After **{c.name}**, the natural next steps are {names}."
                chips = _chips(state, [f"Explain {fu.term(d)} in simple words" for d in deps[:3]])
                _save(state, cs)
                return _reply(state, text, "feedback", chips, cid=cid, cs=cs, events={"verdict": "next_topic"})
        r = _path_reply(state, cs)
        _save(state, cs)
        return r

    # ---- needs the knowledge base
    cid = fu.concept_for_text(message)
    struggle = conv.difficulty_kind(message) if intent is Intent.STRUGGLE else None

    if intent is Intent.STRUGGLE:
        target = cid or state.topic
        if target is None:
            r = _orientation(state, cs, "lost")
            _save(state, cs)
            return r
        c = K.concept_by_id[target]
        opener = conv.STRUGGLE_OPENERS.get(struggle or "confused", conv.STRUGGLE_OPENERS["confused"])
        _save(state, cs)
        return RagPlan(
            query=f"Explain {c.name} in very simple words with an everyday analogy.", detail_override="eli5",
            lead=opener, concept_id=target, struggling=True, events={"verdict": "simplified_explanation", "struggle": struggle},
        )

    if intent is Intent.EXAMPLE and state.topic and not cid:
        c = K.concept_by_id[state.topic]
        _save(state, cs)
        return RagPlan(query=f"Give a simple example of {c.name} from the course material.", concept_id=state.topic,
                       events={"verdict": "example"})

    mis = ped.find_misconception(K, message)
    note = f"{mis.statement} (A likely misconception; gently address it: {mis.correction})" if mis else ""
    if mis and cid is None:
        cid = mis.concept_id
    _save(state, cs)
    return RagPlan(
        query=message, concept_id=cid, misconception_note=note, continuation=intent is Intent.CONTINUE,
        events={"verdict": "rag", "misconception_id": mis.id if mis else None},
    )


# ----------------------------------------------------------- after the answer


def finish_rag(
    state: TutorState,
    plan: RagPlan,
    *,
    message: str,
    sources: list[dict],
    refused: bool = False,
    socratic: bool = True,
) -> Reply:
    """After the grounded answer: the single Socratic question (if one fits) and
    the follow-up chips. ``Reply.text`` is the suffix to append to the answer."""
    cs = _states(state)
    cid = plan.concept_id
    if cid is None and sources:
        for s in sources[:4]:
            title = str((s.get("metadata") or {}).get("slide_title") or "")
            cid = fu.concept_for_text(title)
            if cid:
                break
    if cid is None:
        cid = fu.concept_for_text(message)
    if cid:
        ped.introduce(cs, cid)
        state.topic = cid

    suffix = plan.resume_line
    chips: list[str] = []

    # An answer that says the material doesn't cover it must not be followed by a quiz on it.
    if refused:
        chips = _chips(state, [conv.ACTIONS["lost"], *fu.starter_chips(state.concepts, 2)], limit=3)
        _save(state, cs)
        return Reply(suffix, {"kind": "answer", "chips": chips}, {"verdict": "refused"})

    if state.pending:
        # A question is already waiting: never stack a second one on it.
        chips = [conv.ACTIONS["tell_me"], conv.ACTIONS["skip"]]
        _save(state, cs)
        ui: dict[str, Any] = {"kind": "answer", "chips": chips}
        return Reply(suffix, ui, {"verdict": "answer_with_pending"})

    opened = None
    if (socratic and cid and not plan.struggling and not plan.continuation and not plan.no_question
            and ped.may_open_followup(cs, cid)):
        q = ped.choose_question(K, cid, cs.get(cid), after_explanation=True)
        if q is not None:
            opened = _ask(state, cs, q, "followup")
    if opened is not None:
        text = (suffix + "\n\n" + opened.text) if suffix else "\n\n" + opened.text
        ui = dict(opened.ui)
        ui["kind"] = "answer"
        ui["sources_chips"] = fu.source_chips(sources, state.asked_chips, limit=1)
        _save(state, cs)
        return Reply(text, ui, {"verdict": "answer_with_followup", **opened.events})

    if plan.struggling and cid:
        chips = _chips(state, fu.support_chips(cid) + [conv.ACTIONS["path"]], limit=3)
    else:
        chips = _next_step_chips(state, cs, cid)
        chips = _chips(state, chips + fu.source_chips(sources, state.asked_chips), limit=3)
        if len(chips) < 3:  # never leave fewer than three ways forward
            pad = ([conv.ACTIONS["example"], conv.ACTIONS["next_topic"], conv.ACTIONS["path"]] if cid
                   else [conv.ACTIONS["path"], *fu.starter_chips(state.concepts, 2)])
            chips = _chips(state, chips + pad, limit=3)
    _remember(state, chips)
    _save(state, cs)
    ui = {"kind": "answer", "chips": chips}
    if cid:
        ui["concept"] = _concept_card(cid, cs)
    return Reply(suffix, ui, {"verdict": "answer"})


def progress(state: TutorState) -> dict[str, Any]:
    """Compact concept-state summary for the UI."""
    cs = _states(state)
    items = []
    for cid, rec in cs.records.items():
        if ped.RANK[rec.state] > 0 and cid in K.concept_by_id:
            items.append({"id": cid, "name": K.concept_by_id[cid].name, "state": rec.state,
                          "label": STATE_LABEL[rec.state], "attempts": rec.attempts})
    items.sort(key=lambda i: -ped.RANK[i["state"]])
    done = sum(1 for r in cs.records.values() if r.state in ped.UNDERSTOOD_OR_BETTER)
    return {"concepts": items, "understood": done, "total": len(K.concepts), "quiz_active": bool(state.quiz)}


def overview() -> dict[str, Any]:
    """Static course map for the empty-state: starters and the learning path."""
    return {
        "starters": list(K.starters),
        "path": [
            {"id": c.id, "name": c.name, "topic": c.topic, "summary": c.description}
            for c in (K.concept_by_id[i] for i in K.learning_path)
        ],
    }
