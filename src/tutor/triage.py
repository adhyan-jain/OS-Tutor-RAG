"""Deterministic triage of an incoming message, before any retrieval or model call.

Same reasoning as LabTutor's triage: some replies must not depend on a model
being reachable or in a good mood. Precision over recall, on purpose: a missed
off-scope question just flows to a tutor already told to stay on topic, but a
false positive refuses a legitimate OS question and teaches the student the tool
is broken. So every pattern is narrow, and a test asserts none of the
course questions trips any of them.

Intents that short-circuit:

``DISTRESS``    the student is struggling in a way an explanation will not fix
``OFF_SCOPE``   clearly not about the course (homework for another subject, chit-chat)
``INJECTION``   an attempt to rewrite the tutor's instructions
"""

from __future__ import annotations

import enum
import re


class Intent(str, enum.Enum):
    COURSE = "course"
    DISTRESS = "distress"
    OFF_SCOPE = "off_scope"
    INJECTION = "injection"
    SMALLTALK = "smalltalk"


#: Chit-chat that real students send first ("how are you", "thanks", "who are you").
#: A warm one-liner plus course chips beats a refusal; matched on the whole message.
_SMALLTALK: tuple[tuple[str, str], ...] = (
    ("how_are_you", r"^\W*(?:(?:hi|hey|hello)\W+)?(?:how\s+(?:are|r)\s+(?:you|u)|how'?s\s+it\s+going|what'?s\s+up|wass?up)\b[^.?]{0,12}\W*$"),
    ("who", r"\bwho\s+(?:are|r)\s+(?:you|u)\b|\byour\s+(?:name|talent|special\w*)\b|\bwho\s+(?:made|built|created)\s+you\b"),
    ("thanks", r"^\W*(?:thanks?|thank\s+you|thx|tysm|ty)\b[^.?]{0,20}\W*$"),
    ("bye", r"^\W*(?:bye|goodbye|see\s+(?:you|ya)|good\s*night|cya)\b[^.?]{0,20}\W*$"),
)

_SMALLTALK_REPLIES: dict[str, str] = {
    "how_are_you": "Doing well, thanks for asking! I'm ready whenever you are. Want to start from the basics, or ask me something specific?",
    "who": "I'm your OS tutor. I answer from your course slides and the OSTEP chapters, and now and then I'll ask a small question so you can check you've really got it.",
    "thanks": "You're welcome! Want to carry on with the next topic, or try a quick question?",
    "bye": "See you! Your progress stays in this chat, so you can pick up right where you left off.",
}


def smalltalk_kind(message: str) -> str | None:
    text = (message or "").strip()
    if not text or len(text.split()) > 9:
        return None
    for kind, pattern in _SMALLTALK:
        if re.search(pattern, text, re.IGNORECASE):
            return kind
    return None


_DISTRESS = (
    r"\b(?:i'?m|i am|im)\s+(?:going\s+to\s+)?fail(?:ing)?\b",
    r"\b(?:i'?m|i am|im)\s+(?:crying|panicking|so\s+stressed|stressed|overwhelmed|burnt?\s*out)\b",
    r"\bi\s+(?:hate|can'?t\s+do)\s+(?:this|os|operating systems?|this course)\b",
    r"\bi\s+want\s+to\s+(?:give\s+up|quit|drop\s+(?:out|the course))\b",
    r"\bi\s+(?:can'?t|cannot)\s+(?:take|handle)\s+(?:this|it)\s+anymore\b",
    r"\bi'?m\s+(?:so\s+)?(?:stupid|dumb|useless|hopeless)\b",
)

_OFF_SCOPE = (
    r"\bwrite\s+(?:my|me)\b[^.]{0,30}\b(?:report|essay|assignment|cover letter|thesis)\b",
    r"\bcapital\s+of\s+\w+",
    r"\btell\s+me\s+a\s+joke\b",
    r"\bwho\s+won\b",
    r"\bweather\b",
    r"\bmy\s+(?:physics|maths?|chemistry|english|history|biology)\s+(?:assignment|homework)\b",
    r"\bfor\s+(?:lunch|dinner|breakfast)\b",
    r"\bmy\s+resume\b|\bresume\s+(?:writing|template)\b",
    r"\bwhen\s+is\s+the\s+(?:exam|test|quiz)\b",
    r"\bstock\s+price\b|\bbitcoin\b",
)

_INJECTION = (
    r"\bignore\s+(?:all\s+|any\s+|your\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|rules)\b",
    r"\bdisregard\s+(?:your|the)\s+(?:instructions?|rules|system prompt)\b",
    r"\b(?:reveal|show|print|repeat)\s+(?:me\s+)?(?:your|the)\s+(?:system\s+)?prompt\b",
    r"\byou\s+are\s+now\s+(?:dan|an?\s+unrestricted)\b",
)


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify(message: str) -> Intent:
    text = (message or "").strip()
    if not text:
        return Intent.COURSE
    if _matches(text, _INJECTION):
        return Intent.INJECTION
    if _matches(text, _DISTRESS):
        return Intent.DISTRESS
    if _matches(text, _OFF_SCOPE):
        return Intent.OFF_SCOPE
    if smalltalk_kind(text):
        return Intent.SMALLTALK
    return Intent.COURSE


#: Fixed replies. No model is consulted, so they are identical whether
#: inference is healthy or entirely unreachable.
_RESPONSES: dict[Intent, str] = {
    Intent.DISTRESS: (
        "That sounds genuinely frustrating, and it is completely normal to feel stuck in a hard course. "
        "Operating systems has a steep start for almost everyone. It is worth telling your instructor or a "
        "friend how you are finding it, too. Whenever you are ready, we can take one tiny piece together: "
        "pick a topic below, or just say \"start from the basics\" and I will go one small step at a time."
    ),
    Intent.OFF_SCOPE: (
        "That one is outside this course, so I'll leave it. I'm happy to help with processes, scheduling, "
        "memory, concurrency, IPC or the shell: pick one below, or ask in your own words."
    ),
    Intent.INJECTION: (
        "I can't change how I work or share my instructions, but I'm happy to keep helping with operating "
        "systems. What would you like to learn?"
    ),
}


def fixed_response(intent: Intent, message: str = "") -> str | None:
    if intent is Intent.SMALLTALK:
        return _SMALLTALK_REPLIES.get(smalltalk_kind(message) or "")
    return _RESPONSES.get(intent)


def short_circuits(intent: Intent) -> bool:
    return intent in _RESPONSES or intent is Intent.SMALLTALK
