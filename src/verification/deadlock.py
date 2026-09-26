"""Deadlock & Banker's Algorithm deterministic verifier."""

from typing import Dict, Any, Tuple, List
from src.verification.base import BaseVerifier
from src.mechanism.schema import MechanismContract, VerificationTrace, VerificationStatus


class DeadlockBankerVerifier(BaseVerifier):
    """Simulates Banker's Algorithm safety check and deadlock detection."""

    @property
    def mechanism_name(self) -> str:
        return "deadlock_banker"

    def execute(self, verification_input: Dict[str, Any]) -> VerificationTrace:
        available = list(verification_input.get("available", [3, 3, 2]))
        max_matrix = verification_input.get("max", [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3]
        ])
        allocation = verification_input.get("allocation", [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2]
        ])

        num_processes = len(allocation)
        num_resources = len(available)

        need = [[max_matrix[i][j] - allocation[i][j] for j in range(num_resources)] for i in range(num_processes)]
        work = list(available)
        finish = [False] * num_processes
        safe_seq = []

        while len(safe_seq) < num_processes:
            found = False
            for i in range(num_processes):
                if not finish[i]:
                    if all(need[i][j] <= work[j] for j in range(num_resources)):
                        for j in range(num_resources):
                            work[j] += allocation[i][j]
                        finish[i] = True
                        safe_seq.append(f"P{i}")
                        found = True
                        break
            if not found:
                break

        is_safe = (len(safe_seq) == num_processes)
        observed = {
            "is_safe": is_safe,
            "safe_sequence": safe_seq if is_safe else [],
            "deadlock_detected": not is_safe,
            "need_matrix": need
        }

        return VerificationTrace(
            verifier_name=self.mechanism_name,
            initial_state={"available": available, "num_processes": num_processes},
            events_executed=[{"action": "banker_safety_check"}],
            final_state={"safe": is_safe},
            observed_values=observed,
            invariants_checked={"need_equals_max_minus_alloc": True},
            raw_logs=[f"Banker's algorithm evaluated. Safe: {is_safe}, Sequence: {safe_seq}"]
        )

    def verify(self, contract: MechanismContract) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        trace = self.execute(contract.verification_input)
        contract.verification_trace = trace

        predicted = contract.predicted_observation
        actual = trace.observed_values

        if "expected_is_safe" in predicted:
            exp_safe = predicted["expected_is_safe"]
            act_safe = actual["is_safe"]
            if exp_safe != act_safe:
                reason = f"Banker safety prediction error: predicted safe={exp_safe}, but actual execution observed safe={act_safe}."
                return VerificationStatus.FAIL, reason, actual

        return VerificationStatus.PASS, "Deadlock/Banker prediction verified.", actual
