# Reference-Choice Robustness in Executable Reasoning Benchmarks

**Abstract**  
Executable reasoning benchmarks evaluate model-generated trajectories by comparing them against gold reference solutions. However, in formal executable domains such as operating system task scheduling, concurrency synchronization, and deadlock avoidance, the set of semantically valid solutions \(V(x)\) is multi-valued (\(|V(x)| > 1\)). In this paper, we formalize **Reference-Choice Robustness (RCR)** to evaluate whether benchmark conclusions—model scores, pairwise model rankings, statistical significance decisions, and failure taxonomies—depend on which valid trajectory is selected as the reference. Evaluating 1,152 generations from four baseline model families across 24 executable OS tasks, we sample 50,000 benchmark-level reference vectors from the Cartesian product \(\prod_{k=1}^{24} V(x_k)\). We demonstrate empirically that changing only the selected gold reference while holding tasks, candidate model outputs, and evaluators fixed causes substantial ranking instability (\(\text{Kendall } \tau_b = 0.490 \pm 0.355\), \(\text{SE} = 0.0016\), computed over 49,914 non-degenerate draws; 86/50,000 draws, 0.17%, had a one-constant score vector and are excluded per the predeclared degenerate-handling policy), flips pairwise model winners in **18.61%** of reference vector pairs, and recovers the oracle model ranking only **23.92%** of the time under normalized reference matching (\(E_2\)) and **2.86%** under strict exact matching (\(E_1\)). Applying the preregistered world-level paired sign-flip permutation test (20,000 sign flips, Holm-Bonferroni corrected over 6 model pairs evaluated over a subsample of 200 sampled reference conditions) reveals that world-level variance dominates pairwise model differences. Furthermore, evaluating stated-convention prompts shows that disclosing canonical tie-breaking rules fails to eliminate noncanonical outputs (\(\text{FRR}_{\text{norm}} = 0.625\)), and unpooled evaluation on Gemma 3 12B (\(n_{\text{valid}} = 42\)) confirms that noncanonical trajectory generation persists under increased capability (\(\text{FRR}_{\text{norm}} = 0.619\)). Replacing arbitrary gold references with reference-independent executable semantic validators (\(E_3\)) eliminates reference dependence entirely, restoring 100% decision stability (\(\text{Kendall } \tau_b = 1.000\)).

---

## 1. Introduction

Evaluation of large language models (LLMs) on multi-step reasoning tasks increasingly relies on executable benchmarks where candidate outputs can be parsed and verified against domain rules. A widespread convention in benchmark design is to select a single "canonical" reference trajectory \(R^*\) for each task specification \(x\), evaluating candidate generations \(y\) via string or sequence matching relative to \(R^*\).

However, in formal executable domains—such as process scheduling, thread synchronization, and resource allocation—many distinct trajectories satisfy all system transition rules and task constraints. When the valid solution space \(V(x)\) is multi-valued (\(|V(x)| > 1\)), choosing an arbitrary single reference trajectory as "gold" introduces an unexamined source of experimental variation: **reference identity**.

In this work, we ask a fundamental scientific question:
> *Can an executable reasoning benchmark produce different scientific conclusions solely because its gold reference trajectory is replaced by another valid trajectory from the task's complete valid-solution space \(V(x)\), while the task specifications, model outputs, and evaluators remain otherwise unchanged?*

We formalize Reference-Choice Robustness (RCR) as a controlled benchmark-level perturbation framework. Our findings demonstrate that standard reference-matching evaluators render benchmarks non-identifiable, whereas reference-independent executable semantic validators eliminate reference dependence entirely.

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
4. **Oracle Recovery Rate**: The fraction of reference vector draws under which evaluator \(E\)'s induced model ranking matches the reference-independent semantic oracle ranking:
   $$\text{Recovery}(E) \triangleq \mathbb{P}_{\mathbf{R} \sim \prod V(x_k)} \left[ \text{Rank}_E(\mathbf{R}) == \text{Rank}_{\text{oracle}} \right]$$

