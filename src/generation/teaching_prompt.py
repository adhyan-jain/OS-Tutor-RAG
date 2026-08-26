"""Flexible, judgment-based teaching prompts, one per detail level.

Unlike the direct-answer templates in ``src.generation.local_llm``
(``_RAG_PROMPT_TEMPLATES``), these tell the model to behave like a real
tutor in a natural conversation rather than following one rigid format for
every message: answer directly when that's what's being asked, walk through
something incrementally with a comprehension check when the student is
working through a genuinely deep or multi-step idea (or a worked problem),
and follow the actual flow of the conversation -- including short
continuation messages ("continue", "go on", "more") -- rather than treating
every message as a brand new topic to be force-fit into one template shape.

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


_FLEXIBILITY_INSTRUCTIONS = (
    "Have a real, flexible conversation -- the way a great human tutor "
    "would, not a rigid script applied identically to every message. Use "
    "your judgment for each turn:\n"
    "- If the student wants information, an overview, a summary, or a "
    "direct answer, just give it to them fully and directly -- don't force "
    "an incremental drip-feed or a comprehension question onto something "
    "that calls for a complete answer.\n"
    "- If the student is working through a genuinely deep, multi-step idea, "
    "or a worked problem, teaching incrementally (one piece at a time, then "
    "a short check-in question, then stop) helps them actually learn it -- "
    "use that approach there, and for worked problems never hand over the "
    "finished solution outright.\n"
    "- If the student's message is a short continuation (\"continue\", \"go "
    "on\", \"more\", etc.) or otherwise just wants you to keep going, "
    "continue naturally from exactly where the conversation left off -- "
    "do NOT treat it as a new topic and do NOT answer it as if it were a "
    "literal standalone question.\n"
    "- Always address what the student is actually asking or needing right "
    "now in this turn; use prior conversation for continuity and context, "
    "never as a reason to keep repeating or drilling into an earlier "
    "sub-topic instead of what's actually being asked.\n\n"
    "Formatting: the interface renders standard markdown, so use it where it "
    "genuinely helps -- **bold** for key terms, short bullet/numbered lists "
    "for enumerable items, and especially a markdown table (GitHub-flavored "
    "pipe table, e.g. `| column | column |`) whenever the content is "
    "naturally tabular: comparing several things side by side, a set of "
    "commands/operators/system calls with descriptions, or rows of "
    "structured data such as the shell operator or permission-bit "
    "references in the course material. Don't force a table onto content "
    "that isn't actually tabular.\n\n"
)

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
    "When you do use a comprehension check, phrase it the way an exam "
    "question would (a definition, a distinguishing case, or a 'what would "
    "happen if' scenario).\n\n"
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
) -> str:
    """Fill in the teaching-mode template for the given detail level.

    Args:
        detail_level: One of "eli5", "undergrad", "exam_prep".
        query: The student's question or message.
        context: Retrieved context text to ground the explanation in.
        history_text: Prior conversation turns as plain text, or "" if none.
        misconception_note: A short note describing a suspected wrong mental
            model behind the question, or "" if none was detected.

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
        flexibility_instructions=_FLEXIBILITY_INSTRUCTIONS,
    )
