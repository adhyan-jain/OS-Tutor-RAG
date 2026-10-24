# Formal Method Note: Exact Margin Distributions, Robustness Certificates, and Reference Sampling

**Date:** October 2026  
**Status:** Methodological and Mathematical Specification  
**Project:** OS-Tutor-RAG / Reference-Choice Robustness (RCR)  

---

## 1. Formal Definitions

Let a benchmark consist of $N$ evaluation tasks (worlds) indexed by $i \in \{1, \ldots, N\}$.

- **Valid Reference Space:** For task $i$, $V_i = \{r_{i, 1}, \ldots, r_{i, |V_i|}\}$ is the non-empty, finite set of formally verified valid references.
- **Candidate Models:** Let $\mathcal{M}$ be the set of evaluated models. For each task $i$, model $m \in \mathcal{M}$ produces $K$ candidate generations $y_{mi}^{(1)}, \ldots, y_{mi}^{(K)}$.
- **Match Count:** For a reference $r \in V_i$, the match count $c_{mi}(r)$ is the integer number of candidate generations matching reference $r$:
  $$c_{mi}(r) = \sum_{k=1}^K \mathbf{1}\{y_{mi}^{(k)} \sim r\}, \quad c_{mi}(r) \in \{0, 1, \ldots, K\}$$
- **Reference Distribution:** For task $i$, let $q_i \in \Delta(V_i)$ be a probability distribution over valid references:
  $$\sum_{r \in V_i} q_i(r) = 1, \quad q_i(r) \ge 0$$
  Across the benchmark, a reference vector $R = (r_1, \ldots, r_N) \in \prod_{i=1}^N V_i$ is drawn independently according to product distribution $q = \prod_{i=1}^N q_i$.
- **Per-Task Score and Difference:** The reference-dependent score of model $m$ on task $i$ under reference $r_i$ is $S_{mi}(r_i) = \frac{c_{mi}(r_i)}{K}$. For a pair of models $(A, B)$, the per-task score difference is:
  $$D_i(r_i) = S_{Ai}(r_i) - S_{Bi}(r_i) = \frac{c_{Ai}(r_i) - c_{Bi}(r_i)}{K} \in [-1, 1]$$
- **Benchmark Pairwise Margin:** The benchmark-level score margin under reference vector $R$ is:
  $$M_{AB}(R) = \frac{1}{N} \sum_{i=1}^N D_i(r_i) = \frac{1}{NK} \sum_{i=1}^N (c_{Ai}(r_i) - c_{Bi}(r_i))$$

---

## 2. PROPOSITION 1: Expected-Score Identity

### Statement
Let $a_{mi}$ denote the total number of valid generations produced by model $m$ on task $i$ (i.e., generations matching *at least one* reference in $V_i$). Under mutually exclusive valid references (each generation matches at most one reference, guaranteed by parser canonicalization and deviation D3(b)), $\sum_{r \in V_i} c_{mi}(r) = a_{mi}$.

Under the uniform reference distribution $q_i(r) = \frac{1}{|V_i|}$, the expected score of model $m$ is:
$$\mathbb{E}_q[S_m(R)] = \frac{1}{N} \sum_{i=1}^N \frac{a_{mi}}{K \cdot |V_i|}$$

### Proof
By linearity of expectation:
$$\mathbb{E}_q[S_m(R)] = \frac{1}{N} \sum_{i=1}^N \mathbb{E}_{q_i}[S_{mi}(r_i)] = \frac{1}{N} \sum_{i=1}^N \sum_{r \in V_i} q_i(r) \frac{c_{mi}(r)}{K}$$
Substituting $q_i(r) = \frac{1}{|V_i|}$:
$$\mathbb{E}_q[S_m(R)] = \frac{1}{N} \sum_{i=1}^N \frac{1}{|V_i| K} \sum_{r \in V_i} c_{mi}(r) = \frac{1}{N} \sum_{i=1}^N \frac{a_{mi}}{K \cdot |V_i|}$$
$\blacksquare$

### Implications
1. **Inverse Space Weighting:** In the unweighted reference-independent semantic evaluation (E3), the overall score is $S_m^{E3} = \frac{1}{N K} \sum_{i=1}^N a_{mi}$. Here, every generation has uniform weight $\frac{1}{NK}$.
2. Under uniform reference matching (E2), each task $i$ is implicitly weighted by $\frac{1}{|V_i|}$. Tasks with smaller valid spaces $|V_i|$ contribute disproportionately to the expected score.
3. When $|V_i|$ varies widely across benchmark tasks (in SSR pilot, $|V_i|$ ranges from 1 to 24), this distortion can reorder models even in expectation compared to the true semantic pass rate.

---

## 3. Hand-Checkable Concrete Example

Consider $N=2$ tasks ($i=1, 2$), models $A$ and $B$, $K=2$ generations per task, and $|V_1|=|V_2|=2$ references each.

