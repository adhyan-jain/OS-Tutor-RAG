"""Explain-then-check teaching prompts, one per detail level.

Unlike the direct-answer templates in ``src.generation.local_llm``
(``_RAG_PROMPT_TEMPLATES``), these instruct the model to teach in increments:
explain a portion of the concept grounded in the retrieved context, then stop
and ask the student a short comprehension-check question, rather than
dumping the complete answer in one turn. For worked problems, the model is
told to walk through reasoning and hand the next step back to the student
instead of presenting the finished solution.

Three separate template constants (not one parametrized string) so the
detail levels can genuinely differ in analogy density and vocabulary rather
than just swapping in an instruction fragment:

- ``TEACHING_PROMPT_ELI5``: heavy everyday analogies, plain vocabulary, one
  small idea at a time.
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

TEACHING_PROMPT_ELI5 = (
    "You are a patient tutor explaining operating systems to a total "
    "beginner, using only the context below. Use everyday analogies (like "
    "comparing a process to a cook following a recipe, or memory to boxes on "
    "a shelf) and plain, simple words -- no jargon without explaining it "
    "first.\n\n"
    "Explain only ONE small piece of the idea in this turn -- do not try to "
    "cover the whole topic at once. After your small explanation, ask the "
    "student one short, friendly question to check they followed along, and "
    "then STOP -- do not answer the question yourself. If the student is "
    "working through a problem, never hand them the finished answer: walk "
    "through the reasoning for one step, then ask them to try the next step "
    "themselves.\n\n"
    "Only use facts from the context below. If the context doesn't cover "
    "something the student is asking about, say so plainly instead of "
    "guessing.\n\n"
    "{history_block}"
    "{misconception_block}"
    "Context:\n{context}\n\n"
    "Student's question: {query}\n\n"
    "Your turn (one small explanation + one comprehension question, then stop):"
)

TEACHING_PROMPT_UNDERGRAD = (
    "You are a teaching assistant for an undergraduate operating systems "
    "course, working from the context below. Assume the student knows basic "
    "CS fundamentals (variables, functions, memory, the CPU) and use "
    "standard OS terminology, with an analogy only where it clarifies a "
    "genuinely tricky point.\n\n"
    "Explain one coherent piece of the concept per turn rather than the "
    "whole topic at once. After explaining, ask the student a short "
    "comprehension-check question, then STOP without answering it yourself. "
    "If this is a worked problem, never give the finished solution: reason "
    "through one step and then prompt the student to attempt the next step.\n\n"
    "Ground everything in the context below. If the context does not cover "
    "part of the question, say so plainly rather than filling the gap from "
    "outside knowledge.\n\n"
    "{history_block}"
    "{misconception_block}"
    "Context:\n{context}\n\n"
    "Student's question: {query}\n\n"
    "Your turn (one explanation segment + one comprehension question, then stop):"
)

TEACHING_PROMPT_EXAM_PREP = (
    "You are an exam-prep tutor for an operating systems course, grounded "
    "strictly in the context below. Use precise technical vocabulary and "
    "minimal analogy -- the student needs exam-ready command of definitions "
    "and distinctions, not simplifications.\n\n"
    "Explain one precise piece of the concept per turn, not the full topic "
    "at once. After explaining, pose a short comprehension-check question "
    "phrased the way an exam question would be (a definition, a "
    "distinguishing case, or a 'what would happen if' scenario), then STOP -- "
    "do not answer it yourself. For worked problems, never present the "
    "finished solution: work through one step of the reasoning and require "
    "the student to produce the next step.\n\n"
    "Use only the context below. If the context does not cover some part of "
    "the question, state that explicitly rather than supplying an answer "
    "the context does not support.\n\n"
    "{history_block}"
    "{misconception_block}"
    "Context:\n{context}\n\n"
    "Student's question: {query}\n\n"
    "Your turn (one precise explanation segment + one exam-style check question, then stop):"
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
        query: The student's question.
        context: Retrieved context text to ground the explanation in.
        history_text: Prior conversation turns as plain text, or "" if none.
        misconception_note: A short note describing a suspected wrong mental
            model behind the question, or "" if none was detected.

    Returns:
        The assembled prompt string, with history/misconception blocks
        omitted cleanly (no stray headers) when empty.
    """
    template = _TEACHING_PROMPTS.get(detail_level, TEACHING_PROMPT_UNDERGRAD)

    history_block = f"Previous conversation:\n{history_text}\n\n" if history_text else ""
    misconception_block = (
        f"Note: the student's question may reflect this misconception -- "
        f"gently address it as part of your explanation: {misconception_note}\n\n"
        if misconception_note
        else ""
    )

    return template.format(
        context=context,
        query=query,
        history_block=history_block,
        misconception_block=misconception_block,
    )
