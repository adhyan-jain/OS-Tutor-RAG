# RCR Theory Decision Gate: Formal Evaluation & Verdict

**Repository:** OS-Tutor-RAG / Reference-Choice Robustness (RCR)  
**Date:** October 2026  
**Document Status:** Hard Decision Gate & Formal Audit  
**Track A Verdict:** **FAIL** (Theory-Led Route Terminated; Fallback to Empirical Methodology Paper Mandatory)

---

## 1. Executive Summary and Verdict

This document records the formal decision gate for **Track A** of the RCR research rescue: determining whether Reference-Choice Robustness can support a genuinely novel, non-empirical theoretical or formal-methods paper.

Following an exhaustive review of contemporary primary literature (including Casola et al., INLG 2025; Kulshreshtha et al., arXiv:2610.03825, Oct 2026; Feng et al., arXiv:2608.25654, Aug 2026) and mathematical investigations into three candidate directions (Distribution-Free Geometry, Metric Identifiability/Impossibility, and Equivalence-Class Invariance), the definitive verdict is **FAIL**.

### Core Findings
1. **Mathematical Machinery is Elementary:** The exact dynamic programming convolution is standard discrete polynomial multiplication ($O(N^2 K^2)$); the total variation (TV) robustness bound is textbook coupling (Levin & Peres, 2017, Lemma 4.2); and the winner reversal probability $2 p_+ p_-$ is a two-line elementary independence identity.
2. **Empirical Vacuity of the TV Certificate:** The sufficient condition for expected margin sign invariance ($|\mu| > 2 \cdot \overline{\mathrm{TV}}$) is vacuous on realistic distribution shifts. Because the benchmark expected margins are small ($|\mu| \le 0.0368$) and the worst-case Lipschitz constant ($L=2$) assumes adversarial concentration on extreme differences ($D_i = -1.0$), the certificate requires $\overline{\mathrm{TV}} < 0.0184$. For canonical bias $p = 0.50$, $\overline{\mathrm{TV}} = 0.3308$ yielding a bound of $0.6616$—18 times larger than the largest margin. Crucially, failure to certify does *not* imply sign reversal: empirical evaluation across $p \in [0.10, 0.99]$ demonstrates that true expected margins never flip sign.
3. **Prior-Art Saturation:** Contemporary literature has already established reference-induced ranking instability in empirical benchmarks (Casola et al., INLG 2025; Kulshreshtha et al., 2026) and formalized incomplete-reference calibration reversals (Feng et al., 2026).
4. **Stripping Notation Test:** When domain notation ("benchmark worlds", "generations", "reference matching") is stripped away, the candidate theorems reduce to elementary properties of bounded discrete random variables, interval arithmetic, and Manski partial identification bounds.

Per the decision protocol, the theory route is formally terminated. No further effort will be spent attempting to frame RCR as a theory contribution. All focus is directed to Track B: producing a defensible empirical methodology paper.

---

## 2. Prior-Art Matrix

