# Reference-Choice Robustness in Executable Reasoning Benchmarks

**Abstract**  
Executable reasoning benchmarks evaluate model-generated trajectories by comparing them against reference solutions. However, in formal domains such as operating system task scheduling, synchronization interleaving, and deadlock avoidance, the set of semantically valid solutions \(V(x)\) is multi-valued (\(|V(x)| > 1\)). In this paper, we formalize **Reference-Choice Robustness (RCR)** to evaluate whether benchmark conclusions—model accuracy, pairwise model rankings, statistical significance decisions, and failure taxonomies—depend on which valid trajectory is arbitrarily selected as the gold reference. Evaluating 1,152 generations from four baseline model families across 24 executable OS tasks, we show empirically that changing only the selected gold reference while holding tasks, model outputs, and evaluators fixed causes substantial ranking instability (\(\text{Kendall } \tau = 0.463 \pm 0.343\)), flips pairwise model winners in **18.45%** of reference pairs, and shifts statistical significance decisions (\(p < 0.05 \leftrightarrow p \ge 0.05\)) in **50.0%** of reference selections. Canonical reference matching recovers the reference-invariant semantic oracle ranking only **4.0%** of the time. Furthermore, evaluating 576 generations from stronger local models (`gemma3:12b` and `olmo2:7b`) demonstrates that false rejection of valid noncanonical trajectories remains high (pooled \(\text{FRR}_{\text{norm}} = 0.667\), 95% CI: [0.500, 0.867]), proving that reference-choice instability persists under increased capability. We demonstrate that replacing arbitrary gold references with reference-independent executable semantic oracles restores 100% decision stability (\(\text{Kendall } \tau = 1.000\)).

---

## 1. Introduction

Evaluation of large language models (LLMs) on multi-step reasoning tasks increasingly relies on executable benchmarks where outputs can be parsed and verified. A widespread convention in benchmark design is to select a single "canonical" reference trajectory \(R^*\) for each task \(x\), evaluating candidate generations \(y\) via string or sequence matching relative to \(R^*\).

However, in formal executable domains—such as process scheduling, thread synchronization, and resource allocation—many distinct trajectories satisfy all system transition rules and task constraints. When the valid solution space \(V(x)\) is multi-valued (\(|V(x)| > 1\)), choosing an arbitrary single reference trajectory as "gold" introduces an unexamined source of variation: **reference identity**.

In this work, we ask a fundamental scientific question:
> *Can an executable reasoning benchmark produce different scientific conclusions solely because its gold reference trajectory is replaced by another valid trajectory from the task's complete valid-solution space \(V(x)\), while the task, model outputs, and evaluator remain otherwise unchanged?*

We formalize Reference-Choice Robustness (RCR) as a diagnostic framework to audit benchmark identifiability. Our findings demonstrate that standard reference-matching evaluators render benchmarks non-identifiable, whereas executable semantic oracles eliminate reference dependence entirely.

---

## 2. Problem Formulation & RCR Framework

### 2.1 Formal Valid-Solution Space \(V(x)\)
For a task specification \(x\), let \(V(x)\) denote the complete set of executable trajectories \(y\) that satisfy formal transition rules and task constraints:

$$V(x) \triangleq \{ y \in \mathcal{Y} \mid \text{RulesCheck}(x, y) = \text{TRUE} \land \text{ConstraintsCheck}(x, y) = \text{TRUE} \}$$

Each solution in \(V(x)\) is independently verified by replaying actions through the domain's state transition engine.

### 2.2 Reference-Choice Robustness Metrics
Holding candidate outputs \(\{y_{m,k}\}\) and task semantics fixed, we evaluate benchmark conclusions under reference vector draws \(\mathbf{R} = (R_1, \dots, R_N) \in \prod_{k=1}^N V(x_k)\):

1. **Model Score**: \(S_m(E \mid \mathbf{R}) \triangleq \frac{1}{N} \sum_{k=1}^N E(y_{m,k} \mid R_k)\)
2. **Rank Correlation Stability**: Kendall's \(\tau\) between model rankings induced by \(\mathbf{R}\) and the canonical reference vector \(\mathbf{R}_{\text{canonical}}\):
   $$\tau_{\text{mean}} = \mathbb{E}_{\mathbf{R} \sim \mathcal{U}(V(x))} \left[ \tau\left(\text{Rank}_E(\mathbf{R}), \text{Rank}_E(\mathbf{R}_{\text{canonical}})\right) \right]$$
3. **Pairwise Winner Reversal Probability**:
   $$P(\text{Reversal}) = \mathbb{P}_{\mathbf{R}_1, \mathbf{R}_2} \left[ \text{Winner}_{A,B}(\mathbf{R}_1) \neq \text{Winner}_{A,B}(\mathbf{R}_2) \right]$$
