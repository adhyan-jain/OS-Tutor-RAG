# Final Audited Statistics & Evidence Matrix

This document presents the re-audited, verified statistical metrics for all baseline and stronger-model evaluations.

---

## 1. Primary Benchmark Identifiability Metrics (Baseline 1,152 Generations)

- **Experimental Unit**: World/Task (24 tasks: 8 Scheduling, 8 Synchronization, 8 Banker's Algorithm).
- **Bootstrap Method**: World-clustered bootstrap with 2,000 resamples (seed 0).
- **Evaluated Baseline Models**: `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b` (288 generations per model).

### Audited Metrics Table
| Evaluator | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b-instruct` Score | `llama3.1:8b` Score | Kendall \(\tau\) Stability | Pairwise Reversal Prob | Oracle Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Exact Match** | 4.86% (14/288) | 0.69% (2/288) | 0.00% (0/288) | 0.00% (0/288) | 0.820 ± 0.396 | 5.39% | **4.0%** (4/100) |
| **\(E_2\) Normalized Match** | 13.19% (38/288) | 2.43% (7/288) | 3.47% (10/288) | 0.35% (1/288) | 0.463 ± 0.343 | **18.45%** | **28.0%** (28/100) |
| **\(E_3\) Semantic Oracle** | 30.90% (89/288) | 17.01% (49/288) | 7.64% (22/288) | 6.60% (19/288) | **1.000 ± 0.000** | **0.00%** | **100.0%** (100/100) |

---

## 2. Statistical Significance Flips (\(\alpha = 0.05\))

Paired McNemar / Binomial significance tests across 100 reference vector draws \(\mathbf{R} \sim \mathcal{U}(V(x))\):

1. **`gemma2:9b` vs `qwen3:8b` under \(E_2\)**:
   - Significant (\(p < 0.05\)): **50.0%** ("SIGNIFICANT_B_WINS")
   - Non-Significant (\(p \ge 0.05\)): **50.0%** ("NON_SIGNIFICANT")
   - Mean \(p\)-value: \(0.1737 \pm 0.2861\) (Range: [0.00003, 1.0])

2. **`llama3.1:8b` vs `qwen3:8b` under \(E_2\)**:
   - Significant (\(p < 0.05\)): **50.0%** ("SIGNIFICANT_B_WINS")
   - Non-Significant (\(p \ge 0.05\)): **50.0%** ("NON_SIGNIFICANT")
   - Mean \(p\)-value: \(0.1684 \pm 0.2849\) (Range: [0.0001, 1.0])

3. **Under \(E_3\) Semantic Oracle**:
   - `gemma2:9b` vs `qwen3:8b`: **100.0% Significant** (\(p = 0.0001\)), 0% Flips.

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
