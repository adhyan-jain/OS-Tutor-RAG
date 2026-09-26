"""8-Class Error Attribution Taxonomy Classifier for OS-Tutor-RAG (MGEV)."""

from enum import Enum
from typing import Dict, Any


class ErrorCategory(str, Enum):
    RETRIEVAL_FAILURE = "retrieval_failure"
    EVIDENCE_SELECTION_FAILURE = "evidence_selection_failure"
    CONTEXT_ASSEMBLY_FAILURE = "context_assembly_failure"
    CLAIM_DECOMPOSITION_FAILURE = "claim_decomposition_failure"
    MECHANISM_MAPPING_FAILURE = "mechanism_mapping_failure"
    VERIFICATION_FAILURE = "verification_failure"
    GENERATION_FAILURE = "generation_failure"
    EVALUATION_FAILURE = "evaluation_failure"


class ErrorAttributor:
    """Classifies system failures into an 8-class error taxonomy."""

    @staticmethod
    def attribute_error(pipeline_trace: Dict[str, Any]) -> ErrorCategory:
        if not pipeline_trace.get("retrieved_chunks"):
            return ErrorCategory.RETRIEVAL_FAILURE

        if not pipeline_trace.get("evidence_selected"):
            return ErrorCategory.EVIDENCE_SELECTION_FAILURE

        if pipeline_trace.get("context_truncated", False):
            return ErrorCategory.CONTEXT_ASSEMBLY_FAILURE

        if not pipeline_trace.get("claims_extracted"):
            return ErrorCategory.CLAIM_DECOMPOSITION_FAILURE

        if not pipeline_trace.get("target_mechanism"):
            return ErrorCategory.MECHANISM_MAPPING_FAILURE

        if pipeline_trace.get("verifier_status") == "FAIL":
            return ErrorCategory.VERIFICATION_FAILURE

        if pipeline_trace.get("answer_hallucinated", False):
            return ErrorCategory.GENERATION_FAILURE

        return ErrorCategory.EVALUATION_FAILURE
