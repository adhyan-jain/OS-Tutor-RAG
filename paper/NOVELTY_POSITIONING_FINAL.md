# Novelty Positioning & Prior Art Comparative Audit

## 1. Differentiator Matrix

| Scientific Metric / Dimension | Prior Reference-Free Evaluation (TRACE, OTAP, LogicGraph) | Multi-Reference Code Evaluation (CodeBLEU, Multi-Ref Pass@k) | Reference-Choice Robustness (Our Work) |
| :--- | :--- | :--- | :--- |
| **Primary Variable** | Output correctness without reference | Test-case execution coverage | **Identity of valid reference trajectory \(R \in V(x)\)** |
| **Formal Solution Space** | Heuristic candidate set | Program execution space | **Complete formal valid-solution space \(V(x)\)** |
| **Benchmark Identifiability** | Not evaluated | Not evaluated | **Quantified via Kendall \(\tau\), winner reversals, and significance flips** |
| **Decision Stability** | Evaluated per output | Evaluated per code sample | **Evaluated at benchmark conclusion level (\(P(\text{Reversal})\), \(RCR(E)\))** |

---

## 2. Positioning Relative to Key Prior Work

1. **TRACE / OTAP / LogicGraph**:
   - *What They Do*: Develop trajectory-level or graph-level reference-free evaluation metrics for agent steps.
   - *What We Add*: We do not merely propose a new metric; we formalize reference selection as an experimental variable and measure benchmark non-identifiability induced by reference choice across complete formal spaces \(V(x)\).

2. **Multi-Reference Code Evaluation**:
   - *What They Do*: Demonstrate that single-reference exact match penalizes correct code alternatives.
   - *What We Add*: We extend from trajectory scoring to benchmark-level conclusion stability, proving that reference choice flips statistical hypothesis decisions ($p < 0.05 \leftrightarrow \text{n.s.}$) and model rankings.

3. **LLM-as-a-Judge Robustness**:
   - *What They Do*: Analyze prompt sensitivity and position bias in LLM evaluators.
   - *What We Add*: We study deterministic reference-matching evaluators over formal executable state spaces.
