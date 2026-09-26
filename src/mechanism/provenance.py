"""Provenance tracking for linking atomic claims to retrieved course chunks."""

from typing import List, Dict, Any
from src.mechanism.schema import AtomicClaim, EvidenceCitation, MechanismContract


class ProvenanceTracker:
    """Tracks and calculates evidence coverage for atomic claims."""

    @staticmethod
    def calculate_evidence_coverage(claims: List[AtomicClaim], contracts: List[MechanismContract]) -> Dict[str, Any]:
        if not claims:
            return {"coverage_ratio": 0.0, "total_claims": 0, "supported_claims": 0}
        
        supported = 0
        for contract in contracts:
            if contract.citations:
                supported += 1

        total = len(claims)
        return {
            "coverage_ratio": supported / total if total > 0 else 0.0,
            "total_claims": total,
            "supported_claims": supported,
            "unsupported_claims": total - supported
        }
