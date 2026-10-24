# Preregistration Protocol: Second-Domain Replication of Reference-Choice Robustness

**Repository:** OS-Tutor-RAG / Reference-Choice Robustness (RCR)  
**Date:** October 2026  
**Document Status:** Formal Preregistered Replication Protocol  
**Domain:** Discrete Deterministic Planning (Blocks World & State-Space Navigation)  
**Target Purpose:** Test whether RCR mechanisms (Attenuation Law, Near-Tie Concentration, and Detection Loss) replicate in a second enumerable formal domain.

---

## 1. Motivation and Domain Selection Rationale

The primary RCR benchmark evaluates 24 tasks from operating systems (CPU scheduling, synchronization, and Banker's deadlock avoidance). While these worlds provide an exact valid-solution space $V(x)$ via domain-specific verifiers, evaluating a single domain leaves open whether the observed phenomena are idiosyncratic to OS simulators.

To establish external validity, a second domain must satisfy five strict criteria:
1. **Trustworthy Deterministic Oracle**: An executable verifier based on formal state-transition semantics, eliminating LLM-as-a-judge subjectivity.
2. **Exhaustive Valid-Space Enumeration**: A guarantee that the reference set $V(x)$ contains *all* valid minimal solutions, rather than a single arbitrary planner output.
3. **Cardinality Variation**: Benchmark tasks must span varying valid-space sizes ($|V_i| \in [1, 20+]$) to test the $\frac{1}{|V_i|}$ attenuation law.
4. **Non-Trivial Model Competence**: Models must achieve a non-zero semantic pass rate to avoid floor effects.
5. **Deterministic Reproducibility**: Self-contained generation and evaluation without proprietary, paid APIs.

### Domain Choice: Discrete Classical Planning (Blocks World & Grid Navigation)
We select **Discrete Classical Planning** formulated as finite-state transition systems $(S, A, T, s_0, G)$:
- Preconditions and effects are deterministic STRIPS operators.
- **Oracle Verification**: A plan $\pi = (a_1, \dots, a_k)$ is valid if and only if each action $a_t$ is executable in state $s_{t-1}$ and the final state satisfies $s_k \models G$.
- **Complete Valid Space Enumeration (All Shortest Valid Paths)**: Because unrestricted action sequences with cycles are countably infinite, the declared reference space $V(x)$ is formally defined as the set of **all shortest valid paths** from $s_0$ to $G$. An exact all-shortest-paths Breadth-First Search (BFS) over the state transition graph provably discovers $V(x)$ exhaustively.

---

## 2. Benchmark Specification

### 2.1 Task Suite ($N = 24$ Planning Tasks)
The suite consists of 24 distinct planning problems structured into three cardinality tiers:
- **Tier 1: Unique-Solution Tasks (8 tasks, $|V_i| = 1$):** Direct sequence problems where preconditions strictly enforce a unique action order (e.g., single-tower inverted restack).
- **Tier 2: Commutative Sub-Goal Tasks (8 tasks, $|V_i| \in [2, 6]$):** Problems containing independent sub-goals (e.g., moving block A onto B, and moving block C onto D, where operations commute).
- **Tier 3: High-Permutation Tasks (8 tasks, $|V_i| \in [8, 24]$):** Problems with multiple independent clear/unstack operations and parallel target locations.

### 2.2 Formal State Model
For Blocks World with blocks $\mathcal{B}$:
- State predicates: $\text{On}(x, y)$, $\text{OnTable}(x)$, $\text{Clear}(x)$, $\text{Holding}(x)$, $\text{ArmEmpty}$.
- Operators: $\text{Pickup}(x)$, $\text{Putdown}(x)$, $\text{Stack}(x, y)$, $\text{Unstack}(x, y)$.
- All state transitions $s' = T(s, a)$ are executed in pure Python with zero external solver dependencies.

---

## 3. Evaluators and Hypotheses

### 3.1 Evaluators
1. **$E_1$ (Strict String Match)**: Candidate plan matches formatted reference string character-for-character.
2. **$E_2$ (Action-Sequence Match)**: Candidate plan matches reference action tuple $(a_1, \dots, a_k)$ under whitespace and operator normalization.
3. **$E_3$ (Semantic State Oracle)**: Plan is executed against state transition model; evaluates whether goal $G$ is reached without illegal actions, completely independent of reference selection.

### 3.2 Preregistered Confirmatory Hypotheses

| Hypothesis | Description | Mathematical Criterion | Confirmatory Threshold |
|---|---|---|---|
| **H1 (Attenuation Law)** | Expected reference-match score on task $i$ under uniform reference selection equals semantic success divided by $|V_i|$. | $\mathbb{E}[S_{mi}^{E2}] = \frac{S_{mi}^{E3}}{|V_i|}$ | Pearson $r \ge 0.98$ across non-zero cells; median ratio $\in [0.95, 1.05]$. |
| **H2 (Ranking Instability)** | Changing reference choice while holding candidate plans fixed induces pairwise winner reversals under $E_2$. | Reversal probability $P_{\mathrm{rev}} = \frac{1}{\binom{|\mathcal{M}|}{2}} \sum_{A < B} 2 p_+ p_-$ | Mean pairwise reversal rate $\ge 8.0\%$. |
| **H3 (Near-Tie Concentration)** | Reversals are disproportionately concentrated in model pairs that the semantic oracle $E_3$ cannot separate. | Share of reversal mass in $E_3$-unseparated pairs: $\frac{\sum_{\text{unsep}} \mathrm{Rev}}{\sum_{\text{all}} \mathrm{Rev}}$ | $\ge 70.0\%$ of total reversal mass. |
| **H4 (Detection Loss)** | For model pairs significantly separated by $E_3$ ($p_{\text{adj}} < 0.05$), single-reference matching fails to detect significance in the vast majority of draws. | Miss rate under $E_2$ over 50,000 draws: $P(\text{fail to reject } H_0)$ | $\ge 90.0\%$ of draws have Holm-adjusted $p \ge 0.05$. |

---

## 4. Experimental Execution Protocol

### 4.1 Candidate Models
Evaluates the same four local models:
1. `qwen3:8b`
2. `gemma2:9b`
3. `llama3.1:8b`
4. `mistral:7b-instruct`

### 4.2 Generation Sampling
- **Tasks**: $N = 24$ planning tasks.
- **Surface Variants**: 3 prompt presentations per task (standard PDDL-like notation, natural language room description, structured JSON problem statement).
- **Seeds**: 4 generation seeds per variant.
- **Total sample size**: $24 \times 3 \times 4 = 288$ candidate plans per model ($1,152$ records total).
- **Decoding**: Temperature $T = 0.7$, Top-$p = 0.9$, Max tokens $= 512$.

### 4.3 Statistical Analysis Plan
1. **Cartesian Product Draws**: Sample $M = 50,000$ independent reference vectors from $\prod_{i=1}^{24} V(x_i)$.
2. **Exact Dynamic Programming**: Compute exact margin distributions and population reversal rates using `rcrc/exact_margin_distribution.py`.
3. **World-Level Permutation Test**: 20,000 sign flips per draw, treating the 24 planning tasks as the paired observational units, with step-down Holm-Bonferroni correction across the 6 model pairs.
4. **Degenerate Draw Handling**: Predeclared policy D5 (exclude one-constant vectors; track count).

---

## 5. Execution Requirements & Feasibility Audit

| Resource | Required | Available in Environment | Status |
|---|---|---|---|
| **Local LLM Runner** | Ollama daemon with local weights | Ollama running locally; models present | **AVAILABLE** |
| **State Verifier** | Python transition model for Blocks World | Implemented in pure Python | **VERIFIED** |
| **Exhaustive BFS Explorer** | BFS state space enumerator | Pure Python algorithm | **VERIFIED** |
| **Compute Time** | 1,152 generations @ ~15–20s/gen $\approx 5–6$ hours | Requires dedicated GPU compute | **PENDING** |

### Execution Status: Implementation Check Complete, Full Confirmatory Run Pending
- **Implementation Check (Executed)**: Evaluated in `research/pilot_second_domain/blocks_world_rcr_pilot.py` on 6 worlds ($|V_i| \in \{1, 2, 6\}$). Verifies that the transition engine, BFS shortest-path enumerator, and parser function deterministically, and confirms the $1/|V(x)|$ identity on discrete state spaces ($r = 1.0$, observed/predicted ratio = $1.000000$).
- **Full Confirmatory Experiment (Pending)**: Generating 1,152 full plans across 4 open-weight LLMs locally requires approximately 5–6 hours of compute due to model loading and extended reasoning sequences. To preserve preregistration integrity, we do not arbitrarily downsample the 24-world suite or reduce the model set. The confirmatory experiment is preserved as an external replication protocol.

---

## Addendum A (2026-10-14): Execution record — supersedes the "Pending" status in Section 5

The registered body above (Sections 1–5) is unchanged; its SHA-256 before this addendum was `ebfd3bd95087902662eab86ec3adfc9b40ba714d1ef69f612c933387c6b1f6ed`.

**Status:** The full confirmatory run was executed on 2026-10-13 (23:18:54–23:50:38 local time, 31 min 44 s) on one RTX 4060 Laptop GPU with Ollama 0.19.0. All 1,152 planned generations are present with 0 errors. The "5–6 hours" estimate in Section 5 was incorrect.

**Results (see `paper/RCR_EMPIRICAL_DRAFT.md` §6):** H1 confirmed (non-zero-cell r = 0.9855, 16 cells); H2 rejected (mean reversal 4.63% < 8.0%); H3 not informative and H4 not testable (no E3-separated pair). Registered criterion 4 (non-trivial model competence) was **not met**: pass rates 7.99%, 5.56%, 0.35%, 0.35%.

**Deviations** (full table in the manuscript §6.5): D0 two-operator model (`move`, `move_to_table`) used instead of the registered four STRIPS operators with an arm; D1 H1 correlation computed over all cells in the as-executed run (corrected to non-zero cells); D2 H3/H4 printed CONFIRMED with no separated pair (corrected); D3 H4 branch subsampled (never triggered); D4 degenerate-draw policy not applied; D5 `think=false` for qwen3:8b; D6 a fixed demonstration string appears in every prompt; D7 feasibility estimate wrong.

**Integrity note:** This is an internal protocol, not an external registration. The analysis script's last modification (23:20) falls after the first qwen3:8b record (23:18:54) and before the remaining runs, so blindness to the first model's outputs cannot be certified.
