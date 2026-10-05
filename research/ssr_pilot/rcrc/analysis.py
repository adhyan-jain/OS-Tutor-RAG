"""
Analysis runner and report builder for Reference-Choice Robustness (RCR).
Evaluates existing 1,152 generations from research/ssr_pilot/runs/ across all V(x) valid references.
"""

import glob
import json
import os
from typing import Dict, List, Tuple

import numpy as np

from research.ssr_pilot import render
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.core.evaluators import evaluate_with_reference
from research.ssr_pilot.core.oracle import evaluate_oracle, verify_oracle_reference_invariance
from research.ssr_pilot.core.provenance import capture_provenance
from research.ssr_pilot.core.references import get_references
from research.ssr_pilot.core.schema import EvaluatorVerdict, ReferenceRegime
from research.ssr_pilot.core.valid_space import build_all_valid_spaces
from research.ssr_pilot.rcrc.oracle_recovery import compute_oracle_recovery, diagnose_canonical_reference
from research.ssr_pilot.rcrc.ranking_metrics import (
    compute_kendall_tau,
    compute_model_scores,
    compute_pairwise_win_matrix,
    get_model_ranking,
)
from research.ssr_pilot.rcrc.significance_metrics import compute_significance_stability
from research.ssr_pilot.rcrc.taxonomy_metrics import compute_failure_taxonomy, compute_taxonomy_stability
from research.ssr_pilot.rcrc.trace_metrics import compute_reference_distribution, compute_trace_metrics
from research.ssr_pilot.worlds import load_worlds

RCRC_RESULTS_DIR = "research/ssr_pilot/results/rcrc"
RUNS_DIR = "research/ssr_pilot/runs"


