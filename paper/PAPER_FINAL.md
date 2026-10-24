# Reference-Choice Robustness in Executable Reasoning Benchmarks

**Abstract**  
Executable reasoning benchmarks evaluate model-generated trajectories by comparing them against gold reference solutions. However, in formal executable domains such as operating system task scheduling, concurrency synchronization, and deadlock avoidance, the set of semantically valid solutions \(V(x)\) is multi-valued (\(|V(x)| > 1\)). We formalize **Reference-Choice Robustness (RCR)**, a protocol that exhaustively enumerates \(V(x)\) and asks whether benchmark conclusions—model scores, pairwise model rankings, and statistical significance decisions—depend on which valid trajectory is selected as the reference. Evaluating 1,152 generations from four baseline model families across 24 executable OS tasks, we sample 50,000 benchmark-level reference vectors from the Cartesian product \(\prod_{k=1}^{24} V(x_k)\). Under uniform reference sampling, changing only the selected gold reference while holding tasks, candidate model outputs, and evaluators fixed causes substantial ranking instability (\(\text{Kendall } \tau_b = 0.618 \pm 0.351\), \(\text{SE} = 0.0016\), computed over 49,913 non-degenerate draws; 87/50,000 draws, 0.17%, had a one-constant score vector and are excluded per the predeclared degenerate-handling policy), flips pairwise model winners in **17.56%** of reference vector pairs, and recovers the \(E_3\) reference-invariant point-estimate ranking only **13.63%** of the time under normalized reference matching (\(E_2\)) and **2.86%** under strict exact matching (\(E_1\)); under the single canonical reference, by contrast, \(E_2\) reproduces the \(E_3\) ordering exactly, so the instability appears only when other valid references are used. A world-level paired sign-flip analysis over all 50,000 draws (20,000 flips, Holm-Bonferroni over 6 pairs, \(N=24\) worlds as the inferential unit; a legacy analysis had used a subsample of 200 sampled reference conditions) shows that the dominant failure is one of *detection* rather than reshuffling: the reference-independent validator \(E_3\) finds `qwen3:8b` significantly better than both `llama3.1:8b` and `mistral:7b-instruct` (Holm-adjusted \(p = 0.013\) and \(0.018\), identical under every reference choice), whereas reference-matching evaluators miss both differences in 100% (\(E_1\)) and 99.99% (\(E_2\)) of draws, retaining only 15–16% of the true gap on average. A decomposition shows that 85.6% of \(E_2\)'s winner-reversal mass lies in model pairs that \(E_3\) itself cannot separate, so the headline reversal rate is largely a near-tie phenomenon; in \(E_3\)-separated pairs the mean \(E_2\) reversal rate is 7.4%. Reversal rates are robust to curator selection bias: 17.04% under inverse structural distance weighting, 12.14% under 50% canonical bias (\(p=0.50\)), 7.35% at \(p=0.80\), and 2.30% at \(p=0.95\). The effect is heterogeneous across mechanism families (\(E_2\) reversal 21.0% for Banker's, 10.0% for synchronization, 0% for scheduling, where three of four models score zero under every evaluator). The attenuation is exact and explained by a one-line law: because every valid output equals exactly one valid reference, \(\mathbb{E}[E_2] = E_3/|V(x)|\) (\(r = 1.000\) over 42 model–task cells). Scoring an output as correct if it matches any of \(k\) sampled references restores detection of the oracle-significant differences to 48–57% at \(k=5\) and 84–88% at \(k=25\) (100% at \(k=|V(x)|\)), whereas an inverse-\(|V|\) (Horvitz–Thompson) correction removes the bias but not the variance and does not restore power (Section 4.7). Stated-convention prompts do not remove noncanonical outputs (\(\text{FRR}_{\text{norm}} = 0.625\)), and a small feasibility arm on Gemma 3 12B (\(n_{\text{valid}} = 42\)) shows the same pattern (\(\text{FRR}_{\text{norm}} = 0.619\)). Replacing gold references with a reference-independent executable validator (\(E_3\)) removes reference dependence by construction (\(\text{Kendall } \tau_b = 1.000\)); the empirical content of this study is the measured cost of not doing so. A preregistered follow-up on four Claude models that clear the capability floor (73%–99% validity) reproduces the detection failure (reference matching detects \(E_3\)-separated differences in 3.0% of draws), finds canonical-solution inflation of 2.3–3.3 times uniform choice, and raises the uniform-reference winner-reversal rate to 26.9%, while a preregistered 1.5-fold canonical ranking-distortion prediction was not met (Section 4.8). The main results come from one 24-world benchmark and four sub-10B models, and the RCR metrics are a post-hoc reanalysis of a pilot whose preregistered verdict was CONDITIONAL (Sections 9–10).

---

## 1. Introduction

Evaluation of large language models (LLMs) on multi-step reasoning tasks increasingly relies on executable benchmarks where candidate outputs can be parsed and verified against domain rules. A widespread convention in benchmark design is to select a single "canonical" reference trajectory \(R^*\) for each task specification \(x\), evaluating candidate generations \(y\) via string or sequence matching relative to \(R^*\).

However, in formal executable domains—such as process scheduling, thread synchronization, and resource allocation—many distinct trajectories satisfy all system transition rules and task constraints (for concurrency, interleavings of independent events form equivalence classes in the sense of Mazurkiewicz, 1987). When the valid solution space \(V(x)\) is multi-valued (\(|V(x)| > 1\)), choosing an arbitrary single reference trajectory as "gold" introduces an unexamined source of experimental variation: **reference identity**.

We ask a measurement question:
> *How much do an executable reasoning benchmark's scientific conclusions change solely because its gold reference trajectory is replaced by another valid trajectory from the task's complete valid-solution space \(V(x)\), while the task specifications, model outputs, and evaluators remain otherwise unchanged?*

That reference choice matters for reference-based metrics is not new (Section 8): reference-set variation is known to destabilize metric values and even system rankings in summarization (Casola et al., 2025) and radiology report generation (Jeong et al., 2026), and recent evaluators already target sets of valid solutions (Barazandeh et al., 2026; Wu et al., 2026). Our contribution is narrower and methodological:

1. **An exact-enumeration protocol.** Because \(V(x)\) is computed exhaustively and a reference-independent validator exists, reference choice can be varied as a controlled factor over the full Cartesian product \(\prod_k V(x_k)\), with the ground-truth ranking known exactly rather than estimated from human judgments.
2. **Conclusion-level metrics.** We report rank-correlation distributions, pairwise winner-reversal probabilities, oracle recovery, and—new in this version—*detection* behaviour: whether reference matching finds the differences a reference-independent test finds.
3. **Decomposition of where instability lives.** We separate reversals in statistically separated pairs from near-tie pairs and break results down by mechanism family.
4. **Mechanism and remedy.** Reference matching obeys an exact attenuation law, \(\mathbb{E}[E_2] = E_3/|V(x)|\); scoring against \(k\) references (match-any) is a practical remedy with a measured power curve, and an inverse-\(|V|\) correction is shown to remove bias but not variance (Section 4.7).
5. **Candid scoping.** The results are a controlled case study on one 24-world benchmark; Sections 9 and 10 document the pilot's CONDITIONAL preregistered verdict and all post-hoc analyses.

---

## 2. Problem Formulation & RCR Formal Framework

### 2.1 Formal Valid-Solution Space \(V(x)\)
For a task specification \(x\), let \(V(x)\) denote the complete set of executable trajectories \(y\) that satisfy formal transition rules and task constraints:

