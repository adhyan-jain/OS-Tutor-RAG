"""Data models and schemas for Mechanism-Grounded Evidence Verification (MGEV)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class ClaimType(str, Enum):
    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    STATE_TRANSITION = "state_transition"
    NUMERICAL = "numerical"
    CODE_TRACE = "code_trace"
    COUNTERFACTUAL = "counterfactual"
    MISCONCEPTION = "misconception"


class VerificationStatus(str, Enum):
    PASS = "PASS"
    CONDITIONAL = "CONDITIONAL"
    FAIL = "FAIL"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass
class AtomicClaim:
    """Represents a single atomic claim extracted from a user question or candidate answer."""
    claim_id: str
    text: str
    claim_type: ClaimType
    topic: str
    target_mechanism: Optional[str] = None
    preconditions: Dict[str, Any] = field(default_factory=dict)
    assumptions: Dict[str, Any] = field(default_factory=dict)
    expected_state_transition: Dict[str, Any] = field(default_factory=dict)
    expected_observable: Dict[str, Any] = field(default_factory=dict)
    required_evidence_keywords: List[str] = field(default_factory=list)


@dataclass
class EvidenceCitation:
    """Links a claim to retrieved course content."""
    chunk_id: str
    parent_id: Optional[str]
    source_file: str
    page_or_heading: str
    excerpt: str
    relevance_score: float = 0.0


@dataclass
class VerificationTrace:
    """Detailed trace from a deterministic execution verifier."""
    verifier_name: str
    initial_state: Dict[str, Any]
    events_executed: List[Dict[str, Any]]
    final_state: Dict[str, Any]
    observed_values: Dict[str, Any]
    invariants_checked: Dict[str, bool]
    raw_logs: List[str] = field(default_factory=list)


@dataclass
class MechanismContract:
    """Claim-Evidence-Mechanism Contract (MGEV Contract).

    Binds a natural-language claim to retrieved evidence, target OS operational semantics,
    executable verifiers, and counterfactual test outcomes.
    """
    contract_id: str
    question_id: str
    claim: AtomicClaim
    citations: List[EvidenceCitation] = field(default_factory=list)
    verifier_id: Optional[str] = None
    verification_input: Dict[str, Any] = field(default_factory=dict)
    predicted_observation: Dict[str, Any] = field(default_factory=dict)
    actual_observation: Optional[Dict[str, Any]] = None
    verification_trace: Optional[VerificationTrace] = None
    status: VerificationStatus = VerificationStatus.UNVERIFIABLE
    status_reason: str = ""
    is_counterfactual_tested: bool = False
    counterfactual_result: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
