# Formal Definition of Reference-Choice Robustness (RCR)

## 1. Mathematical Task & Solution Space Formalization

Let \(x \in \mathcal{X}\) be an executable reasoning task defined over a state transition domain \(\mathcal{S}\).
Let \(\mathcal{Y}\) be the language of candidate execution trajectories.

### Definition 1 (Formal Valid-Solution Space \(V(x)\))
The complete valid-solution space \(V(x) \subseteq \mathcal{Y}\) is the set of all trajectories \(y \in \mathcal{Y}\) that satisfy the domain transition rules and task constraints of \(x\):

$$V(x) \triangleq \{ y \in \mathcal{Y} \mid \text{RulesCheck}(x, y) = \text{TRUE} \land \text{ConstraintsCheck}(x, y) = \text{TRUE} \}$$

Each solution \(y \in V(x)\) is validated independently of any selected reference trajectory.

---

## 2. Reference Regimes & Reference Distributions

### Definition 2 (Reference Vector \(\mathbf{R}\))
For a benchmark dataset of \(N\) tasks \(\mathcal{X} = \{x_1, x_2, \dots, x_N\}\), a reference vector \(\mathbf{R} = (R_1, R_2, \dots, R_N)\) is a joint selection of valid reference trajectories:

$$\mathbf{R} \in \prod_{k=1}^N V(x_k)$$

### Definition 3 (Neutral Reference Distribution \(\mathcal{D}_R\))
Let \(\mathcal{D}_R\) be a probability distribution over the reference space \(\prod_{k=1}^N V(x_k)\).
- **Canonical Reference Selection**: \(\mathbf{R}_{\text{canonical}} = (R_{1,0}, R_{2,0}, \dots, R_{N,0})\) where \(R_{k,0}\) is the single gold reference chosen by the benchmark designer.
- **Uniform Reference Distribution \(\mathcal{U}_{\text{valid}}\)**: Independent uniform draw over \(V(x_k)\) for each task \(x_k\):

  $$\mathbf{R} \sim \mathcal{U}_{\text{valid}} \iff R_k \sim \text{Uniform}(V(x_k)), \quad \forall k \in \{1, \dots, N\}$$

---

## 3. Evaluator Class Definitions

An evaluator \(E(y \mid R)\) outputs a binary or scalar verdict for candidate trajectory \(y\) relative to reference \(R\):

1. **Strict Canonical Match (\(E_1\))**:
   $$E_1(y \mid R) \triangleq \mathbb{I}\left[ \text{Squash}(y) == \text{Squash}(R) \right]$$

2. **Normalized Trajectory Match (\(E_2\))**:
   $$E_2(y \mid R) \triangleq \mathbb{I}\left[ \text{Normalize}(y) == \text{Normalize}(R) \right]$$

3. **Executable Semantic Oracle (\(E_3\))**:
   $$E_3(y, x) \triangleq \mathbb{I}\left[ y \in V(x) \right]$$
   *(Note: \(E_3\) is reference-invariant: \(\forall R_1, R_2 \in V(x), \, E_3(y \mid R_1) \equiv E_3(y \mid R_2)\)).*

---

## 4. Benchmark Conclusion Instability Quantities

For a model set \(\mathcal{M} = \{m_1, \dots, m_M\}\) and candidate output set \(\{y_{m,k}\}\), the benchmark evaluation under reference selection \(\mathbf{R}\) induces:

1. **Model Score**:
   $$S_m(E \mid \mathbf{R}) \triangleq \frac{1}{N} \sum_{k=1}^N E(y_{m,k} \mid R_k)$$

2. **Model Ranking**:
   $$\text{Rank}_E(\mathbf{R}) \triangleq \text{argsort}_{m \in \mathcal{M}} \left( -S_m(E \mid \mathbf{R}) \right)$$

3. **Pairwise Winner Identity**:
   $$\text{Winner}_{A,B}(E \mid \mathbf{R}) \triangleq \text{sign}\left(S_A(E \mid \mathbf{R}) - S_B(E \mid \mathbf{R})\right)$$

4. **Statistical Significance Decision (\(\alpha = 0.05\))**:
   $$D_{A,B}(E \mid \mathbf{R}) \in \{ \text{SIG\_A\_WINS}, \text{SIG\_B\_WINS}, \text{NON\_SIGNIFICANT} \}$$

---

## 5. Reference-Choice Robustness (RCR) Metric

### Definition 4 (Oracle Recovery Rate \(RCR(E; \mathcal{D}_R)\))
The Reference-Choice Robustness / Oracle Recovery Rate of an evaluator \(E\) under reference distribution \(\mathcal{D}_R\) is the probability that the model ranking induced by reference-dependent evaluation under \(\mathbf{R} \sim \mathcal{D}_R\) matches the reference-invariant ranking of the executable semantic oracle \(E_3\):

$$RCR(E; \mathcal{D}_R) \triangleq \mathbb{P}_{\mathbf{R} \sim \mathcal{D}_R} \left[ \text{Rank}_E(\mathbf{R}) == \text{Rank}_{E_3} \right]$$

### Distinction: Exact Enumeration vs. Monte Carlo Estimation
- **Exact RCR**: Computed by exhaustive enumeration over the finite joint space \(\prod_{k=1}^N V(x_k)\) when computationally feasible.
- **Monte Carlo RCR**: Estimated via \(B\) independent random draws \(\mathbf{R}^{(1)}, \dots, \mathbf{R}^{(B)} \sim \mathcal{D}_R\) with standard error \(\sqrt{\frac{\hat{p}(1-\hat{p})}{B}}\).