| Paper | Problem Solved | Formal Assumptions | Existing Theorems / Algorithms | Addressed Quantities | What Remains Unanswered | Strongest Skeptical Argument that RCR Duplicates Work |
|---|---|---|---|---|---|---|
| **Casola et al. (INLG 2025)**<br>*References Matter: Reference Set Variation in Summarization* | Evaluates impact of varying human reference summaries on automated metrics (ROUGE, BERTScore, etc.). | Multi-reference NLP datasets (SummEval, GUMSum, DUC2004); human references sampled without replacement. | Empirical Monte Carlo resampling of reference sets; Kendall $\tau$ and Pearson $r$ stability against human judgment. | Ranking reversals; metric instability; degradation of human correlation outside newswire. | Does not characterize the exhaustive valid space $V(x)$; cannot separate annotation noise from true multi-solution validity. | "Reference-induced ranking instability is an established empirical observation in multi-reference NLP; evaluating it in OS tasks is merely changing the application domain." |
| **Kulshreshtha et al. (arXiv:2610.03825, Oct 2026)**<br>*Same Output, Different Gold* | Measures how reference choice moves multilingual benchmark scores when candidate outputs remain identical. | Retained multi-annotator PII labeling records across 6 languages; fixed system generation outputs. | Introduces the "reference-sensitivity band"; quantifies variance induced by undocumented pipeline defaults. | Score shifts (up to 7.55 $F_1$); pairwise ranking interaction shifts (+2.95 points); gold-standard variance. | Focuses on annotator disagreement and aggregation defaults, not formal state-space valid-solution spaces. | "Kulshreshtha et al. already proved that holding outputs fixed and swapping gold references moves pairwise rankings and margins. RCR's core empirical premise is identical." |
| **Feng, Chen & Zhang (arXiv:2608.25654, Aug 2026)**<br>*Unmatched Does Not Mean False* | Incomplete reference sets reverse calibration rankings in open-ended Theory-of-Mind tracking. | Agent behavioral predictions evaluated against incomplete subsets of valid mental state transitions. | Formal analysis of false-negative penalty bias; demonstrates ranking inversions in Brier score and ECE. | Calibration reversals; incomplete reference penalty; false-negative rate quantification. | Bounded to open-ended ToM tracking; does not provide exact discrete margin convolutions or TV bounds. | "Feng et al. already formalized the principle that penalizing unmatched valid outputs reverses comparative rankings under incomplete references." |
| **Manski (1989, 2003)**<br>*Partial Identification in Econometrics* | Nonparametric bounds on parameters under missing or partially observed outcomes. | Bounded outcome space; observable indicator is a subset of true valid event ($Y = r \implies Y \in V$). | Manski bounds: $\theta \in [P(Y=r), 1]$; sharp identification regions without exclusion restrictions. | Identifiability of expectations, ranking identification regions, missing data bounds. | General econometrics; did not instantiate on LLM execution traces or benchmark ranking metrics. | "The 'impossibility of identifying semantic correctness from a single reference' is literally Manski's 1989 lower bound $P(Y \in V) \ge P(Y=r)$." |
| **Mazurkiewicz (1977); Diekert & Rozenberg (1995)**<br>*Trace Theory* | Algebraic semantics for concurrent systems; equivalence of execution sequences under independent actions. | Symmetric irreflexive independence relation $I \subseteq \Sigma \times \Sigma$; traces as congruence classes. | Foata normal forms; trace languages; partial-order reduction algorithms (Peled 1993). | Equivalence of interleavings; combinatorial counting of linearizations per trace. | Pure concurrency theory; does not address LLM benchmark evaluation or reference sampling. | "Weighting traces by $1/|[r]|$ is standard trace theory. Applying it to 8 concurrency worlds does not make it a novel formal-methods paper." |

---

## 3. Investigation of Candidate Theoretical Directions

### 3.1 Candidate A: Distribution-Free Characterization of Reference-Induced Rankings

#### Setup and Problem Statement
Let a benchmark comprise $N$ tasks $i \in \{1, \dots, N\}$. For task $i$, let $V_i$ be the finite set of verified valid references ($|V_i| \ge 1$). An evaluator chooses a product reference distribution $q = \prod_{i=1}^N q_i$, where each $q_i \in \Delta(V_i)$ is a probability vector over $V_i$.  
For two frozen models $A$ and $B$, let $D_i(r) = S_{Ai}(r) - S_{Bi}(r) \in [-1, 1]$ be the per-task score difference under reference $r \in V_i$.  
The expected pairwise score margin across the benchmark is:
$$\mu_{AB}(q) = \frac{1}{N} \sum_{i=1}^N \sum_{r \in V_i} q_i(r) D_i(r)$$

#### Theoretical Inquiry
What is the geometry of attainable expected margins $\mu_{AB}(q)$ as $q_i$ varies freely across $\Delta(V_i)$? Under what conditions is the pairwise winner invariant?

#### Derivation and Results
1. **Attainable Expected Margin Set:**  
   Because each simplex $\Delta(V_i)$ is compact and convex, and the expectation is linear in $q_i$, the set of attainable values for $\mathbb{E}_{q_i}[D_i]$ is the closed interval:
   $$\mathcal{I}_i = [d_i^{\min}, d_i^{\max}], \quad \text{where } d_i^{\min} = \min_{r \in V_i} D_i(r), \; d_i^{\max} = \max_{r \in V_i} D_i(r)$$
   Since the product distribution factors independently across tasks without cross-task coupling, the set of attainable benchmark margins $\mu_{AB}(q)$ is the Minkowski sum divided by $N$:
   $$\mathcal{I}_{AB} = \left[ \frac{1}{N} \sum_{i=1}^N d_i^{\min}, \; \frac{1}{N} \sum_{i=1}^N d_i^{\max} \right]$$

