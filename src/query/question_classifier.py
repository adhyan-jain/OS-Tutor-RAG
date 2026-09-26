"""Question classification module for MGEV.

Classifies incoming student questions into categories:
- factual / conceptual -> Standard baseline RAG
- procedural / state_transition / numerical / counterfactual -> Activated MGEV
"""

from typing import Dict, Any
from src.mechanism.schema import ClaimType


class QuestionClassifier:
    """Classifies user questions to determine whether MGEV mechanism verification is required."""

    @staticmethod
    def classify(question: str) -> Dict[str, Any]:
        q_lower = question.lower()

        is_counterfactual = any(w in q_lower for w in ["what if", "if we change", "if quantum is reduced", "if frames increase", "counterfactual", "decreasing the scheduling quantum", "increasing frame count", "affect system behavior"])
        is_numerical = any(w in q_lower for w in ["calculate", "how many page faults", "context switches", "turnaround time", "safe sequence", "banker"])
        is_state = any(w in q_lower for w in ["state transition", "blocked to running", "when a process blocks", "cpu schedule", "fork", "exec"])
        is_procedural = any(w in q_lower for w in ["how does", "what sequence", "steps involved", "page replacement algorithm", "round robin"])

        if is_counterfactual:
            category = ClaimType.COUNTERFACTUAL
            requires_mgev = True
        elif is_numerical:
            category = ClaimType.NUMERICAL
            requires_mgev = True
        elif is_state:
            category = ClaimType.STATE_TRANSITION
            requires_mgev = True
        elif is_procedural:
            category = ClaimType.PROCEDURAL
            requires_mgev = True
        else:
            category = ClaimType.FACTUAL
            requires_mgev = False

        return {
            "question": question,
            "category": category,
            "requires_mgev": requires_mgev
        }