---

## 3. Experimental Setup & Protocol

- **Domains**: 24 formal OS tasks across 3 mechanism families:
  1. *CPU Scheduling*: Non-preemptive FCFS, SJF, Priority, and Round-Robin (8 worlds).
  2. *Concurrency Synchronization*: Mutex locks and Semaphore wait/signal interleavings (8 worlds).
  3. *Banker's Deadlock Avoidance*: Safe resource allocation sequences (8 worlds).
- **Baseline Models (1,152 Generations)**: `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b` (24 worlds \(\times\) 3 surface variants \(\times\) 4 seeds).
- **Stated-Convention Control (1,152 Generations)**: Identical 24 worlds and models with canonical tie-breaking rules explicitly stated in the prompt.
- **Competence Pilot (576 Generations)**: `gemma3:12b` (12B parameters) and `olmo2:7b` (7B parameters) under stated-convention prompts.
- **Evaluator Classes**:
  - \(E_1\) **Canonical Exact Match**: Whitespace-normalized exact string comparison against selected reference \(R \in V(x)\).
  - \(E_2\) **Normalized Match**: Normalized schedule/event trajectory comparison against selected reference \(R \in V(x)\).
  - \(E_3\) **Reference-Independent Executable Semantic Validator**: Replay & constraint checker independent of \(R\).

---

## 4. Primary RCR Results (1,152 Baseline Generations)

### 4.1 Benchmark Identifiability & Ranking Instability
Table 1 presents the primary RCR metrics computed from 50,000 independent uniform reference vector draws sampled from \(\prod_{k=1}^{24} V(x_k)\). The canonical reference vector \(\mathbf{R}_{\text{canonical}}\) is evaluated separately as Draw 0.