$$V(x) \triangleq \{ y \in \mathcal{Y} \mid \text{RulesCheck}(x, y) = \text{TRUE} \land \text{ConstraintsCheck}(x, y) = \text{TRUE} \}$$

Each solution in \(V(x)\) is independently verified by replaying state transitions through the domain engine (`research/simulator/validators.py`).

### 2.2 Benchmark-Level Reference Vectors
For a benchmark of \(N\) tasks \((x_1, \dots, x_N)\), a benchmark reference vector is an element of the Cartesian product:

$$\mathbf{R} = (R_1, \dots, R_N) \in \prod_{k=1}^N V(x_k)$$

The canonical reference vector \(\mathbf{R}_{\text{canonical}}\) is the deterministic trace produced by canonical ties (e.g., FCFS arrival order, lowest process ID). A uniform random reference vector is sampled independently per world: \(R_k \sim \text{Uniform}(V(x_k))\).

### 2.3 RCR Evaluation Metrics
Holding candidate outputs \(\{y_{m,k}\}\) and task semantics fixed across 50,000 sampled reference vectors \(\mathbf{R}\):

1. **Model Score**: \(S_m(E \mid \mathbf{R}) \triangleq \frac{1}{N} \sum_{k=1}^N E(y_{m,k} \mid R_k)\)
2. **Rank Correlation Stability (\(\tau_b\))**: Kendall's \(\tau_b\) between model score vectors under \(\mathbf{R}\) and \(\mathbf{R}_{\text{canonical}}\), with native tie handling:
   $$\tau_b(\mathbf{R}) = \text{KendallTauB}\left( S(\cdot \mid \mathbf{R}), S(\cdot \mid \mathbf{R}_{\text{canonical}}) \right)$$
3. **Pairwise Winner Reversal Probability**: The probability that drawing two independent reference vectors \(\mathbf{R}_1, \mathbf{R}_2\) reverses the strict pairwise winner between model \(A\) and model \(B\):
   $$P(\text{Reversal}) = \mathbb{P}_{\mathbf{R}_1, \mathbf{R}_2} \left[ \text{sign}(S_A(\mathbf{R}_1) - S_B(\mathbf{R}_1)) \cdot \text{sign}(S_A(\mathbf{R}_2) - S_B(\mathbf{R}_2)) = -1 \right]$$
4. **\(E_3\) Ranking Recovery Rate**: The fraction of reference vector draws under which evaluator \(E\)'s induced model ranking matches the \(E_3\) reference-invariant executable-validator point-estimate ranking (identical sign of every pairwise score difference, ties preserved):
   $$\text{Recovery}(E) \triangleq \mathbb{P}_{\mathbf{R} \sim \prod V(x_k)} \left[ \text{Rank}_E(\mathbf{R}) == \text{Rank}_{E_3} \right]$$
   Recovery is a descriptive measure of reproducing a *point-estimate* ordering, much of which is not statistically supported (Section 4.5).
5. **Detection Behaviour** (Section 4.4): for each model pair, the distribution over {significant A, significant B, not significant} of the world-level sign-flip test with Holm correction, compared with the \(E_3\) decision.
6. **Evaluator Effect on a Gap** (Section 4.4): for each pair, the per-world difference between the \(E_3\) gap and the reference-matching gap averaged over a uniformly random reference, with a world-level paired bootstrap (5,000 resamples) confidence interval.
7. **Attenuation Law, \(k\)-Reference Power and Correction** (Section 4.7): the prediction \(\mathbb{E}[E_2] = E_3/|V(x)|\), detection power of match-any evaluation against \(k\) sampled references, and an inverse-\(|V|\) (Horvitz–Thompson) corrected estimator.

---

## 3. Experimental Setup & Protocol

- **Domains**: 24 formal OS tasks across 3 mechanism families, following standard textbook formulations (Silberschatz et al., 2018):
  1. *CPU Scheduling*: Non-preemptive FCFS, SJF, Priority, and Round-Robin (8 worlds).
  2. *Concurrency Synchronization*: Mutex locks and Semaphore wait/signal interleavings (8 worlds).
  3. *Banker's Deadlock Avoidance*: Safe resource allocation sequences (8 worlds).
- **Baseline Models (1,152 Generations)**: `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b` (24 worlds \(\times\) 3 surface variants \(\times\) 4 seeds), temperature 0.7.
- **Stated-Convention Control (1,152 Generations)**: Identical 24 worlds and models with canonical tie-breaking rules explicitly stated in the prompt.
- **Competence/Feasibility Arm (576 Generations)**: `gemma3:12b` (12B parameters) and `olmo2:7b` (7B parameters) under stated-convention prompts.
- **Evaluator Classes**:
  - \(E_1\) **Canonical Exact Match**: Whitespace-normalized exact string comparison against selected reference \(R \in V(x)\).
  - \(E_2\) **Normalized Match**: Normalized schedule/event trajectory comparison against selected reference \(R \in V(x)\).
  - \(E_3\) **Reference-Independent Executable Semantic Validator**: Replay & constraint checker independent of \(R\).
- **Score scale.** Under \(E_3\) the four models solve 6.6%–30.9% of tasks (`qwen3:8b` 30.9%, `gemma2:9b` 17.0%, `mistral:7b-instruct` 7.6%, `llama3.1:8b` 6.6%). Under \(E_2\) with a uniformly random reference, mean scores fall to 0.5%–4.1%: a random reference rejects roughly 87% of semantically valid outputs for the strongest model. All comparisons therefore operate in a low-accuracy regime (Section 10).

---

## 4. Primary RCR Results (1,152 Baseline Generations)

### 4.1 Benchmark Identifiability & Ranking Instability
Table 1 presents the primary RCR metrics computed from 50,000 independent uniform reference vector draws sampled from \(\prod_{k=1}^{24} V(x_k)\). The canonical reference vector \(\mathbf{R}_{\text{canonical}}\) is evaluated separately as Draw 0.

