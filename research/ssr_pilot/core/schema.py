"""
Data structures and schema definitions for Reference-Choice Robustness (RCR).
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple, Union


class ReferenceRegime(str, Enum):
    ACTUAL_CANONICAL = "ACTUAL_CANONICAL"
    FULL_REFERENCE_ENUMERATION = "FULL_REFERENCE_ENUMERATION"
    UNIFORM_REFERENCE_SAMPLE = "UNIFORM_REFERENCE_SAMPLE"
    STRATIFIED_REFERENCE_SAMPLE = "STRATIFIED_REFERENCE_SAMPLE"


@dataclass
class ValidSpaceSpec:
    world_id: str
    family: str
    n_rules: int
    n_valid_task: int
    valid_solutions: List[Tuple]
    canonical_reference: Tuple
    exhaustive: bool = True
    enumeration_method: str = "exact_replay_search"

    def to_dict(self) -> Dict:
        return {
            "world_id": self.world_id,
            "family": self.family,
            "n_rules": self.n_rules,
            "n_valid_task": self.n_valid_task,
            "valid_solutions": [list(s) for s in self.valid_solutions],
            "canonical_reference": list(self.canonical_reference),
            "exhaustive": self.exhaustive,
            "enumeration_method": self.enumeration_method,
        }


@dataclass
class EvaluatorVerdict:
    evaluator_id: str
    world_id: str
    generation_id: str
    model: str
    variant: str
    seed: int
    reference_idx: int
    reference_steps: Tuple
    semantic_valid: str  # "TRUE", "FALSE", "UNVERIFIABLE"
    ref_match_norm: bool
    ref_match_strict: bool
    obs_equiv: bool
    evaluator_pass: bool
    reason: str = ""

    def to_dict(self) -> Dict:
        return {
            "evaluator_id": self.evaluator_id,
            "world_id": self.world_id,
            "generation_id": self.generation_id,
            "model": self.model,
            "variant": self.variant,
            "seed": self.seed,
            "reference_idx": self.reference_idx,
            "reference_steps": list(self.reference_steps),
            "semantic_valid": self.semantic_valid,
            "ref_match_norm": self.ref_match_norm,
            "ref_match_strict": self.ref_match_strict,
            "obs_equiv": self.obs_equiv,
            "evaluator_pass": self.evaluator_pass,
            "reason": self.reason,
        }


@dataclass
class BenchmarkConclusion:
    reference_regime: str
    reference_idx: Optional[int]
    evaluator_id: str
    model_scores: Dict[str, float]
    model_rankings: List[str]
    pairwise_winners: Dict[str, str]  # "A_vs_B": "A" | "B" | "TIE" | "INDETERMINATE"
    pairwise_p_values: Dict[str, float]
    failure_taxonomy_distribution: Dict[str, int]
    is_oracle_invariant: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)