2. **Invariance Condition:**  
   The expected pairwise winner is strictly invariant ($\mu_{AB}(q) > 0$ for all admissible product distributions $q \in \prod_i \Delta(V_i)$) if and only if:
   $$\frac{1}{N} \sum_{i=1}^N d_i^{\min} > 0$$
   Equivalently, Model $A$ maintains a positive expected margin even when an adversary selects the worst possible valid reference for $A$ on every task independently.

3. **Reversal Realizability Condition:**  
   There exist valid reference distributions $q, q'$ such that $\mu_{AB}(q) > 0$ and $\mu_{AB}(q') < 0$ if and only if:
   $$\frac{1}{N} \sum_{i=1}^N d_i^{\min} < 0 < \frac{1}{N} \sum_{i=1}^N d_i^{\max}$$

4. **Minimum Distribution Perturbation to Reverse (Knapsack LP):**  
   Given a baseline distribution $q^0$ where $\mu_{AB}(q^0) > 0$, the minimum total variation distance $\sum_{i=1}^N \mathrm{TV}(q_i, q_i^0)$ required to force $\mu_{AB}(q) \le 0$ is the solution to the continuous linear program:
   $$\min_{\{q_i\}} \sum_{i=1}^N \frac{1}{2} \|q_i - q_i^0\|_1 \quad \text{s.t.} \quad \sum_{i=1}^N \sum_{r \in V_i} q_i(r) D_i(r) \le 0, \quad q_i \in \Delta(V_i)$$
   This problem reduces to a 1D continuous fractional knapsack: for each task $i$, the maximum margin reduction per unit TV distance is achieved by shifting probability mass from references with large $D_i(r)$ to the minimizer $r_i^* = \arg\min D_i(r)$. Tasks are greedily perturbed in decreasing order of efficiency $( \mathbb{E}_{q_i^0}[D_i] - d_i^{\min} ) / \mathrm{TV}_i$.

#### Why Candidate A Fails the Novelty Gate
- The attainable set $\mathcal{I}_{AB}$ is simple 1D interval arithmetic.
- The invariance condition is an elementary min-sum bound.
- The distance-to-reversal calculation is a standard continuous knapsack problem / $L_1$ projection onto a halfspace.
- **Skeptical verdict:** Any reviewer in optimization, COLT, or formal methods will recognize this as basic textbook linear programming with no substantive new mathematical content.

---

### 3.2 Candidate B: Identifiability and Impossibility

#### Setup and Problem Statement
Let $\mathcal{Y}$ be the output space. For task $x$, let $V(x) \subset \mathcal{Y}$ be the finite set of valid outputs, with $|V(x)| > 1$. Let the evaluator observe only single-reference match scores against a selected reference $r(x) \in V(x)$:
$$S(y, r(x)) = \mathbf{1}\{y = r(x)\}$$
The unobserved quantity of interest is the model's true semantic correctness:
$$\theta_m(x) = P_m(Y \in V(x) \mid x)$$

#### Theoretical Inquiry
Can $\theta_m(x)$ or the relative semantic ordering $\mathrm{sign}(\theta_A(x) - \theta_B(x))$ be identified from single-reference match rates without assuming $|V(x)| = 1$ or knowing the full set $V(x)$?

#### Derivation and Results
1. **Nonparametric Identification Region:**  
   Because $r(x) \in V(x)$, observing $y = r(x)$ implies $y \in V(x)$. Thus:
   $$P_m(Y = r(x)) \le P_m(Y \in V(x))$$
   Without further assumptions on the distribution of probability mass across unobserved valid references $V(x) \setminus \{r(x)\}$, any mass assigned to $y \notin \{r(x)\}$ could belong to $V(x)$ or to invalid outputs $\mathcal{Y} \setminus V(x)$.  
   Hence, the sharp identification region for $\theta_m(x)$ is:
   $$\mathcal{H}(\theta_m(x)) = [P_m(Y = r(x)), \; 1]$$
   The length of this uncertainty interval is $1 - P_m(Y = r(x))$. For a single reference, identifiability is impossible.

