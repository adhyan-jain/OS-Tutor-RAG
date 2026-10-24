"""Teaching prompts for the chat tutor, one per detail level.

Unlike the direct-answer templates in ``src.generation.local_llm``
(``_RAG_PROMPT_TEMPLATES``, which the evaluation measures), these make the
model a patient tutor: explain first, from the context, assuming the student may
know nothing. The Socratic part -- which short question to ask next, grading the
reply, hints, misconception probes, when to just tell the student -- is *policy*
and lives in code (``src/tutor``), because code can grade an answer and a prompt
cannot be tested. So the model is told not to quiz; the tutoring layer appends
one graded question after the answer. Also follows the flow of the conversation,
including short continuation messages ("continue", "go on", "more").

Three separate template constants (not one parametrized string) so the
detail levels can genuinely differ in analogy density and vocabulary rather
than just swapping in an instruction fragment:

- ``TEACHING_PROMPT_ELI5``: heavy everyday analogies, plain vocabulary, one
  small idea at a time when teaching incrementally.
- ``TEACHING_PROMPT_UNDERGRAD``: standard CS terminology, moderate analogy
  use, assumes prior CS fundamentals.
- ``TEACHING_PROMPT_EXAM_PREP``: minimal analogy, precise technical
  vocabulary, comprehension checks framed as what an exam would ask.

Faithfulness requirement carried over unchanged from the original prompts:
ground everything in the provided context, and say so honestly if the
context doesn't cover something.
"""

from __future__ import annotations

from typing import Literal

# Short messages that mean "keep going from where you left off", not "answer
# this literally". Matched against the whole message, case-insensitively,
# after stripping punctuation/whitespace -- see is_continuation_message().
_CONTINUATION_PHRASES = {
    "continue",
    "go on",
    "keep going",
    "more",
    "please continue",
    "carry on",
    "go ahead",
    "next",
    "and then",
    "what next",
    "what's next",
    "elaborate",
    "keep explaining",
    "continue please",
}


def is_continuation_message(question: str) -> bool:
    """True if `question` looks like a "keep going" nudge rather than a new,
    literal question -- e.g. after an error, or when the student just wants
    the explanation to proceed.

    Deliberately conservative (exact/near-exact phrase match on a short
    message) so an actual question that happens to contain one of these
    words (e.g. "what's next after fork() returns in the child?") is never
    misclassified -- only short, standalone nudges match.
    """
    normalized = question.strip().strip(".!?").lower()
    if not normalized:
        return False
    if normalized in _CONTINUATION_PHRASES:
        return True
    # A few words at most, e.g. "ok continue" / "yes go on".
    return len(normalized.split()) <= 4 and any(
        phrase in normalized for phrase in ("continue", "go on", "keep going")
    )


# Two instruction sets, chosen per request. Policy about *when to quiz the
# student* lives in code (src/tutor), not here: the tutoring layer appends one
# graded Socratic question after the answer and handles the reply to it. So the
# model's job is to explain well and kindly, from the context, and to leave the
# questioning to the layer that can actually grade it.
_FORMAT_SHARED = (
    "Start with the answer itself (no greeting, no 'Great question', no restating the "
    "question) and stop when the idea is across. No headings. Use a markdown table only "
    "if the student asks to compare or tabulate. If the context does not cover the "
    "question, say so in ONE friendly sentence and name one related operating-systems "
    "topic the student could ask about instead.\n\n"
)

# Each level gets its own length, structure and vocabulary rules: a shared "3 short
# sentences, assume the student knows nothing" rule made undergrad and exam-prep
# answers nearly identical, so the student's chosen level was barely visible.
_FORMAT = {
    "eli5": (
        "Length and format (strict): this is a chat, so keep it SHORT -- at most 4 short "
        "sentences, about 70 words. Build the explanation around ONE everyday analogy and "
        "then say what it maps to in the OS. Use **bold** for at most two key terms and no "
        "bullet lists. " + _FORMAT_SHARED
    ),
    "undergrad": (
        "Length and format (strict): about 5 sentences, 90 to 110 words. Explain the "
        "mechanism: what happens, in what order, and why the OS does it that way. Use "
        "standard OS terminology (define a term only if it is advanced). Include one "
        "concrete example in one sentence. Use **bold** for at most three key terms. Use a "
        "short numbered list only for real steps (at most 4). " + _FORMAT_SHARED
    ),
    "exam_prep": (
        "Length and format (strict): exam-ready notes, up to 8 short lines, about 120 to "
        "150 words. Use this shape: (1) a precise one-sentence definition; (2) the key "
        "points or steps as 3 to 5 terse bullets (use exact terms: PCB, trap, TLB, "
        "mutual exclusion, and so on); (3) one final line starting 'Exam tip:' with the "
        "distinction or common mistake an exam tests. No analogies. Use **bold** for "
        "key terms. " + _FORMAT_SHARED
    ),
}

_TONE = {
    "eli5": (
        "Tone: you are a patient, friendly tutor, like a helpful senior guiding a "
        "junior. Be warm and encouraging without gushing; never condescending. "
        "Assume the student knows nothing about the topic: define any term a "
        "beginner would not know the first time you use it, and keep sentences short.\n\n"
    ),
    "undergrad": (
        "Tone: you are a clear, friendly teaching assistant for an undergraduate OS "
        "course. Assume the student knows basic CS (variables, functions, the CPU, "
        "memory) but is new to OS; be precise but approachable.\n\n"
    ),
    "exam_prep": (
        "Tone: you are a concise, exacting exam coach. Assume the student has met the "
        "material before and now needs precise, complete, exam-ready statements; "
        "no hand-holding or pleasantries.\n\n"
    ),
}

