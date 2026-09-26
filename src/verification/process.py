"""Process lifecycle & state transition deterministic verifier."""

from typing import Dict, Any, Tuple, List
from src.verification.base import BaseVerifier
from src.mechanism.schema import MechanismContract, VerificationTrace, VerificationStatus
from src.mechanism.ontology import OS_MECHANISMS


class ProcessStateVerifier(BaseVerifier):
    """Verifies process state machine transitions and invalid transition assertions."""

    @property
    def mechanism_name(self) -> str:
        return "process_lifecycle"

    def execute(self, verification_input: Dict[str, Any]) -> VerificationTrace:
        initial_state = verification_input.get("initial_state", "READY")
        events = verification_input.get("events", [])
        
        valid_transitions = OS_MECHANISMS["process_lifecycle"]["valid_transitions"]
        
        current_state = initial_state
        events_executed = []
        raw_logs = []
        is_valid_path = True
        
        for event in events:
            ev_name = event.get("event")
            target_state = event.get("target_state")
            
            allowed_next = valid_transitions.get(current_state, [])
            if target_state in allowed_next:
                raw_logs.append(f"Transition {current_state} -> {target_state} on event '{ev_name}': VALID")
                events_executed.append({"from": current_state, "to": target_state, "event": ev_name, "valid": True})
                current_state = target_state
            else:
                raw_logs.append(f"Transition {current_state} -> {target_state} on event '{ev_name}': INVALID (Allowed: {allowed_next})")
                events_executed.append({"from": current_state, "to": target_state, "event": ev_name, "valid": False})
                is_valid_path = False
                break

        invariants_checked = {
            "valid_state_sequence": is_valid_path,
            "blocked_never_directly_runs": not any(
                e["from"] == "BLOCKED" and e["to"] == "RUNNING" for e in events_executed
            )
        }

        return VerificationTrace(
            verifier_name=self.mechanism_name,
            initial_state={"state": initial_state},
            events_executed=events_executed,
            final_state={"state": current_state},
            observed_values={"final_state": current_state, "is_valid_sequence": is_valid_path},
            invariants_checked=invariants_checked,
            raw_logs=raw_logs
        )

    def verify(self, contract: MechanismContract) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        trace = self.execute(contract.verification_input)
        contract.verification_trace = trace
        
        predicted = contract.predicted_observation
        expected_valid = predicted.get("is_valid_sequence", True)
        expected_final = predicted.get("final_state")
        
        actual_valid = trace.observed_values["is_valid_sequence"]
        actual_final = trace.observed_values["final_state"]
        
        if expected_valid != actual_valid:
            reason = f"State transition validity mismatch: predicted valid={expected_valid}, but verifier observed valid={actual_valid}."
            return VerificationStatus.FAIL, reason, trace.observed_values
            
        if expected_final and expected_final != actual_final:
            reason = f"Final state mismatch: predicted {expected_final}, but observed {actual_final}."
            return VerificationStatus.FAIL, reason, trace.observed_values
            
        return VerificationStatus.PASS, "State transitions and invariants verified successfully.", trace.observed_values
