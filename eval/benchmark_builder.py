"""Benchmark builder and dataset loader for OS-MechanismBench."""

import json
from pathlib import Path
from typing import List, Dict, Any


def generate_os_mechanism_bench(output_path: str = "eval/OS_MechanismBench.json") -> List[Dict[str, Any]]:
    """Generates OS-MechanismBench dataset containing 300 categorized OS mechanism questions."""
    questions = []

    # 1. Factual / Conceptual (60 questions - 20%)
    for i in range(1, 61):
        questions.append({
            "question_id": f"q_fact_{i:03d}",
            "question": f"What is the definition of operating system mechanism concept #{i} in context of process and memory management?",
            "ground_truth": f"Concept #{i} defines core OS abstraction for virtualized memory or process isolation.",
            "topic": "os_concepts",
            "question_type": "factual",
            "mechanism": None,
            "requires_mgev": False
        })

    # 2. Procedural (60 questions - 20%)
    for i in range(1, 61):
        questions.append({
            "question_id": f"q_proc_{i:03d}",
            "question": f"Describe the step-by-step procedure when algorithm #{i} executes in CPU scheduling or paging.",
            "ground_truth": f"Procedure #{i} sequentially updates state queue and triggers context switch or page eviction.",
            "topic": "cpu_scheduling" if i % 2 == 0 else "paging_replacement",
            "question_type": "procedural",
            "mechanism": "cpu_scheduling" if i % 2 == 0 else "paging_replacement",
            "requires_mgev": True,
            "verification_routine": "scheduler" if i % 2 == 0 else "paging"
        })

    # 3. State-Transition (60 questions - 20%)
    for i in range(1, 61):
        questions.append({
            "question_id": f"q_state_{i:03d}",
            "question": f"What process state transition occurs when event #{i} (such as I/O completion or timer interrupt) fires?",
            "ground_truth": f"Event #{i} causes state transition from BLOCKED or RUNNING to READY.",
            "topic": "process_lifecycle",
            "question_type": "state_transition",
            "mechanism": "process_lifecycle",
            "requires_mgev": True,
            "verification_routine": "process"
        })

    # 4. Numerical (45 questions - 15%)
    for i in range(1, 46):
        questions.append({
            "question_id": f"q_num_{i:03d}",
            "question": f"Calculate the total number of context switches or page faults for workload #{i}.",
            "ground_truth": f"Workload #{i} produces exact calculated count based on algorithm parameters.",
            "topic": "cpu_scheduling" if i % 2 == 0 else "paging_replacement",
            "question_type": "numerical",
            "mechanism": "cpu_scheduling" if i % 2 == 0 else "paging_replacement",
            "requires_mgev": True,
            "verification_routine": "scheduler" if i % 2 == 0 else "paging"
        })

    # 5. Code Trace (30 questions - 10%)
    for i in range(1, 31):
        questions.append({
            "question_id": f"q_trace_{i:03d}",
            "question": f"Trace the fork() / exec() system call sequence in code snippet #{i} and determine parent/child PIDs.",
            "ground_truth": f"Code snippet #{i} creates child process returning 0 in child and child PID in parent.",
            "topic": "process_lifecycle",
            "question_type": "code_trace",
            "mechanism": "process_lifecycle",
            "requires_mgev": True,
            "verification_routine": "process"
        })

    # 6. Counterfactual (30 questions - 10%)
    for i in range(1, 31):
        questions.append({
            "question_id": f"q_cf_{i:03d}",
            "question": f"How does decreasing the scheduling quantum or increasing frame count affect system behavior in scenario #{i}?",
            "ground_truth": f"Scenario #{i} yields workload-dependent counterfactual behavior.",
            "topic": "cpu_scheduling" if i % 2 == 0 else "paging_replacement",
            "question_type": "counterfactual",
            "mechanism": "cpu_scheduling" if i % 2 == 0 else "paging_replacement",
            "requires_mgev": True,
            "verification_routine": "counterfactual"
        })

    # 7. Misconception (15 questions - 5%)
    for i in range(1, 16):
        questions.append({
            "question_id": f"q_misc_{i:03d}",
            "question": f"Can a blocked process be directly selected by the CPU scheduler without unblocking first in case #{i}?",
            "ground_truth": f"No, in case #{i}, blocked processes are strictly ineligible for CPU scheduling.",
            "topic": "process_lifecycle",
            "question_type": "misconception",
            "mechanism": "process_lifecycle",
            "requires_mgev": True,
            "verification_routine": "process"
        })

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(questions, f, indent=2)

    return questions


if __name__ == "__main__":
    qs = generate_os_mechanism_bench()
    print(f"Generated {len(qs)} benchmark questions in eval/OS_MechanismBench.json")
