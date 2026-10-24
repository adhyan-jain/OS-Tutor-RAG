"""In-memory session store for multi-turn chat.

No DB, no persistence across restarts -- intentional per the API spec. Each
session_id maps to (a) the list of (question, answer) turns, in order, and (b)
the tutoring state for that thread (concept understanding, the one pending
Socratic question, the quiz in progress). Both are scoped to the thread: a new
chat starts with neither.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.tutor.conversation import TutorState


@dataclass
class Turn:
    question: str
    answer: str
    # The retrieved context text (and the sources payload derived from it)
    # this turn's answer was actually grounded in. Used so a later
    # continuation message ("continue", "go on", ...) can keep explaining the
    # SAME material instead of triggering a fresh retrieval on unrelated text
    # (see chat.py's is_continuation_message handling).
    context_text: str = ""
    sources_payload: list = field(default_factory=list)


_SESSIONS: dict[str, list[Turn]] = {}
_TUTOR: dict[str, TutorState] = {}


def get_history(session_id: str) -> list[Turn]:
    """Return the list of prior turns for a session (empty if unseen)."""
    return _SESSIONS.get(session_id, [])


def append_turn(
    session_id: str,
    question: str,
    answer: str,
    context_text: str = "",
    sources_payload: list | None = None,
) -> None:
    """Record a finished exchange onto a session's history."""
    _SESSIONS.setdefault(session_id, []).append(
        Turn(
            question=question,
            answer=answer,
            context_text=context_text,
            sources_payload=sources_payload or [],
        )
    )


def get_tutor_state(session_id: str) -> TutorState:
    """The thread's tutoring state, created empty on first use."""
    state = _TUTOR.get(session_id)
    if state is None:
        state = _TUTOR[session_id] = TutorState()
    return state


def clear(session_id: str) -> None:
    """Drop a session's history and tutoring state entirely."""
    _SESSIONS.pop(session_id, None)
    _TUTOR.pop(session_id, None)


def format_history(session_id: str, max_turns: int = 6) -> str:
    """Render the most recent turns as plain text, for prepending to a new
    prompt. Capped so a long conversation cannot crowd out the context."""
    turns = get_history(session_id)[-max_turns:]
    if not turns:
        return ""
    lines = []
    for turn in turns:
        lines.append(f"Q: {turn.question}")
        lines.append(f"A: {turn.answer[:900]}")
    return "\n".join(lines)
