"""In-memory session store for multi-turn chat history.

No DB, no persistence across restarts — intentional per the API spec. Each
session_id maps to a list of (question, answer) turns, kept in the order they
happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Turn:
    question: str
    answer: str
    # The retrieved context text (and the sources payload derived from it)
    # this turn's answer was actually grounded in. Used so a later
    # continuation message ("continue", "go on", ...) can keep explaining the
    # SAME material instead of triggering a fresh retrieval on unrelated text
    # (see chat.py's is_continuation_message handling) -- retrieving fresh
    # content for a continuation and telling the model to ground its answer
    # in that new content silently derails it onto whatever topic the
    # retrieval happened to surface.
    context_text: str = ""
    sources_payload: list = field(default_factory=list)


_SESSIONS: dict[str, list[Turn]] = {}


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


def clear(session_id: str) -> None:
    """Drop a session's history entirely."""
    _SESSIONS.pop(session_id, None)


def format_history(session_id: str) -> str:
    """Render prior turns as plain text, for prepending to a new prompt.

    Returns "" if the session has no history yet.
    """
    turns = get_history(session_id)
    if not turns:
        return ""
    lines = []
    for turn in turns:
        lines.append(f"Q: {turn.question}")
        lines.append(f"A: {turn.answer}")
    return "\n".join(lines)