_GUIDED_BODY = (
    "How to answer:\n"
    "- Answer what the student actually asked, directly and completely, from the "
    "context. Explain first; never withhold the explanation to make the student "
    "guess. A separate step of the app adds one short check-your-understanding "
    "question after your answer, so do NOT end with a question of your own and do "
    "NOT quiz the student.\n"
    "- Keep it focused on what the student needs now, at the level and length set below; "
    "the student can ask for more, an example, or a simpler version.\n"
    "- If a note below says the student may hold a misconception, address it "
    "gently inside your explanation without making them feel foolish.\n"
    "- If the student's message is a short continuation (\"continue\", \"go on\", "
    "\"more\"), continue naturally from exactly where the conversation left off -- "
    "do NOT treat it as a new topic.\n"
    "- Always address what the student needs right now; use earlier turns for "
    "continuity, never as a reason to repeat or drill into an old sub-topic.\n\n"
)

_DIRECT_BODY = (
    "How to answer:\n"
    "- The student has asked for direct answers: answer completely from the "
    "context and do not ask them any questions.\n"
    "- If a note below says the student may hold a misconception, address it "
    "gently inside your explanation.\n"
    "- If the student's message is a short continuation (\"continue\", \"go on\", "
    "\"more\"), continue exactly where the conversation left off.\n\n"
)


def _instructions(level: str, socratic: bool) -> str:
    level = level if level in _FORMAT else "undergrad"
    return _TONE[level] + (_GUIDED_BODY if socratic else _DIRECT_BODY) + _FORMAT[level]

TEACHING_PROMPT_ELI5 = (
    "You are a patient, friendly tutor explaining operating systems to a "
    "total beginner, using only the context below. Use everyday analogies "
    "(like comparing a process to a cook following a recipe, or memory to "
    "boxes on a shelf) and plain, simple words -- no jargon without "
    "explaining it first.\n\n"
    "{flexibility_instructions}"
    "Only use facts from the context below. If the context doesn't cover "
    "something the student is asking about, say so plainly instead of "
    "guessing.\n\n"
    "{history_block}"
    "{misconception_block}"
    "{continuation_block}"
    "Context:\n{context}\n\n"
    "Student's message: {query}\n\n"
    "Your turn:"
)

TEACHING_PROMPT_UNDERGRAD = (
    "You are a knowledgeable teaching assistant for an undergraduate "
    "operating systems course, working from the context below. Assume the "
    "student knows basic CS fundamentals (variables, functions, memory, the "
    "CPU) and use standard OS terminology, with an analogy only where it "
    "clarifies a genuinely tricky point.\n\n"
    "{flexibility_instructions}"
    "Ground everything in the context below. If the context does not cover "
    "part of the question, say so plainly rather than filling the gap from "
    "outside knowledge.\n\n"
    "{history_block}"
    "{misconception_block}"
    "{continuation_block}"
    "Context:\n{context}\n\n"
    "Student's message: {query}\n\n"
    "Your turn:"
)

TEACHING_PROMPT_EXAM_PREP = (
    "You are an exam-prep tutor for an operating systems course, grounded "
    "strictly in the context below. Use precise technical vocabulary and "
    "minimal analogy -- the student needs exam-ready command of definitions "
    "and distinctions, not simplifications.\n\n"
    "{flexibility_instructions}"
    "Where it helps, frame the explanation the way an exam rewards it (a "
    "definition, a distinguishing case, or a 'what would happen if' scenario).\n\n"
    "Use only the context below. If the context does not cover some part of "
    "the question, state that explicitly rather than supplying an answer "
    "the context does not support.\n\n"
    "{history_block}"
    "{misconception_block}"
    "{continuation_block}"
    "Context:\n{context}\n\n"
    "Student's message: {query}\n\n"
    "Your turn:"
)

_TEACHING_PROMPTS = {
    "eli5": TEACHING_PROMPT_ELI5,
    "undergrad": TEACHING_PROMPT_UNDERGRAD,
    "exam_prep": TEACHING_PROMPT_EXAM_PREP,
}


def build_teaching_prompt(
    detail_level: Literal["eli5", "undergrad", "exam_prep"],
    query: str,
    context: str,
    history_text: str = "",
    misconception_note: str = "",
    socratic: bool = True,
) -> str:
    """Fill in the teaching-mode template for the given detail level.

    Args:
        detail_level: One of "eli5", "undergrad", "exam_prep".
        query: The student's question or message.
        context: Retrieved context text to ground the explanation in.
        history_text: Prior conversation turns as plain text, or "" if none.
        misconception_note: A short note describing a suspected wrong mental
            model behind the question, or "" if none was detected.
        socratic: True when the tutoring layer will append a graded Socratic
            question after the answer (so the model must not ask one itself);
            False for direct-answer mode.

    Returns:
        The assembled prompt string, with history/misconception/continuation
        blocks omitted cleanly (no stray headers) when not applicable.
    """
    template = _TEACHING_PROMPTS.get(detail_level, TEACHING_PROMPT_UNDERGRAD)

    history_block = f"Previous conversation:\n{history_text}\n\n" if history_text else ""
    misconception_block = (
        f"Note: the student's question may reflect this misconception -- "
        f"gently address it as part of your explanation: {misconception_note}\n\n"
        if misconception_note
        else ""
    )
    continuation_block = (
        "Note: the student's message is a short continuation nudge, not a "
        "new topic -- continue naturally from exactly where you left off in "
        "the previous conversation turn above.\n\n"
        if is_continuation_message(query)
        else ""
    )

    return template.format(
        context=context,
        query=query,
        history_block=history_block,
        misconception_block=misconception_block,
        continuation_block=continuation_block,
        flexibility_instructions=_instructions(detail_level, socratic),
    )