4. **Oracle Recovery Rate \(RCR(E)\)**:
   $$RCR(E) \triangleq \mathbb{P}_{\mathbf{R} \sim \mathcal{U}(V(x))} \left[ \text{Rank}_E(\mathbf{R}) == \text{Rank}_{\text{oracle}} \right]$$

---

## 3. Experimental Setup

- **Domains**: 24 formal OS tasks across 3 families:
  1. *CPU Scheduling*: Non-preemptive FCFS, SJF, Priority, and Round-Robin (8 worlds).
  2. *Concurrency Synchronization*: Mutex locks and Semaphore wait/signal interleavings (8 worlds).
  3. *Banker's Deadlock Avoidance*: Safe resource allocation sequences (8 worlds).
- **Baseline Models (1,152 Generations)**: `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b`.
- **Stronger Models (576 Generations)**: `gemma3:12b` (12B model) and `olmo2:7b` (OLMo 2 architecture).
- **Evaluator Classes**:
  - \(E_1\) **Canonical Exact Match**: Strict string comparison against selected reference \(R \in V(x)\).
  - \(E_2\) **Normalized Match**: Normalized schedule/event trajectory comparison against selected reference \(R \in V(x)\).
  - \(E_3\) **Executable Semantic Oracle**: Reference-invariant replay & constraint checker.

---

## 4. Primary Results

### 4.1 Benchmark Identifiability & Ranking Instability
Table 1 presents the primary RCR metrics evaluated on 1,152 baseline model generations across all valid reference selections in \(V(x)\).

#### Table 1: Primary Reference-Choice Robustness Metrics (Baseline 1,152 Generations)
| Evaluator Class | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b-instruct` Score | `llama3.1:8b` Score | Kendall \(\tau\) Stability | Pairwise Reversal Prob | Oracle Recovery Rate \(RCR(E)\) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Canonical Exact** | 4.86% | 0.69% | 0.00% | 0.00% | 0.820 ± 0.396 | 5.39% | **4.0%** |
| **\(E_2\) Normalized Match** | 13.19% | 2.43% | 3.47% | 0.35% | 0.463 ± 0.343 | **18.45%** | **28.0%** |
| **\(E_3\) Semantic Oracle** | 30.90% | 17.01% | 7.64% | 6.60% | **1.000 ± 0.000** | **0.00%** | **100.0%** |

### 4.2 Statistical Significance Decision Flips
Evaluating paired McNemar / Binomial tests (\(\alpha = 0.05\)) across valid reference choices reveals extreme decision instability:
- For `gemma2:9b` vs `qwen3:8b` under \(E_2\): **50.0% of valid reference choices yield a statistically significant difference (\(p < 0.05\))**, while **50.0% yield a non-significant result (\(p \ge 0.05\))**.
- For `llama3.1:8b` vs `qwen3:8b`: **50.0% significant**, **50.0% non-significant**.

### 4.3 Stronger-Model Replication
Evaluated on 576 completed generations from stronger local models (`gemma3:12b` and `olmo2:7b`), normalized reference matching exhibits a pooled False Rejection Rate of **66.7%** (95% CI: [0.500, 0.867]). Increased model capability does not eliminate noncanonical trajectory diversity, proving that reference-choice instability is a structural property of reference-matching evaluators rather than a weak-model artifact.

---

## 5. Adversarial & Meta-Evaluation Analysis

Evaluating evaluators on a controlled contrast dataset of 79 real model outputs demonstrates severe proxy bias:
- **\(E_1\) Exact Match & \(E_2\) Normalized Match**: False Rejection Rate (FRR) = **50.0%**. Pass rate on noncanonical valid solutions = **0.0%** (100% of noncanonical valid solutions rejected).
- **\(E_3\) Semantic Oracle**: Sensitivity = 100.0%, Specificity = 100.0%, FRR = 0.0%, Accuracy = 100.0%.
- *Tautology Note*: \(E_3\)'s 100% accuracy on adversarial sets is tautological relative to the domain specification because \(E_3\) defines valid execution; the critical empirical finding is that \(E_1\) and \(E_2\) reject 100% of noncanonical valid trajectories.

---

## 6. Discussion & Limitations

### 6.1 Benchmark Design Implications
Benchmark creators must not rely on single gold reference trajectories when evaluating multi-valued executable tasks. Reference-matching evaluators introduce systematic error, underestimating model competence and creating non-identifiable rankings.

### 6.2 Bounded Scope & Limitations
- The semantic oracle is reference-invariant relative to the formal task specification; it is not claimed to be philosophically absolute beyond formal domain rules.
- Results are bounded to the OS domain execution tasks and tested model families.

---

## 7. Conclusion
Evaluating executable reasoning models against arbitrary gold references compromises benchmark identifiability. Replacing reference matching with reference-independent executable semantic oracles restores 100% decision stability and eliminates reference-choice bias.