### Setup
- **Task 1 ($V_1 = \{r_{11}, r_{12}\}$):**
  - Model A: $c_{A1}(r_{11}) = 2, c_{A1}(r_{12}) = 0 \implies a_{A1} = 2$.
  - Model B: $c_{B1}(r_{11}) = 0, c_{B1}(r_{12}) = 1 \implies a_{B1} = 1$.
  - Differences: $D_1(r_{11}) = \frac{2 - 0}{2} = 1.0$; $D_1(r_{12}) = \frac{0 - 1}{2} = -0.5$.
  - Under uniform $q_1 = (0.5, 0.5)$: $\mathbb{E}[D_1] = 0.5(1.0) + 0.5(-0.5) = +0.25$.
- **Task 2 ($V_2 = \{r_{21}, r_{22}\}$):**
  - Model A: $c_{A2}(r_{21}) = 1, c_{A2}(r_{22}) = 1 \implies a_{A2} = 2$.
  - Model B: $c_{B2}(r_{21}) = 2, c_{B2}(r_{22}) = 0 \implies a_{B2} = 2$.
  - Differences: $D_2(r_{21}) = \frac{1 - 2}{2} = -0.5$; $D_2(r_{22}) = \frac{1 - 0}{2} = +0.5$.
  - Under uniform $q_2 = (0.5, 0.5)$: $\mathbb{E}[D_2] = 0.5(-0.5) + 0.5(0.5) = 0.0$.

### Full Product Space Enumeration ($2 \times 2 = 4$ draws)
Each draw has joint probability $0.5 \times 0.5 = 0.25$.

| Draw $(r_1, r_2)$ | $D_1$ | $D_2$ | Margin $M = \frac{D_1 + D_2}{2}$ | Prob |
|---|---|---|---|---|
| $(r_{11}, r_{21})$ | $+1.0$ | $-0.5$ | $+0.25$ | $0.25$ |
| $(r_{11}, r_{22})$ | $+1.0$ | $+0.5$ | $+0.75$ | $0.25$ |
| $(r_{12}, r_{21})$ | $-0.5$ | $-0.5$ | $-0.50$ | $0.25$ |
| $(r_{12}, r_{22})$ | $-0.5$ | $+0.5$ | $0.00$ | $0.25$ |

### Distribution Summary
- $P(M > 0) = P(M = 0.25) + P(M = 0.75) = 0.25 + 0.25 = 0.50$ ($p_+ = 0.50$).
- $P(M < 0) = P(M = -0.50) = 0.25$ ($p_- = 0.25$).
- $P(M = 0) = P(M = 0.00) = 0.25$ ($p_0 = 0.25$).
- **Expected Margin:** $\mathbb{E}[M] = \frac{0.25 + 0.0}{2} = +0.125$.
- **Winner Reversal Probability:**
  $$P(\text{reversal}) = 2 \cdot p_+ \cdot p_- = 2 \cdot (0.50) \cdot (0.25) = 0.25$$

---

## 4. PROPOSITION 2: Total-Variation Robustness Bound

### Statement
Let $D_i: V_i \to [-1, 1]$. For any baseline distribution $q_i^0$ and perturbed distribution $q_i$ on $V_i$:
$$|\mathbb{E}_{q_i}[D_i] - \mathbb{E}_{q_i^0}[D_i]| \le 2 \cdot \mathrm{TV}(q_i, q_i^0)$$
where $\mathrm{TV}(q_i, q_i^0) = \frac{1}{2} \sum_{r \in V_i} |q_i(r) - q_i^0(r)|$.

Consequently, for the benchmark expected margin $\mu_{AB}(q) = \frac{1}{N} \sum_{i=1}^N \mathbb{E}_{q_i}[D_i]$:
$$|\mu_{AB}(q) - \mu_{AB}(q^0)| \le \frac{2}{N} \sum_{i=1}^N \mathrm{TV}(q_i, q_i^0)$$

### Proof
For any bounded function $f: V_i \to [-1, 1]$:
$$|\mathbb{E}_q[f] - \mathbb{E}_{q^0}[f]| = \left| \sum_{r \in V_i} f(r) (q(r) - q^0(r)) \right| \le \sup_{r \in V_i} |f(r)| \cdot \sum_{r \in V_i} |q(r) - q^0(r)|$$
By definition of total variation:
$$\sum_{r \in V_i} |q(r) - q^0(r)| = 2 \cdot \mathrm{TV}(q, q^0)$$
Since $D_i(r) \in [-1, 1]$, $\sup_{r \in V_i} |D_i(r)| \le 1$. Hence:
$$|\mathbb{E}_{q_i}[D_i] - \mathbb{E}_{q_i^0}[D_i]| \le 2 \cdot \mathrm{TV}(q_i, q_i^0)$$
Applying triangle inequality over the benchmark average:
$$|\mu_{AB}(q) - \mu_{AB}(q^0)| \le \frac{1}{N} \sum_{i=1}^N |\mathbb{E}_{q_i}[D_i] - \mathbb{E}_{q_i^0}[D_i]| \le \frac{2}{N} \sum_{i=1}^N \mathrm{TV}(q_i, q_i^0)$$
$\blacksquare$

