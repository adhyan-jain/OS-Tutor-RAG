# Novelty Positioning: Reference-Choice Robustness (RCR)

## Novelty & Differentiator Matrix

| Aspect | Prior Art (TRACE / OTAP / LogicGraph / Multi-ref) | Our Work (Reference-Choice Robustness) |
| :--- | :--- | :--- |
| **Problem Statement** | "Exact match fails when multiple references exist" | "Benchmark conclusions (rankings, significance, failure taxonomies) fluctuate as a function of arbitrary reference selection from valid space \(V(x)\)" |
| **Object of Perturbation** | Model outputs or prompt formulations | Reference identity itself chosen from complete valid space \(V(x)\) |
| **Ground Truth Baseline** | Reference trajectory heuristics | Independent reference-invariant executable semantic oracle |
| **Formal Space** | Heuristic candidate set | Complete valid-solution space \(V(x)\) formalizing state transition rules + task constraints |
| **Benchmark Identifiability** | Not measured | Formally defined and empirically evaluated via Kendall \(\tau\), winner reversal probability, and statistical decision stability |

## Positioning Statement
While prior work has noted that reference matching degrades when multiple valid trajectories exist, our work is the first to prove that **executable benchmarks become non-identifiable** when evaluated against arbitrary gold references: changing only the reference choice within the valid space \(V(x)\) alters pairwise model rankings, flips statistical significance decisions, and distorts model competence estimates.