2. **Minimal Finite-State Counterexample (Ranking Reversal under Identical Outputs):**  
   Let $V(x) = \{r_1, r_2\}$. Let the benchmark curator select $r_1$ as the reference.
   - **Model A distribution:** $P_A(Y = r_1) = 0.40$, $P_A(Y = r_2) = 0.00$, $P_A(Y \text{ invalid}) = 0.60$.  
     Semantic pass rate: $\theta_A = 0.40$.
   - **Model B distribution:** $P_B(Y = r_1) = 0.10$, $P_B(Y = r_2) = 0.80$, $P_B(Y \text{ invalid}) = 0.10$.  
     Semantic pass rate: $\theta_B = 0.90$.
   - **Evaluation under selected reference $r_1$:**  
     $S_A(r_1) = 0.40 > S_B(r_1) = 0.10 \implies \mathbf{A \succ B}$ (Margin: $+0.30$).
   - **Evaluation under true semantic oracle:**  
     $\theta_A = 0.40 < \theta_B = 0.90 \implies \mathbf{B \succ A}$ (Margin: $-0.50$).
   - **Evaluation under alternative valid reference $r_2$:**  
     $S_A(r_2) = 0.00 < S_B(r_2) = 0.80 \implies \mathbf{B \succ A}$ (Margin: $-0.80$).

3. **What an Executable Semantic Oracle Changes:**  
   An executable oracle is an algorithm $\mathcal{O}: \mathcal{Y} \times \mathcal{X} \to \{0, 1\}$ satisfying $\mathcal{O}(y, x) = 1 \iff y \in V(x)$.  
   By computing the indicator $\mathbf{1}\{y \in V(x)\}$ directly without conditioning on an individual reference token $r$, the oracle collapses the identification region $[P_m(Y=r), 1]$ to the singleton $\{\theta_m(x)\}$.

#### Why Candidate B Fails the Novelty Gate
- The identification region $[P(Y=r), 1]$ is Manski's standard 1989 lower bound under partial outcome observation.
- The minimal counterexample demonstrates the obvious set-theoretic fact that $\mathbf{1}\{y = r\} \neq \mathbf{1}\{y \in V\}$ when $|V| > 1$.
- Feng et al. (arXiv:2608.25654, Aug 2026) already published this exact formal argument for open-ended tracking benchmarks ("Unmatched Does Not Mean False").
- **Skeptical verdict:** Presenting this as an "Impossibility Theorem of Reference Evaluation" would be dismissed as rebranding basic set inclusion and Manski bounds under a new name.

---

### 3.3 Candidate C: Representation and Equivalence-Class Invariance

#### Setup and Problem Statement
In concurrent systems, multiple execution traces may correspond to the same operational behavior due to interleavings of independent actions.  
Let $\Sigma$ be a finite alphabet of actions. Let $I \subseteq \Sigma \times \Sigma$ be a symmetric, irreflexive independence relation. In Mazurkiewicz trace theory (Mazurkiewicz, 1977), two traces $w, w' \in \Sigma^*$ are equivalent ($w \equiv_I w'$) if one can be obtained from the other by successively transposing adjacent independent actions ($a b \equiv_I b a$ for $(a, b) \in I$).  
A valid solution space $V \subset \Sigma^*$ is partitioned into equivalence classes $\mathcal{C} = \{c_1, \dots, c_m\}$ such that $V = \bigsqcup_{c \in \mathcal{C}} c$.

#### Theoretical Inquiry
When do uniform sampling over raw execution traces and uniform sampling over semantic equivalence classes induce identical expected scores and model rankings?

#### Derivation and Results
1. **Raw Trace Sampling ($q_{\text{raw}}$):**  
   Each raw trace $r \in V$ has probability $q_{\text{raw}}(r) = \frac{1}{|V|}$.  
   The probability mass assigned to equivalence class $c \in \mathcal{C}$ is:
   $$P_{\text{raw}}(c) = \sum_{r \in c} \frac{1}{|V|} = \frac{|c|}{|V|}$$

2. **Equivalence-Class Sampling ($q_{\text{equiv}}$):**  
   An evaluator first selects an equivalence class $c \in \mathcal{C}$ uniformly with probability $\frac{1}{|\mathcal{C}|}$, and then selects a trace uniformly within that class with probability $\frac{1}{|c|}$:
   $$q_{\text{equiv}}(r) = \frac{1}{|\mathcal{C}| \cdot |c|} \quad \text{for } r \in c$$
   Under $q_{\text{equiv}}$, every equivalence class has equal mass $P_{\text{equiv}}(c) = \frac{1}{|\mathcal{C}|}$.

