"""What the student wants *right now*, independent of the topic they are on.

Pure and deterministic (no model, no I/O). The pending Socratic question never
outranks what the student says: "just tell me" is a request, "I'm lost" is not a
wrong answer, and "what is a TLB?" mid-question is a new question, not an
attempt. Patterns are built from small families rather than exact sentences so
paraphrases land in the same intent.

Chips (suggested next messages) are produced elsewhere; here lives the table of
chip texts and the rule that a tapped chip behaves exactly like the same words
typed by hand.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

_FILLER = r"^\s*(?:(?:and|also|ok|okay|so|but|sorry|hmm+|umm*|bro|sir|honestly|actually|please)\b[\s,.!]*)*"


class Intent(str, Enum):
    ANSWER = "answer"  # an attempt at whatever was asked; the caller grades it
    QUESTION = "question"
    HINT = "hint"
    TELL_ME = "tell_me"
    SKIP = "skip"
    EXAMPLE = "example"
    QUIZ = "quiz"
    PAUSE = "pause"
    PATH = "path"
    LOST = "lost"
    HELP_OPENER = "help_opener"
    GREETING = "greeting"
    CONTINUE = "continue"
    STRUGGLE = "struggle"
    PREREQS = "prereqs"
    NEXT_TOPIC = "next_topic"
    ACK = "ack"  # "done", "yes", "ok": a bare acknowledgement, not an answer
    FORMAT = "format"  # "as bullet points", "step by step"
    CAPABILITY = "capability"  # asks for video / audio / slides / images
    DISSATISFIED = "dissatisfied"  # "that didn't help", "not satisfied"


# ----------------------------------------------------------------- patterns

# "no clue" is an admission of not knowing, not a request, so "clue" counts only
# as a request ("give me a clue").
_HINT_RE = re.compile(r"\b(?:hints?|nudge|a little help|give me a push|(?:give|need|want|got)\s+(?:me\s+)?a\s+clue)\b", re.I)
_TELL_RE = re.compile(
    r"\b(?:just\s+tell\s+me|tell\s+me\s+the\s+answer|give\s+me\s+the\s+answer|what\s+is\s+the\s+answer|"
    r"show\s+(?:me\s+)?the\s+answer|i\s+give\s+up|reveal\s+(?:the\s+)?answer|stop\s+(?:quizzing|asking)\s+me)\b", re.I)
_SKIP_RE = re.compile(
    r"^\s*(?:(?:please|ok|okay|yes|yeah|so)\W+)*(?:skip(?:\s+(?:this|it|that|this question|the question))?"
    r"|next(?:\s+(?:question|step|topic|one|concept|part))?|pass|move on)"
    r"(?:\s+please)?\s*[.!]*\s*$", re.I)
# A bare acknowledgement ("done", "yes", "ok"): it answers nothing. After an offer it
# means "go on"; with a question pending it is a non-answer.
_ACK_WORDS = (r"done|yes|yeah|yep|yup|ya|ok|okay|k|kk|sure|alright|fine|cool|great|nice|good|got\s+it|i\s+see|"
              r"understood|makes\s+sense|right|please|finished|completed|did\s+it|next|go|lets?\s+go|let'?s\s+go")
_ACK_RE = re.compile(rf"^\W*(?:(?:{_ACK_WORDS})\b[\s,.!]*)+$", re.I)
_FORMAT_RE = re.compile(
    r"\b(?:bullet(?:ed|s)?(?:\s+(?:points?|list))?|in\s+points|as\s+(?:a\s+)?list|point[\s-]?wise|step[\s-]*by[\s-]*step|"
    r"numbered\s+(?:list|steps)|in\s+steps|tl;?dr|summari[sz]e\s+(?:it|that|this)|in\s+short|briefly|"
    r"(?:make\s+it\s+)?shorter|short(?:er)?\s+version|in\s+(?:a\s+)?(?:few|two|three|one)\s+(?:lines?|sentences?|words?))\b", re.I)
_CAPABILITY_RE = re.compile(
    r"\b(?:give|show|send|provide|generate|make|create|play|share|get|need|want|can\s+(?:you|u)|could\s+(?:you|u))\b[^.?!]{0,40}"
    r"\b(?:videos?|audio|voice|podcast|ppts?|pptx|powerpoint|youtube|animations?|images?|pictures?|photos?)\b", re.I)
_DISSATISFIED_RE = re.compile(
    r"\bnot\s+(?:satisfied|happy|helpful|clear|convinced)\b|\b(?:that|this|it)(?:'s|\s+is|\s+was)?\s+(?:not|n'?t)\s+"
    r"(?:helping|helpful|useful|right|correct|what\s+i)\b|\b(?:wrong|bad|useless|rubbish|nonsense)\s+answer\b|"
    r"\b(?:doesn'?t|didn'?t|does\s+not|did\s+not)\s+help\b|\bnot\s+what\s+i\s+(?:asked|wanted|meant)\b|"
    r"\byou'?re\s+not\s+(?:answering|helping)\b", re.I)
_SIMPLE_WORDS_RE = re.compile(
    r"^\W*(?:(?:please|pls|can you|could you|just|give me|tell me|say it|put it|explain it|and|also)\W+)*"
    r"in\s+(?:very\s+)?(?:simple|easy|plain)\s+(?:words|terms|english|language)\b|\bmake\s+it\s+(?:more\s+)?(?:simple|simpler|easier|easy)\b", re.I)
_EXAMPLE_RE = re.compile(
    r"\b(?:show\s+(?:me\s+)?an?\s+example|give\s+(?:me\s+)?an?\s+example|with\s+an?\s+(?:simple\s+)?example|"
    r"for\s+example\s*\?|example\s+please|use\s+an?\s+analogy)\b", re.I)
_QUIZ_RE = re.compile(
    r"\b(?:test\s+my\s+understanding|test\s+me|quiz\s+me|check\s+my\s+understanding|ask\s+me\s+(?:a\s+)?question|"
    r"question\s+me|give\s+me\s+a\s+quiz|practice\s+questions?)\b", re.I)
_PAUSE_RE = re.compile(
    r"^\s*(?:pause|stop|end|exit|quit|cancel)(?:\s+(?:the\s+|this\s+)?(?:quiz|questions?|session|test))?\s*[.!]*\s*$"
    r"|\b(?:stop|end|exit|quit|pause)\s+(?:the\s+|this\s+)?(?:quiz|test|questions?)\b"
    r"|\b(?:no\s+more\s+questions|stop\s+asking\s+(?:me\s+)?questions)\b", re.I)
_PATH_RE = re.compile(
    r"\b(?:where\s+(?:do|should|can)\s+i\s+(?:start|begin)|how\s+(?:do|should)\s+i\s+(?:start|begin)|"
    r"i(?:'m|\s+am)\s+(?:new|a\s+beginner|a\s+complete\s+beginner)|i\s+know\s+(?:nothing|zero)|start\s+from\s+(?:the\s+)?(?:basics|scratch|beginning)|"
    r"(?:learning|study)\s+(?:path|plan|roadmap)|roadmap|what\s+should\s+i\s+(?:learn|study)(?:\s+(?:first|next))?|"
    r"teach\s+me\s+(?:operating\s+systems?|os|from)|new\s+to\s+(?:operating\s+systems?|os)|beginner|"
    r"let'?s\s+(?:start|begin)|(?:start|begin)\s+(?:from\s+)?(?:the\s+)?(?:basics|beginning|start))\b", re.I)
_LOST_RE = re.compile(
    r"\b(?:(?:not\s+sure|don'?t\s+know|do\s+not\s+know|no\s+idea|dunno|unsure)\s+(?:what|where|how)\s+(?:to\s+)?(?:ask|start|begin|do|learn)"
    r"|what\s+(?:should|can|do)\s+i\s+ask|what\s+can\s+(?:you|i)\s+(?:do|ask)|what\s+(?:else\s+)?can\s+i\s+ask|suggest\s+(?:some\s+)?(?:questions|topics)|"
    r"give\s+me\s+(?:some\s+)?(?:ideas|questions|topics))\b", re.I)
_HELP_OPENER_RE = re.compile(
    r"^\W*(?:hey\W+|hi\W+|hello\W+)?(?:please\W+)?(?:can|could|will|would)\s+(?:you|u)\s+(?:please\s+)?help(?:\s+me)?(?:\s+out)?"
    r"(?:\s+(?:please|pls|plz))?\W*$|^\W*(?:i\s+)?need\s+(?:some\s+)?help(?:\s+please)?\W*$|^\W*help(?:\s+me)?(?:\s+(?:please|pls|plz))?\W*$", re.I)
_GREETING_RE = re.compile(
    r"^\W*(?:hi+|hello+|hey+|hola|namaste|good\s+(?:morning|afternoon|evening)|yo|sup)\b\W*"
    r"(?:there|tutor|bot|bro|sir|mam|madam|buddy|dude|friend|man|guys)?\W*$", re.I)
_CONTINUE_RE = re.compile(r"^\W*(?:continue|go on|keep going|more|please continue|carry on|go ahead|and then|what next|what'?s next|elaborate)\W*$", re.I)
_PREREQS_RE = re.compile(r"\b(?:what\s+(?:do\s+i|should\s+i)\s+(?:need\s+to\s+)?know\s+before|prerequisites?\s+(?:for|of)|what\s+comes\s+before)\b", re.I)
_NEXT_RE = re.compile(r"\b(?:what\s+(?:should\s+i|do\s+i)\s+(?:learn|study)\s+(?:next|after)|what\s+comes\s+after|what'?s\s+next\s+after|where\s+(?:do\s+i|should\s+i)\s+go\s+next)\b", re.I)

_QUESTION_START_RE = re.compile(
    r"^\s*(?:what|why|how|when|where|which|who|can|could|should|is|are|does|do|did|will|explain|describe|compare|"
    r"define|list|difference|tell me (?:about|what|why|how)|give|show|walk me through|derive|trace|calculate|"
    r"write|draw|summari[sz]e)\b", re.I)

# --------------------------------------------------- learning difficulty

_DIFFICULTY: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("frustrated", re.compile(
        r"(?:getting|got|get)\s+(?:everything|it all|all of (?:it|this|them))\s+wrong|keep\s+getting\s+(?:it|this|them|everything)\s+wrong"
        r"|\bi\s+can'?t\s+do\s+(?:this|it|anything)\b|\bi\s+give\s+up\b|\bi'?m\s+(?:so\s+|really\s+)?(?:bad|terrible|hopeless|useless|stupid|dumb)\s+at\b", re.I)),
    ("overwhelmed", re.compile(
        r"(?:not|don'?t|do not|can'?t)\s+understand(?:ing)?\s+anything|understand\s+nothing|\btoo\s+(?:difficult|hard|complicated|much)\b"
        r"|\b(?:this|it|the)\s+(?:topic\s+|chapter\s+)?(?:is\s+)?(?:way\s+|so\s+)(?:difficult|hard|complicated|much)\b|\boverwhelm(?:ed|ing)\b", re.I)),
    ("repeat", re.compile(
        _FILLER + r"(?:(?:can|could)\s+you\s+)?(?:explain|say|go\s+(?:through|over))\s+(?:it|that|this)\s+again\b"
        r"|\bstill\s+(?:don'?t|do not|can'?t)\s+(?:get|understand|follow)\b|\bone\s+more\s+time\b|^\s*again\s*\??\s*$", re.I)),
    ("confused", re.compile(
        _FILLER + r"(?:i'?m|i\s+am)\s+(?:so\s+|really\s+|a\s+bit\s+|kind\s+of\s+|totally\s+)?(?:confused|lost|stuck)\b"
        r"|" + _FILLER + r"i\s+(?:don'?t|do\s+not|didn'?t|did\s+not)\s+(?:get|understand|follow)(?:\s+(?:it|this|that))?\s*[.!]*\s*$"
        r"|\b(?:explain|say)\s+(?:[\w-]+\s+){0,4}?(?:more\s+)?simpl(?:y|er)\b|\bin\s+simpler\s+words\b|\bexplain\s+like\s+i'?m\s+(?:5|five)\b|\beli5\b"
        r"|^\s*(?:what|huh)\s*\?+\s*$", re.I)),
    ("confused", _SIMPLE_WORDS_RE),
    ("uncertain", re.compile(
        _FILLER + r"(?:i\s+|i'?m\s+|i\s+am\s+)?(?:(?:really\s+|honestly\s+)?(?:don'?t|do\s+not|dont)\s+know|not\s+sure|no\s+idea|idk|dunno|have\s+no\s+(?:idea|clue))\b", re.I)),
)
DIFFICULTY_MAX_WORDS = 14

#: Replies are never "correct!" for a wrong answer; openers rotate so the same
#: words do not start every reply.
UNSURE_OPENERS = (
    "That's completely fine, you don't need to know this already.",
    "No problem at all, that's what we're here for.",
    "That's okay, we can work it out together.",
)
MISCONCEPTION_OPENERS = (
    "That is a very common way to think about it, and it needs one adjustment.",
    "Good attempt: lots of people see it that way at first, but one part needs a rethink.",
)
PARTIAL_OPENERS = (
    "You're on the right track: part of that is right.",
    "Nice, you have part of it already.",
)
CORRECT_OPENERS = ("**Yes.**", "**Exactly.**", "**That's right.**", "**Well reasoned.**")
STRUGGLE_OPENERS = {
    "confused": "That's okay, this one can take a moment to click.",
    "repeat": "Sure, let's try it a different way.",
    "overwhelmed": "That's fair, there is a lot here. Let's take just one small piece.",
    "frustrated": "Mistakes are part of learning this, so let's slow down and take one small step.",
    "uncertain": UNSURE_OPENERS[0],
}


def difficulty_kind(text: str) -> str | None:
    """"frustrated" | "overwhelmed" | "repeat" | "confused" | "uncertain" or None.
    Only short messages that are *about the student*: never a content question
    ("What is a TLB?") and never an attempted answer."""
    t = (text or "").strip()
    if not t or len(t.split()) > DIFFICULTY_MAX_WORDS:
        return None
    for kind, pattern in _DIFFICULTY:
        if pattern.search(t):
            return kind
    return None


def pick(options: tuple[str, ...], seq: int) -> str:
    return options[seq % len(options)]


# -------------------------------------------------------------- chip texts

#: Fixed chips (tapped text == typed text). Concept-specific chips are built in
#: followups.py and carry the concept name so each stands alone when tapped.
ACTIONS: dict[str, str] = {
    "hint": "Give me a hint",
    "tell_me": "Just tell me",
    "skip": "Skip this question",
    "example": "Show an example",
    "pause": "Pause the quiz",
    "path": "Where should I start?",
    "lost": "Suggest some questions I could ask",
    "next_quiz": "Next question",
    "continue": "Continue",
    "simpler": "Explain that more simply",
    "bullets": "Give that as short bullet points",
    "next_topic": "Next topic",
}
_CHIP_INTENTS: dict[str, Intent] = {
    ACTIONS["hint"].lower(): Intent.HINT,
    ACTIONS["tell_me"].lower(): Intent.TELL_ME,
    ACTIONS["skip"].lower(): Intent.SKIP,
    ACTIONS["example"].lower(): Intent.EXAMPLE,
    ACTIONS["pause"].lower(): Intent.PAUSE,
    ACTIONS["path"].lower(): Intent.PATH,
    ACTIONS["lost"].lower(): Intent.LOST,
    ACTIONS["next_quiz"].lower(): Intent.SKIP,
    ACTIONS["continue"].lower(): Intent.CONTINUE,
    ACTIONS["simpler"].lower(): Intent.STRUGGLE,
    ACTIONS["bullets"].lower(): Intent.FORMAT,
    ACTIONS["next_topic"].lower(): Intent.SKIP,
}


def classify(text: str) -> Intent:
    """One intent per message, most specific first."""
    t = (text or "").strip()
    if not t:
        return Intent.ANSWER
    forced = _CHIP_INTENTS.get(t.lower())
    if forced is not None:
        return forced
    if _PAUSE_RE.search(t):
        return Intent.PAUSE
    if _QUIZ_RE.search(t):
        return Intent.QUIZ
    if _TELL_RE.search(t):
        return Intent.TELL_ME
    if _SKIP_RE.match(t):
        return Intent.SKIP
    if _HINT_RE.search(t) and len(t.split()) <= 8:
        return Intent.HINT
    if _PREREQS_RE.search(t):
        return Intent.PREREQS
    if _NEXT_RE.search(t):
        return Intent.NEXT_TOPIC
    if _PATH_RE.search(t):
        return Intent.PATH
    if _LOST_RE.search(t):
        return Intent.LOST
    if _HELP_OPENER_RE.match(t):
        return Intent.HELP_OPENER
    if _GREETING_RE.match(t):
        return Intent.GREETING
    if _CONTINUE_RE.match(t):
        return Intent.CONTINUE
    if _ACK_RE.match(t):
        return Intent.ACK
    if len(t.split()) <= 14:
        if _DISSATISFIED_RE.search(t):
            return Intent.DISSATISFIED
        if _CAPABILITY_RE.search(t):
            return Intent.CAPABILITY
    if difficulty_kind(t) is not None:
        return Intent.STRUGGLE
    if is_format_request(t):
        return Intent.FORMAT
    if _EXAMPLE_RE.search(t) and len(t.split()) <= 8:
        return Intent.EXAMPLE
    if _QUESTION_START_RE.match(t) or ("?" in t and len(t.split()) >= 6):
        return Intent.QUESTION
    return Intent.ANSWER


def is_format_request(text: str) -> bool:
    """A short ask to re-shape the last answer ("as bullet points", "step by step").
    The engine still checks that no new topic is named before treating it so."""
    t = (text or "").strip()
    return bool(t) and len(t.split()) <= 16 and bool(_FORMAT_RE.search(t))


def is_new_request(text: str) -> bool:
    """Clearly a fresh question or instruction, not an attempt at the pending
    question. A short answer that merely ends in "?" ("tetrahedral?") is still an
    attempt."""
    t = (text or "").strip()
    if _QUESTION_START_RE.match(t):
        return len(t.split()) >= 4
    return "?" in t and len(t.split()) >= 7


# ------------------------------------------------------------------- state


@dataclass
class TutorState:
    """Conversation state for ONE chat thread (a new chat starts empty)."""

    concepts: dict[str, Any] = field(default_factory=dict)  # pedagogy.ConceptStates as dict
    #: The one Socratic question waiting for an answer, or None.
    #: authored: {"kind":"authored","question_id","concept_id","hinted","simplified","source"}
    #: free:     {"kind":"free","question","concept_id","context"}
    pending: dict[str, Any] | None = None
    #: Active "test my understanding" run: {"concept_id","asked","total","correct"}.
    quiz: dict[str, Any] | None = None
    topic: str | None = None  # concept id of the last concept discussed
    asked_chips: list[str] = field(default_factory=list)  # lower-cased, never re-offered
    turns: int = 0
    lost_count: int = 0
    last_text: str = ""  # last authored reply, so the same words are never sent twice in a row

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TutorState":
        base = cls()
        for key, value in (data or {}).items():
            if hasattr(base, key):
                setattr(base, key, copy.deepcopy(value))
        return base