### Sign Certification: Sufficient Condition vs. Necessary Condition
A **sufficient condition** for the sign of $\mu_{AB}(q)$ to remain invariant over all product distributions within TV budget $\sum_{i=1}^N \mathrm{TV}(q_i, q_i^0) \le B_{\mathrm{TV}}$ is:
$$|\mu_{AB}(q^0)| > \frac{2}{N} B_{\mathrm{TV}}$$

**Crucial Distinction:**
1. This is a **sufficient** condition, **NOT** an "if and only if" condition.
2. If $|\mu_{AB}(q^0)| > \frac{2}{N} B_{\mathrm{TV}}$, the triangle inequality guarantees that $|\mu_{AB}(q) - \mu_{AB}(q^0)| < |\mu_{AB}(q^0)|$, forcing $\mathrm{sign}(\mu_{AB}(q)) = \mathrm{sign}(\mu_{AB}(q^0))$.
3. If $|\mu_{AB}(q^0)| \le \frac{2}{N} B_{\mathrm{TV}}$, the sufficient certificate **fails to certify**. However, this certificate failure is **NOT** a proof of instability or sign reversal. The actual expected margin may remain strictly invariant under all feasible distributions.

### Hand-Checkable Counterexample: Certificate Failure on an Invariant Sign
Consider $N=1$ task with $V_1 = \{r_1, r_2\}$. Suppose Model A outperforms Model B on *both* valid references:
$$D_1(r_1) = +0.5, \quad D_1(r_2) = +0.4$$
Under *any* arbitrary probability distribution $q = (p, 1-p)$ on $V_1$ ($p \in [0, 1]$):
$$\mathbb{E}_q[D_1] = 0.5 p + 0.4(1 - p) = 0.4 + 0.1 p \in [+0.4, +0.5]$$
The sign of the expected margin is strictly positive under **100% of all possible distributions** on $V_1$, even for maximum perturbation $\mathrm{TV}(q, q^0) = 1.0$. The true margin sign is unconditionally invariant.

Now apply the TV certificate with baseline $q^0 = (0.5, 0.5)$:
- Expected baseline margin: $\mu(q^0) = 0.5(0.5) + 0.5(0.4) = +0.45$.
- Consider a perturbation budget $B_{\mathrm{TV}} = 0.30$.
- The TV Lipschitz bound gives:
  $$\text{Bound} = 2 \cdot B_{\mathrm{TV}} = 2 \cdot 0.30 = 0.60$$
- Checking the certificate condition:
  $$|\mu(q^0)| = 0.45 \le 0.60 = \text{Bound}$$
The certificate **fails** (reports uncertified / "sufficient bound cannot certify"). Yet, as shown above, the sign never flips for any distribution in the simplex (min margin $+0.40 > 0$).

This occurs because the Lipschitz constant $2$ assumes worst-case adversarial alignment where probability mass is shifted to references with maximal negative values (e.g. $D = -1.0$). When $D_i(r)$ does not span $[-1, 1]$, the bound is loose and its failure is merely a failure of the certificate, not a property of the data.

---

## 5. PROPOSITION 3: Winner-Reversal Probability Identity

### Statement
Let $R_1, R_2 \sim \prod_{i=1}^N q_i$ be two independent draws of the reference vector. Under any independent reference distributions $q$, the probability that the pairwise winner reverses between $R_1$ and $R_2$ is:
$$P(\text{winner reversal}) = 2 \cdot p_+ \cdot p_-$$
where $p_+ = P(M_{AB}(R) > 0)$ and $p_- = P(M_{AB}(R) < 0)$.

### Proof
Because $R_1$ and $R_2$ are independent and identically distributed, the scalar margins $M_1 = M_{AB}(R_1)$ and $M_2 = M_{AB}(R_2)$ are independent and identically distributed random variables.

A strict winner reversal occurs when model A wins under $R_1$ and model B wins under $R_2$, or vice versa:
$$\text{Reversal} = \{M_1 > 0 \wedge M_2 < 0\} \cup \{M_1 < 0 \wedge M_2 > 0\}$$
These two events are mutually exclusive. By independence:
$$P(M_1 > 0 \wedge M_2 < 0) = P(M_1 > 0) \cdot P(M_2 < 0) = p_+ \cdot p_-$$
$$P(M_1 < 0 \wedge M_2 > 0) = P(M_1 < 0) \cdot P(M_2 > 0) = p_- \cdot p_+$$
Summing the disjoint events yields:
$$P(\text{reversal}) = p_+ p_- + p_- p_+ = 2 \cdot p_+ \cdot p_-$$
$\blacksquare$

