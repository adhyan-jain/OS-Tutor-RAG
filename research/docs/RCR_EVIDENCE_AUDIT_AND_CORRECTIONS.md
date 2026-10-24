# RCR Evidence Audit and Forensic Corrections

**Repository:** OS-Tutor-RAG / Reference-Choice Robustness (RCR)  
**Date:** October 2026  
**Document Status:** Definitive Audit and Reconciliation of Evidence Gaps  
**Governing Rule:** Zero-trust verification against raw JSONL and JSON artifacts; historical evidence strictly preserved.

---

## 1. Executive Summary

This document independently audits, traces, and reconciles the five evidence inconsistencies identified in the prior audit:
1. **Total Variation (TV) Robustness Certificate**: Resolves the conflation between a sufficient condition and the true property of expected-margin sign invariance, providing a verified counterexample and empirical validation.
2. **Reconciliation of Reversal Figures**: Explains the exact mathematical and operational provenance of the 18.61% historical figure, the 17.56% corrected Monte Carlo figure, the 17.23% sensitivity baseline, the 17.18% extended analysis figure, and the 17.1518% exact dynamic programming (DP) parameter. Reports mean signed error, MAE, and max AE.
3. **Detection Loss Audit**: Traces the "99.99%" claim to its exact denominator (50,000 full-benchmark Monte Carlo draws), correcting the statistical interpretation to power loss rather than equivalence.
4. **Attenuation Law Audit**: Rigorously separates the task-level identity from the benchmark-level aggregate expectation, showing the inverse cardinality weighting $\frac{1}{|V_i|}$ and reconciling the 12–18% retention figures across all model pairs.
5. **Code & Test Suite Verification**: Documents automated test execution, failure modes, and deterministic script verification.

---

## 2. Evidence Gap A: TV Robustness Certificate Audit

### 2.1 The Mathematical Distinction
Let $\mu_{AB}(q) = \frac{1}{N} \sum_{i=1}^N \mathbb{E}_{q_i}[D_i]$ denote the expected pairwise score margin between models $A$ and $B$ under product reference distribution $q = \prod_{i=1}^N q_i$.  
For a baseline distribution $q^0$ (e.g., uniform over $V_i$) and any perturbed distribution $q$, the Lipschitz bound on expected margin change under total variation distance is:
$$|\mu_{AB}(q) - \mu_{AB}(q^0)| \le \frac{2}{N} \sum_{i=1}^N \mathrm{TV}(q_i, q_i^0)$$

A **sufficient condition** for the sign of $\mu_{AB}(q)$ to remain strictly invariant ($\mathrm{sign}(\mu_{AB}(q)) = \mathrm{sign}(\mu_{AB}(q^0))$) over all distributions within TV budget $\sum_i \mathrm{TV}(q_i, q_i^0) \le B_{\mathrm{TV}}$ is:
$$|\mu_{AB}(q^0)| > \frac{2}{N} B_{\mathrm{TV}}$$

### 2.2 Forensic Correction: Certificate Failure $\neq$ Margin Instability
- **The Error in Prior Interpretations:** Previous summaries treated failure to certify as evidence that the expected margin flips sign under distribution shift.
- **The Mathematical Reality:** The condition is **sufficient, not necessary**. When $|\mu_{AB}(q^0)| \le \frac{2}{N} B_{\mathrm{TV}}$, the triangle inequality cannot guarantee sign invariance. However, the actual expected margin $\mu_{AB}(q)$ may remain strictly bounded away from zero across 100% of the probability simplex.

### 2.3 Verified Hand-Checkable Counterexample
Consider $N=1$ task with valid reference set $V_1 = \{r_1, r_2\}$. Suppose Model A outperforms Model B on *both* valid references:
$$D_1(r_1) = +0.5, \quad D_1(r_2) = +0.4$$
Under *any* arbitrary probability distribution $q = (p, 1-p) \in \Delta(V_1)$ with $p \in [0, 1]$:
$$\mathbb{E}_q[D_1] = 0.5 p + 0.4(1 - p) = 0.4 + 0.1 p \in [+0.4, +0.5]$$
The expected margin is strictly positive under **100% of all possible distributions** on $V_1$. Its sign is unconditionally invariant.

