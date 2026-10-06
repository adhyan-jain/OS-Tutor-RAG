# Final Audited Statistics & Evidence Matrix

This document presents the re-audited, verified statistical metrics for all baseline and stronger-model evaluations.

---

## 1. Primary Benchmark Identifiability Metrics (Baseline 1,152 Generations)

- **Experimental Unit**: World/Task (24 tasks: 8 Scheduling, 8 Synchronization, 8 Banker's Algorithm).
- **Bootstrap Method**: World-clustered bootstrap with 2,000 resamples (seed 0).
- **Evaluated Baseline Models**: `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b` (288 generations per model).

### Audited Metrics Table (50,000 Monte Carlo Draws)
| Evaluator | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b-instruct` Score | `llama3.1:8b` Score | Kendall \(\tau_b\) (Mean ± Std) | Pairwise Reversal Prob | Oracle Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Exact Match** | 4.86% (14/288) | 0.69% (2/288) | 0.00% (0/288) | 0.00% (0/288) | 0.769 ± 0.301 | 4.66% | **2.86%** (1,430/50,000) |
| **\(E_2\) Normalized Match** | 13.19% (38/288) | 2.43% (7/288) | 3.47% (10/288) | 0.35% (1/288) | 0.490 ± 0.355 (n=49,914)† | **18.61%** | **23.92%** (11,960/50,000) |
| **\(E_3\) Semantic Oracle** | 30.90% (89/288) | 17.01% (49/288) | 7.64% (22/288) | 6.60% (19/288) | **1.000 ± 0.000** | **0.00%** | **100.0%** (50,000/50,000) |

†86 draws (0.17%) excluded per predeclared degenerate-handling policy (one model with a constant score vector).

---

## 2. Statistical Significance Inference (World-Level Permutation)

Preregistered world-level paired sign-flip permutation tests (20,000 sign flips) with Holm-Bonferroni step-down correction across all 6 model pairs evaluated over 200 sampled reference draws:

1. **World-Level Variance**: Across 100% of the 200 sampled reference conditions, no model pair achieves statistical significance at \(\alpha = 0.05\) after Holm correction. World-level variance dominates pairwise model differences on this 24-world benchmark.
2. **Oracle Stability under \(E_3\)**: Under the reference-independent executable semantic validator \(E_3\), rankings are 100% invariant (\(\tau_b = 1.000 \pm 0.000\)) and pairwise winner reversal probability is strictly 0.00%.

---

## 3. Stronger-Model Competence Audit (576 Generations)

- **Completed Runs**: `gemma3:12b` (288 calls) and `olmo2:7b` (288 calls).
- **Semantically Valid Outputs**: \(n = 48\).
- **Pooled False Rejection Rate (\(\text{FRR}_{\text{norm}}\))**: **0.667** (66.7%), 95% CI: [0.500, 0.867].
- **Drop vs Baseline FRR (0.625)**: \(-0.042\) (False rejection remains high at 66.7% under stronger models).

---

## 4. Adversarial Meta-Evaluation Audit (79 Controlled Cases)

- **\(E_1\) Exact Match**: Sensitivity = 50.0%, Specificity = 100.0%, FRR = 50.0%, Noncanonical Pass Rate = **0.0%**.
- **\(E_2\) Normalized Match**: Sensitivity = 50.0%, Specificity = 100.0%, FRR = 50.0%, Noncanonical Pass Rate = **0.0%**.
- **\(E_3\) Semantic Oracle**: Sensitivity = 100.0%, Specificity = 100.0%, FRR = 0.0%, Noncanonical Pass Rate = **100.0%**.
- **Tautology Note**: \(E_3\)'s 100% accuracy on adversarial cases is tautological relative to the domain specification because \(E_3\) defines valid execution; the critical empirical finding is that \(E_1\) and \(E_2\) reject 100% of noncanonical valid trajectories.
