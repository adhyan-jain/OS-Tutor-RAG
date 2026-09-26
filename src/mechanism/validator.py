"""Mechanism contract semantic validator."""

from src.mechanism.schema import MechanismContract, VerificationStatus
from src.mechanism.ontology import OS_MECHANISMS


class MechanismValidator:
    """Validates structural and semantic validity of Mechanism Contracts before execution."""

    @staticmethod
    def validate_contract(contract: MechanismContract) -> bool:
        if not contract.claim or not contract.claim.target_mechanism:
            contract.status = VerificationStatus.UNVERIFIABLE
            contract.status_reason = "Missing target mechanism specification"
            return False

        mech_name = contract.claim.target_mechanism
        if mech_name not in OS_MECHANISMS:
            contract.status = VerificationStatus.UNVERIFIABLE
            contract.status_reason = f"Unknown or unsupported OS mechanism: {mech_name}"
            return False

        return True