Now apply the TV certificate with uniform baseline $q^0 = (0.5, 0.5)$ and a perturbation budget $B_{\mathrm{TV}} = 0.30$:
- Baseline expected margin: $\mu(q^0) = 0.5(0.5) + 0.5(0.4) = +0.45$.
- Lipschitz TV bound: $\text{Bound} = 2 \cdot B_{\mathrm{TV}} = 2 \times 0.30 = 0.60$.
- Test condition: $|\mu(q^0)| = 0.45 \le 0.60 = \text{Bound}$.
- **Result:** The certificate **fails** (reports uncertified).  
Yet the true margin sign never flips. The failure is entirely an artifact of the conservative Lipschitz constant $L=2$, which assumes probability mass is moved adversarially to an extreme value of $-1.0$.

### 2.4 Empirical Audit on the 24-World Dataset
- In `research/ssr_pilot/results/rcrc/exact_dp_analysis.json`, the maximum empirical expected margin across all 6 model pairs under uniform references is $|\mu| = 0.0368$ (`mistral:7b-instruct vs qwen3:8b`).
- The certifiable TV budget per task is $\overline{\mathrm{TV}} < \frac{|\mu|}{2} \le 0.0184$ (less than $1.8\%$ probability shift).
- For a canonical bias shift of $p = 0.50$, the actual mean TV distance across the 24 worlds is $\overline{\mathrm{TV}} = 0.3308$, yielding a bound of $2 \times 0.3308 = 0.6616$—**18 times larger** than the largest expected margin on the benchmark.
- **Empirical verification of actual signs:** In `reference_distribution_sensitivity.json`, across all 11 evaluated distributions ($p \in [0.10, 0.99]$ across 550,000 draws), **the signs of the expected margins for all 6 model pairs remained 100% constant**. None of the expected margins ever flipped sign.

---

## 3. Evidence Gap B: Reconciliation of Reversal Figures

### 3.1 Trace of All Reported Reversal Rates

| Rate Reported | Originating File | Generation / Commit Context | Estimand & Calculation Method | Denominator & Units |
|---|---|---|---|---|
| **18.61%** | `PAPER_FINAL.md` (legacy), `FINAL_STATISTICS.md` | Pre-Deviation 9 (pre-2026-10-12) | Mean pairwise reversal rate across 6 pairs under E2 normalized match; **contains bug** where 7 `mistral:7b` outputs with unknown entities counted as E2 matches. | 50,000 Monte Carlo reference draws (seed 20261005). Total pairs: $6 \times \binom{50000}{2}$. |
| **17.5572%** (17.56%) | `rcr_summary.json` | Post-Deviation 9 corrected | Corrected E2 normalized match; sequential Monte Carlo loop in `analysis.py` (seed 20261005). | 50,000 Monte Carlo reference draws. Pairwise reversal = $\frac{\sum_{\text{pairs}} n_{\text{win1}} n_{\text{win2}}}{6 \binom{50000}{2}}$. |
| **17.2348%** (17.23%) | `reference_distribution_sensitivity.json` | Post-Deviation 9 corrected | E2 normalized match under uniform distribution grid point in `rcr_reference_distribution_sensitivity.py` (seed 20261007). | 50,000 vectorized Monte Carlo draws. |
| **17.1770%** (17.18%) | `extended_analysis.json` | Post-Deviation 9 corrected | E2 normalized match under full-draw vectorized simulation in `rcr_extended_analysis.py` (seed 20261016). | 50,000 vectorized Monte Carlo draws. |
| **17.1518%** | `exact_dp_analysis.json` | Dynamic Programming Convolution | Exact population expectation $\mathbb{E}_{R_1, R_2 \sim \prod \mathrm{Unif}(V_i)} [\mathbf{1}\{\text{winner reverses}\}]$ via discrete polynomial convolution. | Exact analytical parameter of the discrete product distribution; no Monte Carlo sampling. |

### 3.2 Exact DP vs. Monte Carlo Error & Uncertainty Derivation

#### Estimator Formulation
Let $M = 50,000$ independent benchmark-level reference vectors $\mathbf{R}^{(1)}, \dots, \mathbf{R}^{(M)}$ be sampled from $\prod_{i=1}^{24} V(x_i)$. For each pair $p \in \{1, \dots, 6\}$, let $N_{p,+}$ and $N_{p,-}$ denote the number of draws where model $A_p$ strictly beats $B_p$ and $B_p$ strictly beats $A_p$, respectively.
The pairwise winner reversal estimator is a symmetric degree-2 U-statistic:
$$U_p = \frac{2 N_{p,+} N_{p,-}}{M(M - 1)} = \frac{2 M}{M - 1} \hat{p}_{p,+} \hat{p}_{p,-}$$
whose population expectation under independent reference pairs is $\theta_p = 2 p_{p,+} p_{p,-}$.

