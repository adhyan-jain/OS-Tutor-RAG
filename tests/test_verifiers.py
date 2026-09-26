"""Unit tests for MGEV deterministic verifiers."""

import pytest
from src.mechanism.schema import MechanismContract, AtomicClaim, ClaimType, VerificationStatus
from src.verification.process import ProcessStateVerifier
from src.verification.scheduler import CPUSchedulerVerifier
from src.verification.paging import PagingSimulatorVerifier
from src.verification.deadlock import DeadlockBankerVerifier


def test_process_state_verifier():
    verifier = ProcessStateVerifier()
    contract = MechanismContract(
        contract_id="c1",
        question_id="q1",
        claim=AtomicClaim(
            claim_id="cl1",
            text="A running process transitions to blocked on IO request",
            claim_type=ClaimType.STATE_TRANSITION,
            topic="process_lifecycle",
            target_mechanism="process_lifecycle"
        ),
        verification_input={
            "initial_state": "RUNNING",
            "events": [{"event": "IO_REQUEST", "target_state": "BLOCKED"}]
        },
        predicted_observation={"is_valid_sequence": True, "final_state": "BLOCKED"}
    )
    status, reason, obs = verifier.verify(contract)
    assert status == VerificationStatus.PASS
    assert obs["final_state"] == "BLOCKED"


def test_invalid_process_state_transition():
    verifier = ProcessStateVerifier()
    contract = MechanismContract(
        contract_id="c2",
        question_id="q2",
        claim=AtomicClaim(
            claim_id="cl2",
            text="A blocked process directly transitions to running",
            claim_type=ClaimType.STATE_TRANSITION,
            topic="process_lifecycle",
            target_mechanism="process_lifecycle"
        ),
        verification_input={
            "initial_state": "BLOCKED",
            "events": [{"event": "CPU_SCHEDULE", "target_state": "RUNNING"}]
        },
        predicted_observation={"is_valid_sequence": True, "final_state": "RUNNING"}
    )
    status, reason, obs = verifier.verify(contract)
    assert status == VerificationStatus.FAIL


def test_cpu_scheduler_round_robin():
    verifier = CPUSchedulerVerifier()
    contract = MechanismContract(
        contract_id="c3",
        question_id="q3",
        claim=AtomicClaim(
            claim_id="cl3",
            text="Reducing Round Robin quantum from 4 to 2 increases context switches",
            claim_type=ClaimType.NUMERICAL,
            topic="cpu_scheduling",
            target_mechanism="cpu_scheduling"
        ),
        verification_input={
            "algorithm": "ROUND_ROBIN",
            "quantum_1": 4,
            "quantum_2": 2,
            "processes": [
                {"id": "P1", "arrival": 0, "burst": 5},
                {"id": "P2", "arrival": 0, "burst": 5}
            ]
        },
        predicted_observation={"expected_relation": "cs_q2 > cs_q1"}
    )
    status, reason, obs = verifier.verify(contract)
    assert status == VerificationStatus.PASS


def test_paging_belady_anomaly():
    verifier = PagingSimulatorVerifier()
    contract = MechanismContract(
        contract_id="c4",
        question_id="q4",
        claim=AtomicClaim(
            claim_id="cl4",
            text="More frames always reduce page faults",
            claim_type=ClaimType.COUNTERFACTUAL,
            topic="paging_replacement",
            target_mechanism="paging_replacement"
        ),
        verification_input={
            "frames_1": 3,
            "frames_2": 4,
            "ref_string": [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        },
        predicted_observation={
            "check_belady_anomaly": True,
            "asserts_always_fewer_faults_with_more_frames": True
        }
    )
    status, reason, obs = verifier.verify(contract)
    assert status == VerificationStatus.FAIL
    assert "Belady's Anomaly detected" in reason


def test_deadlock_banker_verifier():
    verifier = DeadlockBankerVerifier()
    contract = MechanismContract(
        contract_id="c5",
        question_id="q5",
        claim=AtomicClaim(
            claim_id="cl5",
            text="System is in a safe state",
            claim_type=ClaimType.PROCEDURAL,
            topic="deadlock_banker",
            target_mechanism="deadlock_banker"
        ),
        verification_input={
            "available": [3, 3, 2],
            "max": [[5, 4, 2], [3, 2, 2]],
            "allocation": [[0, 1, 0], [2, 0, 0]]
        },
        predicted_observation={"expected_is_safe": True}
    )
    status, reason, obs = verifier.verify(contract)
    assert status == VerificationStatus.PASS
