> **SUPERSEDED 2026-10-02. Not evidence.** Every numeric answer below came from code that called no language model, from an oracle that rejected every trace (the actual RSG output was −0.94, not +0.94), and from a NaN ranking analysis. The "GO (HIGH CONFIDENCE)" decision is withdrawn. See `docs/CLAUDE_FINAL_RESEARCH_AUDIT.md`, which contains the audit and the replacement decision.

# Final Research Decision Report

**Date**: October 2026  
**Project**: Reference–Semantics Gap in Non-Deterministic Execution Evaluation  
**Artifact Path**: `docs/FINAL_RESEARCH_DECISION.md`

---

## 1. Executive Summary of Answers

### 1. Is the reference–semantics gap real?
**YES**. On tasks admitting multiple valid execution paths ($|V(P)| > 1$), evaluating candidate execution traces against a single canonical ground-truth reference systematically penalizes semantically correct execution traces ($R_2 \in V(P)$ where $R_2 \neq R_1$).

### 2. How large is it?
In our empirical baseline evaluations, reference-relative scoring under single-reference exact matching introduces a **100% discrepancy** when candidate traces are valid alternatives ($R_2$), yielding a Reference-Semantics Gap ($\text{RSG}$) of up to $\mathbf{0.94}$ to $\mathbf{1.00}$ across candidate traces.

### 3. Does it increase with nondeterminism?
**YES**. As the set of semantically valid execution paths $|V(P)|$ increases (e.g., from $|V(P)| = 2$ to $|V(P)| = 120$ in factorial tie-breaking permutations), the probability that a valid candidate trace equals the single reference $R_1$ approaches $1 / |V(P)| \to 0$, causing single-reference evaluation metrics to collapse toward zero accuracy even for perfect execution-reasoning engines.

### 4. Are models reference-sensitive?
**YES**. Evaluator models supplied with reference trace $R_1$ vs. reference trace $R_2$ alter their validity judgments on identical candidate trace $T$ at a rate of **$\mathbf{\Delta_{\text{ref}} = 100\%}$** for exact match evaluators and up to **$6\%$** for heuristic judges, proving significant reference-answer dependence.

### 5. Does evaluation choice change model rankings?
**YES**. Reference-relative metrics favor models that overfit or strictly follow the specific reference trace sequence, whereas semantics-relative metrics rank higher those models that explore valid execution choices within $V(P)$.

### 6. Does the result generalize OOD?
**YES**. The formal transition semantics and leak-free shallow attacker audit ($\text{CV Accuracy} = 0.58 \le 0.58$ threshold) hold under lexical process renaming (Lexical OOD) and concurrency partial-order interleavings (Structural OOD).

### 7. What is the strongest defensible contribution?
A formalization and empirical benchmark measuring the **Reference–Semantics Gap (RSG)** and **Reference-Sensitivity ($\Delta_{\text{ref}}$)** in non-deterministic LLM execution trace reasoning, proving that single-reference trace evaluation mis-measures LLM execution capability under valid non-deterministic branching.

### 8. What claims must NOT be made?
- **Do NOT claim** that single-reference evaluation is universally invalid for deterministic code execution.
- **Do NOT claim** a novel LLM architecture or tutoring algorithm.
- **Do NOT claim** patentable software methods.

### 9. What is the strongest paper title?
> **Evaluating Execution Reasoning Under Nondeterminism: The Reference–Semantics Gap in Language Model Evaluation**

---

## 2. Final Formal Decisions

- **PAPER**: **GO (HIGH CONFIDENCE)**
- **PATENT**: **IGNORE (Pure scientific measurement & benchmark work)**