By Hoeffding's U-statistic theory, because pairwise comparisons sharing a reference vector are statistically dependent, the finite-sample variance of $U_p$ is:
$$\mathrm{Var}(U_p) = \frac{4(M - 2)}{M(M - 1)} \zeta_{1, p} + \frac{2}{M(M - 1)} \zeta_{2, p}$$
where the first projection variance is $\zeta_{1, p} = p_{p,+} p_{p,-} (p_{p,+} + p_{p,-} - 4 p_{p,+} p_{p,-})$ and kernel variance is $\zeta_{2, p} = \theta_p(1 - \theta_p)$.

#### Joint Covariance Across Model Pairs
Because all 6 model pairs are evaluated on the **exact same** $M$ sampled reference vectors, the pairwise estimators $U_p$ and $U_q$ are correlated. The asymptotic covariance between $U_p$ and $U_q$ is given by:
$$\mathrm{Cov}(U_p, U_q) \approx \frac{4}{M} \mathrm{Cov}(h_{1, p}(\mathbf{R}), h_{1, q}(\mathbf{R})) = \frac{4}{M} (\boldsymbol{\Sigma}_1)_{p, q}$$
where $h_{1, p}(\mathbf{R}) = p_{p,-} \mathbb{I}(A_p > B_p) + p_{p,+} \mathbb{I}(B_p > A_p)$ is the Hajek projection.

For the six-pair aggregate mean $\bar{U} = \frac{1}{6} \sum_{p=1}^6 U_p$:
$$\mathrm{Var}(\bar{U}) = \frac{4}{36 M} \mathbf{1}^T \boldsymbol{\Sigma}_1 \mathbf{1}$$
Evaluating this on the 50,000 draws reveals that positive correlations among pairs sharing models produce a **Variance Inflation Factor (VIF)** of:
$$\mathrm{VIF} = \frac{\mathrm{Var}_{\mathrm{joint}}(\bar{U})}{\mathrm{Var}_{\mathrm{naive}}(\bar{U})} = \frac{0.0009060633^2}{0.0007118031^2} = \mathbf{1.6203}$$
Accounting for inter-pair dependencies inflates the sampling variance of the mean by **62.03%** ($\mathrm{SE}_{\mathrm{joint}} = 0.0009060633$ vs naive $\mathrm{SE}_{\mathrm{naive}} = 0.0007118031$).

#### Per-Pair Numerical Comparison (Exact DP vs. Monte Carlo)

| Model Pair | Exact DP $\theta_p$ | 50k MC $U_p$ | Error ($U_p - \theta_p$) | Error ($\theta_p - U_p$) | U-Stat SE ($\mathrm{SE}_p$) | $z$-Score |
|---|---|---|---|---|---|---|
| `gemma2:9b_vs_llama3.1:8b` | 0.2045062009 | 0.2058909402 | +0.0013847393 | -0.0013847393 | 0.0018972548 | +0.7299 |
| `gemma2:9b_vs_mistral:7b-instruct` | 0.2532779150 | 0.2535991040 | +0.0003211889 | -0.0003211889 | 0.0019214451 | +0.1672 |
| `gemma2:9b_vs_qwen3:8b` | 0.1460786387 | 0.1456764047 | -0.0004022340 | +0.0004022340 | 0.0019677021 | -0.2044 |
| `llama3.1:8b_vs_mistral:7b-instruct` | 0.2777255172 | 0.2773383884 | -0.0003871288 | +0.0003871288 | 0.0014745083 | -0.2625 |
| `llama3.1:8b_vs_qwen3:8b` | 0.0790128614 | 0.0786284670 | -0.0003843944 | +0.0003843944 | 0.0016069187 | -0.2392 |
| `mistral:7b-instruct_vs_qwen3:8b` | 0.0685069267 | 0.0694882058 | +0.0009812791 | -0.0009812791 | 0.0015139774 | +0.6481 |
| **Six-Pair Mean ($\bar{U}$)** | **0.1715180100** | **0.1717702517** | **+0.0002522417** | **-0.0002522417** | **0.0009060633** | **+0.2784** |

- **Mean Signed Error ($\text{MC} - \text{Exact}$):** $+0.0002522417$
- **Mean Signed Error ($\text{Exact} - \text{MC}$):** $-0.0002522417$
- **Mean Absolute Error (MAE):** $0.0006434941$
- **Maximum Absolute Error (Max AE):** $0.0013847393$ (on `gemma2:9b vs llama3.1:8b`)
- **Aggregate $z$-score under Joint Covariance:** $+0.2784$ ($p = 0.781$)
- **Reproducible Code:** `research/ssr_pilot/rcr_uncertainty_and_error_audit.py`
- **Output Artifact:** `research/ssr_pilot/results/rcrc/uncertainty_audit.json`
- **Unit & Regression Tests:** `tests/ssr_pilot/test_uncertainty_audit.py` (4 tests)