---

## 6. Algorithm Pseudocode and Complexity

```python
def exact_margin_distribution(task_data, K):
    # Step 1: Discrete distributions per task
    per_task_dists = []
    for (c_A, c_B, q) in task_data:
        diff_counts = defaultdict(float)
        for r in range(len(q)):
            diff_int = c_A[r] - c_B[r]   # in [-K, K]
            diff_counts[diff_int] += q[r]
        per_task_dists.append(diff_counts)
    
    # Step 2: DP convolution of raw integer sums
    raw_dist = {0: 1.0}
    for task_dist in per_task_dists:
        next_dist = defaultdict(float)
        for cur_sum, cur_p in raw_dist.items():
            for d_int, prob in task_dist.items():
                next_dist[cur_sum + d_int] += cur_p * prob
        raw_dist = next_dist
    
    # Step 3: Scale to margin
    N = len(task_data)
    margin_dist = {raw_sum / (N * K): p for raw_sum, p in raw_dist.items()}
    return margin_dist
```

### Complexity Analysis
- **Per-task distribution:** $O(|V_i|)$ per task.
- **DP Convolution:** At step $i \in \{1, \ldots, N\}$, the current state support has size at most $2 i K + 1$. Convolving with the next task of support at most $2 K + 1$ requires:
  $$\sum_{i=1}^N (2 i K + 1)(2 K + 1) = O(N^2 K^2)$$
- **Numerical Example:** For $N = 24$ tasks and $K = 12$ generations:
  $$N^2 K^2 = 24^2 \times 12^2 = 576 \times 144 = 82,944 \text{ operations}$$
  Execution completes in $< 2$ milliseconds in Python, with exactness up to IEEE-754 precision ($\sim 10^{-15}$).

---

## 7. Explicit Novelty Assessment

**NONE of the mathematics in this note is novel:**
1. The TV bound is the textbook coupling / Lipschitz bound for bounded functions (see e.g., Levin & Peres, *Markov Chains and Mixing Times*, 2017, Lemma 4.2).
2. The dynamic programming convolution of discrete independent distributions is standard polynomial multiplication / discrete Fourier convolution, taught in introductory algorithms.
3. The winner-reversal identity $2 p_+ p_-$ is elementary independence algebra for binary events.

While the application to multi-reference evaluation in code/OS benchmarks provides clean closed forms, the mathematical machinery is entirely classical.

---

## 8. Edge Cases and Limitations

1. **Expectation vs. Realization:** The TV certificate bounds $\mathbb{E}[M_{AB}]$, *not* individual draws. Even if the expected margin sign is certified positive ($\mu_{AB} > 0$), individual sampled reference vectors can still reverse with non-zero probability $2 p_+ p_-$.
2. **TV Bound Conservatism:** The Lipschitz factor of 2 assumes the worst-case perturbation where probability mass is shifted exclusively onto references with maximal negative difference. For real benchmarks, distribution shifts (such as canonical bias) do not align adversarially with $D_i$. In our empirical evaluation, the TV bound for canonical bias $p=0.50$ is $0.6616$, whereas expected margins are $\le 0.0368$. Hence, the certificate certifies **no realistic shifts**.
3. **Task Independence:** The DP convolution assumes reference choices across tasks are drawn independently. If human authors or test designers share systematic stylistic biases across tasks (correlated references), the product distribution assumption is violated.

---

## 9. Note on Equivalence-Class Sampling

In domains with multiple valid solutions, should reference sampling be uniform over raw syntactical solutions $V_i$, or uniform over semantic equivalence classes $\mathcal{C}_i$?

- **Concurrency (`sync` family):** Traces admit a formal equivalence relation via **Mazurkiewicz trace theory**, where two execution traces are equivalent iff they differ only by permutations of independent (non-conflicting) operations. Here, sampling uniformly over equivalence classes corresponds to weighting each trace $r$ by $\frac{1}{|[r]|}$. This is formally defensible.
- **CPU Scheduling (`scheduling` family):** Valid schedules (e.g., tie-breaking between processes with equal burst time under SJF) represent distinct operational schedules. No canonical algebraic equivalence relation collapses them without making arbitrary domain assumptions.
- **Deadlock Avoidance (`banker` family):** Different safe sequences represent distinct topological sorts of resource allocations. While all avoid deadlock, they are not executionally equivalent traces.

**Conclusion:** Only the synchronization family has a mathematically defensible equivalence relation (Mazurkiewicz traces), and even there, only if trace equivalence classes are formally characterized and partitioned. Uniform sampling over the raw valid space remains the most transparent baseline.
