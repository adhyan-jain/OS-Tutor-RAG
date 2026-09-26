"""Claim decomposer module for extracting atomic claims from questions or generated answers."""

from typing import List
from src.mechanism.schema import AtomicClaim, ClaimType
from src.query.mechanism_parser import MechanismParser


class ClaimDecomposer:
    """Decomposes explanations or mechanism queries into structured atomic claims."""

    @staticmethod
    def decompose_question_into_claims(question: str, category: ClaimType) -> List[AtomicClaim]:
        mechanism = MechanismParser.identify_mechanism(question)
        claims = []

        q_lower = question.lower()

        if "quantum" in q_lower and "context switch" in q_lower:
            claims.append(AtomicClaim(
                claim_id="cl_q1",
                text="Reducing Round Robin quantum size increases context switch frequency.",
                claim_type=ClaimType.COUNTERFACTUAL,
                topic="cpu_scheduling",
                target_mechanism="cpu_scheduling",
                required_evidence_keywords=["round robin", "quantum", "context switch"]
            ))
        elif "blocked" in q_lower or "i/o" in q_lower:
            claims.append(AtomicClaim(
                claim_id="cl_p1",
                text="When a running process requests I/O, it transitions to the BLOCKED state.",
                claim_type=ClaimType.STATE_TRANSITION,
                topic="process_lifecycle",
                target_mechanism="process_lifecycle",
                required_evidence_keywords=["blocked", "i/o", "running"]
            ))
            claims.append(AtomicClaim(
                claim_id="cl_p2",
                text="A blocked process cannot be directly scheduled to RUNNING until I/O completes and it becomes READY.",
                claim_type=ClaimType.STATE_TRANSITION,
                topic="process_lifecycle",
                target_mechanism="process_lifecycle",
                required_evidence_keywords=["ready", "running", "unblock"]
            ))
        elif "page fault" in q_lower or "frames" in q_lower:
            claims.append(AtomicClaim(
                claim_id="cl_vm1",
                text="Page replacement algorithms evict pages when all allocated physical frames are full.",
                claim_type=ClaimType.PROCEDURAL,
                topic="paging_replacement",
                target_mechanism="paging_replacement",
                required_evidence_keywords=["page fault", "frame", "replacement"]
            ))
        elif "banker" in q_lower or "deadlock" in q_lower:
            claims.append(AtomicClaim(
                claim_id="cl_dl1",
                text="Banker's Algorithm tests for safe state by finding a process sequence that can complete with available resources.",
                claim_type=ClaimType.PROCEDURAL,
                topic="deadlock_banker",
                target_mechanism="deadlock_banker",
                required_evidence_keywords=["banker", "safe state", "allocation"]
            ))
        else:
            claims.append(AtomicClaim(
                claim_id="cl_gen1",
                text=question,
                claim_type=category,
                topic="os_general",
                target_mechanism=mechanism,
                required_evidence_keywords=question.split()[:4]
            ))

        return claims
