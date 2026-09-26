"""Maps student questions to targeted OS mechanisms."""

from typing import Optional
from src.mechanism.ontology import OS_MECHANISMS


class MechanismParser:
    """Parses questions to identify the underlying OS mechanism domain."""

    @staticmethod
    def identify_mechanism(question: str) -> Optional[str]:
        q_lower = question.lower()

        if any(w in q_lower for w in ["round robin", "quantum", "context switch", "sjf", "fcfs", "scheduler", "scheduling"]):
            return "cpu_scheduling"
        if any(w in q_lower for w in ["page fault", "page replacement", "lru", "fifo", "belady", "frames", "ref string", "paging"]):
            return "paging_replacement"
        if any(w in q_lower for w in ["process state", "ready state", "blocked", "running", "io_request", "context switch"]):
            return "process_lifecycle"
        if any(w in q_lower for w in ["banker", "deadlock", "safe state", "allocation", "resource allocation"]):
            return "deadlock_banker"

        return None