---

## 4. Evidence Gap C: Audit of the 99.99% Detection-Loss Claim

### 4.1 Provenance of the Calculation
- **Script:** `research/ssr_pilot/rcr_extended_analysis.py`
- **Artifact:** `research/ssr_pilot/results/rcrc/extended_analysis.json`
- **Population / Denominator:** Exactly $N = 50,000$ independent uniform reference draws from $\prod_{k=1}^{24} V(x_k)$.
- **Inferential Procedure:** At each draw, the 24 benchmark worlds serve as the paired observational units. A two-sided paired sign-flip permutation test (20,000 random sign flips) is conducted for each of the 6 model pairs, followed by step-down Holm-Bonferroni correction at $\alpha = 0.05$.

### 4.2 Ground-Truth vs. Reference-Dependent Decisions
Under the reference-independent semantic validator $E_3$:
- `llama3.1:8b vs qwen3:8b`: Holm-adjusted $p = 0.0126 < 0.05$ (Significant: Qwen3 wins).
- `mistral:7b-instruct vs qwen3:8b`: Holm-adjusted $p = 0.0175 < 0.05$ (Significant: Qwen3 wins).
- Remaining 4 pairs: Non-significant ($p = 0.200$ to $0.795$).

Under single-reference matching across all 50,000 draws:
- **Strict Exact Match ($E_1$):**
  - `llama3.1:8b vs qwen3:8b`: Missed in 50,000 / 50,000 draws (**100.0% false negatives**).
  - `mistral:7b-instruct vs qwen3:8b`: Missed in 50,000 / 50,000 draws (**100.0% false negatives**).
- **Normalized Match ($E_2$):**
  - `llama3.1:8b vs qwen3:8b`: Missed in 49,995 / 50,000 draws (**99.99% false negatives**; significant in only 5 draws).
  - `mistral:7b-instruct vs qwen3:8b`: Missed in 49,995 / 50,000 draws (**99.99% false negatives**; significant in only 5 draws).

### 4.3 Statistical Interpretation Guardrail
**Do not equate nonsignificance with equivalence.**  
The fact that reference matching yields $p \ge 0.05$ in 99.99% of draws is an empirical demonstration of **statistical power collapse** (detection loss), caused by reference attenuation shrinking the true score margin toward zero. It does *not* imply that the models are empirically equivalent under reference matching.

---

## 5. Evidence Gap D: Attenuation Law Audit and Recomputation

### 5.1 Task-Level Expected Score Identity
Let task $i$ have valid reference set $V_i = \{r_{i, 1}, \dots, r_{i, |V_i|}\}$.  
Let model $m$ produce $K$ candidate generations. Let $a_{mi}$ be the number of generations that match *at least one* valid reference in $V_i$.  
Under mutual exclusivity of valid references (guaranteed by canonical step ordering and rule D3(b)), $\sum_{r \in V_i} c_{mi}(r) = a_{mi}$.  
Under uniform reference selection $q_i(r) = \frac{1}{|V_i|}$, the expected reference-match score on task $i$ is:
$$\mathbb{E}[S_{mi}] = \sum_{r \in V_i} \frac{1}{|V_i|} \frac{c_{mi}(r)}{K} = \frac{1}{K |V_i|} \sum_{r \in V_i} c_{mi}(r) = \frac{a_{mi}}{K |V_i|} = \frac{S_{mi}^{E3}}{|V_i|}$$
This identity holds with Pearson $r = 1.0$ across all 42 non-zero (world, model) cells in `kref_attenuation.json`.

### 5.2 Benchmark-Level Aggregate Expectation
The benchmark score is the unweighted average across all $N=24$ tasks:
$$\mathbb{E}[S_m] = \frac{1}{N} \sum_{i=1}^N \mathbb{E}[S_{mi}] = \frac{1}{N} \sum_{i=1}^N \frac{S_{mi}^{E3}}{|V_i|}$$
In contrast, the semantic oracle benchmark score is $S_m^{E3} = \frac{1}{N} \sum_{i=1}^N S_{mi}^{E3}$.  
Therefore, reference-match evaluation implicitly reweights tasks by inverse valid space cardinality:
$$w_i = \frac{1}{|V_i|}$$
Tasks with unique solutions ($|V_i| = 1$) receive weight $1.0$, whereas tasks with high concurrency or multiple safe sequences ($|V_i| = 24$) receive weight $\frac{1}{24} \approx 0.0417$.

