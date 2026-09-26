"""Counterfactual verification module for MGEV.

Tests explanations under controlled parameter perturbations to detect overgeneralization.
"""

from typing import Dict, Any, Tuple
from src.mechanism.schema import MechanismContract, VerificationStatus
from src.verification.engine import VerificationEngine


class CounterfactualVerifier:
    """Evaluates counterfactual stability of mechanism explanations."""

    def __init__(self, engine: VerificationEngine = None):
        self.engine = engine or VerificationEngine()

    def test_counterfactual(self, contract: MechanismContract, perturbation: Dict[str, Any]) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        """Applies a parameter perturbation to the verification input and checks stability."""
        baseline_input = dict(contract.verification_input)
        modified_input = dict(baseline_input, **perturbation)

        # Baseline execution
        baseline_contract = MechanismContract(
            contract_id=f"{contract.contract_id}_base",
            question_id=contract.question_id,
            claim=contract.claim,
            verification_input=baseline_input,
            predicted_observation=contract.predicted_observation
        )
        b_res = self.engine.verify_contract(baseline_contract)

        # Perturbed execution
        perturbed_contract = MechanismContract(
            contract_id=f"{contract.contract_id}_pert",
            question_id=contract.question_id,
            claim=contract.claim,
            verification_input=modified_input,
            predicted_observation=contract.predicted_observation
        )
        p_res = self.engine.verify_contract(perturbed_contract)

        if b_res.status == VerificationStatus.PASS and p_res.status == VerificationStatus.FAIL:
            reason = f"Claim is CONDITIONAL or OVERGENERALIZED: holds under baseline {baseline_input}, but fails under perturbed condition {perturbation}."
            return VerificationStatus.CONDITIONAL, reason, {
                "baseline_status": b_res.status,
                "perturbed_status": p_res.status,
                "baseline_obs": b_res.actual_observation,
                "perturbed_obs": p_res.actual_observation
            }

        return b_res.status, b_res.status_reason, {
            "baseline_status": b_res.status,
            "perturbed_status": p_res.status
        }
