"""In-memory session store for multi-turn chat history.

No DB, no persistence across restarts — intentional per the API spec. Each
session_id maps to a list of (question, answer) turns, kept in the order they
happened.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Turn:
    question: str
    answer: str


_SESSIONS: dict[str, list[Turn]] = {}


def get_history(session_id: str) -> list[Turn]:
    """Return the list of prior turns for a session (empty if unseen)."""
    return _SESSIONS.get(session_id, [])


def append_turn(session_id: str, question: str, answer: str) -> None:
    """Record a finished exchange onto a session's history."""
    _SESSIONS.setdefault(session_id, []).append(Turn(question=question, answer=answer))


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
