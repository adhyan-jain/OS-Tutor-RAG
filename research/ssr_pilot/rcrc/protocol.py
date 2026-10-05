"""
Main RCR protocol script. Runs analysis on 1,152 existing generations across V(x).
"""

import argparse
import sys
from research.ssr_pilot.core.schema import ReferenceRegime
from research.ssr_pilot.rcrc.analysis import run_rcr_analysis


def main():
    parser = argparse.ArgumentParser(description="Run RCR Analysis on existing 1,152 generations.")
    parser.add_argument("--regime", type=str, default="FULL_REFERENCE_ENUMERATION",
                        choices=["ACTUAL_CANONICAL", "FULL_REFERENCE_ENUMERATION", "UNIFORM_REFERENCE_SAMPLE"])
    args = parser.parse_args()

    regime = ReferenceRegime[args.regime]
    print(f"[*] Starting Reference-Choice Robustness (RCR) Protocol under regime: {regime.value}")
    
    results = run_rcr_analysis(regime=regime)
    
    print("[+] RCR Analysis complete!")
    print(f"[+] Output written to research/ssr_pilot/results/rcrc/rcr_summary.json")
    
    # Print key findings summary
    for e_id, summary in results["evaluators"].items():
        print(f"\n--- Evaluator: {e_id} ---")
        print(f"Canonical Model Scores: {summary['canonical_model_scores']}")
        print(f"Canonical Ranking: {summary['canonical_model_ranking']}")
        print(f"Oracle Model Scores: {summary['oracle_model_scores']}")
        print(f"Oracle Ranking: {summary['oracle_model_ranking']}")
        print(f"Kendall Tau Mean: {summary['kendall_tau_mean']:.3f} ± {summary['kendall_tau_std']:.3f}")
        print(f"Pairwise Reversal Prob: {summary['pairwise_win_matrix']['pairwise_reversal_probability']:.4f}")
        print(f"Oracle Recovery Rate: {summary['oracle_recovery']['oracle_recovery_rate']:.4f}")


if __name__ == "__main__":
    main()
