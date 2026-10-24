"""
Generate the extended-analysis tables (Tables 3-6) for the manuscript from
research/ssr_pilot/results/rcrc/extended_analysis.json.

Usage: python paper/build_tables.py
Writes paper/TABLES/table3_*.md ... table6_*.md and prints them.
"""

import json

SRC = "research/ssr_pilot/results/rcrc/extended_analysis.json"
SHORT = {"gemma2:9b": "gemma2", "llama3.1:8b": "llama3.1", "mistral:7b-instruct": "mistral", "qwen3:8b": "qwen3"}


def pair_label(name: str) -> str:
    a, b = name.split("_vs_")
    return f"{SHORT[a]} vs {SHORT[b]}"


def pct(x, nd=1):
    return "n/a" if x is None else f"{100 * x:.{nd}f}%"


def main():
    d = json.load(open(SRC))
    out = {}

    # Table 3: significance (all 50,000 draws) and detection
    rows = ["| Model pair | Oracle (E3) Holm-adj. p | Oracle decision | E1 mean adj. p | E1 misses | E2 mean adj. p | E2 misses |",
            "|:---|:---:|:---:|:---:|:---:|:---:|:---:|"]
    for p in d["pairs"]:
        s3 = d["significance_all_draws"]["E3_SEMANTIC_ORACLE"][p]
        s1 = d["significance_all_draws"]["E1_CANONICAL_EXACT"][p]
        s2 = d["significance_all_draws"]["E2_NORMALIZED_MATCH"][p]
        dec = d["detection_vs_oracle"]["E3_SEMANTIC_ORACLE"][p]["oracle_decision"]
        sep = dec != "NON_SIGNIFICANT"
        m1 = d["detection_vs_oracle"]["E1_CANONICAL_EXACT"][p]["miss_true_difference"]
        m2 = d["detection_vs_oracle"]["E2_NORMALIZED_MATCH"][p]["miss_true_difference"]
        rows.append(
            f"| {pair_label(p)} | {s3['mean_adj_p']:.4f} | {'qwen3 better' if sep else 'n.s.'} | "
            f"{s1['mean_adj_p']:.3f} | {pct(m1, 2) if sep else '-'} | {s2['mean_adj_p']:.3f} | {pct(m2, 2) if sep else '-'} |"
        )
    out["table3_significance_detection.md"] = "\n".join(rows)

    # Table 4: evaluator effect on gap
    rows = ["| Model pair | Oracle gap | E2 expected gap (uniform ref.) | Evaluator effect [95% world-bootstrap CI] | Gap retained by E2 |",
            "|:---|:---:|:---:|:---:|:---:|"]
    for p in d["pairs"]:
        x = d["evaluator_effect_on_gap"]["E2_NORMALIZED_MATCH"][p]
        kept = x["expected_matching_gap_uniform_reference"] / x["oracle_gap"]
        rows.append(
            f"| {pair_label(p)} | {x['oracle_gap']:+.3f} | {x['expected_matching_gap_uniform_reference']:+.3f} | "
            f"{x['evaluator_effect_on_gap']:+.3f} [{x['ci95_low']:+.3f}, {x['ci95_high']:+.3f}]"
            f"{'' if x['ci_excludes_zero'] else ' (spans 0)'} | {pct(kept, 0)} |"
        )
    out["table4_evaluator_effect.md"] = "\n".join(rows)

    # Table 5: near-tie decomposition (E2)
    rows = ["| Model pair | Separated by E3? | E3 Holm-adj. p | E2 reversal prob. | E2 score tie prob. | E2 winner opposes E3 |",
            "|:---|:---:|:---:|:---:|:---:|:---:|"]
    nt = d["near_tie_decomposition"]["E2_NORMALIZED_MATCH"]
    for p, x in nt["pairs"].items():
        rows.append(
            f"| {pair_label(p)} | {'yes' if x['oracle_separated'] else 'no'} | {x['oracle_adj_p']:.4f} | "
            f"{pct(x['reversal_probability'])} | {pct(x['p_tied_score'])} | {pct(x['p_winner_opposes_oracle_gap'])} |"
        )
    rows.append(f"| **Mean, not separated (4 pairs)** | | | **{pct(nt['mean_reversal_nonseparated_pairs'])}** | | |")
    rows.append(f"| **Mean, separated (2 pairs)** | | | **{pct(nt['mean_reversal_separated_pairs'])}** | | |")
    rows.append(f"| **Share of reversal mass in non-separated pairs** | | | **{pct(nt['reversal_mass_share_in_oracle_nonseparated_pairs'])}** | | |")
    out["table5_near_tie.md"] = "\n".join(rows)

    # Table 6: by mechanism family
    rows = ["| Mechanism family | Worlds | E1 reversal | E2 reversal | E2 Kendall tau_b (valid draws) | E3 scores (gemma2 / llama3.1 / mistral / qwen3) |",
            "|:---|:---:|:---:|:---:|:---:|:---|"]
    for fam in ["scheduling", "sync", "banker"]:
        f = d["by_family"][fam]
        e2 = f["E2_NORMALIZED_MATCH"]
        s3 = f["E3_SEMANTIC_ORACLE"]["mean_score_by_model"]
        tau = "undefined" if e2["kendall_tau_b_mean"] is None else f"{e2['kendall_tau_b_mean']:.3f} (n={e2['kendall_tau_b_n_valid']:,})"
        rows.append(
            f"| {fam} | {f['n_worlds']} | {pct(f['E1_CANONICAL_EXACT']['pairwise_reversal_probability'])} | "
            f"{pct(e2['pairwise_reversal_probability'])} | {tau} | "
            + " / ".join(f"{s3[m]:.3f}" for m in d["models"]) + " |"
        )
    out["table6_by_family.md"] = "\n".join(rows)

    # Table 7: k-reference evaluation (match-any); separate artifact
    kd = json.load(open("research/ssr_pilot/results/rcrc/kref_attenuation.json"))
    rows = [r"| \(k\) | Detect qwen3 > llama3.1 | Detect qwen3 > mistral | Gap retained (llama / mistral) | False positive, any non-separated pair | Full-ordering recovery |",
            "|:---:|:---:|:---:|:---:|:---:|:---:|"]
    for key, v in kd["k_reference"].items():
        det = list(v["detect_oracle_separated_pairs"].values())
        gap = list(v["mean_gap_retained_separated_pairs"].values())
        label = r"all (\(E_3\))" if key == "all" else key
        rows.append(
            f"| {label} | {pct(det[0])} | {pct(det[1])} | {100 * gap[0]:.0f}% / {100 * gap[1]:.0f}% | "
            f"{pct(v['false_positive_any_nonseparated_pair'])} | {pct(v['oracle_ordering_recovery'])} |"
        )
    out["table7_kref.md"] = "\n".join(rows)

    for name, text in out.items():
        with open(f"paper/TABLES/{name}", "w") as fh:
            fh.write(text + "\n")
        print(f"### {name}\n{text}\n")


if __name__ == "__main__":
    main()