#### Table 1: Primary Reference-Choice Robustness Metrics (50,000 Monte Carlo Draws)
| Evaluator Class | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b` Score | `llama3.1:8b` Score | Kendall \(\tau_b\) (Mean ± Std) | Monte Carlo SE | Pairwise Reversal Prob | \(E_3\) Ranking Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Canonical Exact** | 4.86% | 0.69% | 0.00% | 0.00% | 0.769 ± 0.301 | 0.0014 | 4.66% | **2.86%** |
| **\(E_2\) Normalized Match** | 13.19% | 2.43% | 1.74% | 0.35% | 0.618 ± 0.351 (n=49,913)† | 0.0016 | **17.56%** | **13.63%** |
| **\(E_3\) Semantic Validator** | 30.90% | 17.01% | 7.64% | 6.60% | **1.000 ± 0.000** | 0.0000 | **0.00%** | **100.0%** |

†87 draws (0.17%) excluded: one model had a constant score vector (all models tied), making τ_b undefined. Both-constant draws (0 observed) are assigned 1.0 by the degenerate-handling policy. See deviation log D5 below.

Table 1 scores are canonical-reference (Draw 0) scores. Under the canonical reference \(E_2\) ranks the models `qwen3:8b` > `gemma2:9b` > `mistral:7b` > `llama3.1:8b`, identical to the \(E_3\) ordering (the pilot report likewise found \(\tau = 1.0\) at the canonical reference), so the canonical reference is a favourable special case; instability arises when other valid references are drawn. \(E_2\) in all RCR analyses follows preregistered deviation D3(b): an output mentioning entities outside the world never counts as a match. An earlier revision omitted this rule in the RCR modules (7 `mistral:7b-instruct` outputs affected); correcting it is Deviation 9, which lists the before/after values. An independent vectorized re-implementation of the sampler (Section 4.4; different random stream) reproduces the headline statistics within Monte Carlo error (\(E_2\) reversal 17.18% vs 17.56%, uniform-baseline reproduction 17.23%; \(E_2\) \(\tau_b\) 0.616 vs 0.618; \(E_2\) recovery 13.50% vs 13.63%).

### 4.2 World-Level Sign-Flip Inference
The statistical unit is the world (\(N=24\)), with surface variants and seeds nested. For each reference vector, model pass rates are averaged within each world to yield 24 paired world-level difference observations, tested with 20,000 paired sign-flip permutations and Holm-Bonferroni step-down correction across all 6 model pairs (\(\alpha = 0.05\)).

*Legacy analysis and its correction.* The first analysis ran this test on a subsample of 200 sampled reference conditions (seed 20261005) because of its computational cost, and the manuscript summarized it as "no model pair achieves statistical significance". That summary was accurate only for \(E_1\) and \(E_2\): the same output shows two pairs significant under \(E_3\), and the summary did not separate the evaluators. Prior uncorrected reports performed McNemar testing on individual \((w, v, s)\) cells (\(N=288\)), which treated nested seeds and variants as independent observations (pseudoreplication). Both issues are repaired in Section 4.4, which evaluates all 50,000 draws for each evaluator separately.

### 4.3 Reference-Selection Distribution Sensitivity Analysis
To test whether the observed RCR instability is an artifact of uniform sampling across \(V(x)\), we evaluated 50,000 Monte Carlo benchmark reference-vector draws across alternative reference-selection distributions while holding the 1,152 candidate generations strictly frozen:

1. **Canonical Bias (\(p \in [0.0, 0.99]\))**: A benchmark curator selects the canonical reference \(R_0\) with probability \(p\) and samples uniformly from \(V(x) \setminus \{R_0\}\) with probability \(1-p\). (\(p=0\) is the non-canonical-only condition, not a uniform one.)
2. **Similarity Bias**: Valid references are weighted inversely by normalized structural distance to the canonical reference: \(w(R) = 1 / (1 + d(R, R_0))\).
3. **Adversarial Stress Condition (single draw)**: A deterministic condition selecting, per world, the reference that maximizes candidate score divergence from canonical evaluation. It yields one benchmark reference vector, so its \(\tau_b = 0.6667\) is a point value, not a distribution, and is not used for inference.

#### Table 2: Reference-Selection Distribution Sensitivity Matrix (50,000 Draws per Distribution)
| Reference Selection Distribution | Parameter | \(E_1\) Reversal | \(E_2\) Reversal | \(E_1\) \(E_3\)-Recovery | \(E_2\) \(E_3\)-Recovery | \(E_2\) Kendall \(\tau_b\) (Mean ± Std) | Valid \(\tau_b\) Draws |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Uniform Baseline (Reproduction)** | N/A | 4.67% | **17.23%** | 5.34% | 17.29% | 0.6171 ± 0.3485 | 49,916 |
| **Canonical Bias (\(p=0.00\))** | \(p=0.00\) | 6.99% | **16.86%** | 2.14% | 5.58% | 0.4972 ± 0.4003 | 49,369 |
| **Canonical Bias (\(p=0.25\))** | \(p=0.25\) | 4.25% | **14.60%** | 4.59% | 25.93% | 0.6986 ± 0.3063 | 49,911 |
| **Canonical Bias (\(p=0.50\))** | \(p=0.50\) | 1.50% | **12.14%** | 4.80% | 44.47% | 0.7839 ± 0.2526 | 49,991 |
| **Canonical Bias (\(p=0.75\))** | \(p=0.75\) | 0.29% | **8.40%** | 3.07% | 69.62% | 0.8751 ± 0.2215 | 50,000 |
| **Canonical Bias (\(p=0.80\))** | \(p=0.80\) | 0.19% | **7.35%** | 2.58% | 75.74% | 0.8964 ± 0.2096 | 50,000 |
| **Canonical Bias (\(p=0.90\))** | \(p=0.90\) | 0.04% | **4.33%** | 1.38% | 88.12% | 0.9450 ± 0.1647 | 50,000 |
| **Canonical Bias (\(p=0.95\))** | \(p=0.95\) | 0.01% | **2.30%** | 0.68% | 94.45% | 0.9724 ± 0.1211 | 50,000 |
| **Canonical Bias (\(p=0.99\))** | \(p=0.99\) | 0.00% | **0.47%** | 0.13% | 99.01% | 0.9946 ± 0.0554 | 50,000 |
| **Similarity Bias (Structural Distance)** | N/A | 4.57% | **17.04%** | 6.27% | 21.75% | 0.6451 ± 0.3340 | 49,947 |
| **Adversarial Stress Condition (single draw)** | Worst-case | 0.00% | 0.00% | 0.00% | 0.00% | 0.6667 (n=1) | 1 |

*Sensitivity Interpretation*: Increasing canonical bias attenuates ranking flips monotonically, but \(E_2\) pairwise winner reversals remain **17.04%** under structural similarity weighting, **12.14%** under 50% canonical bias (\(p=0.50\)), **7.35%** at \(p=0.80\), and **2.30%** even when 95% of reference choices are canonical (\(p=0.95\)). \(E_2\)'s recovery of the \(E_3\) ordering rises toward 99% as \(p \to 1\) because the canonical reference itself reproduces the \(E_3\) ordering (Section 4.1). The instability is therefore not an artifact of uniform sampling, but it does require that alternative valid references enter evaluation with non-negligible probability; at \(p \to 1\) it vanishes by definition. (The sensitivity grid uses uniform-over-\(V(x)\) sampling for the non-canonical mass and reuses the frozen generations; E2 reversal at \(p=0\) differs from the uniform baseline because the canonical reference is excluded.)

### 4.4 Detection: What Reference Matching Fails to Find
All results in this subsection use all 50,000 reference-vector draws (an independent vectorized sampler, seed 20261016; shared sign-flip matrix of 20,000 flips, seed 20261017; Holm correction over 6 pairs per draw; artifact `extended_analysis.json`).

#### Table 3: World-Level Significance Under Each Evaluator (All 50,000 Draws)
| Model pair | Oracle (E3) Holm-adj. p | Oracle decision | E1 mean adj. p | E1 misses | E2 mean adj. p | E2 misses |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| gemma2 vs llama3.1 | 0.1998 | n.s. | 1.000 | - | 0.991 | - |
| gemma2 vs mistral | 0.1998 | n.s. | 1.000 | - | 0.991 | - |
| gemma2 vs qwen3 | 0.1998 | n.s. | 0.992 | - | 0.946 | - |
| llama3.1 vs mistral | 0.7948 | n.s. | 1.000 | - | 0.995 | - |
| llama3.1 vs qwen3 | 0.0126 | qwen3 better | 0.991 | 100.00% | 0.929 | 99.99% |
| mistral vs qwen3 | 0.0175 | qwen3 better | 0.991 | 100.00% | 0.928 | 99.99% |

Under \(E_3\) the decision is constant across draws (the oracle does not consult the reference): `qwen3:8b` is significantly better than `llama3.1:8b` and `mistral:7b-instruct`, and no other pair is separated. Under a uniformly random reference, \(E_1\) never detects either difference and \(E_2\) detects them in 5 of 50,000 draws each. There are no wrong-direction significant results, and one spurious significant result in 50,000 draws (\(E_2\), gemma2 vs qwen3). The failure is thus a loss of power, not a reversal of sign. For context, the pilot report (`SSR_PILOT_REPORT.md`) found the same pairs at Holm \(p = 0.078\) under the single canonical reference; a random reference is substantially worse for detection than the canonical one.

A difference between "significant under one evaluator" and "not significant under another" is not itself evidence of an evaluator effect. We therefore test the effect directly: for each pair, the per-world difference between the oracle gap and the \(E_2\) gap averaged over a uniform reference, bootstrapped over worlds.

#### Table 4: Evaluator Effect on Each Pairwise Gap (Uniform Reference; 24 Worlds; 5,000 Bootstrap Resamples)
| Model pair | Oracle gap | E2 expected gap (uniform ref.) | Evaluator effect [95% world-bootstrap CI] | Gap retained by E2 |
|:---|:---:|:---:|:---:|:---:|
| gemma2 vs llama3.1 | +0.104 | +0.012 | +0.092 [+0.018, +0.176] | 12% |
| gemma2 vs mistral | +0.094 | +0.012 | +0.081 [+0.004, +0.170] | 13% |
| gemma2 vs qwen3 | -0.139 | -0.024 | -0.115 [-0.231, -0.006] | 18% |
| llama3.1 vs mistral | -0.010 | +0.000 | -0.011 [-0.060, +0.032] (spans 0) | -2% |
| llama3.1 vs qwen3 | -0.243 | -0.037 | -0.206 [-0.329, -0.090] | 15% |
| mistral vs qwen3 | -0.233 | -0.037 | -0.196 [-0.321, -0.073] | 16% |

For five of six pairs the interval excludes zero: a random gold reference compresses the true pairwise gap to 12%–18% of its oracle value. The sign of the expected gap never changes. The practical consequence is attenuation (a loss of statistical power and a compressed leaderboard) rather than systematic reordering.

### 4.5 Where the Reversals Live: Near-Tie Decomposition
A natural objection is that winner reversals merely reflect models that are indistinguishable. We test this by splitting the six pairs by whether \(E_3\) separates them (Table 3).

#### Table 5: Reversals by Oracle Separation (E2; 50,000 Draws)
| Model pair | Separated by E3? | E3 Holm-adj. p | E2 reversal prob. | E2 score tie prob. | E2 winner opposes E3 |
|:---|:---:|:---:|:---:|:---:|:---:|
| gemma2 vs llama3.1 | no | 0.1998 | 20.6% | 15.0% | 14.6% |
| gemma2 vs mistral | no | 0.1998 | 25.4% | 12.9% | 18.5% |
| gemma2 vs qwen3 | no | 0.1998 | 14.6% | 4.6% | 9.7% |
| llama3.1 vs mistral | no | 0.7948 | 27.7% | 24.9% | 42.5% |
| llama3.1 vs qwen3 | yes | 0.0126 | 7.9% | 2.6% | 4.2% |
| mistral vs qwen3 | yes | 0.0175 | 6.9% | 2.6% | 3.7% |
| **Mean, not separated (4 pairs)** | | | **22.1%** | | |
| **Mean, separated (2 pairs)** | | | **7.4%** | | |
| **Share of reversal mass in non-separated pairs** | | | **85.6%** | | |

The suspicion is largely correct: 85.6% of \(E_2\)'s reversal mass (78.6% for \(E_1\)) lies in pairs the oracle cannot separate at \(N=24\), and the reversal rate there (22.1%) is about three times that in separated pairs (7.4%). Two qualifications apply. First, "not separated" is absence of evidence at \(N=24\), not evidence of equality. Second, in the two separated pairs the reference-matching winner still opposes the oracle winner in 3.7%–4.2% of draws, and the evaluator effect on the gap is large (Table 4). We therefore state the finding as: *reference choice makes already-weak ranking evidence arbitrary and strongly attenuates the evidence that is real.* The headline 18.61% reversal rate and 23.92% "recovery" should not be read as the share of well-supported orderings that are overturned.

### 4.6 Heterogeneity Across Mechanism Families
#### Table 6: Reversal by Mechanism Family (50,000 Draws)
| Mechanism family | Worlds | E1 reversal | E2 reversal | E2 Kendall tau_b (valid draws) | E3 scores (gemma2 / llama3.1 / mistral / qwen3) |
|:---|:---:|:---:|:---:|:---:|:---|
| scheduling | 8 | 0.0% | 0.0% | 1.000 (n=41,677) | 0.000 / 0.000 / 0.000 / 0.250 |
| sync | 8 | 2.1% | 10.0% | 0.495 (n=42,333) | 0.312 / 0.073 / 0.062 / 0.490 |
| banker | 8 | 1.1% | 21.0% | 0.158 (n=47,617) | 0.198 / 0.125 / 0.167 / 0.188 |

Instability is concentrated in Banker's (21.0%) and synchronization (10.0%). Scheduling shows none, but only because three of the four models solve none of its eight worlds under any evaluator, leaving no pair to reverse; the scheduling null is uninformative. Per-family \(\tau_b\) uses the family's own canonical score vector, which is heavily tied in scheduling and synchronization (the number of draws with defined \(\tau_b\) is reported). Because each family contains only eight worlds, these are descriptive within-benchmark breakdowns, not independent replications.

### 4.7 Attenuation Law, \(k\)-Reference Evaluation and an Inverse-\(|V|\) Correction
This subsection is post-hoc (Deviation 10) and uses the same frozen generations (artifact `kref_attenuation.json`; 2,000 draws per setting; 20,000 sign flips).

**Attenuation law.** For a uniformly random reference \(R \in V(x)\), \(E_2\) passes an output iff it equals \(R\) after normalization. If every valid output equals exactly one element of \(V(x)\) and no invalid output equals any, a valid output matches with probability \(1/|V(x)|\), hence \(\mathbb{E}[E_2] = E_3/|V(x)|\) for each (task, model) cell. This holds exactly in the data: all 179 semantically valid generations match exactly one reference and none of the invalid generations matches any (Pearson \(r = 1.000\) over the 42 cells with positive \(E_3\) score; median observed/predicted ratio 1.00). The fraction of a pairwise gap that survives is therefore the \(E_3\)-gap-weighted mean of \(1/|V(x_k)|\), e.g. 15.1% for `qwen3:8b` vs `llama3.1:8b` (observed 15.1%), so attenuation is predictable from the sizes of the valid-solution spaces alone, before any model is run. The law is close to an identity once the one-match property holds; its value is that it identifies the mechanism and licenses the remedies below. It would fail in domains where distinct references can be equivalent under normalization.

**\(k\)-reference evaluation.** An output passes if it matches *any* of \(k\) uniformly sampled references (\(k = |V(x)|\) recovers \(E_3\)).

#### Table 7: Detection and Gap Retention versus Number of References \(k\) (Match-Any, 2,000 Draws per \(k\))
| \(k\) | Detect qwen3 > llama3.1 | Detect qwen3 > mistral | Gap retained (llama / mistral) | False positive, any non-separated pair | Full-ordering recovery |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 0.0% | 0.0% | 15% / 16% | 0.0% | 13.4% |
| 2 | 1.4% | 1.6% | 30% / 31% | 0.6% | 28.1% |
| 3 | 9.0% | 10.2% | 43% / 45% | 1.7% | 42.4% |
| 5 | 47.9% | 57.0% | 65% / 67% | 4.9% | 55.0% |
| 10 | 57.6% | 78.5% | 75% / 78% | 2.2% | 50.1% |
| 25 | 83.8% | 88.1% | 86% / 88% | 0.2% | 55.5% |
| 50 | 93.0% | 86.1% | 90% / 91% | 0.2% | 72.9% |
| all (\(E_3\)) | 100.0% | 100.0% | 100% / 100% | 0.0% | 100.0% |

Detection of the two oracle-significant differences rises from 0% at \(k=1\) to roughly 85% at \(k=25\), with the false-positive rate on the four non-separated pairs staying near or below the nominal 5%. Full-ordering recovery plateaus at about 50–55% for \(5 \le k \le 25\) because the `llama3.1:8b`/`mistral:7b` gap (\(-0.010\)) is too small to resolve; it is the same near-tie that dominates the reversals of Section 4.5. Curves are approximately monotone (Monte Carlo SE about 1 percentage point).

**Inverse-\(|V|\) correction.** Multiplying the mean match over \(k\) sampled references by \(|V(x)|\) is a Horvitz–Thompson estimator (Horvitz & Thompson, 1952) of the \(E_3\) score under the one-match property, and corresponds to the standard correction for regression dilution (Frost & Thompson, 2000). It is unbiased here (estimated/oracle gap 0.99–1.02) but has a large variance: the standard deviation of the estimated qwen3-vs-llama3.1 gap is 0.37 at \(k=1\), 0.21 at \(k=3\) and 0.10 at \(k=10\), against a true gap of 0.243. Detection of the two oracle-significant differences is 0.1% / 0.1% at \(k=1\), 6.5% / 9.2% at \(k=3\) and 40.2% / 31.0% at \(k=10\)—well below match-any at the same \(k\) (57.6% / 78.5%). Correcting the bias therefore does not restore power; the practical remedies are to enumerate \(V(x)\) and use a validator, or to use match-any against many references (\(k \gtrsim 25\) here).

### 4.8 Follow-up: Claude-Family Capability Ladder (Above the Floor)

The main study sits at the capability floor (Section 10, item 2). To test whether the reference-matching findings survive when models are competent, we re-ran the identical 24-world benchmark (288 prompts per model; same worlds, prompts, scorer, oracle and RCR modules) on four Claude models, `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-haiku-5-5` and `claude-sonnet-5-5`, through headless `claude -p` (no tools, thinking disabled, no settings or hooks, empty working directory). The plan and hypotheses H1–H4 were frozen in `docs/research/RCR_CLAUDE_FAMILY_PREREG.md` before any generation (an internal, SHA-256-stamped freeze, not an external registration). All 1,152 calls completed with no permanent failures. Sampling parameters are provider defaults and not controllable through the CLI, so this arm is not sampling-matched to the local-model arm; it is reported as a separate experiment, not pooled with Table 1.

**Table 8: Claude-family arm (24 worlds; 288 generations per model).**

| Model | \(E_3\) validity | \(E_2\) canonical | \(E_1\) canonical | Canonical share of valid outputs | CIF (95% world bootstrap) |
|---|---|---|---|---|---|
| claude-sonnet-5-5 | 99.3% | 55.6% | 23.3% | 55.9% | 3.30 (2.27–5.10) |
| claude-haiku-5-5 | 98.3% | 45.1% | 19.8% | 45.9% | 2.67 (2.01–3.73) |
| claude-sonnet-4-5 | 79.9% | 25.7% | 12.2% | 32.2% | 2.26 (1.36–3.58) |
| claude-haiku-4-5 | 73.3% | 32.3% | 15.3% | 44.1% | 3.11 (1.94–5.18) |

CIF is the canonical inflation factor: observed valid outputs that match the canonical reference divided by the number expected if the model chose uniformly among valid solutions, \(\sum 1/|V(x)|\) over valid outputs.

**Preregistered hypotheses, reported as outcomes.**
- **H1 (floor) supported:** 4 of 4 Claude models exceed 30% \(E_3\) validity (73.3%–99.3%), so the floor that dominated the main study is absent. Scheduling remains the hardest family for the 4.5 models (validity 39.6% and 55.2%).
- **H2 (detection loss) supported:** \(E_3\) separates 4 of 6 pairs; uniform-reference \(E_2\) detects those differences, in the correct direction and Holm-significant, in 3.0% of 50,000 draws pooled (1.7%–4.3% per pair), so the detection failure persists when models are strong. The two non-separated pairs (haiku-4.5 vs sonnet-4.5, haiku-5.5 vs sonnet-5.5) show 0.5%–0.7% spurious significance.
- **H3 (canonical inflation) supported as preregistered, with a caveat on the test:** CIF exceeds 1 for all four models (CIF = 3.30 for sonnet-5.5 down to CIF = 2.26 for sonnet-4.5), i.e. the canonical (first-enumerated) solution is produced 2.3–3.3 times more often than uniform choice among valid solutions would give. The preregistered "spread excludes 0" criterion (bootstrap of max minus min CIF, 95% CI 0.42–2.69) is **weak evidence**: the maximum minus minimum of noisy estimates is positive by construction, and the individual CIF intervals overlap heavily. We therefore claim canonical inflation above 1 for every model, and do **not** claim that models differ reliably in their canonical bias.
- **H4 (ranking distortion) not supported:** under the canonical reference, the largest distortion of an adjacent \(E_2\) versus \(E_3\) score ratio is a factor of 1.43, below the preregistered 1.5. Descriptively, canonical \(E_2\) does reverse the order of the two 4.5 models relative to \(E_3\) (haiku-4.5 above sonnet-4.5), but that pair is not separated by \(E_3\).

**Reference-choice instability above the floor.** Under uniform reference sampling (50,000 draws) \(E_2\) flips the pairwise winner in 26.9% of reference pairs (Kendall \(\tau_b = 0.472\), oracle-ordering recovery 22.6%), higher than the 17.56% of the floor-limited main study. The attenuation law holds exactly again (\(r = 1.000\) over 92 model–task cells; no valid output matches zero or more than one reference). Match-any scoring with \(k = 5\) detects the four \(E_3\)-separated pairs in 36%–44% of draws and \(k = 25\) in 51%–69% (versus 2%–5% at \(k = 1\)), so the k-reference remedy helps here but restores less power than in the main study. Outputs: `research/ssr_pilot/results/rcrc_claude/` (`hypotheses.json`, `extended_analysis.json`, `kref_attenuation.json`).

**Status.** H1–H3 are confirmed and H4 is not, in the sense of the frozen plan; but the plan is internal, the CLI deviates from the original sampling protocol, the two newest models are close to ceiling on \(E_3\) (so \(E_3\) cannot separate them), and the benchmark is still 24 worlds in one domain. We do not claim generality beyond this benchmark.

---

## 5. Stated-Convention Robustness Control

A primary reviewer objection is that models generated noncanonical valid traces simply because the prompt did not state the benchmark's canonical tie-breaking convention (e.g., FCFS process ID ordering).

Evaluating 1,152 generations under stated-convention prompts demonstrates that **disclosing canonical tie-breaking rules fails to eliminate noncanonical valid outputs**:
- Pooled False Rejection Rate under stated conventions remains high: \(\text{FRR}_{\text{norm}} = 0.625\) (95% CI: [0.443, 0.816]), compared to 0.715 [0.511, 0.891] in the original prompt arm.
- 9.5% of all stated-convention outputs (110 / 1,152) are valid-noncanonical trajectories.
- Stated conventions increase canonical exact matches slightly (from 4.4% to 5.7%), but 62.5% of semantically valid outputs remain rejected by reference-matching evaluators.

---

## 6. Small Higher-Parameter Feasibility/Consistency Arm

To evaluate whether noncanonical trajectory diversity persists in higher-parameter models, we evaluated 576 generations from `gemma3:12b` (12B parameters) and `olmo2:7b` (7B parameters) under stated-convention prompts.

Reporting the models unpooled demonstrates marked capability divergence:
- **`gemma3:12b`**: 42 semantically valid outputs (\(B = 0.146\)). Of these, 16 match canonical references and 26 are valid-noncanonical. \(\text{FRR}_{\text{norm}} = 0.619\) (95% CI: [0.440, 0.839]).
- **`olmo2:7b`**: 6 semantically valid outputs (\(B = 0.021\)). Of these, 0 match canonical references and 6 are valid-noncanonical. \(\text{FRR}_{\text{norm}} = 1.000\) (95% CI: [1.000, 1.000]).

*Capability Scope*: Unpooling confirms that noncanonical trajectory diversity persists in `gemma3:12b` (\(\text{FRR}_{\text{norm}} = 61.9\%\)). However, because `olmo2:7b` produced only 6 valid outputs (\(n_{\text{valid}} = 6\)), pooled figures (\(n_{\text{valid}} = 48\)) serve as supporting feasibility evidence and must not be used to assert general frontier-model trends. The degenerate interval for `olmo2:7b` (\([1.000, 1.000]\)) reflects the absence of any canonical match among 6 outputs, not certainty.

---

## 7. Adversarial Controlled Meta-Evaluation Analysis

Evaluating evaluators on an adversarial controlled contrast dataset of 79 real model outputs across 7 structural categories demonstrates severe proxy bias:
- **\(E_1\) Exact Match & \(E_2\) Normalized Match**: Sensitivity = **50.0%**, Specificity = **100.0%**, False Rejection Rate = **50.0%**. Pass rate on noncanonical valid solutions = **0.0%** (100% of noncanonical valid solutions rejected).
- **\(E_3\) Executable Semantic Validator**: Sensitivity = **100.0%**, Specificity = **100.0%**, FRR = **0.0%**. Pass rate on noncanonical valid solutions = **100.0%**.

*Evidence Scope Note*: \(E_3\)'s 100% accuracy on adversarial sets is tautological relative to domain specifications because \(E_3\) defines valid execution; the critical empirical finding is controlled evidence that single-reference matching evaluators reject 100% of noncanonical valid trajectories. This is an adversarial stress diagnostic and is not presented as an unbiased estimate of natural evaluator error rates.

---

## 8. Related Work & Novelty Positioning

We position RCR against five literatures; every cited work was checked against its primary source (`paper/references_verified.csv`).

1. **Reference-set variation in evaluation.** Casola et al. (2025) show that many summarization metrics are unstable under changes of the human reference set and that, for ROUGE, model rankings vary with the reference set. Jeong et al. (2026) rewrite radiology reference reports along a taxonomy of reporting practice and show that rewriting can change which system ranks first. These works establish that reference choice can alter system *rankings*, so ranking-level instability is **not** claimed as new here. What differs is the setting: they rely on human-written or LLM-rewritten references of unknown completeness, so the true ranking is not exactly known; RCR enumerates \(V(x)\) exhaustively and uses a reference-independent validator, which allows the full distribution over reference vectors and the detection analysis of Section 4.4 to be computed exactly.
2. **Evaluation against sets of valid solutions.** OTAP (Barazandeh et al., 2026) scores agent trajectories by optimal transport between an execution graph and a *set* of valid solution graphs, so valid-but-different plans are not penalized; its authors also report that strict surface metrics do better when a formal verifier exists, which is consistent with our \(E_3\). LogicGraph (Wu et al., 2026) supplies solver-verified full sets of minimal proofs and a reference-free evaluation framework for multi-path reasoning. Both are *evaluators/benchmarks* that avoid single-reference matching; neither measures how much a benchmark's conclusions change when a single gold reference is swapped, which is the diagnostic we contribute. A planning or constraint-validator literature outside LLM evaluation also checks plans without references; we do not claim novelty for reference-free verification.
3. **Robustness of benchmark conclusions to evaluation choices.** Alzahrani et al. (2024) show that minor perturbations of multiple-choice benchmarks (option order, answer-selection method) change leaderboard rankings by several places, and Li et al. (2025) propose instance-level randomization to stabilize evaluations against random factors such as few-shot choice. RCR adds a different, exactly enumerable perturbation axis—reference identity in multi-valued executable domains—rather than a new class of fragility.
4. **Executable and formal reasoning benchmarks.** PetriBench (Koussios et al., 2026), TempoBench (Holzer et al., 2025), CES (Liu et al., 2026), MechSim (Yang et al., 2026), FAX (Kim et al., 2026), and falsification-based verification (Li & Hai, 2026) evaluate state-tracking or use reference-free checkers in other domains. None, to our knowledge, treats reference identity as an experimental factor over an exhaustively enumerated valid space; we did not search exhaustively and cannot exclude unreported work.
5. **Valid-set coverage and multi-reference evaluation.** HypoSpace (Chen et al., 2026) also pairs exactly enumerated admissible sets with deterministic validators, and reports a *Recovery* metric; it asks how much of the admissible set a *model* covers, whereas RCR asks how much an *evaluator's conclusions* change with the reference chosen from that set (our "oracle recovery rate" is a different quantity and should not be confused with HypoSpace's Recovery). VTC-Bench (Le Bronnec & Yokota, 2026) shows that coverage-based and single-output evaluation can rank configurations differently, but varies the model's outputs, not the reference. Scoring against several references or taking the best match is established practice for LLM judges (the multi-reference variants of Shi et al., 2026) and for code metrics (PROBE, Nogueira et al., 2026, provides multiple reference solutions per problem), and reference-based code metrics are known to favour surface similarity over function (Dristi & Dwyer, 2025). We therefore claim the *k*-reference remedy of Section 4.7 only as a measured power curve, not as a new idea. In planning, validators such as VAL are standard instead of gold-plan matching; the premise that benchmarks score multi-valued tasks by single-reference matching is therefore a property of particular benchmarks, which we do not audit here (Section 10).

**Narrow claim.** In multi-valued executable domains with exhaustively enumerable \(V(x)\), swapping the gold reference while holding tasks, outputs, and evaluators fixed measurably degrades benchmark conclusions—mainly by hiding real differences and making near-tie orderings arbitrary—on the benchmark studied here. We make no "first" claim and no claim of generality beyond this benchmark. LLM-judge evaluators have their own documented biases (Zheng et al., 2023; Wataoka et al., 2024); \(E_3\) is a deterministic validator, not an LLM judge, and is correct only insofar as the simulator is.

---

## 9. Preregistration Status, Relation to the Pilot, and Deviations Log

**Status of the preregistration.** `docs/research/SSR_PILOT_PREREG.md` is an internal, SHA-256-stamped freeze dated 2026-10-02; it was not externally registered or independently time-stamped, and in version control it was first committed together with the first runs. We therefore describe the analysis plan as *pre-specified*, not externally preregistered.

**Relation to the pilot.** The pilot's preregistered decision rule yielded **CONDITIONAL** (K0–K3 and K5 passed; K4, "a model-level conclusion changes", failed *without adequate precision*: no stable ranking reversal under the canonical reference, and the significance change for the qwen3 pairs did not reproduce in at least 70% of world bootstraps). The pilot's follow-up conditions were models clearing a competence floor (for example at least 50% semantic validity), at least 65 worlds, and a stated-convention arm. This study ran the stated-convention arm and a small competence arm, but did **not** satisfy the competence-floor or world-count conditions. The RCR protocol (50,000-draw reference vectors, \(\tau_b\), reversal and recovery rates, the sensitivity grid, and the detection, near-tie and family analyses) was designed after the pilot data were seen and is a post-hoc reanalysis of the same frozen generations; it is exploratory and should be replicated before being treated as confirmatory.

1. **Deviation 1 (Statistical Unit Repair)**: Replaced cell-level McNemar tests with preregistered world-level paired sign-flip permutation tests (20,000 flips) and Holm-Bonferroni correction over 6 model pairs. *Impact*: Corrected pseudoreplication; eliminated false significance flip claims.
2. **Deviation 2 (Monte Carlo Draw Expansion)**: Expanded benchmark reference vector sampling from 100 to 50,000 independent uniform draws from \(\prod_{k=1}^{24} V(x_k)\), separating canonical reference Draw 0. *Impact*: Reduced Monte Carlo SE to 0.0016; proved numerical stability.
3. **Deviation 3 (Tie-Aware Ranking)**: Implemented Kendall \(\tau_b\) directly on score vectors using `scipy.stats.kendalltau(variant='b')`, removing alphabetical string tie-breaking. *Impact*: Eliminated artificial ranking flips caused by tie-breaking code.
4. **Deviation 4 (Competence Unpooling)**: Unpooled Gemma 3 12B and OLMo 2 7B reporting. *Impact*: Prevented overclaiming competence persistence from underpowered OLMo 2 outputs.
5. **Deviation 5 (Degenerate-Vector Kendall τ Policy)**: 87 of 50,000 draws (0.17%) had one model with a constant score vector, making τ_b undefined. These are excluded from the aggregate mean and tracked as `kendall_tau_n_degenerate_draws`. Both-constant draws (0 observed) are assigned 1.0 (identical ranking structure). *Impact*: Headline τ_b mean changes from 0.6167 (using 0.0 for degenerate) to 0.6177 (excluding degenerate). Effect is small (0.0011) but is disclosed. (Code comments in earlier revisions labeled this policy "D4"; D5 is the correct label.)
6. **Deviation 6 (Significance Subsampling, superseded)**: The first sign-flip stability analysis used a subsample of 200 of 50,000 reference draws (seed 20261005) because of computational cost. *Impact*: superseded by Deviation 7; the legacy result is retained in `rcr_summary.json`.
7. **Deviation 7 (Full-Draw, Per-Evaluator Significance)**: The sign-flip analysis was re-run on all 50,000 draws for each evaluator with a vectorized sampler (seed 20261016; separate stream from the legacy loop, cross-checked in Section 4.1) and a shared 20,000-flip sign matrix (seed 20261017). *Impact*: Reveals that \(E_3\) separates two pairs that \(E_1\)/\(E_2\) never separate; the earlier "no pair is significant" summary is withdrawn for \(E_3\).
8. **Deviation 8 (Post-hoc Analyses)**: The detection analysis, evaluator-effect bootstrap (5,000 resamples), near-tie decomposition, and per-family breakdown were added after the main results and are exploratory.
9. **Deviation 9 (E2 Scoring-Rule Correction, 2026-10-12)**: The pilot scorer (`scoring.py`) applies preregistered deviation D3(b)—an output that mentions entities outside the world never counts as a normalized match—but the RCR modules omitted it, so 7 `mistral:7b-instruct` outputs (sync_01 once, sync_06 twice, sync_07 four times; all surface variant v2) were counted as \(E_2\) matches. All RCR artifacts were regenerated with the rule applied. *Before → after*: \(E_2\) canonical `mistral:7b` score 3.47% → 1.74%; \(\tau_b\) 0.490 → 0.618; pairwise reversal 18.61% → 17.56%; \(E_3\) recovery 23.92% → 13.63%; uniform-baseline reversal 18.22% → 17.23%; near-tie share 86.4% → 85.6%; synchronization reversal 11.6% → 10.0%; the single-draw adversarial \(\tau_b\) 0.3333 → 0.6667. \(E_1\), \(E_3\), the detection counts and the Banker's/scheduling results are unchanged. The qualitative conclusions are unchanged, but the canonical reference now reproduces the \(E_3\) ordering (before, `mistral:7b` and `gemma2:9b` were swapped), which also removes an apparent conflict with the pilot report. The earlier numbers were produced by a bug, not a design choice, and are not retained as alternative results.
10. **Deviation 10 (Attenuation, \(k\)-Reference and Correction Analyses)**: Section 4.7 was added after the main results (seeds 20261020/20261021) and is exploratory.
11. **Deviation 11 (Claude-Family Follow-up, 2026-10-24)**: A second arm (Section 4.8) was run under `docs/research/RCR_CLAUDE_FAMILY_PREREG.md`, frozen before generation. Declared deviations from the original protocol: headless CLI with provider-default sampling, repeat index instead of sampling seed, fixed Agent-SDK preamble in context. H1–H3 supported, H4 not supported; the H3 spread criterion is weak by construction (Section 4.8). The freeze is internal and should be uploaded to OSF/AsPredicted.

---

## 10. Limitations & Threats to Validity

1. **Domain Scope**: Results are bounded to formal operating system scheduling, concurrency, and deadlock avoidance task specifications across the six tested local model families (\(\le\)13B parameters). Whether reference-choice instability extends to other domains, larger models, or natural-language task specifications is an open question not addressed by this work.
2. **Low-accuracy regime and power.** Under \(E_3\) the best model solves 30.9% of tasks and the weakest 6.6%; under random-reference \(E_2\) scores are 0.5%–4.1%. With 24 worlds and these floors, most model pairs cannot be separated by any evaluator (Table 3), per-world variance is high, and reversal rates in near-tie pairs (Table 5) mostly reflect noise amplification. The pilot's recommended competence floor (at least 50% semantic validity) and at least 65 worlds were not met.
3. **Descriptive recovery and tau.** \(E_3\)-ranking recovery and \(\tau_b\) are defined against the \(E_3\) point-estimate ordering, of which only two pairwise relations are statistically supported (Section 4.4). They quantify sensitivity of point-estimate rankings, not the overturning of established orderings.
4. **E3 is a simulator, not a human gold standard.** \(E_3\) is correct only insofar as the replay validators are; the Banker's family uses an independent state-transition enumerator (`BankerSolver` in `research/simulator/banker.py`) with a separate safety validator (`validate_banker` in `research/simulator/validators.py`), cross-validated against exhaustive permutation search for all 8 Banker specifications. Validator bugs remain a threat; \(E_3\)'s perfect scores on the adversarial set (Section 7) are tautological.
5. **No External Replication.** No clean external public benchmark with exhaustive formal valid-solution enumeration was identified. PetriBench (Petri nets) has the closest formal structure but a different domain and was not evaluated for reference-choice sensitivity. The per-family breakdown (Section 4.6) is a within-benchmark check, not a second domain.
6. **Competence Ceiling**: The highest-capability model tested is Gemma 3 12B (\(n_{\text{valid}}=42\)). OLMo 2 7B has \(n_{\text{valid}}=6\), too small for stable estimates. Larger instruction-tuned models were not evaluated due to hardware constraints (about 83 GB needed versus 78 GB free; see `airllm_feasibility.md`).
7. **Post-hoc framing.** The RCR protocol and extended analyses are a reanalysis of pilot data (Section 9); the stated-convention and competence arms are small and exploratory.
8. **Reference-distribution realism.** The sensitivity grid models curator behavior with simple parametric distributions; real curation processes are unknown.
9. **Remedy analyses are post-hoc and benchmark-specific.** The attenuation law relies on the one-match property (each valid output equals exactly one reference), which could fail where normalization makes distinct references equivalent. The \(k\)-reference power curve rests on two oracle-significant pairs among 24 worlds and four models, so the specific thresholds (for example \(k \approx 25\) for roughly 85% detection) are not transferable to other benchmarks.
10. **Corrected scoring rule.** Deviation 9 documents a bug in the RCR scoring modules found during this revision; all reported values are from the corrected pipeline, and the test suite now pins them, but any residual implementation divergence between the pilot scorer and the RCR modules would shift \(E_2\) results.
11. **Claude-family arm limitations.** Provider-default sampling and CLI preamble differ from the local-model protocol; the 5.5 models are near ceiling so \(E_3\) cannot separate them; model-version drift may change results on rerun; the "single-reference matching is prevalent" premise is not audited for planning benchmarks, where executable validators are common, so the practical reach of the findings is unverified.

---

## 11. Conclusion & Recommendations

Within this OS-domain benchmark, replacing the gold reference by another valid trajectory has two measurable consequences. First, it hides real differences: the reference-independent validator finds `qwen3:8b` significantly better than two other models under every reference choice, while single-reference matching detects this in at most 5 of 50,000 draws and retains only 12%–18% of the true pairwise gaps on average, exactly as the attenuation law \(\mathbb{E}[E_2] = E_3/|V(x)|\) predicts. Second, it makes weakly supported orderings arbitrary: pairwise winners reverse in 17.56% of reference pairs under uniform sampling and 17.04% under structural similarity weighting, although 85.6% of that reversal mass sits in pairs that the oracle itself cannot separate. A reference-independent executable validator removes reference dependence by construction (0% winner reversals, 100% recovery across all sampled reference conditions, scoped to the 50,000-draw Monte Carlo distribution over the 24-world benchmark reported here).

**Recommendations.** For multi-valued executable domains, (i) prefer executable validators over single gold references where one exists; (ii) if references must be used, enumerate or sample \(V(x)\) and report conclusion stability, including detection power, not only scores; (iii) report which pairwise comparisons are statistically supported before reporting a full ranking; (iv) where no validator exists, score against many references (match-any with \(k \gtrsim 25\) restored roughly 85% detection here) rather than correcting a single-reference score by \(|V(x)|\), which removes bias but not variance. A Claude-family follow-up above the capability floor reproduced the detection loss (3.0% detection) and showed canonical inflation (CIF 2.3–3.3), but did not meet the preregistered 1.5-fold ranking-distortion prediction (Section 4.8). Replication on a second domain with at least 65 tasks is the main outstanding step.

---

## References

1. Alzahrani, N., Alyahya, H. A., Alnumay, Y., Alrashed, S., Alsubaie, S., Almushaykeh, Y., Mirza, F., Alotaibi, N., Altwairesh, N., Alowisheq, A., Bari, M. S., & Khan, H. (2024). When Benchmarks are Targets: Revealing the Sensitivity of Large Language Model Leaderboards. *Proceedings of ACL 2024*. arXiv:2402.01781.
2. Barazandeh, B., Majumdar, S., & Michailidis, G. (2026). OTAP: Structure-Aware Optimal Transport for Evaluating Planning and Execution in Agent Trajectories. arXiv:2607.17082.
3. Casola, S., Liu, Y. J., Peng, S., Kraus, O., Gatt, A., & Plank, B. (2025). References Matter: Investigating the Impact of Reference Set Variation on Summarization Evaluation. *Proceedings of the 18th International Natural Language Generation Conference (INLG 2025)*, 274–291. arXiv:2506.14335.
4. Frost, C., & Thompson, S. G. (2000). Correcting for regression dilution bias: comparison of methods for a single predictor variable. *Journal of the Royal Statistical Society: Series A*, 163(2), 173–189.
5. Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6(2), 65–70.
6. Holzer, N., Fishell, W., Ray, B., & Santolucito, M. (2025). TempoBench: Reasoning Execution Without Causal Attribution Is Just Simulation. arXiv:2510.27544.
7. Horvitz, D. G., & Thompson, D. J. (1952). A Generalization of Sampling Without Replacement from a Finite Universe. *Journal of the American Statistical Association*, 47(260), 663–685.
8. Jeong, D. P., Li, C. Q., Hosseiny, H., Bhalla, N. M., Uyar Morency, F., Ravikumar, P., Lipton, Z. C., & Oberst, M. (2026). Reporting Practice Matters: The Impact of Reference Choice on Chest X-ray Report Evaluation. arXiv:2609.19093.
9. Kendall, M. G. (1945). The Treatment of Ties in Ranking Problems. *Biometrika*, 33(3), 239–251.
10. Kim, J., Mun, S., Lee, S., Cho, J., & Ok, J. (2026). Towards Faithful Agentic XAI: A Verification Method and an Open-World Benchmark for Better Model Faithfulness. arXiv:2605.27879.
11. Koussios, P., Jäger, B., Yao, J. H., Sridhar, A., Xiang, V., & Li, C. (2026). PetriBench: Benchmarking LLM Reasoning over Dynamic State Spaces. arXiv:2609.19883.
12. Li, H., & Hai, M. (2026). Falsification-Based Verification of LLM-Generated Optimization Models: Sound Test Batteries and Their Detection Limits. arXiv:2607.16646.
13. Li, Y., Wu, Y., Luo, Y., Sun, L., Qin, Z., Qiu, L., Cao, X., & Cai, X. (2025). Instance-level Randomization: Toward More Stable LLM Evaluations. *Findings of EMNLP 2025*, 3411–3425. arXiv:2509.12678.
14. Liu, C., Chen, Y., & Jabbarvand, R. (2026). Assessing Coherency and Consistency of Code Execution Reasoning by Large Language Models. *Proceedings of ICSE 2026*. arXiv:2510.15079.
15. Mazurkiewicz, A. (1987). Trace Theory. In *Petri Nets: Applications and Relationships to Other Models of Concurrency*, LNCS 255, 279–324. Springer.
16. Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating System Concepts* (10th ed.). John Wiley & Sons.
17. Wataoka, K., Takahashi, T., & Ri, R. (2024). Self-Preference Bias in LLM-as-a-Judge. arXiv:2410.21819.
18. Wu, Y., Zhang, L., Zhang, X., Chang, J., Li, P., Jiang, X., Hu, J., & Liu, J. (2026). LogicGraph: Benchmarking Multi-Path Logical Reasoning via Neuro-Symbolic Generation and Verification. arXiv:2602.21044.
19. Yang, Y., Li, R., & Rodríguez, A. (2026). Simulate, Reason, Decide: Scientific Reasoning with LLMs for Simulation-Driven Decision Making. arXiv:2606.04505.
20. Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *Advances in Neural Information Processing Systems 36 (Datasets and Benchmarks Track)*. arXiv:2306.05685.
21. Chen, T., Lin, Yuan, Zou, He, Goyal, Ong, & Liu (2026). HypoSpace: A Diagnostic Benchmark for Set-Valued Hypothesis Generation under Underdetermination and Sublinear Coverage Bounds. arXiv:2510.15614 (ICML 2026, PMLR 306).
22. Dristi, & Dwyer (2025). Analyzing and Mitigating Surface Bias in Code Evaluation Metrics. arXiv:2509.15397.
23. Le Bronnec, & Yokota (2026). Evaluating Multiple LLM Generations with Validated Task Coverage. arXiv:2608.24228.
24. Nogueira, Vieira, & Campos (2026). PROBE: Benchmarking Code Generation in Large Language Models. arXiv:2607.13820 (*Empirical Software Engineering*).
25. Shi, Liu, Wang, Fabbri, Joty, & Cohan (2026). References Improve LLM Alignment in Non-Verifiable Domains. arXiv:2602.16802 (ICLR 2026).
