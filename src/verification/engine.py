"""Verification Engine for MGEV.

Orchestrates verification across deterministic verifiers and synthesizes results.
"""

from typing import Dict, Any, List
from src.mechanism.schema import MechanismContract, VerificationStatus
from src.mechanism.validator import MechanismValidator
from src.verification.process import ProcessStateVerifier
from src.verification.scheduler import CPUSchedulerVerifier
from src.verification.paging import PagingSimulatorVerifier
from src.verification.deadlock import DeadlockBankerVerifier


class VerificationEngine:
    """Central engine for executing claim verification against OS mechanism models."""

    def __init__(self):
        self.verifiers = {
            "process_lifecycle": ProcessStateVerifier(),
            "cpu_scheduling": CPUSchedulerVerifier(),
            "paging_replacement": PagingSimulatorVerifier(),
            "deadlock_banker": DeadlockBankerVerifier()
        }

    def verify_contract(self, contract: MechanismContract) -> MechanismContract:
        if not MechanismValidator.validate_contract(contract):
            return contract

        mech_name = contract.claim.target_mechanism
        verifier = self.verifiers.get(mech_name)

        if not verifier:
            contract.status = VerificationStatus.UNVERIFIABLE
            contract.status_reason = f"No active verifier for mechanism '{mech_name}'"
            return contract

        status, reason, observed = verifier.verify(contract)
        contract.status = status
        contract.status_reason = reason
        contract.actual_observation = observed
        return contract

    def verify_all_contracts(self, contracts: List[MechanismContract]) -> List[MechanismContract]:
        return [self.verify_contract(c) for c in contracts]
