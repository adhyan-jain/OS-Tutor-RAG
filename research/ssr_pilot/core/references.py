"""
Reference sampling and regime selection protocols for RCR.
"""

import random
from typing import Dict, List, Tuple
from research.ssr_pilot.core.schema import ReferenceRegime, ValidSpaceSpec


def get_references(valid_space: ValidSpaceSpec, regime: ReferenceRegime,
                   sample_size: int = 50, seed: int = 20261005) -> List[Tuple[int, Tuple]]:
    """
    Returns a list of (reference_index, reference_steps) according to the requested regime.
    """
    solutions = valid_space.valid_solutions
    
    if regime == ReferenceRegime.ACTUAL_CANONICAL:
        return [(0, valid_space.canonical_reference)]
        
    if regime == ReferenceRegime.FULL_REFERENCE_ENUMERATION:
        return list(enumerate(solutions))
        
    if regime == ReferenceRegime.UNIFORM_REFERENCE_SAMPLE:
        if len(solutions) <= sample_size:
            return list(enumerate(solutions))
        rng = random.Random(f"{seed}-{valid_space.world_id}")
        indices = sorted(rng.sample(range(len(solutions)), sample_size))
        return [(i, solutions[i]) for i in indices]
        
    if regime == ReferenceRegime.STRATIFIED_REFERENCE_SAMPLE:
        # If solutions space is small, return all; otherwise pick representative quantiles
        if len(solutions) <= sample_size:
            return list(enumerate(solutions))
        # Deterministic quantile sampling
        step_size = len(solutions) / sample_size
        indices = sorted(list({int(i * step_size) for i in range(sample_size)}))
        return [(i, solutions[i]) for i in indices]
        
    raise ValueError(f"Unknown reference regime: {regime}")
