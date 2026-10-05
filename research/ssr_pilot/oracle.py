"""
Reference-independent semantic oracle for the SSR pilot.

`evaluate_candidate` has NO reference argument: it parses the candidate,
replays it through the world's rules, and checks the task constraints.
It returns a tri-state verdict:
  TRUE           complete replay, rules and constraints satisfied
  FALSE          a named witness (violated rule, violated constraint, or an
                 untruncated trace that never finishes the task)
  UNVERIFIABLE   validity cannot be established (nothing parseable, entity
                 names outside the world, or a truncated output whose visible
                 prefix shows no violation)

`compare_to_reference` is a separate function that takes the reference and adds
observational equivalence and reference match. Keeping the two apart is what
lets the test suite prove that the semantic verdict never consults the
canonical trajectory.
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence

from research.simulator.traces import normalize_schedule
from research.ssr_pilot import families as F

TRUE, FALSE, UNVERIFIABLE = "TRUE", "FALSE", "UNVERIFIABLE"


@dataclass
class Verdict:
    parseable: bool
    valid_transitions: Optional[bool]
    violated_rule: Optional[str]
    constraints_ok: Optional[bool]
    violated_constraints: List[Dict] = field(default_factory=list)
    semantic_valid: str = UNVERIFIABLE
    reason: str = ""
    quality: Optional[float] = None
    steps: Optional[tuple] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["steps"] = [list(s) if isinstance(s, tuple) else s for s in (self.steps or [])]
        return d


def evaluate_candidate(world: Dict, raw_text: str, truncated: bool = False,
                       shown2canon: Optional[Dict[str, str]] = None) -> Verdict:
    steps, info = F.parse(world, raw_text, shown2canon)
    if steps is None:
        return Verdict(False, None, None, None, semantic_valid=UNVERIFIABLE, reason="unparseable")
    if info["unknown"]:
        return Verdict(True, None, None, None, semantic_valid=UNVERIFIABLE, reason="unknown_entity", steps=steps)
    ok, rule = F.rules_check(world, steps)
    if not ok and rule == "incomplete" and truncated:
        return Verdict(True, None, None, None, semantic_valid=UNVERIFIABLE, reason="truncated", steps=steps)
    if not ok:
        return Verdict(True, False, rule, None, semantic_valid=FALSE, reason=f"rule:{rule}", steps=steps)
    bad = F.violated_constraints(world, steps)
    if bad:
        return Verdict(True, True, None, False, bad, FALSE, f"constraint:{bad[0]['type']}",
                       F.quality(world, steps), steps)
    return Verdict(True, True, None, True, [], TRUE, "ok", F.quality(world, steps), steps)


def _norm(world: Dict, steps: Sequence):
    return normalize_schedule(steps) if world["family"] == "scheduling" else tuple(steps)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def compare_to_reference(world: Dict, steps: Optional[Sequence], raw_text: str, reference: Sequence,
                         reference_text: Optional[str] = None) -> Dict:
    """Reference-relative fields. Never feeds back into `semantic_valid`."""
    if steps is None:
        return {"ref_match_norm": False, "ref_match_strict": False, "obs_equiv": False}
    region, _ = F._region(raw_text)
    return {
        "ref_match_norm": _norm(world, steps) == _norm(world, reference),
        "ref_match_strict": reference_text is not None and _squash(region) == _squash(reference_text),
        "obs_equiv": F.observe(world, steps) == F.observe(world, reference),
    }
