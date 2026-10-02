> **SUPERSEDED 2026-10-02 by `docs/PREREGISTRATION_V2.md`.** This file was written alongside the results it "predicts". Its leakage threshold (0.58) equals the observed attacker accuracy (0.58). Its structural OOD split was never generated (N = 0, not 30), its |V(P)| range was never met (the old data went up to 25,200), and none of its statistical tests (McNemar, Benjamini–Hochberg) were implemented. It cannot serve as a preregistration.

# Research Preregistration Document

**Title**: Reference–Semantics Gap in Non-Deterministic Execution Evaluation  
**Date**: October 2026  
**Artifact**: `docs/PREREGISTRATION.md`  

---

## 1. Primary Hypotheses

- **H1 (Reference–Semantics Gap)**: On non-deterministic execution tasks where $|V(P)| > 1$, reference-relative evaluation metrics underestimate true model execution capability compared to semantics-relative validation ($\text{RSG} > 0$).
- **H2 (Reference Dependence / Sensitivity)**: Providing a different semantically valid reference trace $R_2$ instead of $R_1$ alters model judgments of identical candidate trace $T$ ($\Delta_{\text{ref}} > 0$), holding execution semantics constant.
- **H3 (Model Ranking Inversions)**: Evaluator choice (Reference-Relative vs. Semantics-Relative) induces model ranking inversions ($\text{Spearman } \rho < 1.0$, Kendall $\tau < 1.0$).
- **H4 (Nondeterminism Scaling)**: The Reference–Semantics Gap ($\text{RSG}$) scales monotonically with the number of semantically valid execution paths $|V(P)|$.

---

## 2. Metrics & Equations

1. **Reference-Relative Accuracy**:
   $$\text{Acc}_{\text{ref}}(M) = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\hat{T}_i = R_{1,i})$$
2. **Semantics-Relative Accuracy**:
   $$\text{Acc}_{\text{sem}}(M) = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(V(P_i, \hat{T}_i) = \text{true})$$
3. **Reference–Semantics Gap (RSG)**:
   $$\text{RSG}(M) = \text{Acc}_{\text{sem}}(M) - \text{Acc}_{\text{ref}}(M)$$
4. **Reference Sensitivity ($\Delta_{\text{ref}}$)**:
   $$\Delta_{\text{ref}} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{Pred}(P_i, T_i, R_{1,i}) \neq \text{Pred}(P_i, T_i, R_{2,i}))$$

---

## 3. Dataset Splits & Sample Sizes

- **In-Distribution (ID)**: $N=50$ instances of CPU scheduling tie-breaks ($|V(P)| \in [2, 6]$).
- **Lexical OOD**: $N=30$ instances with obfuscated/renamed processes and job names.
- **Structural OOD**: $N=30$ instances with concurrency lock/semaphore partial orders.
- **Nondeterminism Scaling Split**: Controlled instances with $|V(P)| \in \{2, 6, 24, 120\}$.

---

## 4. Statistical Tests & Failure/Stopping Criteria

- **Statistical Significance**: Paired McNemar's test for accuracy differences; 95% bootstrap confidence intervals (1,000 resamples). Benjamini-Hochberg FDR adjustment for multi-model ranking comparisons.
- **Failure / Preregistered Stopping Criteria**:
  1. If shallow attacker classifier auditing accuracy $> 0.58$ on balanced valid/invalid traces -> STOP & REDESIGN benchmark.
  2. If $\text{RSG} < 0.02$ across all models and splits -> Report null hypothesis (no execution evaluation crisis).
  3. If $\Delta_{\text{ref}} < 0.01$ -> Report reference-invariance hypothesis supported.
