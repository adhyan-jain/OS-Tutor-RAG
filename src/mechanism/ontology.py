"""OS Mechanism Ontology for MGEV.

Defines bounded operational semantics for core OS topics:
- Process Lifecycle & Transitions
- CPU Scheduling
- Virtual Memory & Page Replacement
- Resource Allocation & Deadlock
"""

from typing import Dict, List, Set, Any

# Taxonomy of bounded mechanisms supported by the course corpus
OS_MECHANISMS: Dict[str, Dict[str, Any]] = {
    "process_lifecycle": {
        "name": "Process Lifecycle & Transitions",
        "states": ["EMBRYO", "READY", "RUNNING", "BLOCKED", "ZOMBIE"],
        "events": ["CREATE", "SCHEDULE", "DESCHEDULE", "IO_REQUEST", "IO_COMPLETE", "EXIT"],
        "valid_transitions": {
            "EMBRYO": ["READY"],
            "READY": ["RUNNING"],
            "RUNNING": ["READY", "BLOCKED", "ZOMBIE"],
            "BLOCKED": ["READY"],
            "ZOMBIE": []
        },
        "invariants": [
            "At most 1 process in RUNNING state per CPU core",
            "BLOCKED process cannot transition directly to RUNNING without becoming READY first"
        ]
    },
    "cpu_scheduling": {
        "name": "CPU Scheduling Algorithms",
        "algorithms": ["FCFS", "SJF", "STCF", "ROUND_ROBIN"],
        "state_variables": ["quantum", "arrival_time", "burst_time", "time_remaining"],
        "observables": ["context_switches", "turnaround_time", "response_time", "wait_time"],
        "invariants": [
            "Context switches increase monotonic with quantum reduction for non-zero CPU bound processes",
            "SJF minimizes average waiting time for simultaneous arrivals"
        ]
    },
    "paging_replacement": {
        "name": "Virtual Memory & Page Replacement",
        "algorithms": ["FIFO", "LRU", "OPTIMAL", "CLOCK"],
        "state_variables": ["allocated_frames", "reference_string", "page_table"],
        "observables": ["page_faults", "hits", "evicted_pages"],
        "invariants": [
            "Optimal replacement yields minimal or equal page faults compared to FIFO/LRU on any reference string",
            "Belady's anomaly can occur under FIFO where increasing frames increases page faults"
        ]
    },
    "deadlock_banker": {
        "name": "Deadlock & Banker's Algorithm",
        "state_variables": ["Available", "Max", "Allocation", "Need"],
        "observables": ["is_safe", "safe_sequence", "deadlock_detected"],
        "invariants": [
            "Need[i][j] = Max[i][j] - Allocation[i][j]",
            "A system is safe if there exists at least one execution sequence where all processes complete"
        ]
    }
}


def get_mechanism_info(mechanism_name: str) -> Dict[str, Any]:
    return OS_MECHANISMS.get(mechanism_name, {})