3. **Condition for Equivalence:**  
   $q_{\text{raw}}(r) = q_{\text{equiv}}(r)$ for all $r \in V$ if and only if:
   $$\frac{|c|}{|V|} = \frac{1}{|\mathcal{C}|} \iff |c| = \frac{|V|}{|\mathcal{C}|} \quad \forall c \in \mathcal{C}$$
   That is, raw uniform sampling is representation-invariant if and only if all equivalence classes have **strictly equal cardinality**.

4. **Counterexample (Combinatorial Volume Bias):**  
   Consider a concurrency task with two valid execution strategies:
   - Strategy 1 (High Concurrency): Two threads execute 2 mutually independent actions each. The number of valid interleavings is $\binom{4}{2} = 6$. Class size $|c_1| = 6$.
   - Strategy 2 (Strict Serialization): Threads acquire a coarse lock, forcing sequential execution. Only $1$ valid interleaving exists. Class size $|c_2| = 1$.  
   Total valid traces: $|V| = 6 + 1 = 7$.
   - Under $q_{\text{raw}}$: Strategy 1 receives weight $\frac{6}{7} \approx 0.857$, while Strategy 2 receives $\frac{1}{7} \approx 0.143$. A model generating Strategy 1 receives a 6x higher score solely due to combinatorial trace volume.
   - Under $q_{\text{equiv}}$: Each strategy receives weight $\frac{1}{2} = 0.500$.

#### Why Candidate C Fails the Novelty Gate
- **Domain limitation:** Mazurkiewicz equivalence applies strictly to concurrency (8 of 24 benchmark worlds). It does not apply to CPU scheduling (where SJF tie-breaking schedules represent distinct operational schedules without an algebraic independence relation) or Banker's deadlock avoidance (where safe sequences are topological sorts of resource release dependencies, not commutative traces).
- **Prior art:** Mazurkiewicz trace theory has been established since 1977. The distinction between counting linearizations versus counting partially ordered traces is standard in formal verification (e.g., partial-order reduction, Peled 1993).
- **Skeptical verdict:** Applying 1977 trace equivalence to 8 toy concurrency tasks does not constitute a publishable formal-methods paper.

---

## 4. Deconstruction of Attempted Theorems

To ensure no viable theoretical angle is overlooked, we formalize the strongest combined theoretical statement and submit it to rigorous scrutiny.

### Theorem Attempt: "Distributional Ranking Invariance & Attenuation Bounds"

```
[Candidate Theorem Statement]
Let benchmark B = {(V_i, q_i^0)}_{i=1}^N have mutually exclusive verified references V_i.
Let models A, B produce K generations per task with valid generation counts a_{Ai}, a_{Bi}.
Then:
1. (Attenuation Law) Under uniform reference selection q_i^0 = Unif(V_i), the expected
   benchmark score satisfies E[S_m] = (1/N) \sum_{i=1}^N a_{mi} / (K |V_i|).
2. (Invariance Halfspace) The pairwise ranking sign(E[M_{AB}]) is invariant under all
   perturbations within product TV-ball \sum_i TV(q_i, q_i^0) \le B_{TV} if:
     | \mu_{AB}(q^0) | > (2/N) B_{TV}
3. (Exact Convolution) The exact probability of winner reversal across two independent
   draws R_1, R_2 \sim \prod q_i is P(reversal) = 2 p_+ p_-, computable in O(N^2 K^2) time.
```

### The "Stripping Notation" Test
Let us strip away the domain terminology ("benchmarks", "models", "generations", "references", "evaluators"):
1. **Part 1:** If $X$ is a discrete random variable uniformly distributed over a finite set $V$, and $Y \in V$ is fixed, then $P(X = Y) = 1/|V|$. Summing over independent events yields an expectation weighted by $1/|V|$.  
   *Assessment:* Trivial identity of uniform discrete probability.
2. **Part 2:** If $f: \Omega \to [-1, 1]$ is bounded, $|\mathbb{E}_p[f] - \mathbb{E}_q[f]| \le 2 \mathrm{TV}(p, q)$. By triangle inequality, if $|\mathbb{E}_p[f]| > 2 \mathrm{TV}(p, q)$, the sign cannot change.  
   *Assessment:* Textbook coupling lemma (Levin & Peres, 2017, Lemma 4.2).
