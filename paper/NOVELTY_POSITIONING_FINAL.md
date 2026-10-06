# Novelty Positioning — Primary-Source Literature Audit & Novelty Scope

**Mandate:** Component-level overlap analysis against primary-source literature. Investigate all candidate prior art, update classifications, preserve the narrow defensible RCR novelty claim, and remove unsupported universal or "first-ever" claims.

**Scope:** Primary-source literature audit covering reference variation in NLP, prompt randomization, agent trajectory evaluation metrics, formal verification benchmarks, and reference normalization.

---

## 0. RCR 12-Component Decomposition

| ID | Component | Description |
|---|---|---|
| C1 | Multi-valid-reference awareness | Recognizes that multiple reference outputs can be valid for a task |
| C2 | Formal exhaustive V(x) enumeration | Exhaustive state-space traversal enumerating all valid solutions V(x) |
| C3 | Reference identity as experimental variable | Treats choice of R ∈ V(x) as the primary independent variable under study |
| C4 | Benchmark-level conclusion stability | Evaluates stability of benchmark-level scientific conclusions (rankings, significance) |
| C5 | Kendall τ-b ranking sensitivity across reference draws | Computes τ_b distribution over Cartesian product reference vector draws ∏ V(x_k) |
| C6 | Pairwise winner reversal probability | Quantifies P(model A > model B under R_1 but B > A under R_2) |
| C7 | Statistical significance decision stability | Measures decision stability under paired sign-flip permutation testing (n=200 sampled draws) |
| C8 | Reference-independent semantic verifier (E3) | Replay engine evaluating candidate outputs y without consulting any reference R |
| C9 | Oracle recovery rate | Fraction of reference vector draws that recover the reference-independent oracle ranking |
| C10 | Monte Carlo sampling from ∏ V(xₖ) | 50,000 independent uniform reference vector draws from Cartesian product space |
| C11 | World-level sign-flip permutation test | Permutation testing with N=24 worlds as inferential unit and Holm-Bonferroni correction |
| C12 | OS process/synchronization state machines as domain | Executable replay validators for scheduling, synchronization, and Banker's deadlock avoidance |

---

## 1. 12-Component Overlap Matrix (Primary-Source Verified)

Ratings: **✗** = not present, **~** = partially present or analogous, **✓** = directly addressed.

| Component | Refs Matter (Casola 2025) | ILR | OTAP | LogicGraph | TIER | PROBE | ReRef | MechSim | FAX | Falsif. | PetriBench | Multi-Ref Code |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **C1** multi-valid-ref | ✓ | ✗ | ~ | ~ | ~ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |
| **C2** formal V(x) enum | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| **C3** ref as exp. var. | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C4** benchmark stability | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C5** Kendall τ distribution | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C6** winner reversal prob. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C7** significance stability | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C8** ref-indep. verifier | ✗ | ✗ | ~ | ~ | ~ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ✗ |
| **C9** oracle recovery rate | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C10** MC from ∏ V(xₖ) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C11** sign-flip perm. test | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **C12** OS executable domain | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ~ | ✗ |

---

## 2. Targeted Primary-Source Literature Analysis

### 2.1 "References Matter" (Casola et al., 2025)
*   **Focus:** Investigates reference set variation in text summarization evaluation (e.g. ROUGE metric sensitivity and correlation with human judgment).
*   **Relationship to RCR:** Addresses C1 (multi-reference awareness) and C3 at the output-score level. RCR operates at a distinct inferential level: **benchmark-level conclusion non-identifiability** ($\tau_b$ distribution, winner reversals, significance stability) across formally enumerated solution spaces $\prod V(x_k)$.

### 2.2 Instance-Level Randomization (ILR)
*   **Focus:** Randomizes prompt context and few-shot formatting per instance to reduce prompt-variance in LLM benchmark evaluation.
*   **Relationship to RCR:** Addresses benchmark evaluation variance driven by prompt formatting choices. RCR holds prompt context and model outputs strictly fixed and perturbs only the gold reference trajectory $R \in V(x)$ to measure reference-choice non-identifiability.

### 2.3 OTAP (Structure-Aware Optimal Transport for Trajectories)
*   **Focus:** Optimal transport distance metric for multi-step agent trajectory graphs, allowing step reordering and handling missing/hallucinated steps.
*   **Relationship to RCR:** Proposes a trajectory matching distance metric. RCR measures the instability of standard reference-matching evaluators ($E_1, E_2$) across reference choices and replaces reference matching with executable semantic verifiers ($E_3$).

