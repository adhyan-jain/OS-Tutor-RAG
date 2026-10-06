"""
Analysis runner and report builder for Reference-Choice Robustness (RCR).
Evaluates existing 1,152 generations from research/ssr_pilot/runs/ across all V(x) valid references.
"""

import glob
import json
import os
import re
from typing import Dict, List, Tuple

import numpy as np

from research.ssr_pilot import render
from research.ssr_pilot import families as F
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
    # Pre-parsed evaluation loop (cached for 100x speedup across reference choices)
    formatted_refs_cache: Dict[str, Dict[int, str]] = {}
    norm_refs_cache: Dict[str, Dict[int, Tuple]] = {}
    obs_refs_cache: Dict[str, Dict[int, Tuple]] = {}

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

        oracle_verdict = evaluate_oracle(world, raw_text, truncated=truncated, shown2canon=s2c)
        parsed_steps, _ = F.parse(world, raw_text, s2c)
        
        if parsed_steps is None:
            norm_cand = None
            region_squashed = ""
            cand_obs = None
        else:
            norm_cand = F.normalize_schedule(parsed_steps) if world["family"] == "scheduling" else tuple(parsed_steps)
            region, _ = F._region(raw_text)
            region_squashed = re.sub(r"\s+", " ", region).strip()
            cand_obs = F.observe(world, parsed_steps)

        ref_list = get_references(v_space, regime)

        if w_id not in formatted_refs_cache:
            formatted_refs_cache[w_id] = {}
            norm_refs_cache[w_id] = {}
            obs_refs_cache[w_id] = {}
            for ref_idx, ref_steps in ref_list:
                norm_ref = F.normalize_schedule(ref_steps) if world["family"] == "scheduling" else tuple(ref_steps)
                formatted_ref = F.format_steps(world, ref_steps)
                norm_refs_cache[w_id][ref_idx] = norm_ref
                formatted_refs_cache[w_id][ref_idx] = re.sub(r"\s+", " ", formatted_ref).strip()
                obs_refs_cache[w_id][ref_idx] = F.observe(world, ref_steps)

        for ref_idx, ref_steps in ref_list:
            norm_ref = norm_refs_cache[w_id][ref_idx]
            formatted_ref_squashed = formatted_refs_cache[w_id][ref_idx]
            ref_obs = obs_refs_cache[w_id][ref_idx]
            
            ref_match_norm = (norm_cand == norm_ref) if norm_cand is not None else False
            ref_match_strict = (region_squashed == formatted_ref_squashed) if norm_cand is not None else False
            obs_equiv = (cand_obs == ref_obs) if cand_obs is not None else False

            for e_id in evaluator_ids:
                if e_id == "E1_CANONICAL_EXACT":
                    eval_pass = ref_match_strict
                elif e_id == "E2_NORMALIZED_MATCH":
                    eval_pass = ref_match_norm
                elif e_id == "E3_SEMANTIC_ORACLE":
                    eval_pass = (oracle_verdict.semantic_valid == "TRUE")
                else:
                    eval_pass = obs_equiv
                
                v = EvaluatorVerdict(
                    evaluator_id=e_id,
                    world_id=w_id,
                    generation_id=gen_id,
                    model=model,
                    variant=variant,
                    seed=seed,
                    reference_idx=ref_idx,
                    reference_steps=ref_steps,
                    semantic_valid=oracle_verdict.semantic_valid,
                    ref_match_norm=ref_match_norm,
                    ref_match_strict=ref_match_strict,
                    obs_equiv=obs_equiv,
                    evaluator_pass=eval_pass,
                    reason=oracle_verdict.reason,
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
        n_bench_samples = 50000
        
        # Draw 0: Canonical reference vector (r_idx = 0 for all worlds)
        canonical_verdicts: List[EvaluatorVerdict] = []
        canonical_verdicts_by_model: Dict[str, List[EvaluatorVerdict]] = {}
        for w_id in worlds:
            w_verdicts = verdicts_by_ref[e_id][w_id][0]
            canonical_verdicts.extend(w_verdicts)
            for v in w_verdicts:
                canonical_verdicts_by_model.setdefault(v.model, []).append(v)
        canonical_scores = compute_model_scores(canonical_verdicts)
        canonical_ranking = get_model_ranking(canonical_scores)

        # Draws 1..50,000: Independent uniform draws from Cartesian product \prod_{k=1}^{24} V(x_k)
        benchmark_scores_by_draw: Dict[int, Dict[str, float]] = {0: canonical_scores}
        random_scores_by_draw: Dict[int, Dict[str, float]] = {}
        benchmark_rankings_by_draw: Dict[int, List[str]] = {0: canonical_ranking}
        benchmark_verdicts_by_draw_and_model: Dict[int, Dict[str, List[EvaluatorVerdict]]] = {0: canonical_verdicts_by_model}
        benchmark_taxonomies_by_draw: Dict[int, Dict[str, int]] = {0: compute_failure_taxonomy(canonical_verdicts)}

        # Pre-extract model scores per (world_id, ref_idx) for high-performance Monte Carlo sampling
        # world_ref_model_scores[w_id][ref_idx][model] -> float
        world_ref_model_scores: Dict[str, Dict[int, Dict[str, float]]] = {}
        for w_id in worlds:
            world_ref_model_scores[w_id] = {}
            for ref_idx, w_verdicts in verdicts_by_ref[e_id][w_id].items():
                m_scores = {}
                for m in set(v.model for v in w_verdicts):
                    m_passes = [v.evaluator_pass for v in w_verdicts if v.model == m]
                    m_scores[m] = float(np.mean(m_passes))
                world_ref_model_scores[w_id][ref_idx] = m_scores

        models_list = sorted(list(canonical_scores.keys()))
        random_ref_vectors: List[Dict[str, int]] = []

        for draw_i in range(1, n_bench_samples + 1):
            # Sample independent uniform reference index per world
            draw_scores = {m: 0.0 for m in models_list}
            ref_vec = {}
            for w_id, w_space in valid_spaces.items():
                refs_available = list(verdicts_by_ref[e_id][w_id].keys())
                chosen_ref_idx = int(rng_bench.choice(refs_available))
                ref_vec[w_id] = chosen_ref_idx
                w_m_scores = world_ref_model_scores[w_id][chosen_ref_idx]
                for m in models_list:
                    draw_scores[m] += w_m_scores[m]
            
            # Mean across 24 worlds
            draw_scores = {m: draw_scores[m] / len(worlds) for m in models_list}
            draw_ranking = get_model_ranking(draw_scores)
            
            random_ref_vectors.append(ref_vec)
            benchmark_scores_by_draw[draw_i] = draw_scores
            random_scores_by_draw[draw_i] = draw_scores
            benchmark_rankings_by_draw[draw_i] = draw_ranking

        # Compute Oracle baseline ranking (reference-invariant)
        oracle_draw_verdicts = []
        for w_id in worlds:
            oracle_draw_verdicts.extend(verdicts_by_ref["E3_SEMANTIC_ORACLE"][w_id][0])
        oracle_scores = compute_model_scores(oracle_draw_verdicts)
        oracle_ranking = get_model_ranking(oracle_scores)

        # Pairwise win matrix & reversal probability on random uniform reference distribution (draws 1..50,000)
        pairwise_summary = compute_pairwise_win_matrix(random_scores_by_draw)

        # Tie-aware Kendall tau-b distribution of random references against canonical reference
        # NaN draws (one-constant degenerate vectors) are tracked separately and excluded from
        # aggregate statistics per the predeclared degenerate handling policy (deviation D4).
        from research.ssr_pilot.rcrc.ranking_metrics import compute_kendall_tau_scores, rankings_are_identical_tie_aware
        kendall_taus_raw = [compute_kendall_tau_scores(canonical_scores, r_scores) for r_scores in random_scores_by_draw.values()]
        n_degen_taus = int(sum(1 for t in kendall_taus_raw if np.isnan(t)))
        kendall_taus = [t for t in kendall_taus_raw if not np.isnan(t)]
        n_valid_taus = len(kendall_taus)
        kendall_tau_mean = float(np.mean(kendall_taus)) if kendall_taus else float('nan')
        kendall_tau_std = float(np.std(kendall_taus)) if kendall_taus else float('nan')
        kendall_tau_se = float(kendall_tau_std / np.sqrt(n_valid_taus)) if n_valid_taus > 0 else float('nan')

        # Significance stability over representative uniform reference draws (subsample 200 draws for 20k sign-flip tests)
        from research.ssr_pilot.rcrc.significance_metrics import compute_significance_stability_fast
        sig_sample_indices = rng_bench.choice(len(random_ref_vectors), size=min(200, n_bench_samples), replace=False)
        sig_vectors_subset = [random_ref_vectors[i] for i in sig_sample_indices]
        sig_summary = compute_significance_stability_fast(world_ref_model_scores, sig_vectors_subset, alpha=0.05, n_flips=20000, seed=20261005)

        # Failure taxonomy stability (draw 0 canonical)
        tax_summary = compute_taxonomy_stability(benchmark_taxonomies_by_draw)


        # Oracle recovery rate on random uniform references.
        # Uses tie-aware ranking identity (not tau==1.0) to correctly handle tied oracle scores.
        oracle_matches = sum(1 for r_scores in random_scores_by_draw.values() if rankings_are_identical_tie_aware(oracle_scores, r_scores))
        oracle_rec_rate = float(oracle_matches / len(random_scores_by_draw))
        rec_summary = {
            "n_references": len(random_scores_by_draw),
            "oracle_ranking": oracle_ranking,
            "oracle_recovery_rate": oracle_rec_rate,
            "rankings_matching_oracle": oracle_matches,
        }

        # Canonical reference diagnostic
        canon_diag = diagnose_canonical_reference(
            valid_solutions=valid_spaces["sched_01"].valid_solutions,
            canonical_reference=valid_spaces["sched_01"].canonical_reference,
            verdicts_by_ref=verdicts_by_ref[e_id]["sched_01"]
        )

        evaluator_summaries[e_id] = {
            "evaluator_id": e_id,
            "canonical_model_scores": canonical_scores,
            "canonical_model_ranking": canonical_ranking,
            "oracle_model_scores": oracle_scores,
            "oracle_model_ranking": oracle_ranking,
            "n_monte_carlo_draws": n_bench_samples,
            "kendall_tau_mean": kendall_tau_mean,
            "kendall_tau_std": kendall_tau_std,
            "kendall_tau_se": kendall_tau_se,
            "kendall_tau_min": float(np.min(kendall_taus)) if kendall_taus else float('nan'),
            "kendall_tau_max": float(np.max(kendall_taus)) if kendall_taus else float('nan'),
            "kendall_tau_n_valid_draws": n_valid_taus,
            "kendall_tau_n_degenerate_draws": n_degen_taus,
            "pairwise_win_matrix": pairwise_summary,
            "significance_stability": sig_summary,
            "significance_n_sampled_draws": len(sig_vectors_subset),
            "taxonomy_stability": tax_summary,
            "oracle_recovery": rec_summary,
            "canonical_reference_diagnostic": canon_diag,
        }

    # Provenance
    input_jsonl_paths = sorted(glob.glob(f"{RUNS_DIR}/*.jsonl"))
    prov = capture_provenance(
        "rcr_core_analysis",
        extra_meta={"n_generations": len(raw_records), "regime": regime.value, "n_draws": n_bench_samples,
                    "n_worlds": len(worlds), "rng_seed": 20261005, "n_sign_flip_subsample": 200,
                    "sign_flip_seed": 20261005},
        input_files=input_jsonl_paths
    )

    output_data = {
        "provenance": prov,
        "n_worlds": len(worlds),
        "n_generations": len(raw_records),
        "n_monte_carlo_draws": 50000,
        "evaluators": evaluator_summaries,
    }

    # Save to JSON
    with open(f"{RCRC_RESULTS_DIR}/rcr_summary.json", "w") as f:
        json.dump(output_data, f, indent=2)

    return output_data

