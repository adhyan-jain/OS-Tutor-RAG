# Reference-Choice Robustness: Quantifying Ranking Instability and Detection Loss in Multi-Reference Executable Benchmarks

**Anonymous Authors**  
*Under Review — Empirical Methodology Track*

---

## Abstract

Executable reasoning benchmarks evaluate language models by comparing their generated outputs against gold reference solutions. In formal procedural domains such as operating system scheduling, concurrency synchronization, and deadlock avoidance, task specifications frequently admit multiple semantically valid execution traces ($|V(x)| > 1$). Benchmark authors routinely select a single valid trace as the "gold" reference.

We formalize **Reference-Choice Robustness (RCR)**, an empirical methodology that exhaustively enumerates the valid-solution space $V(x)$ and quantifies the sensitivity of benchmark conclusions—model scores, pairwise rankings, and statistical significance decisions—to reference selection. Evaluating 1,152 generations from four open-weight models across 24 executable OS tasks, we sample 50,000 benchmark reference vectors from the Cartesian product $\prod_{k=1}^{24} V(x_k)$ and compute exact margin distributions via discrete dynamic programming (DP).

Under uniform reference selection, changing only the reference while holding models and tasks fixed yields an exact population pairwise winner reversal probability of **17.1518%** (50,000-draw Monte Carlo estimate: **17.1770%**; degree-2 U-statistic joint-covariance $\mathrm{SE} = 0.000906$ for the six-pair mean; mean absolute error $0.000643$). Across 50,000 draws, the mean Kendall score correlation against the canonical reference is $\tau_b = 0.618 \pm 0.351$, and normalized reference matching recovers the point-estimate ranking of a reference-independent semantic oracle in only **13.63%** of draws. A near-tie decomposition demonstrates that **85.6% of this reversal probability mass** is concentrated in the four model pairs that the oracle cannot statistically separate at $N=24$; among the two separated pairs, the reversal rate drops to **7.41%**.

More critically, reference matching induces severe **detection loss**: while the semantic oracle finds `qwen3:8b` significantly superior to `llama3.1:8b` and `mistral:7b-instruct` (Holm-adjusted $p = 0.013$ and $0.018$ under every reference choice), single-reference matching fails to detect these differences in **99.99%** of reference draws (49,995 of 50,000 draws; 95% Wilson CI: $[99.98\%, 99.996\%]$). Under mutual exclusivity, reference matching attenuates true task-level scores by an exact factor of $\frac{1}{|V(x)|}$ (an elementary identity that we use as a measurement tool, not a new result) (observed-to-predicted ratio $1.000$), reweighting tasks inversely by solution-space cardinality and retaining only 15.05% and 15.80% (15–16%) of true pairwise margins for separated pairs. Disclosing tie-breaking rules via stated-convention prompts fails to eliminate noncanonical outputs ($\text{FRR}_{\text{norm}} = 0.625$). A preregistered second-domain study (Blocks World; 24 tasks, 1,152 actual generations from the same four models) did **not** replicate the behavioral findings: the arithmetic identity held (non-zero-cell $r = 0.985$), but near-floor competence (0.35%–7.99% valid) left the mean reversal at 4.63% (below the registered 8%) and no model pair separable by the oracle, so near-tie concentration and detection loss could not be tested. The evidence for ranking instability and detection loss rests on the 24-world OS study alone. Within the OS benchmark, single-reference matching compresses score margins and inflates false-negative rates, which argues for reference-independent executable verifiers in multi-solution tasks; the generality of this conclusion is untested.

---

## 1. Introduction

Automated evaluation of large language models (LLMs) on complex reasoning benchmarks increasingly relies on execution-based evaluation: generating code, plans, or formal traces and evaluating their validity. However, when an execution trace must match a predefined "gold" reference (using strict string matching $E_1$ or normalized action matching $E_2$), evaluators implicitly assume that the benchmark task admits a unique valid sequence.

In real-world procedural and formal domains—such as operating system resource allocation, multi-threaded synchronization, database concurrency, and automated planning—this assumption fails. Multiple valid topological sorts, commutations of independent locks, and ties in shortest-job-first scheduling yield multi-valued solution spaces ($|V(x)| > 1$). When benchmark curators pick a single valid trace as ground truth, they introduce an unmodeled experimental variable: **curator reference choice**.

Recent empirical literature in NLP has demonstrated that reference set selection alters metric scores and system rankings in summarization (Casola et al., INLG 2025) and multilingual PII evaluation (Kulshreshtha et al., arXiv:2610.03825, Oct 2026), while incomplete references have been shown to distort calibration rankings in cognitive tracking (Feng et al., arXiv:2608.25654, Aug 2026). However, in unstructured natural language generation, the set of all valid outputs is infinite and impossible to enumerate, confounding reference variation with annotator disagreement and stylistic preference.

In this work, we take advantage of **formally verifiable state spaces** in operating system reasoning to achieve exhaustive valid-space enumeration. Because each benchmark world is governed by explicit state transitions, we construct the complete finite space $V(x)$ of all semantically valid solutions. This allows us to isolate the pure effect of reference selection, free from annotation noise.

### Primary Research Questions
1. **RQ1 (Attenuation & Detection Failure):** Under what quantitative mechanism does single-reference matching distort true model capabilities, and how does this affect statistical hypothesis testing?
2. **RQ2 (Ranking Instability & Near-Tie Decomposition):** When gold references vary over $V(x)$, how frequently do pairwise model winners reverse, and are these reversals concentrated among indistinguishable models or do they overturn well-supported orderings?
3. **RQ3 (Distributional Sensitivity):** Does ranking instability persist under non-uniform reference curation distributions (such as canonical author bias or structural similarity weighting)?
4. **RQ4 (Prompting Mitigation):** Can prompt disclosure of canonical conventions eliminate noncanonical valid outputs, or does reference-independent verification remain necessary?