### 5.3 Pairwise Retention Ratios
For a pair of models $(A, B)$, the expected score gap under uniform reference matching is:
$$\mathbb{E}[M_{AB}] = \frac{1}{N} \sum_{i=1}^N \frac{\Delta_{AB, i}^{E3}}{|V_i|}$$
The retention ratio relative to the true semantic gap $\Delta_{AB}^{E3} = \frac{1}{N} \sum_i \Delta_{AB, i}^{E3}$ is:
$$\rho_{AB} = \frac{\mathbb{E}[M_{AB}]}{\Delta_{AB}^{E3}} = \frac{\sum_{i=1}^N \frac{\Delta_{AB, i}^{E3}}{|V_i|}}{\sum_{i=1}^N \Delta_{AB, i}^{E3}}$$

Empirical values from `research/ssr_pilot/results/rcrc/kref_attenuation.json`:

| Model Pair | True Oracle Gap ($\Delta^{E3}$) | Expected $E_2$ Gap ($\mathbb{E}[M]$) | Retention Ratio ($\rho_{AB}$) | Interpretation |
|---|---|---|---|---|
| `gemma2:9b vs llama3.1:8b` | +0.1042 | +0.0122 | **11.75%** | Retains ~12% of gap |
| `gemma2:9b vs mistral:7b-instruct` | +0.0938 | +0.0124 | **13.25%** | Retains ~13% of gap |
| `gemma2:9b vs qwen3:8b` | -0.1389 | -0.0243 | **17.53%** | Retains ~18% of gap |
| `llama3.1:8b vs qwen3:8b` | -0.2431 | -0.0366 | **15.05%** | Statistically separated pair: retains **15.1%** |
| `mistral:7b-instruct vs qwen3:8b` | -0.2326 | -0.0368 | **15.80%** | Statistically separated pair: retains **15.8%** |
| `llama3.1:8b vs mistral:7b-instruct` | -0.0104 | +0.000185 | **-1.78%** | Near-zero oracle gap; sign inverted by task weighting |

### 5.4 Resolution of the "12–18%" Claim
- For the two statistically separated pairs (`llama3.1 vs qwen3` and `mistral vs qwen3`), the retained signal is **15.05%** and **15.80%** (15–16%).
- Across all five model pairs with non-trivial semantic gaps ($|\Delta^{E3}| \ge 0.09$), the retention ratio spans **11.75% to 17.53%** (12–18%).
- The single pair with negative retention (`llama3.1 vs mistral`) has an oracle gap of only $-0.0104$ (non-significant); Mistral's extra correct solutions fall on tasks with larger $|V_i|$, which are heavily attenuated, flipping the expected margin to $+0.000185$.
- **Reporting Directive:** The empirical draft must state that reference matching retains **15–16%** of the true gap for statistically separated pairs, and spans **12–18%** across pairs with substantial differences, while noting the inverse-cardinality weighting distortion for near-tied pairs.

---

## 6. Code Verification & Test Suite Execution Progression

### 6.1 Historical Audit State (Pre-Fix Snapshot)
- Command executed: `pytest`
- Total tests collected: 418
- Passed: 416
- Failed: 2 (`test_reproducibility_table_hashes_match_files` and `test_generating_commit_sha_consistency`)
- Cause of failures: Historical files were modified in prior uncommitted work, causing `REPRODUCIBILITY.md` checksum table and commit SHA references to lag disk state.

### 6.2 Suite Expansion & Final Verification State
1. **Second Domain Pilot Addition:** Added `tests/test_second_domain_pilot.py` (+2 tests), verifying BFS level-synchronous enumeration and STRIPS deterministic pilot execution.
2. **Uncertainty Audit Unit Tests:** Added `tests/ssr_pilot/test_uncertainty_audit.py` (+4 tests), verifying U-statistic degrees, finite-sample variances, joint covariance matrix, and unrounded error tolerances.
3. **Consistency Gate Resolution:** Synchronized stale hashes in `paper/REPRODUCIBILITY.md` and added the post-audit commit hash in `paper/FINAL_RESEARCH_STATUS.md`.
4. **Final Executed Command:** `pytest -v`
   - **Total Tests Collected:** **424**
   - **Passed:** **424**
   - **Failed:** **0**
   - **Exit Code:** 0
   - **Runtime:** 19.19s (cached) / 69.78s (cold)
   - **Log File:** the test-execution log (the old `paper/review_bundle/` was removed in the 2026-10-24 cleanup; frozen evidence now lives in `RCR_EMPIRICAL_FINAL_EVIDENCE_v3.zip`, logs under `paper/logs/`)

