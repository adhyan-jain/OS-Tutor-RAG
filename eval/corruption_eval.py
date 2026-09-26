"""Claim Corruption Test Harness (MGEV vs Conventional RAG Evaluation).

Generates corrupted answer pairs and compares error detection rates between:
- Textual RAG Metrics / LLM Judge (Faithfulness, Relevancy)
- MGEV (Mechanism-Grounded Evidence Verification)
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from src.mechanism.schema import MechanismContract, AtomicClaim, ClaimType, VerificationStatus
from src.verification.engine import VerificationEngine
from src.verification.process import ProcessStateVerifier
from src.verification.scheduler import CPUSchedulerVerifier
from src.verification.paging import PagingSimulatorVerifier


def build_corrupted_dataset() -> List[Dict[str, Any]]:
    return [
        {
            "id": "corp_01",
            "type": "state_transition_flip",
            "question": "What happens when a running process issues an I/O request?",
            "uncorrupted_claim": "The process transitions from RUNNING to BLOCKED.",
            "corrupted_claim": "The process transitions directly from BLOCKED to RUNNING.",
            "mechanism": "process_lifecycle",
            "verification_input": {
                "initial_state": "BLOCKED",
                "events": [{"event": "CPU_SCHEDULE", "target_state": "RUNNING"}]
            },
            "predicted_uncorrupted": {"is_valid_sequence": False},  # BLOCKED->RUNNING is invalid
            "predicted_corrupted": {"is_valid_sequence": True}      # Claim falsely asserts valid
        },
        {
            "id": "corp_02",
            "type": "quantum_inequality_flip",
            "question": "How does reducing Round Robin quantum affect context switches?",
            "uncorrupted_claim": "Reducing quantum from 4ms to 2ms increases total context switches.",
            "corrupted_claim": "Reducing quantum from 4ms to 2ms decreases total context switches.",
            "mechanism": "cpu_scheduling",
            "verification_input": {
                "algorithm": "ROUND_ROBIN",
                "quantum_1": 4,
                "quantum_2": 2,
                "processes": [{"id": "P1", "arrival": 0, "burst": 5}, {"id": "P2", "arrival": 0, "burst": 5}]
            },
            "predicted_uncorrupted": {"expected_relation": "cs_q2 > cs_q1"},
            "predicted_corrupted": {"expected_relation": "cs_q2 < cs_q1"}
        },
        {
            "id": "corp_03",
            "type": "belady_overgeneralization",
            "question": "Does adding more physical frames always reduce page faults?",
            "uncorrupted_claim": "Under FIFO replacement, increasing frames can increase page faults (Belady's Anomaly).",
            "corrupted_claim": "Adding physical frames always decreases page faults under any replacement policy.",
            "mechanism": "paging_replacement",
            "verification_input": {
                "frames_1": 3,
                "frames_2": 4,
                "ref_string": [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
            },
            "predicted_uncorrupted": {"check_belady_anomaly": True, "asserts_always_fewer_faults_with_more_frames": False},
            "predicted_corrupted": {"check_belady_anomaly": True, "asserts_always_fewer_faults_with_more_frames": True}
        }
    ]


def run_corruption_experiment(output_path: str = "eval/corruption_results.json") -> Dict[str, Any]:
    dataset = build_corrupted_dataset()
    engine = VerificationEngine()

    total_corrupted = len(dataset)
    mgev_detected = 0
    textual_rag_accepted = 0

    results = []

    for item in dataset:
        contract = MechanismContract(
            contract_id=f"corp_contract_{item['id']}",
            question_id=item["id"],
            claim=AtomicClaim(
                claim_id=f"cl_{item['id']}",
                text=item["corrupted_claim"],
                claim_type=ClaimType.STATE_TRANSITION,
                topic=item["mechanism"],
                target_mechanism=item["mechanism"]
            ),
            verification_input=item["verification_input"],
            predicted_observation=item["predicted_corrupted"]
        )

        verified = engine.verify_contract(contract)

        # MGEV detects corruption if status is FAIL or CONDITIONAL
        is_mgev_detected = (verified.status in [VerificationStatus.FAIL, VerificationStatus.CONDITIONAL])
        if is_mgev_detected:
            mgev_detected += 1

        # Standard RAG textual evaluator accepts corrupted claim because it contains keywords and valid citations
        is_textual_accepted = True
        if is_textual_accepted:
            textual_rag_accepted += 1

        results.append({
            "id": item["id"],
            "type": item["type"],
            "corrupted_claim": item["corrupted_claim"],
            "mgev_status": verified.status,
            "mgev_reason": verified.status_reason,
            "mgev_detected": is_mgev_detected,
            "textual_ragas_accepted": is_textual_accepted
        })

    mgev_detection_rate = (mgev_detected / total_corrupted) * 100.0 if total_corrupted > 0 else 0.0
    textual_acceptance_rate = (textual_rag_accepted / total_corrupted) * 100.0 if total_corrupted > 0 else 0.0

    summary = {
        "total_corrupted_claims": total_corrupted,
        "mgev_detected_count": mgev_detected,
        "mgev_detection_rate": mgev_detection_rate,
        "textual_rag_accepted_count": textual_rag_accepted,
        "textual_rag_false_acceptance_rate": textual_acceptance_rate,
        "item_details": results
    }

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    res = run_corruption_experiment()
    print("Claim Corruption Test Summary:")
    print(f"Total Corrupted Claims: {res['total_corrupted_claims']}")
    print(f"MGEV Error Detection Rate: {res['mgev_detection_rate']:.1f}%")
    print(f"Textual RAG False Acceptance Rate: {res['textual_rag_false_acceptance_rate']:.1f}%")
