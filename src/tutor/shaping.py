"""Shape a streamed model answer so it is small and never ends mid-sentence.

The chat gives the model a small token budget. A model that hits it stops in the
middle of a word, which reads as broken. ``SentenceGate`` sits between the model
stream and the client: it releases text only up to the last sentence or line
boundary, and when the model was cut off by the budget it drops the unfinished
tail. Pure and synchronous, so it is tested without a model.
"""

from __future__ import annotations

import re

# A sentence ends at . ! ? (optionally followed by closing quotes/brackets/emphasis)
# and whitespace; a line ends at a newline. "e.g. " also matches, which only makes
# text appear a little earlier -- harmless -- and can at worst keep "e.g." when a
# cut lands right after it.
_BOUNDARY = re.compile(r"""(?:[.!?:]["')\]*_]*\s|\n)""")


_UNIT = re.compile(r"""(?:[.!?]["')\]*_]*\s+|\n+)""")


class SentenceGate:
    """feed() each token, send what it returns; call finish() once at the end.

    ``max_units`` caps the answer at that many sentences/lines: once reached,
    ``full`` turns True and nothing more is released, so the caller can stop the
    model early (a small model told "4 sentences" often writes 8)."""

    def __init__(self, max_units: int | None = None) -> None:
        self._held = ""
        self.emitted = ""
        self.max_units = max_units
        self.full = False

    def feed(self, token: str) -> str:
        if self.full:
            return ""
        self._held += token
        last = None
        for m in _BOUNDARY.finditer(self._held):
            last = m
        if last is None:
            return ""
        out, self._held = self._held[: last.end()], self._held[last.end():]
        if self.max_units:
            have = len(_UNIT.findall(self.emitted))
            room = self.max_units - have
            pieces = list(_UNIT.finditer(out))
            if len(pieces) >= room:
                out = out[: pieces[room - 1].end()] if room > 0 else ""
                self.full = True
                self._held = ""
        self.emitted += out
        return out

    def finish(self, truncated: bool) -> str:
        """Release what is left. A truncated stream loses its unfinished tail,
        unless nothing complete was ever sent (then a clipped answer beats none)."""
        tail, self._held = self._held, ""
        if self.full:
            return ""
        if truncated and self.emitted.strip():
            return ""
        if truncated:
            tail = tidy_tail(tail)
        self.emitted += tail
        return tail


def tidy_tail(text: str) -> str:
    """Cut a clipped fragment back to its last whole word and mark it with an ellipsis."""
    text = text.rstrip()
    if not text:
        return text
    if text[-1] in ".!?":
        return text
    cut = text.rsplit(None, 1)[0] if " " in text else text
    return cut.rstrip(",;:-") + "…"
