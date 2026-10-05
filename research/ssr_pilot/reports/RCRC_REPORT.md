# Reference-Choice Robustness (RCR) Primary Experimental Report

## Executive Summary

This report documents the empirical evaluation of **Reference-Choice Robustness (RCR)** on 1,152 model generations across 24 executable operating system reasoning tasks (Scheduling, Synchronization Interleaving, and Banker's Safety).

### Primary Finding
When evaluating reasoning model outputs against a gold reference trajectory selected from the set of valid solutions \(V(x)\), **changing only the chosen valid reference** while keeping tasks, model outputs, and evaluators fixed alters key scientific conclusions:
- **Ranking Instability**: Model rank order fluctuates significantly under normalized matching (\(\text{Kendall } \tau = 0.463 \pm 0.343\)).
- **Pairwise Winner Reversals**: Up to **18.45%** of valid reference pairs flip the relative model ordering.
- **Statistical Significance Flips**: For key model comparisons (e.g., `qwen3:8b` vs `gemma2:9b`), **50% of valid references yield a statistically significant difference (\(p < 0.05\))** while **50% yield a non-significant result (\(p \ge 0.05\))**.
- **Oracle Recovery Failure**: Canonical exact matching recovers the true reference-invariant semantic oracle ranking only **4.0%** of the time, and normalized matching recovers it only **28.0%** of the time.

Conversely, the reference-independent executable semantic oracle (\(E_3\)) achieves **100% decision stability** (\(\text{Kendall } \tau = 1.000\), 0% reversals, 100% oracle recovery).

---

## Experimental Setup

- **Task Set**: 24 formal OS tasks across 3 domain families (8 Scheduling, 8 Synchronization, 8 Banker's Algorithm).
- **Valid Solution Space \(V(x)\)**: Complete set of executable solutions satisfying all world transition rules and task constraints (ranging from 2 to 192 valid solutions per task).
- **Evaluated Models**: `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b`.
- **Generations**: 1,152 raw text generations (24 worlds × 3 prompt variants × 4 seeds × 4 models).
- **Evaluators**:
  - \(E_1\) **Canonical Exact Match**: Strict string comparison against selected reference \(R \in V(x)\).
  - \(E_2\) **Normalized Match**: Normalized schedule/event trajectory comparison against selected reference \(R \in V(x)\).
  - \(E_3\) **Executable Semantic Oracle**: Reference-invariant replay & constraint checker.

---

## Key Results Table

| Evaluator | Canonical Pass Rate (`qwen3:8b`) | Kendall \(\tau\) Stability | Pairwise Reversal Prob | Statistical Decision Flips (\(p < 0.05 \leftrightarrow \text{n.s.}\)) | Oracle Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Canonical Exact** | 4.86% | 0.820 ± 0.396 | 5.39% | 44% - 50% | **4.0%** |
| **\(E_2\) Normalized Match** | 13.19% | 0.463 ± 0.343 | **18.45%** | **50.0%** | **28.0%** |
| **\(E_3\) Semantic Oracle** | 30.90% | **1.000 ± 0.000** | **0.00%** | **0.0%** | **100.0%** |

---

## Detailed Scientific Insights

1. **Exact & Normalized Matching Underestimate True Model Competence**:
   - `qwen3:8b` achieves a 30.90% semantic validity score under the executable oracle, but only 4.86% under exact matching and 13.19% under normalized matching against the canonical reference.
   - The discrepancy is caused by valid trajectory divergence: the model produces valid solutions within \(V(x)\) that differ from the single arbitrary canonical trajectory chosen by the benchmark creator.

2. **Benchmark Identifiability Crisis**:
   - Standard reference-matching evaluators create non-identifiable benchmarks: whether Model A outperforms Model B or whether the difference is statistically significant depends heavily on which valid solution was picked as gold.

3. **Recommendation**:
   - **GREENLIGHT**: Proceed to paper draft and publication preparation. Executable reasoning benchmarks must replace arbitrary gold references with reference-invariant executable semantic oracles.
