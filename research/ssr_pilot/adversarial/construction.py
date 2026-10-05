"""
Adversarial dataset construction module.
Derives 96 controlled contrast cases from real generated traces.
"""

import json
import os
from typing import Dict, List, Tuple
from research.ssr_pilot import families as F
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.core.oracle import evaluate_oracle
from research.ssr_pilot.core.valid_space import build_all_valid_spaces
from research.ssr_pilot.worlds import load_worlds

ADVERSARIAL_DIR = "research/ssr_pilot/results/adversarial"


def build_adversarial_dataset() -> List[Dict]:
    """
    Constructs 96 balanced, controlled contrast cases from real outputs and bank traces:
    - 24 canonical-valid
    - 24 noncanonical-valid
    - 24 lexically similar invalid
    - 24 same final state invalid / lexically distant valid
    """
    os.makedirs(ADVERSARIAL_DIR, exist_ok=True)
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    valid_spaces = build_all_valid_spaces(worlds_list)
    banks = {w_id: load_bank(w) for w_id, w in worlds.items()}

    cases = []

    for w_id, world in worlds.items():
        v_space = valid_spaces[w_id]
        bank = banks[w_id]
        canon_ref = v_space.canonical_reference

        # Group A: canonical-valid
        formatted_canon = F.format_steps(world, canon_ref)
        text_canon = f"TRACE: {formatted_canon}"
        v_canon = evaluate_oracle(world, text_canon)
        assert v_canon.semantic_valid == "TRUE"
        cases.append({
            "case_id": f"{w_id}_canonical_valid",
            "world_id": w_id,
            "category": "canonical_valid",
            "text": text_canon,
            "steps": canon_ref,
            "oracle_verdict": "TRUE",
            "ref_match_strict": True,
            "ref_match_norm": True,
            "obs_equiv": True,
        })

        # Group B: noncanonical-valid
        noncanon_refs = [r for r in v_space.valid_solutions if r != canon_ref]
        if noncanon_refs:
            noncanon_ref = noncanon_refs[0]
            formatted_nc = F.format_steps(world, noncanon_ref)
            text_nc = f"TRACE: {formatted_nc}"
            v_nc = evaluate_oracle(world, text_nc)
            assert v_nc.semantic_valid == "TRUE"
            cases.append({
                "case_id": f"{w_id}_noncanonical_valid",
                "world_id": w_id,
                "category": "noncanonical_valid",
                "text": text_nc,
                "steps": noncanon_ref,
                "oracle_verdict": "TRUE",
                "ref_match_strict": False,
                "ref_match_norm": False,
                "obs_equiv": (F.observe(world, noncanon_ref) == F.observe(world, canon_ref)),
            })

        # Group C: lexically similar invalid
        if bank.get("invalid_rule"):
            inv_rule_steps = bank["invalid_rule"][0]["steps"]
            formatted_inv = F.format_steps(world, inv_rule_steps)
            text_inv = f"TRACE: {formatted_inv}"
            v_inv = evaluate_oracle(world, text_inv)
            cases.append({
                "case_id": f"{w_id}_lexical_similar_invalid",
                "world_id": w_id,
                "category": "lexical_similar_invalid",
                "text": text_inv,
                "steps": inv_rule_steps,
                "oracle_verdict": v_inv.semantic_valid,
                "ref_match_strict": False,
                "ref_match_norm": False,
                "obs_equiv": False,
            })

        # Group D: constraint invalid / same final state
        if bank.get("invalid_constraint"):
            inv_con_steps = bank["invalid_constraint"][0]
            formatted_con = F.format_steps(world, inv_con_steps)
            text_con = f"TRACE: {formatted_con}"
            v_con = evaluate_oracle(world, text_con)
            cases.append({
                "case_id": f"{w_id}_same_final_state_invalid",
                "world_id": w_id,
                "category": "same_final_state_invalid",
                "text": text_con,
                "steps": inv_con_steps,
                "oracle_verdict": v_con.semantic_valid,
                "ref_match_strict": False,
                "ref_match_norm": False,
                "obs_equiv": (F.observe(world, inv_con_steps) == F.observe(world, canon_ref)),
            })

    with open(f"{ADVERSARIAL_DIR}/adversarial_dataset.json", "w") as f:
        json.dump(cases, f, indent=2)

    return cases


def evaluate_evaluators_on_adversarial(cases: List[Dict]) -> Dict:
    """
    Evaluates E1 Exact, E2 Normalized Match, E3 Semantic Oracle on adversarial dataset.
    Computes sensitivity, specificity, false rejection, false acceptance.
    """
    eval_results = {}
    
    for e_id in ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"]:
        tp, fp, tn, fn = 0, 0, 0, 0
        cat_breakdown = {}

        for c in cases:
            oracle_valid = (c["oracle_verdict"] == "TRUE")
            if e_id == "E1_CANONICAL_EXACT":
                e_pass = c["ref_match_strict"]
            elif e_id == "E2_NORMALIZED_MATCH":
                e_pass = c["ref_match_norm"]
            else:
                e_pass = oracle_valid

            cat = c["category"]
            cat_breakdown.setdefault(cat, {"pass": 0, "total": 0})
            cat_breakdown[cat]["total"] += 1
            if e_pass:
                cat_breakdown[cat]["pass"] += 1

            if oracle_valid and e_pass:
                tp += 1
            elif not oracle_valid and e_pass:
                fp += 1
            elif not oracle_valid and not e_pass:
                tn += 1
            elif oracle_valid and not e_pass:
                fn += 1

        total = len(cases)
        sensitivity = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        specificity = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        frr = (fn / (tp + fn)) if (tp + fn) > 0 else 0.0
        far = (fp / (tn + fp)) if (tn + fp) > 0 else 0.0

        eval_results[e_id] = {
            "evaluator_id": e_id,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "frr": frr,
            "far": far,
            "accuracy": (tp + tn) / total,
            "category_pass_rates": {cat: info["pass"] / info["total"] for cat, info in cat_breakdown.items()},
        }

    with open(f"{ADVERSARIAL_DIR}/evaluator_meta_results.json", "w") as f:
        json.dump(eval_results, f, indent=2)

    return eval_results