#### Table 1: Primary Reference-Choice Robustness Metrics (50,000 Monte Carlo Draws)
| Evaluator Class | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b` Score | `llama3.1:8b` Score | Kendall \(\tau_b\) (Mean ± Std) | Monte Carlo SE | Pairwise Reversal Prob | Oracle Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Canonical Exact** | 4.86% | 0.69% | 0.00% | 0.00% | 0.707 ± 0.357 | 0.0016 | 4.66% | **2.86%** |
| **\(E_2\) Normalized Match** | 13.19% | 2.43% | 3.47% | 0.35% | 0.490 ± 0.355 (n=49,914)† | 0.0016 | **18.61%** | **23.92%** |
| **\(E_3\) Semantic Validator** | 30.90% | 17.01% | 7.64% | 6.60% | **1.000 ± 0.000** | 0.0000 | **0.00%** | **100.0%** |

†86 draws (0.17%) excluded: one model had a constant score vector (all models tied), making τ_b undefined. Both-constant draws (0 observed) are assigned 1.0 by the degenerate-handling policy. See deviation log D4 in the preregistration supplement.

### 4.2 Preregistered Statistical Inference (World-Level Sign-Flip Permutation)
Following the frozen preregistration, the statistical unit is the world (\(N=24\)), with surface variants and seeds nested. For each reference vector, model pass rates are averaged within each world to yield 24 paired world-level difference observations.

Running 20,000 paired sign-flip permutations with Holm-Bonferroni step-down correction across all 6 model pairs evaluated over a subsample of 200 sampled reference conditions (due to the computational cost of 20,000 permutations per draw) reveals that **world-level variance dominates pairwise model differences**. Across 100% of these 200 sampled reference conditions, no model pair achieves statistical significance at \(\alpha = 0.05\) after Holm correction.

*Correction Note*: Prior uncorrected reports performed McNemar testing on individual \((w, v, s)\) cells (\(N=288\)), which treated nested seeds and variants as independent observations (pseudoreplication) and artificially reported "50% significance decision flips". World-level inference correctly reflects sample uncertainty and shows that pairwise model differences on this 24-world benchmark cannot be asserted as statistically significant under any reference choice.

---

## 5. Stated-Convention Robustness Control

A primary reviewer objection is that models generated noncanonical valid traces simply because the prompt did not state the benchmark's canonical tie-breaking convention (e.g., FCFS process ID ordering).

Evaluating 1,152 generations under stated-convention prompts demonstrates that **disclosing canonical tie-breaking rules fails to eliminate noncanonical valid outputs**:
- Pooled False Rejection Rate under stated conventions remains high: \(\text{FRR}_{\text{norm}} = 0.625\) (95% CI: [0.443, 0.816]), compared to 0.715 [0.511, 0.891] in the original prompt arm.
- 9.5% of all stated-convention outputs (110 / 1,152) are valid-noncanonical trajectories.
- Stated conventions increase canonical exact matches slightly (from 4.4% to 5.7%), but 62.5% of semantically valid outputs remain rejected by reference-matching evaluators.

---

## 6. Model Competence & Capability Analysis

To evaluate whether noncanonical trajectory diversity persists in more capable models, we evaluated 576 generations from `gemma3:12b` (12B parameters) and `olmo2:7b` (7B parameters) under stated-convention prompts.

Reporting the models unpooled demonstrates marked capability divergence:
- **`gemma3:12b`**: 42 semantically valid outputs (\(B = 0.146\)). Of these, 16 match canonical references and 26 are valid-noncanonical. \(\text{FRR}_{\text{norm}} = 0.619\) (95% CI: [0.440, 0.839]).
- **`olmo2:7b`**: 6 semantically valid outputs (\(B = 0.021\)). Of these, 0 match canonical references and 6 are valid-noncanonical. \(\text{FRR}_{\text{norm}} = 1.000\) (95% CI: [1.000, 1.000]).

*Capability Scope*: Unpooling proves that noncanonical trajectory diversity persists in `gemma3:12b` (\(\text{FRR}_{\text{norm}} = 61.9\%\)). However, because `olmo2:7b` was exceptionally weak (\(n_{\text{valid}} = 6\)), pooled figures (\(n_{\text{valid}} = 48\)) must not be used to assert general frontier-model trends.

---

## 7. Adversarial & Meta-Evaluation Analysis

Evaluating evaluators on a controlled contrast dataset of 79 real model outputs across 7 structural categories demonstrates severe proxy bias:
- **\(E_1\) Exact Match & \(E_2\) Normalized Match**: Sensitivity = **50.0%**, Specificity = **100.0%**, False Rejection Rate = **50.0%**. Pass rate on noncanonical valid solutions = **0.0%** (100% of noncanonical valid solutions rejected).
- **\(E_3\) Executable Semantic Validator**: Sensitivity = **100.0%**, Specificity = **100.0%**, FRR = **0.0%**. Pass rate on noncanonical valid solutions = **100.0%**.

*Tautology Note*: \(E_3\)'s 100% accuracy on adversarial sets is tautological relative to domain specifications because \(E_3\) defines valid execution; the critical empirical finding is that reference-matching evaluators reject 100% of noncanonical valid trajectories.

---

## 8. Related Work & Novelty Audit

We position Reference-Choice Robustness (RCR) within the broader literature on benchmark reliability, reference sensitivity, and execution verification:

1. **Reference Sensitivity & Metric Variance in NLP**: Reference set sensitivity at the individual output metric level is well-documented in natural language generation and open-ended text evaluation. Casola et al. (*References Matter*, INLG 2025) demonstrated that ROUGE and BLEU scores vary significantly across human reference sets in summarization. Similarly, LLM-as-a-Judge frameworks exhibit sensitivity to prompt formatting, few-shot demonstration choice, and judge persona (Zheng et al., NeurIPS 2024; Wataoka et al., 2024). In RAG evaluation, Tamber et al. (2025) and Cruz Blandon et al. (2025) showed that hallucination and faithfulness metrics fluctuate depending on reference phrasing. **Novelty Distinction**: RCR does not claim that reference variation at the score level is unknown. Rather, RCR investigates formal executable domains where task valid-solution spaces \(V(x)\) are mathematically exact and enumerable. The primary claimed contribution is the formal Cartesian product reference perturbation framework across \(\prod_{k=1}^N V(x_k)\) and the measurement of **benchmark-level conclusion propagation**—specifically proving how reference identity alone induces pairwise winner reversals, rank correlation decay (\(\tau_b = 0.490\)), and oracle ranking divergence.

2. **Agent Trajectory & Intermediate Reasoning Evaluation**: Recent benchmarks have shifted from final-answer matching to multi-step reasoning trace evaluation. *TRACE* (Wang et al., 2026) and *CES* (ICSE 2026) evaluate step-by-step intermediate program execution states; *OTAP* (Chen et al., 2024) introduces optimal transport distance for agent trajectory graphs; and *LogicGraph* (Li et al., 2024) evaluates solver-verified proof paths. **Novelty Distinction**: Whereas trajectory benchmarks typically propose matching metrics against single trajectories or heuristic graph distances, RCR provides a meta-evaluation diagnostic framework demonstrating that any single-reference trajectory matching evaluator (\(E_1, E_2\)) renders multi-valued executable benchmarks non-identifiable.

3. **Formal Verification & Executable Simulators**: In formal domains, benchmarks like *PetriBench* (2026) and *TempoBench* (2026) evaluate dynamic state reasoning via solvers (TINA, SYNTCOMP), and *Falsification-Based Verification* (2026) evaluates optimization models via HiGHS solvers. RCR establishes that within operating system task execution, replacing arbitrary reference comparison with reference-independent executable semantic validators (\(E_3\)) completely eliminates reference dependence, restoring 100% decision stability.

---

## 9. Preregistration Deviations Log

In accordance with Section 0 rules, all post-preregistration implementation changes are documented below:

1. **Deviation 1 (Statistical Unit Repair)**: Replaced cell-level McNemar tests with preregistered world-level paired sign-flip permutation tests (20,000 flips) and Holm-Bonferroni correction over 6 model pairs. *Impact*: Corrected pseudoreplication; eliminated false significance flip claims.
2. **Deviation 2 (Monte Carlo Draw Expansion)**: Expanded benchmark reference vector sampling from 100 to 50,000 independent uniform draws from \(\prod_{k=1}^{24} V(x_k)\), separating canonical reference Draw 0. *Impact*: Reduced Monte Carlo SE to 0.0016; proved numerical stability.
3. **Deviation 3 (Tie-Aware Ranking)**: Implemented Kendall \(\tau_b\) directly on score vectors using `scipy.stats.kendalltau(variant='b')`, removing alphabetical string tie-breaking. *Impact*: Eliminated artificial ranking flips caused by tie-breaking code.
4. **Deviation 4 (Competence Unpooling)**: Unpooled Gemma 3 12B and OLMo 2 7B reporting. *Impact*: Prevented overclaiming competence persistence from underpowered OLMo 2 outputs.
5. **Deviation 5 (Degenerate-Vector Kendall τ Policy)**: 86 of 50,000 draws (0.17%) had one model with a constant score vector, making τ_b undefined. These are excluded from the aggregate mean and tracked as `kendall_tau_n_degenerate_draws`. Both-constant draws (0 observed) are assigned 1.0 (identical ranking structure). *Impact*: Headline τ_b mean changes from 0.4893 (using 0.0 for degenerate) to 0.4901 (excluding degenerate). Effect is small (0.0008) but is disclosed.
6. **Deviation 6 (Significance Subsampling)**: The sign-flip stability analysis (K4, significance flip rate) uses a subsample of 200 of 50,000 reference draws (seed 20261005) rather than all 50,000, due to computational cost of 20,000-flip permutation tests per draw. The primary τ distribution and reversal probability use all 50,000 draws. *Impact*: Significance stability estimates are based on 200 sampled reference conditions, not the full distribution; this is a stability check, not the primary claim.

---

## 10. Limitations & Threats to Validity

1. **Domain Scope**: Results are bounded to formal operating system scheduling, concurrency, and deadlock avoidance task specifications across the six tested local model families (\(\le\)13B parameters). Whether reference-choice instability extends to other domains, larger models, or natural-language task specifications is an open question not addressed by this work.
2. **Banker's Validator Architecture**: The Banker's deadlock-avoidance family uses an independent state-transition enumerator (`BankerSolver` in `research/simulator/banker.py`) with memoized path counting and canonical DFS traversal, paired with an independent step-by-step safety validator (`validate_banker` in `research/simulator/validators.py`). Both implementations are cross-validated against exhaustive brute-force permutation search across all 8 Banker task specifications, establishing architectural parity with the scheduling and concurrency simulators.
3. **Validator Implementation Risk**: The reference-independent executable semantic validator relies on formal state transition checkers. While verified for reference independence and tested against ground-truth enumerators, validator bugs remain a potential threat.
4. **No External Benchmark**: No clean external public benchmark with exhaustive formal valid-solution enumeration was identified that could serve as an independent replication domain within the scope of this study. PetriBench (Petri nets) has the closest formal structure but uses a different domain and has not been evaluated for reference-choice sensitivity. This absence is a limitation; the RCR framework's scope is bounded to the 24-world OS benchmark reported here.
5. **Competence Ceiling**: The highest-capability model tested is Gemma 3 12B (\(n_{\text{valid}}=42\)). OLMo 2 7B has \(n_{\text{valid}}=6\), which is too small for stable population estimates. Larger model families and instruction-tuned frontier models were not evaluated due to hardware and network constraints (see `airllm_feasibility.md`).

---

## 11. Conclusion & Recommendations

Evaluating executable reasoning models against arbitrary gold reference trajectories compromises benchmark identifiability. Within this OS-domain benchmark, reference-matching evaluators flip pairwise model winners in 18.61% of valid reference draw pairs. Replacing arbitrary gold references with reference-independent executable semantic validators eliminates reference bias entirely within this benchmark, with 0% winner reversals and 100% oracle recovery across all sampled reference conditions (scoped to the 50,000-draw Monte Carlo distribution over the 24-world OS benchmark reported here).

---

## References

1. Casola, S., Lavelli, A., & Novikova, J. (2025). References Matter: Benchmark Sensitivity in Natural Language Generation Evaluation. *Proceedings of the 18th International Natural Language Generation Conference (INLG 2025)*.
2. Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Xing, E. P., & Zhang, H. (2024). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *Advances in Neural Information Processing Systems (NeurIPS 2024)*, 36.
3. Wang, Z., Zhang, Y., & Liu, T. (2026). TRACE: Execution-Grounded Reasoning Trajectory Evaluation. *arXiv preprint arXiv:2601.07506*.
4. Chen, X., Gao, J., & Song, D. (2024). OTAP: Optimal Transport for Step-by-Step Agent Trajectory Matching. *arXiv preprint arXiv:2408.12885*.
5. Li, H., Zhao, M., & Wang, Y. (2024). LogicGraph: Solver-Verified Multi-Path Reasoning Benchmarks. *arXiv preprint arXiv:2410.15079*.
6. Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). *Operating System Concepts* (10th ed.). John Wiley & Sons.
7. Mazurkiewicz, A. (1987). Trace Theory. *Petri Nets: Applications and Relationships to Other Models of Concurrency*, Lecture Notes in Computer Science, 255, 279–324. Springer.
8. Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6(2), 65–70.
9. Kendall, M. G. (1945). The Treatment of Ties in Ranking Problems. *Biometrika*, 33(3), 239–251.
10. Srivastava, A., et al. (2023). Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models. *Transactions on Machine Learning Research (TMLR)*.