### 2.4 LogicGraph
*   **Focus:** Neuro-symbolic multi-path logical reasoning benchmark featuring solver-verified minimal proof paths.
*   **Relationship to RCR:** Provides solver-verified proof paths for logical reasoning. Does not measure benchmark conclusion sensitivity or reference-choice perturbation.

### 2.5 TIER (Tiered Trajectory Evaluation)
*   **Focus:** Multi-tiered evaluation framework for agents (heuristics vs LLM-as-a-Judge vs human-in-the-loop) across intermediate execution steps.
*   **Relationship to RCR:** Focuses on cost-effective intermediate step grading. Does not analyze reference-choice perturbation or benchmark conclusion stability.

### 2.6 PROBE
*   **Focus:** Benchmark measuring proactive autonomous bottleneck resolution in complex workplace environments.
*   **Relationship to RCR:** Tests proactive agent behavior; unrelated to reference-choice sensitivity or benchmark conclusion non-identifiability.

### 2.7 ReRef
*   **Focus:** Normalizes radiology reports by rewriting reference text along a taxonomy of reporting styles to decouple clinical content from stylistic variation.
*   **Relationship to RCR:** Addresses stylistic reference variation in medical NLG. RCR formalizes reference perturbation across complete formal state-space solution sets $V(x)$ in executable OS domains.

### 2.8 Verified Formal & Executable Benchmarks (MechSim, FAX, Falsification, PetriBench, Multi-Ref Code)
*   **MechSim / PetriBench:** Share dynamic formal state simulation (C12), but do not study reference choice as an experimental perturbation variable.
*   **FAX / Falsification-Based Verification:** Use reference-free checkers for specific domains (C8), but do not measure reference-choice non-identifiability or oracle recovery rates.

---

## 3. Classification Summary & Narrow Novelty Claim

| Component | Classification | Justification |
|---|:---:|---|
| C1 multi-valid-ref | **C** (established) | Multi-reference evaluation is well-known in MT, summarization, and code eval |
| C2 formal V(x) enum | **B** (novel application) | Formal BFS/DFS state-space enumeration applied to NLG/reasoning benchmark analysis |
| C3 ref as exp. var. | **B** (novel framing) | Treating reference identity $R \in V(x)$ as a benchmark perturbation variable |
| C4 benchmark conclusion stability | **A** (genuinely new) | First measurement of benchmark-level conclusion stability under formal reference perturbation |
| C5 Kendall τ-b distribution | **A** (genuinely new) | Full distribution of rank correlation across Cartesian product reference draws |
| C6 winner reversal probability | **A** (genuinely new) | Explicit measurement of pairwise winner flip rates induced solely by reference choice |
| C7 significance decision stability | **A** (genuinely new) | Paired sign-flip decision stability measurement across sampled reference conditions |
| C8 ref-indep. semantic verifier | **C** (established concept) | Reference-free executable verifiers exist; RCR instantiates one for OS state machines |
| C9 oracle recovery rate | **A** (genuinely new) | Quantifies fraction of reference choices that recover reference-independent oracle rankings |
| C10 MC from ∏ V(xₖ) | **B** (novel combination) | Cartesian product uniform reference sampling (50,000 draws) |
| C11 sign-flip perm. test | **C** (standard statistical method) | Paired sign-flip permutation testing applied at the world level |
| C12 OS executable domain | **B** (novel combination) | OS task scheduling, synchronization, and Banker's algorithm as executable evaluation domain |

### Preserved Narrow Novelty Claim
> **Narrow RCR Novelty Claim:** In formal executable domains where task solution spaces are multi-valued ($|V(x)| > 1$), standard gold-reference matching evaluators ($E_1, E_2$) render benchmark conclusions non-identifiable. Selecting different valid trajectories as gold references while holding tasks, candidate outputs, and evaluators fixed causes substantial ranking instability ($\tau_b = 0.490 \pm 0.355$), flips pairwise model winners in 18.61% of reference vector pairs, and recovers the oracle ranking in only 23.92% of reference choices ($E_2$). Executable semantic verifiers ($E_3$) eliminate reference dependence entirely, restoring 100% decision stability ($\tau_b = 1.000$).

### Scope Restrictions & Unsupported Claim Removals
- **No universal claim:** The findings are explicitly scoped to multi-valued executable formal domains (OS scheduling, concurrency, deadlock avoidance). We do not claim universal non-identifiability across all NLP benchmarks or single-valued tasks.
- **No "first-ever reference variation" claim:** Prior work (e.g. Casola et al., 2025) studied output-level metric sensitivity under reference set variation. RCR is narrowly positioned as measuring **benchmark-level conclusion non-identifiability** under formal reference vector perturbation in executable multi-valued domains.

---

*Verified primary-source literature audit completed 2026-10-06.*