---

## 2. Related Work

### 2.1 Multi-Reference and Incomplete-Reference Evaluation
The dependence of automated metrics on reference sets has a long history in machine translation and summarization. Recently, **Casola et al. (INLG 2025)** systematically analyzed reference set variation across SummEval, GUMSum, and DUC2004, demonstrating that common metrics (ROUGE, BERTScore) exhibit ranking instability depending on which human reference set is sampled, and that human correlation degrades substantially outside newswire domains. **Kulshreshtha, Dalmia, and Mukherji (arXiv:2610.03825, Oct 2026)** evaluated multi-annotator multilingual benchmarks, showing that holding model outputs fixed while swapping annotator references shifted $F_1$ scores by up to 7.55 points and moved pairwise model interaction margins by +2.95 points, introducing the "reference-sensitivity band". In open-ended evaluation, **Feng, Chen, and Zhang (arXiv:2608.25654, Aug 2026)** demonstrated that incomplete reference sets reverse calibration rankings (Brier score and expected calibration error) because treating unmatched valid outputs as false introduces severe false-negative bias. Our work differs from these studies by focusing on **enumerable finite-state domains**, where $V(x)$ is exhaustively known and ground truth is determined by an executable semantic verifier.

### 2.2 Execution-Based Benchmarking and Semantic Oracles
Benchmarks such as HumanEval (Chen et al., 2021) and SWE-bench (Jimenez et al., 2024) evaluate functional correctness by executing unit tests. However, in domain-specific tasks—such as CPU scheduling (Gao et al., 2023), robotic planning (Valmeekam et al., 2023), and formal optimization (Falsification Bench, 2026)—benchmarks frequently fall back to reference trajectory matching due to the difficulty of implementing general semantic checkers. When $V(x)$ is multi-valued, trajectory matching penalizes valid alternate solutions, conflating non-canonical valid outputs with hallucinated or erroneous outputs.

---

## 3. Formal Framework and Task Formulation

### 3.1 Task, Space, and Model Definitions
Let a benchmark $\mathcal{B} = \{x_1, \dots, x_N\}$ consist of $N$ evaluation tasks.
- **Valid Solution Space:** For task $x_i$, $V(x_i) = \{r_{i, 1}, \dots, r_{i, |V(x_i)|}\}$ denotes the non-empty, finite set of all semantically valid solutions, exhaustively generated and verified by domain simulators.
- **Candidate Outputs:** Each evaluated model $m \in \mathcal{M}$ generates $K$ candidate solutions $y_{mi}^{(1)}, \dots, y_{mi}^{(K)}$ for task $x_i$.
- **Reference Vector:** A benchmark reference selection is a vector $R = (r_1, \dots, r_N) \in \prod_{i=1}^N V(x_i)$.

### 3.2 Evaluators
We formalize three evaluators operating on candidate output $y$ and task $x_i$:
1. **Canonical Exact Match ($E_1$):** Evaluates whether candidate $y$ exactly matches reference string $r_i$ under squashed whitespace:
   $$E_1(y, r_i) = \mathbf{1}\{\text{squash}(y) = \text{squash}(r_i)\}$$
2. **Normalized Action Match ($E_2$):** Extracts the action sequence from $y$ and evaluates equivalence against normalized reference steps:
   $$E_2(y, r_i) = \mathbf{1}\{\text{norm\_steps}(y) = \text{norm\_steps}(r_i)\} \times \mathbf{1}\{\text{no\_unknown\_entities}(y)\}$$
