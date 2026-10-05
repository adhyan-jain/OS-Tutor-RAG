"""
Failure-taxonomy stability analysis across valid reference choices.
"""

from typing import Dict, List, Sequence
from research.ssr_pilot.core.schema import EvaluatorVerdict


def compute_failure_taxonomy(verdicts: Sequence[EvaluatorVerdict]) -> Dict[str, int]:
    """
    Categorizes errors for a set of EvaluatorVerdict objects under reference R.
    """
    taxonomy = {
        "unparseable": 0,
        "unknown_entity": 0,
        "rule_violation": 0,
        "constraint_violation": 0,
        "canonical_mismatch_only": 0,
        "valid_pass": 0,
    }

    for v in verdicts:
        if v.evaluator_pass:
            taxonomy["valid_pass"] += 1
        elif v.reason == "unparseable":
            taxonomy["unparseable"] += 1
        elif v.reason == "unknown_entity":
            taxonomy["unknown_entity"] += 1
        elif v.reason.startswith("rule:"):
            taxonomy["rule_violation"] += 1
        elif v.reason.startswith("constraint:"):
            taxonomy["constraint_violation"] += 1
        elif v.semantic_valid == "TRUE" and not v.evaluator_pass:
            taxonomy["canonical_mismatch_only"] += 1
        else:
            taxonomy["rule_violation"] += 1

    return taxonomy


def compute_taxonomy_stability(taxonomy_by_ref: Dict[int, Dict[str, int]]) -> Dict:
    """
    Measures taxonomy shifts across valid reference choices.
    """
    categories = list(next(iter(taxonomy_by_ref.values())).keys())
    ref_dominant = []

    for ref_idx, tax in taxonomy_by_ref.items():
        # dominant error excluding valid_pass
        err_tax = {k: v for k, v in tax.items() if k != "valid_pass"}
        dom = max(err_tax.keys(), key=lambda k: err_tax[k]) if any(err_tax.values()) else "none"
        ref_dominant.append(dom)

    counts = {cat: ref_dominant.count(cat) for cat in set(ref_dominant)}
    n_refs = len(taxonomy_by_ref)

    return {
        "n_references": n_refs,
        "dominant_failure_category_distribution": {cat: count / n_refs for cat, count in counts.items()},
        "is_dominant_category_stable": len(set(ref_dominant)) == 1,
    }
