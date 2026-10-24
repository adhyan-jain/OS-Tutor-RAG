# Novelty Positioning: Reference-Choice Robustness (RCR)

## Novelty & Differentiator Matrix

| Aspect | Prior Art (TRACE / OTAP / LogicGraph / Multi-ref) | Our Work (Reference-Choice Robustness) |
| :--- | :--- | :--- |
| **Problem Statement** | "Exact match fails when multiple references exist" | "Benchmark conclusions (rankings, significance, failure taxonomies) fluctuate as a function of arbitrary reference selection from valid space \(V(x)\)" |
| **Object of Perturbation** | Model outputs or prompt formulations | Reference identity itself chosen from complete valid space \(V(x)\) |
| **Ground Truth Baseline** | Reference trajectory heuristics | Independent reference-invariant executable semantic oracle |
| **Formal Space** | Heuristic candidate set | Complete valid-solution space \(V(x)\) formalizing state transition rules + task constraints |
| **Benchmark Identifiability** | Not measured | Formally defined and empirically evaluated via Kendall \(\tau\), winner reversal probability, and statistical decision stability |

## Positioning Statement (revised 2026-10-12)
> **This file is superseded by [`paper/NOVELTY_POSITIONING_FINAL.md`](../paper/NOVELTY_POSITIONING_FINAL.md).** The prior-art column above cited TRACE and a mis-identified OTAP/LogicGraph; those citations did not resolve to the stated works and have been corrected (see `paper/references_verified.csv`).

Reference-set variation is known to destabilize metric values and even system rankings (Casola et al., 2025; Jeong et al., 2026), and evaluators against sets of valid solutions exist (OTAP, LogicGraph). We therefore make **no "first" claim**. In multi-valued executable domains with exhaustively enumerable \(V(x)\), swapping the gold reference while holding tasks, outputs and evaluators fixed measurably degrades benchmark conclusions on the benchmark studied here—chiefly by hiding real differences (reference matching retains 12–18% of the true pairwise gaps) and by making near-tie orderings arbitrary. No claim is made that benchmarks are "non-identifiable" in general.