def run_rcr_analysis(
    regime: ReferenceRegime = ReferenceRegime.FULL_REFERENCE_ENUMERATION,
    evaluator_ids: List[str] = None
) -> Dict:
    if evaluator_ids is None:
        evaluator_ids = ["E1_CANONICAL_EXACT", "E2_NORMALIZED_MATCH", "E3_SEMANTIC_ORACLE"]

    os.makedirs(RCRC_RESULTS_DIR, exist_ok=True)
    os.makedirs(f"{RCRC_RESULTS_DIR}/figures", exist_ok=True)

    # 1. Load worlds, valid spaces, banks, rendered variants
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    valid_spaces = build_all_valid_spaces(worlds_list)
    rendered = {(i, v): render.render_variant(w, v) for i, w in worlds.items() for v in render.VARIANTS}

    # Verify oracle reference invariance audit on all worlds
    for w in worlds_list:
        v_space = valid_spaces[w["id"]]
        test_sample_text = "TRACE: P1 0-24, P2 24-27, P3 27-30"
        inv_ok = verify_oracle_reference_invariance(w, test_sample_text, v_space.valid_solutions)
        assert inv_ok, f"Oracle failed reference invariance audit on world {w['id']}"

    # 2. Load 1,152 generations
    raw_records = []
    for path in sorted(glob.glob(f"{RUNS_DIR}/*.jsonl")):
        with open(path) as f:
            for line in f:
                if line.strip():
                    raw_records.append(json.loads(line))

    # 3. Evaluate each generation across reference choices
    # Structure: verdicts[evaluator_id][world_id][ref_idx] -> List[EvaluatorVerdict]
    verdicts_by_ref: Dict[str, Dict[str, Dict[int, List[EvaluatorVerdict]]]] = {
        e_id: {w_id: {} for w_id in worlds} for e_id in evaluator_ids
    }

    # Oracle verdicts (reference-independent)
    oracle_rankings_by_world = {}

    for rec in raw_records:
        w_id = rec["world"]
        world = worlds[w_id]
        v_space = valid_spaces[w_id]
        variant_info = rendered[(w_id, rec["variant"])]
        s2c = variant_info["s2c"]
        truncated = rec.get("done_reason") == "length"
        gen_id = rec["key"]
        model = rec["model"]
        variant = rec["variant"]
        seed = rec["seed"]
        raw_text = rec["response"]

        ref_list = get_references(v_space, regime)

        for ref_idx, ref_steps in ref_list:
            for e_id in evaluator_ids:
                v = evaluate_with_reference(
                    evaluator_id=e_id,
                    world=world,
                    raw_text=raw_text,
                    reference_steps=ref_steps,
                    generation_id=gen_id,
                    model=model,
                    variant=variant,
                    seed=seed,
                    reference_idx=ref_idx,
                    truncated=truncated,
                    shown2canon=s2c,
                )
                verdicts_by_ref[e_id][w_id].setdefault(ref_idx, []).append(v)

    # 4. Compute RCR summary metrics per evaluator
    evaluator_summaries = {}

    for e_id in evaluator_ids:
        # Collect global reference evaluations across all worlds
        # Map: ref_idx -> List[EvaluatorVerdict] (pooled across worlds where ref_idx exists)
        # Note: since worlds have different numbers of references, we analyze both pooled per-world and pooled global
        
        # Benchmark-level conclusions per reference selection index
        # To evaluate benchmark conclusion under reference regime choice, we draw a reference vector R = (r_1, ..., r_24) across 24 worlds
        # We sample 100 benchmark reference vectors from the cross-product of valid spaces
        
        rng_bench = np.random.RandomState(20261005)
        n_bench_samples = 100
        
        benchmark_scores_by_draw: Dict[int, Dict[str, float]] = {}
        benchmark_rankings_by_draw: Dict[int, List[str]] = {}
        benchmark_verdicts_by_draw_and_model: Dict[int, Dict[str, List[EvaluatorVerdict]]] = {}
        benchmark_taxonomies_by_draw: Dict[int, Dict[str, int]] = {}

        for draw_i in range(n_bench_samples):
            draw_verdicts: List[EvaluatorVerdict] = []
            draw_model_verdicts: Dict[str, List[EvaluatorVerdict]] = {}

            for w_id, w_space in valid_spaces.items():
                refs_available = list(verdicts_by_ref[e_id][w_id].keys())
                if draw_i == 0:
                    chosen_ref_idx = 0  # actual canonical reference
                else:
                    chosen_ref_idx = int(rng_bench.choice(refs_available))

                w_verdicts = verdicts_by_ref[e_id][w_id][chosen_ref_idx]
                draw_verdicts.extend(w_verdicts)
                for v in w_verdicts:
                    draw_model_verdicts.setdefault(v.model, []).append(v)

            scores = compute_model_scores(draw_verdicts)
            ranking = get_model_ranking(scores)
            taxonomy = compute_failure_taxonomy(draw_verdicts)

            benchmark_scores_by_draw[draw_i] = scores
            benchmark_rankings_by_draw[draw_i] = ranking
            benchmark_verdicts_by_draw_and_model[draw_i] = draw_model_verdicts
            benchmark_taxonomies_by_draw[draw_i] = taxonomy

        # Compute Oracle baseline ranking
        oracle_verdicts_pooled = verdicts_by_ref["E3_SEMANTIC_ORACLE"]["sched_01"][0]  # E3 is reference-invariant
        oracle_draw_verdicts = []
        for w_id in worlds:
            oracle_draw_verdicts.extend(verdicts_by_ref["E3_SEMANTIC_ORACLE"][w_id][0])
        oracle_scores = compute_model_scores(oracle_draw_verdicts)
        oracle_ranking = get_model_ranking(oracle_scores)

        # Pairwise matrix & reversal probability
        pairwise_summary = compute_pairwise_win_matrix(benchmark_scores_by_draw)

        # Kendall tau distribution against canonical ranking (draw 0)
        canonical_ranking = benchmark_rankings_by_draw[0]
        kendall_taus = [compute_kendall_tau(canonical_ranking, r) for r in benchmark_rankings_by_draw.values()]

        # Significance stability
        sig_summary = compute_significance_stability(benchmark_verdicts_by_draw_and_model)

        # Failure taxonomy stability
        tax_summary = compute_taxonomy_stability(benchmark_taxonomies_by_draw)

        # Oracle recovery
        rec_summary = compute_oracle_recovery(benchmark_rankings_by_draw, oracle_ranking)

        # Canonical reference diagnostic
        canon_diag = diagnose_canonical_reference(
            valid_solutions=valid_spaces["sched_01"].valid_solutions,
            canonical_reference=valid_spaces["sched_01"].canonical_reference,
            verdicts_by_ref=verdicts_by_ref[e_id]["sched_01"]
        )

        evaluator_summaries[e_id] = {
            "evaluator_id": e_id,
            "canonical_model_scores": benchmark_scores_by_draw[0],
            "canonical_model_ranking": canonical_ranking,
            "oracle_model_scores": oracle_scores,
            "oracle_model_ranking": oracle_ranking,
            "kendall_tau_mean": float(np.mean(kendall_taus)),
            "kendall_tau_std": float(np.std(kendall_taus)),
            "kendall_tau_min": float(np.min(kendall_taus)),
            "kendall_tau_max": float(np.max(kendall_taus)),
            "pairwise_win_matrix": pairwise_summary,
            "significance_stability": sig_summary,
            "taxonomy_stability": tax_summary,
            "oracle_recovery": rec_summary,
            "canonical_reference_diagnostic": canon_diag,
        }

    # Provenance
    prov = capture_provenance("rcr_core_analysis", {"n_generations": len(raw_records), "regime": regime.value})

    output_data = {
        "provenance": prov,
        "n_worlds": len(worlds),
        "n_generations": len(raw_records),
        "evaluators": evaluator_summaries,
    }

    # Save to JSON
    with open(f"{RCRC_RESULTS_DIR}/rcr_summary.json", "w") as f:
        json.dump(output_data, f, indent=2)

    return output_data