3. **Semantic Executable Oracle ($E_3$):** Executes candidate $y$ directly against the underlying state simulator (e.g., verifying that a CPU schedule executes all bursts without preemption violations, or that a Banker's allocation path maintains safety):
   $$E_3(y, x_i) = \mathbf{1}\{y \text{ is semantically valid on } x_i\}$$
   Crucially, $E_3$ is reference-independent: $E_3(y, x_i) = \mathbf{1}\{y \in V(x_i)\}$.

### 3.3 Score Margins and Reversal Probabilities
Under reference vector $R$, the task score of model $m$ is $S_{mi}(r_i) = \frac{1}{K} \sum_{k=1}^K E(y_{mi}^{(k)}, r_i)$, and the benchmark score is $S_m(R) = \frac{1}{N} \sum_{i=1}^N S_{mi}(r_i)$.  
For a pair of models $(A, B)$, the score margin is $M_{AB}(R) = S_A(R) - S_B(R)$.  
For two independent reference vector draws $R_1, R_2 \sim \prod_{i=1}^N q_i$, a **pairwise winner reversal** occurs when the sign of the margin strictly reverses:
$$\mathrm{Rev}_{AB} = (M_{AB}(R_1) > 0 \wedge M_{AB}(R_2) < 0) \vee (M_{AB}(R_1) < 0 \wedge M_{AB}(R_2) > 0)$$
By independence of $R_1$ and $R_2$, the exact reversal probability is:
$$P(\mathrm{Rev}_{AB}) = 2 \cdot P(M_{AB} > 0) \cdot P(M_{AB} < 0) = 2 p_+ p_-$$

---

## 4. Benchmark Construction and Experimental Protocol

### 4.1 Benchmark Worlds ($N = 24$)
The benchmark spans 24 deterministic OS environments across three foundational mechanism families:
1. **CPU Scheduling (8 worlds):** Preemptive and non-preemptive Shortest Job First (SJF) and Priority scheduling. Ties in arrival time and burst lengths create multiple valid execution schedules ($|V_i| \in [1, 4]$).
2. **Concurrency Synchronization (8 worlds):** Mutex lock acquisition, condition variable signaling, and bounded-buffer producer-consumer protocols. Interleavings of independent operations yield Mazurkiewicz-equivalent valid traces ($|V_i| \in [1, 10]$).
3. **Banker's Deadlock Avoidance (8 worlds):** Multi-resource allocation graphs. Multiple distinct process execution sequences satisfy safety criteria ($|V_i| \in [1, 24]$).

Across all 24 tasks, the Cartesian product space contains $|\prod_{i=1}^{24} V(x_i)| \approx 7.08 \times 10^{13}$ distinct benchmark reference vectors.

### 4.2 Evaluated Models and Generation Records
We evaluate four open-weight models across three distinct model families:
- `qwen3:8b` (Qwen family)
- `gemma2:9b` (Gemma family)
- `mistral:7b-instruct` (Mistral family)
- `llama3.1:8b` (Llama family)

For each (world, model) pair, we generate 12 candidate solutions across 3 prompt surface variants and 4 random decoding seeds, yielding $24 \times 12 \times 4 = 1,152$ frozen generation records. In addition, we evaluate a stated-convention arm ($n = 1,152$) and a feasibility arm on `gemma3:12b` ($n = 42$ valid) and `olmo2:7b` ($n = 6$ valid).

### 4.3 Reference Vector Sampling and Dynamic Programming
We implement two complementary analytical pipelines:
1. **50,000-Draw Monte Carlo Simulation:** We sample $M = 50,000$ independent reference vectors $R \sim \prod_{i=1}^{24} \mathrm{Unif}(V(x_i))$, keeping canonical reference Draw 0 strictly isolated. We compute pairwise win matrices, Kendall $\tau_b$ score vector correlations, and world-level sign-flip permutation tests.
2. **Exact Dynamic Programming Convolution:** Because per-task differences $D_i(r) \in [-1, 1]$ take values in integer multiples of $\frac{1}{K}$, we compute the exact discrete probability distribution of $M_{AB}$ via $O(N^2 K^2)$ DP convolution, eliminating Monte Carlo error entirely.

---

## 5. Empirical Results & Reconciliation

### 5.1 Reconciliation of All Reversal Estimates

Historical manuscripts in this repository reported a headline reversal rate of **18.61%**. We forensically trace this figure and reconcile all reported reversal statistics:

| Estimate | Originating Artifact | Method & Configuration | Denominator & Units | Reversal Rate |
|---|---|---|---|---|
| **Legacy 18.61% (Superseded)** | `PAPER_FINAL.md` (legacy), `FINAL_STATISTICS.md` | 50,000 MC draws (seed 20261005). **Contains parser defect**: 7 `mistral:7b` outputs with unknown entities counted as matches. | $6 \times \binom{50000}{2}$ non-tied reference pairs. | **18.61%** |
| **Corrected MC 17.56%** | `rcr_summary.json` | 50,000 MC draws (seed 20261005) with preregistered rule D3(b) applied. | Mean across 6 model pairs. | **17.5572%** (17.56%) |
| **Uniform-Grid MC 17.23%** | `reference_distribution_sensitivity.json` | 50,000 vectorized MC draws (seed 20261007) at uniform grid point. | Mean across 6 model pairs. | **17.2348%** (17.23%) |
| **Extended MC 17.18%** | `extended_analysis.json` | 50,000 vectorized MC draws (seed 20261016). | Mean across 6 model pairs. | **17.1770%** (17.18%) |
| **Exact DP Parameter** | `exact_dp_analysis.json` | Discrete DP convolution of discrete difference distributions; exact parameter of product space. | Exact analytical population value; no sampling. | **17.1518%** |

#### Defect Verification
Under the legacy parser (rule D3(b) omitted), `mistral:7b`'s canonical $E_2$ score was $3.47\%$ ($10/288$), yielding a legacy exact DP reversal of $18.17\%$ and MC reversal of $18.61\%$. When rule D3(b) is correctly applied (unknown entity mentions rejected), `mistral:7b`'s canonical score is $1.74\%$ ($5/288$). The legacy 18.61% figure is fully superseded by the bug correction.

#### Unrounded Per-Pair Exact DP vs. Monte Carlo Error Analysis
Comparing the exact DP population parameter against the 50,000-draw Monte Carlo simulation in `extended_analysis.json` ($M = 50,000$):

| Model Pair | Exact DP ($p_{\mathrm{exact}}$) | 50k MC ($p_{\mathrm{mc}}$) | Error ($\mathrm{MC} - \mathrm{Exact}$) | Error ($\mathrm{Exact} - \mathrm{MC}$) | Absolute Error | U-Stat $\mathrm{SE}$ | $z$-Score |
|---|---|---|---|---|---|---|---|
| `gemma2:9b vs llama3.1:8b` | 0.20450620 | 0.20589094 | +0.00138474 | -0.00138474 | 0.00138474 | 0.00189725 | +0.7299 |
| `gemma2:9b vs mistral:7b` | 0.25327792 | 0.25359910 | +0.00032119 | -0.00032119 | 0.00032119 | 0.00192145 | +0.1672 |
| `gemma2:9b vs qwen3:8b` | 0.14607864 | 0.14567640 | -0.00040223 | +0.00040223 | 0.00040223 | 0.00196770 | -0.2044 |
| `llama3.1:8b vs mistral:7b` | 0.27772552 | 0.27733839 | -0.00038713 | +0.00038713 | 0.00038713 | 0.00147451 | -0.2625 |
| `llama3.1:8b vs qwen3:8b` | 0.07901286 | 0.07862847 | -0.00038439 | +0.00038439 | 0.00038439 | 0.00160692 | -0.2392 |
| `mistral:7b vs qwen3:8b` | 0.06850693 | 0.06948821 | +0.00098128 | -0.00098128 | 0.00098128 | 0.00151398 | +0.6481 |
| **Six-Pair Mean ($\bar{U}$)** | **0.17151801** | **0.17177025** | **+0.00025224** | **-0.00025224** | **0.00064349** | **0.00090606** | **+0.2784** |

- **Mean Signed Error ($\mathrm{MC} - \mathrm{Exact}$):** $+0.00025224$ (+0.0252 percentage points).
- **Mean Signed Error ($\mathrm{Exact} - \mathrm{MC}$):** $-0.00025224$ (-0.0252 percentage points).
- **Mean Absolute Error (MAE):** $0.00064349$ (0.0643 percentage points).
- **Maximum Absolute Error (Max AE):** $0.00138474$ (0.1385 percentage points, on `gemma2 vs llama3.1`).
- **Uncertainty Derivation (Degree-2 U-Statistic):** Because comparisons sharing a sampled vector are dependent, the pairwise reversal rate is estimated via a degree-2 U-statistic $U_p = \frac{2 N_{p,+} N_{p,-}}{M(M-1)}$ with first projection variance $\zeta_{1, p} = p_+ p_- (p_+ + p_- - 4 p_+ p_-)$. Furthermore, because all 6 model pairs are evaluated on the identical $M = 50,000$ sampled reference vectors, the uncertainty of the six-pair mean $\bar{U} = \frac{1}{6} \sum U_p$ is governed by the full $6 \times 6$ covariance matrix $\boldsymbol{\Sigma}_1 = \mathrm{Cov}(h_1(\mathbf{R}))$. Positive covariance among pairs sharing candidate models produces a Variance Inflation Factor $\mathrm{VIF} = 1.6203$, inflating the standard error from a naive independent-pair estimate of $0.000712$ to $\mathrm{SE}_{\mathrm{joint}} = \mathbf{0.00090606}$. The aggregate discrepancy yields $z = +0.2784$ ($p = 0.781$).

---

### 5.2 Primary Benchmark Summary

Table 1 summarizes the performance of the three evaluators across the 24 OS tasks.

| Metric | $E_1$ (Canonical Exact) | $E_2$ (Normalized Match) | $E_3$ (Semantic Oracle) |
|---|---|---|---|
| **Canonical Draw 0 Scores** | | | |
| `qwen3:8b` | 4.86% | 13.19% | 30.90% |
| `gemma2:9b` | 0.69% | 2.43% | 17.01% |
| `mistral:7b-instruct` | 0.00% | 1.74% | 7.64% |
| `llama3.1:8b` | 0.00% | 0.35% | 6.60% |
| **Point-Estimate Canonical Ranking** | Qwen > Gemma > Llama = Mistral | Qwen > Gemma > Mistral > Llama | Qwen > Gemma > Mistral > Llama |
| **Ranking Stability over 50,000 Draws** | | | |
| Mean Kendall $\tau_b$ vs. Canonical | $0.767 \pm 0.380$ | $0.618 \pm 0.351$ | **1.000** (Reference-Invariant) |
| Standard Error ($\mathrm{SE}$) | 0.0018 | 0.0016 | 0.0000 |
| Degenerate Draws Excluded (D5) | 4,118 / 50,000 (8.2%) | 87 / 50,000 (0.17%) | 0 / 50,000 (0.0%) |
| **Mean Pairwise Winner Reversal Rate** | **4.68%** | **17.56%** (MC) / **17.15%** (DP) | **0.00%** |
| **Oracle Ordering Recovery Rate** | **2.86%** | **13.63%** | **100.00%** |

---

### 5.3 The Attenuation Law & Retention Mechanics (RQ1)

#### Mathematical Identity vs. Empirical Fit
We distinguish the mathematically derived identity from empirical observations:
- **Mathematical Identity:** When every valid generation matches at most one valid reference (mutual exclusivity), and reference $r$ is drawn uniformly from $V(x_i)$, the expectation of the indicator $\mathbf{1}\{y = r\}$ is identically $\frac{\mathbf{1}\{y \in V(x_i)\}}{|V(x_i)|}$. Therefore, the task-level relation $\mathbb{E}[S_{mi}^{E2}] = \frac{S_{mi}^{E3}}{|V(x_i)|}$ is a **mathematical theorem**, not a separate empirical finding.
- **Empirical Verification:** The fact that Pearson $r = 1.0$ and the observed-to-predicted ratio is $1.000$ across all 42 non-zero cells in `kref_attenuation.json` empirically confirms that our parsing and validation pipeline preserves mutual exclusivity without double-matching or missed valid matches.

#### Benchmark Aggregate & Inverse Cardinality Weighting
At the benchmark level across $N=24$ tasks, the expected score is:
$$\mathbb{E}[S_m^{E2}] = \frac{1}{N} \sum_{i=1}^N \frac{S_{mi}^{E3}}{|V(x_i)|}$$
Reference matching implicitly reweights task contributions by $w_i = \frac{1}{|V(x_i)|}$. Tasks with unique solutions ($|V| = 1$) receive weight $1.0$, whereas tasks with 24 permutations receive weight $0.0417$.

#### Pairwise Retention Ratios
The retained margin ratio $\rho_{AB} = \frac{\mathbb{E}[M_{AB}^{E2}]}{\Delta_{AB}^{E3}} = \frac{\sum_{i=1}^N \frac{\Delta_{AB, i}^{E3}}{|V(x_i)|}}{\sum_{i=1}^N \Delta_{AB, i}^{E3}}$ behaves as follows:

| Model Pair | True Oracle Gap ($\Delta^{E3}$) | Expected $E_2$ Gap ($\mathbb{E}[M]$) | Retention Ratio ($\rho_{AB}$) | Explanation |
|---|---|---|---|---|
| `llama3.1:8b vs qwen3:8b` | -0.2431 | -0.0366 | **15.05%** | Separated pair: robust denominator |
| `mistral:7b vs qwen3:8b` | -0.2326 | -0.0368 | **15.80%** | Separated pair: robust denominator |
| `gemma2:9b vs qwen3:8b` | -0.1389 | -0.0243 | **17.53%** | Large non-separated gap |
| `gemma2:9b vs mistral:7b` | +0.0938 | +0.0124 | **13.25%** | Moderate non-separated gap |
| `gemma2:9b vs llama3.1:8b` | +0.1042 | +0.0122 | **11.75%** | Moderate non-separated gap |
| `llama3.1:8b vs mistral:7b` | -0.0104 | +0.000185 | **-1.78%** | **Near-zero denominator instability** |

- **Statistically Separated Pairs:** For the two pairs separated by $E_3$, reference matching retains **15.05%** and **15.80%** (15–16%) of the true gap.
- **Pairs with Substantial Gaps ($|\Delta^{E3}| \ge 0.09$):** Retention spans **11.75% to 17.53%** (12–18%).
- **Near-Zero Denominator Instability:** In `llama3.1 vs mistral`, the true gap is tiny ($-0.0104$, non-significant). Because Mistral's extra correct solutions fall on tasks with $|V| = 24$ (heavily down-weighted), the expected $E_2$ gap flips to $+0.000185$, yielding a negative retention of $-1.78\%$. This confirms that retention ratios become unstable when the true margin is near zero.

---

### 5.4 Detection Loss in Hypothesis Testing (RQ1)

We evaluate detection power across all 50,000 reference draws using world-level paired sign-flip permutation tests (20,000 flips) with Holm-Bonferroni correction ($\alpha = 0.05$):

| Model Pair | $E_3$ Oracle Ground Truth | $E_3$ Adjusted $p$ | $E_1$ Detection Rate ($p < 0.05$) | $E_2$ Detection Rate ($p < 0.05$) |
|---|---|---|---|---|
| `llama3.1:8b vs qwen3:8b` | **Significant (Qwen wins)** | **0.0126** | **0.00%** (0 / 50k) | **0.01%** (5 / 50k) |
| `mistral:7b vs qwen3:8b` | **Significant (Qwen wins)** | **0.0175** | **0.00%** (0 / 50k) | **0.01%** (5 / 50k) |
| `gemma2:9b vs qwen3:8b` | Non-significant | 0.1998 | 0.00% (0 / 50k) | 0.00% (0 / 50k) |
| `gemma2:9b vs llama3.1:8b` | Non-significant | 0.1998 | 0.00% (0 / 50k) | 0.00% (0 / 50k) |
| `gemma2:9b vs mistral:7b` | Non-significant | 0.1998 | 0.00% (0 / 50k) | 0.00% (0 / 50k) |
| `llama3.1:8b vs mistral:7b` | Non-significant | 0.7948 | 0.00% (0 / 50k) | 0.00% (0 / 50k) |

- **Exact Counts:** Out of 50,000 draws, $E_2$ fails to detect Qwen3's significant superiority in **49,995 draws** (**99.99%**; 95% Wilson score CI: $[99.977\%, 99.996\%]$), detecting it in only 5 draws. $E_1$ fails in **50,000 draws** (**100.0%**).
- **Proper Statistical Interpretation:** Failing to reject the null hypothesis in 99.99% of draws reflects a **loss of statistical power** caused by score compression. It is conditional on the frozen dataset and evaluation procedure, and must **never be equated with model equivalence**.

---

### 5.5 Near-Tie Decomposition of Reversals (RQ2)

We decompose the total pairwise reversal probability mass across all 6 model pairs:

| Pair Group | Model Pairs Included | Sum of Reversal Probabilities | Share of Total Reversal Mass | Mean Reversal Rate |
|---|---|---|---|---|
| **$E_3$-Unseparated Pairs** | `llama vs mistral`, `gemma vs mistral`, `gemma vs llama`, `gemma vs qwen` (4 pairs) | 0.882505 | **85.63%** | **22.06%** |
| **$E_3$-Separated Pairs** | `llama vs qwen`, `mistral vs qwen` (2 pairs) | 0.148117 | **14.37%** | **7.41%** |
| **All Pairs Combined** | All 6 pairs | 1.030622 | **100.00%** | **17.18%** |

- **Aggregation Clarification:** **85.6% is the fraction of total pairwise reversal probability mass**, not the share of model pairs (unseparated pairs comprise $4/6 = 66.7\%$ of pairs).
- **Separated Pair Persistence:** Even in the two statistically separated pairs, the mean reversal rate is **7.41%**, and the reference-matching winner opposes the oracle winner in 3.7%–4.2% of draws.

---

### 5.6 Distributional Sensitivity Analysis (RQ3)

Evaluating 11 reference-selection distributions across 550,000 Monte Carlo draws:

| Distribution | Canonical Weight ($p$) | Mean $E_2$ Pairwise Reversal Rate |
|---|---|---|
| Uniform over $V(x)$ | $1/|V(x)|$ | **17.23%** |
| Inverse Structural Distance | Heuristic similarity | **17.04%** |
| Mild Canonical Bias | $p = 0.25$ | **14.88%** |
| Moderate Canonical Bias | $p = 0.50$ | **12.14%** |
| Strong Canonical Bias | $p = 0.80$ | **7.35%** |
| Extreme Canonical Bias | $p = 0.95$ | **2.30%** |

Reversals attenuate monotonically as curators concentrate on the canonical reference, but remain substantial (12.14% at 50% bias) across all realistic curation distributions.

---

### 5.7 Mechanism Family Heterogeneity & Prompt Controls (RQ4)

- **Family Breakdown:** Banker's Deadlock Avoidance ($|V| \le 24$): **21.0%** reversal; Concurrency Synchronization ($|V| \le 10$): **10.0%** reversal; CPU Scheduling ($|V| \le 4$): **0.0%** reversal (floor effect; 3 models score zero).
- **Stated-Convention Control:** Disclosing canonical tie-breaking rules leaves $\text{FRR}_{\text{norm}} = 0.625$ ($62.5\%$ of valid solutions remain noncanonical). On `gemma3:12b`, $\text{FRR}_{\text{norm}} = 0.619$.

---

## 6. Second-Domain Study: Blocks World Planning

### 6.0 Three categories of evidence

This paper rests on three evidence sets that are **not pooled** and carry different weight.

| Evidence set | Tasks | Candidate outputs | Role |
|---|---|---|---|
| **Original OS study** (§4–§5) | 24 OS worlds | 1,152 frozen LLM generations | Primary empirical result |
| **Blocks World pilot** | 6 worlds, $\lvert V\rvert\in\{1,2,6\}$ | *Synthetic* candidate distributions (no LLM) | Implementation check of the evaluator and enumerator only; carries no behavioral claim |
| **Blocks World confirmatory study** | 24 planning tasks | 1,152 actual generations from four local models | Preregistered replication attempt (this section) |

The preregistration (`research/docs/SECOND_DOMAIN_PREREGISTRATION.md`) is an **internal, dated protocol, not an externally registered one**. The analysis script was last modified at 23:20 on 2026-10-13, after the first `qwen3:8b` record was written (23:18:54) but before that model finished (23:23:20) and before the other three models ran. Strict blindness to the first model's outputs therefore cannot be certified from file times alone.

### 6.1 Declared reference space and its verification

For a deterministic transition system, unrestricted action sequences with cycles are infinite. The declared space $V(x)$ is therefore the set of **all shortest valid paths** from $s_0$ to the goal. The operator model is `move(X,Y)` and `move_to_table(X)` (deviation D0, §6.6).

Enumeration used a level-synchronous BFS. It was then verified by a separate implementation that shares no code with it (`verify_reference_spaces.py`). The verifier uses a different state encoding (stacks), iterative-deepening DFS over *all* action sequences with no visited-state pruning, and independent legality rules. For all 24 tasks it agrees on the shortest length $L^*$, on $\lvert V\rvert$, and on the plan *sets* (not just their sizes). It also confirms there are no duplicates, that every plan replays validly, and that no shorter plan exists. Cardinalities: Tier 1 (8 tasks) $\lvert V\rvert=1$; Tier 2 (8 tasks) $\lvert V\rvert\in\{2,2,2,3,4,6,6,6\}$; Tier 3 (8 tasks) $\lvert V\rvert\in\{10,10,12,12,20,20,24,24\}$.

### 6.2 Execution

All 1,152 planned generations ran: 4 models × 24 tasks × 3 prompt surfaces (PDDL-like, natural language, JSON) × 4 seeds. Every `(model, task, variant, seed)` cell is present exactly once, with no duplicate keys. There were **0 errors** and **0 empty responses**. 1,151 stopped normally; one `qwen3:8b` response hit the 512-token cap (`done_reason=length`). It was kept and scored under the same rules. Each record stores prompt, prompt SHA-256, settings, response, timestamp, latency and token counts. Decoding was $T=0.7$, top-$p=0.9$, `num_predict=512`, with the Ollama seed set per record; for `qwen3:8b` thinking mode was disabled (D5). Hardware was one NVIDIA RTX 4060 Laptop GPU (8 GB), 15 GB RAM and Ollama 0.19.0. The generation timestamps span 31 min 44 s (23:18:54 → 23:50:38). The preregistered 5–6 hour estimate was therefore wrong by roughly an order of magnitude.

No answer key reaches a prompt. A test verifies that no task's reference plan string occurs in any of its prompts. Every prompt does contain one fixed demonstration string, `move_to_table(A), move(A, B)`, which is not a reference plan for any task. Eighteen responses (10 `qwen3:8b`, 8 `gemma2:9b`) reproduced it verbatim and were invalid.

### 6.3 Model competence: a severe floor effect

| Model | Valid / 288 | $E_3$ pass rate | 95% CI (task-cluster bootstrap) | Tasks with ≥1 valid | Tier 1 | Tier 2 | Tier 3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `qwen3:8b` | 23 | 7.99% | [3.1%, 13.2%] | 8 / 24 | 1/96 | 14/96 | 8/96 |
| `gemma2:9b` | 16 | 5.56% | [1.4%, 10.8%] | 6 / 24 | 6/96 | 6/96 | 4/96 |
| `llama3.1:8b` | 1 | 0.35% | [0.0%, 1.0%] | 1 / 24 | 0/96 | 0/96 | 1/96 |
| `mistral:7b-instruct` | 1 | 0.35% | [0.0%, 1.0%] | 1 / 24 | 1/96 | 0/96 | 0/96 |

The independent unit is the **task** (24 per model), not the generation: the 12 generations inside a cell share a task, a model and prompts. Between-task differences explain 22% (`qwen3`), 27% (`gemma2`) and 8% (`llama3.1`, `mistral`) of generation-level pass/fail variance.

Of 1,152 generations, 41 (3.6%) are semantically valid. Of those, 39 are shortest plans in $V$ and 2 are valid but longer. This is **far below the competence floor** the preregistration required (criterion 4, "non-trivial model competence"). The criterion is **not met**: two of four models have a single valid output each, and `qwen3:8b` solves Tier 1 once in 96 tries.

Failure taxonomy (counts of 288 per model):

| Model | Illegal at step 1 | Illegal later | Legal, goal not reached | Copied prompt example (invalid) | Valid, shortest | Valid, longer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `qwen3:8b` | 144 | 108 | 3 | 10 | 23 | 0 |
| `gemma2:9b` | 96 | 156 | 12 | 8 | 16 | 0 |
| `llama3.1:8b` | 215 | 63 | 9 | 0 | 0 | 1 |
| `mistral:7b-instruct` | 224 | 60 | 3 | 0 | 0 | 1 |

Of the 1,111 invalid generations, 1,066 (96%) contain an *illegal action* at some step (for example, moving a block that is not clear); some of the 18 copied examples are illegal as well. These failures are not parser artifacts: responses all carry a `PLAN:` prefix and parse to non-empty plans. Competence is also strongly **prompt-surface dependent**. All 23 valid `qwen3:8b` plans come from the natural-language prompt (24.0% there, versus 0% under both the PDDL-like and JSON prompts). `gemma2:9b` passes 8.3% / 8.3% / 0% (PDDL-like / natural language / JSON).

### 6.4 Preregistered hypotheses

| Hypothesis | Registered criterion | Result | Verdict |
|---|---|---|---|
| **H1** attenuation | Pearson $r\ge0.98$ over non-zero cells and median ratio ∈ [0.95, 1.05] | $r=0.9855$ over 16 non-zero cells (of 96); median ratio 1.000; mean ratio 0.875 | **Confirmed** |
| **H2** ranking instability | Mean pairwise reversal ≥ 8.0% | Exact DP mean **4.63%** (qwen3–gemma2 27.78%; the other five pairs 0.00%) | **Rejected** |
| **H3** near-tie concentration | ≥ 70% of reversal mass in $E_3$-unseparated pairs | 100%, but no pair is $E_3$-separated, so the share holds by construction | **Not informative** |
| **H4** detection loss | ≥ 90% miss rate for $E_3$-separated pairs | No pair is $E_3$-separated (smallest Holm $p=0.0975$) | **Not testable** |

**H1.** The identity $\mathbb{E}[S^{E2}_{mi}]=S^{E3}_{mi}/\lvert V_i\rvert$ is algebra, not a finding (§5.3). What the test establishes is that the pipeline respects it. Only 16 of 96 cells have any signal. The mean ratio of 0.875 reflects the two cells where a model's only valid plan was a *longer* valid plan, outside $V$ (observed 0, predicted $>0$). This shows that the identity requires $E_3$ to be restricted to shortest plans. The as-executed run reported $r=0.9884$ over all 96 cells, a deviation from the registered wording (D1). Both values pass.

**H2.** Rejected, and robustly so. Reference-choice variability is integrated out *exactly* by the DP. The remaining uncertainty comes from the finite generations and the finite task set. Resampling the 12 generations inside every cell (2,000 replicates) gives a mean-reversal 95% interval of [0.003%, 7.93%], with 1.9% of replicates at or above 8%. Resampling the 24 tasks gives [0.0%, 6.89%], with 0.4% at or above 8%. Placing extra mass $p$ on the canonical reference (exact DP) gives mean reversal of 4.63% ($p=0$), 6.12% (0.25), 5.94% (0.5), 2.52% (0.8) and 0.25% (0.95), never reaching 8%.

The one non-zero pair, `qwen3` vs `gemma2`, has 27.78% reversal ($P(A>B)=0.208$, $P(B>A)=0.667$, expected margin $-0.0064$) *although* `qwen3` has the higher semantic pass rate. This illustrates the inverse-cardinality weighting. But it rests on 23 versus 16 valid generations, and the oracle cannot separate the pair (Holm $p=1.0$). It is a descriptive observation, not evidence of a replicated effect.

**H3 and H4.** With $N=24$ and four near-floor models, the oracle separates no pair after Holm correction (Qwen3 vs LLaMA and vs Mistral: raw $p\approx0.016$, Holm $0.0975$ in the confirmatory code; $0.089$ with the $+1$ Monte Carlo correction). H3 and H4 are therefore *undefined*. The as-executed run printed "CONFIRMED" for both; this was a logic error (D2). In an exploratory analysis over all 50,000 reference vectors with 20,000 sign flips, $E_2$ detects *no* pair in any draw (0/50,000), but since the oracle itself does not reach significance, no *detection loss* can be attributed to reference choice.

### 6.5 Deviations from the preregistration

| ID | Deviation | Treatment |
|---|---|---|
| D0 | Two-operator model (`move`, `move_to_table`) instead of the registered `Pickup/Putdown/Stack/Unstack` with `Holding`/`ArmEmpty` | Fixed in the task file before any generation; changes the content of $V$ and plan lengths. Registered body not edited; an addendum records it |
| D1 | As executed, H1's $r$ used all 96 cells; the protocol says non-zero cells | Code corrected; both reported; verdict unchanged |
| D2 | As executed, H3 and H4 printed CONFIRMED when no pair was separated | Code corrected to NOT INFORMATIVE / NOT TESTABLE; as-executed JSON preserved |
| D3 | The H4 branch subsampled 2,000 draws × 5,000 flips instead of 50,000 × 20,000 | Branch never triggered; the exploratory analysis used the full 50,000 × 20,000 |
| D4 | Degenerate-draw policy D5 not applied | The DP is exact over the full population; only the exploratory Monte Carlo uses draws |
| D5 | `think=false` for `qwen3:8b` (not registered) | Needed to fit the 512-token cap; disclosed |
| D6 | Fixed demonstration string in every prompt | Not a reference; 18 verbatim invalid copies reported |
| D7 | The 5–6 h feasibility estimate in the protocol was incorrect | Actual span 31 min 44 s |

### 6.6 Interpretation and contrast with the OS study

1. **What replicated:** only the arithmetic identity, which is guaranteed by construction (H1).
2. **What did not:** the behavioral claims. The registered reversal threshold (H2) was missed, and H3 and H4 could not be tested. The second-domain study therefore provides **no independent behavioral confirmation** of ranking instability or detection loss.
3. **Why it differs from the OS study:** in OS, the best model reaches 30.9% $E_3$ and the oracle separates two pairs. Here the best model reaches 8.0% and no pair is separated. The planning difficulty of 7–9B models without tool access is consistent with prior work (Valmeekam et al., 2023), but it makes this particular task suite unsuitable for testing the question.
4. **No pooling:** the domains differ in competence, task structure and prompt format, so no composite is formed. Twenty-four planning tasks establish nothing about planning or coding benchmarks in general.
5. **What would make it informative:** a model or prompting regime with a substantially higher pass rate (the registered criterion is non-zero competence across all four models, which a single natural-language prompt format or few-shot examples might provide) and a larger task set to give the oracle power. That would be a new study, not a rerun of this one.


---

## 7. Threats to Validity and Limitations

1. **Task Sample Size ($N = 24$ per Domain):** Both the OS benchmark and the Blocks World confirmatory benchmark evaluate 24 tasks. While sufficient to establish exact finite-state properties and observe large attenuation effects, $N=24$ provides limited statistical power to separate closely ranked sub-10B models after Holm-Bonferroni correction.
2. **Sub-10B Parameter Scale:** Evaluated models are sub-10B open models (`qwen3:8b`, `gemma2:9b`, `llama3.1:8b`, `mistral:7b-instruct`). Frontier models (GPT-4o, Claude 3.5 Sonnet) were not evaluated due to the local zero-cost mandate.
3. **Absence of Evidence vs. Equivalence:** Failure of paired permutation tests to reject the null for closely matched models reflects finite benchmark power, not evidence that models possess identical capabilities.
4. **One Domain with Behavioral Evidence:** The behavioral findings (reversal, near-tie concentration, detection loss) come from the OS benchmark only. The Blocks World study replicated the arithmetic identity but, because of floor-level model competence, neither confirmed nor refuted the other findings (§6). Generalization to other domains is untested.
5. **Internal Preregistration:** The preregistrations are internal dated protocols, not external registrations, and the second-domain analysis script cannot be shown to predate sight of the first model's outputs (§6.0). Seven deviations are listed in §6.5.
6. **Conditional Detection Estimate:** The 99.99% miss rate is a count over reference draws, conditional on the 24 frozen worlds and the frozen generations (49,995 of 50,000); it carries no generation-sampling uncertainty.

---

## 8. Conclusion

When evaluating language models on executable formal tasks with multiple valid solutions, single-reference matching introduces severe measurement error. By exhaustively enumerating valid solution spaces across 24 operating system tasks, we demonstrated that reference matching attenuates true model differences by an exact factor of $\frac{1}{|V(x)|}$, causing an exact pairwise winner reversal rate of 17.1518% and inducing a 99.99% detection loss in statistical significance testing. On this benchmark, reference-independent executable verification recovers separations that single-reference matching misses. We do not claim that the effect generalizes beyond the OS benchmark: the second-domain study was uninformative about it because the models were near floor.

---

## References

- Casola, S., Liu, Y. J., Peng, S., Kraus, O., Gatt, A., & Plank, B. (2025). References Matter: Investigating the Impact of Reference Set Variation on Summarization Evaluation. *INLG 2025*.
- Chen, M., et al. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*.
- Feng, Z., Chen, W.-X., & Zhang, B. (2026). Unmatched Does Not Mean False: Incomplete Reference Sets Can Reverse Calibration Rankings in Open-Ended Theory-of-Mind Tracking. *arXiv:2608.25654*.
- Jimenez, C. E., et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*.
- Kulshreshtha, P., Dalmia, S., & Mukherji, A. (2026). Same Output, Different Gold: Measuring How Reference Choice Moves a Multilingual Benchmark Score. *arXiv:2610.03825*.
- Levin, D. A., & Peres, Y. (2017). *Markov Chains and Mixing Times*. American Mathematical Society.
- Manski, C. F. (1989). Anatomy of the Selection Problem. *Journal of Human Resources*, 343-360.
- Mazurkiewicz, A. (1977). Concurrent Program Schemes and Their Partial Interpretations. *DAIMI Report Series*, 6(78).
- Valmeekam, K., et al. (2023). On the Planning Abilities of Large Language Models: A Critical Investigation. *NeurIPS 2023*.