3. **Part 3:** If $M_1, M_2$ are i.i.d. scalar random variables with $p_+ = P(M > 0)$ and $p_- = P(M < 0)$, the probability that $M_1 > 0 \wedge M_2 < 0$ or $M_1 < 0 \wedge M_2 > 0$ is $2 p_+ p_-$. The sum of $N$ independent integer variables bounded in $[-K, K]$ can be computed by discrete dynamic programming convolution in $O(N^2 K^2)$ time.  
   *Assessment:* Elementary independence algebra and standard polynomial multiplication.

### Conclusion of Deconstruction
None of the three components constitutes a substantive mathematical discovery. Presenting this combination to a theory conference (POPL, CAV, LICS, COLT) would result in immediate rejection for lack of technical depth.

---

## 5. Reviewer Attacks and Vulnerability Analysis

### Simulated Attack from a Theory Reviewer (e.g., CAV / POPL / COLT)
> *"The authors claim a formal framework for reference-choice robustness. However, stripping the domain packaging reveals:
> 1. Proposition 1 is a one-line expansion of an expectation under a uniform distribution.
> 2. Proposition 2 is a textbook Lipschitz bound on bounded functions under total variation. Moreover, Section 2 shows the bound is empirically useless: its threshold requires TV < 0.018, whereas realistic shifts have TV > 0.33. Why present a certificate that certifies nothing in practice?
> 3. Proposition 3 is a trivial independence identity (2 p_+ p_-) paired with standard 1D discrete convolution.
> There are no new proof techniques, no nontrivial lower bounds, no hardness results, and no algorithms beyond basic dynamic programming. Reject."*

### Simulated Attack from an NLP / Benchmarking Reviewer (e.g., ACL / NeurIPS)
> *"The premise that gold-standard reference choice affects system scores and rankings is well-established. Casola et al. (INLG 2025) demonstrated this on summarization; Kulshreshtha et al. (arXiv:2610.03825, Oct 2026) demonstrated it for multilingual PII; and Feng et al. (arXiv:2608.25654, Aug 2026) proved calibration reversals under incomplete references. What does RCR add conceptually? The empirical study is restricted to 24 toy OS tasks on four sub-10B models. Reject."*

---

## 6. Decision Gate Checklist & Final Verdict

| Evaluation Criterion | Requirement for PASS | Status | Evidence / Reason |
|---|---|---|---|
| **Criterion 1: Substantive Math Contribution** | At least one genuinely new mathematical theorem or formal guarantee. | **FAIL** | All proofs reduce to textbook discrete probability, coupling bounds, or 1D knapsack. |
| **Criterion 2: Correct & Complete Proof** | Rigorous, non-circular proof checkable by an independent mathematician. | **PASS** | Derivations in Section 3 and `RCR_FORMAL_METHOD_NOTE.md` are mathematically sound. |
| **Criterion 3: Clear Literature Distinction** | Clear conceptual divergence from closest prior art. | **FAIL** | Heavy overlap with Casola (2025), Kulshreshtha (2026), Feng (2026), and Manski (1989). |
| **Criterion 4: Non-Trivial Implication** | Provides an actionable guarantee or unexpected impossibility result. | **FAIL** | TV certificate is empirically vacuous; DP convolution matches 50k MC to 4 decimal places. |
| **Criterion 5: Domain Generalization** | Importance demonstrated beyond the 24 OS benchmark worlds. | **FAIL** | Concurrency equivalence applies only to 8 worlds; no broader formal domain evaluated. |
| **Criterion 6: Plausible Venue Fit** | Realistic chance of acceptance at a recognized theory/FM venue. | **FAIL** | High risk of desk rejection at CAV, POPL, or COLT for lack of technical depth. |

### Final Verdict: **FAIL**

**Directive:**
1. Formally terminate Track A (Theory Paper).
2. The exact DP convolution, $2 p_+ p_-$ identity, and TV certificate discussion must remain in the **empirical paper's methodology and appendix** as clean computational tools and bounded analytical checks, with explicit disclaimers that they are not novel mathematics.
3. Advance immediately to Track B: develop and finalize `paper/RCR_EMPIRICAL_DRAFT.md` and `paper/RCR_EMPIRICAL_READINESS.md`.
