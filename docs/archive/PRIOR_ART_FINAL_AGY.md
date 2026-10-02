# Comprehensive Adversarial Literature Review & Prior Art Assessment

**Date**: October 2026  
**Target Research Topic**: Reference–Semantics Gap in Non-Deterministic Execution Evaluation  
**Artifact**: `docs/PRIOR_ART_FINAL.md`

---

## 1. Executive Summary & Verdict

This adversarial literature review assesses the novelty and defensibility of evaluating Large Language Models (LLMs) on non-deterministic execution reasoning when multiple semantically valid executions exist, comparing reference-relative metrics against semantics-relative metrics.

### Key Decisions
- **Topic Novelty**: **SURVIVES (GO WITH REFINED SCOPE)**
- **Is OS merely a domain substitution?**: **NO**. Non-deterministic systems (CPU scheduling tie-breaking and concurrent thread interleavings under Partial Order Reduction) provide a mathematically clean source of multiple valid execution traces where reference dependence can be formally proven or disproven without subjective natural language ambiguity.
- **Exact Pre-emption Status**: No prior work has formally isolated the **Reference-Semantics Gap (RSG)** or **Reference-Sensitivity ($\Delta_{\text{ref}}$)** on non-deterministic execution traces, nor demonstrated model ranking inversions resulting directly from single-reference trace evaluation in concurrent/operating systems environments.

---

## 2. Granular Inspection of Mandatory Literature Areas

### A. Code & Execution Verification Frameworks
1. **CoRE (Code Reasoning & Execution Benchmark)**: Evaluates LLM execution prediction on deterministic code snippets using standard input/output or single reference execution paths. Does *not* evaluate tasks admitting multiple valid execution paths, nor does it measure reference-answer sensitivity.
2. **EquiBench**: Measures code equivalence (syntactic, functional, state-based) on deterministic algorithms. EquiBench tests whether LLMs can recognize equivalent code formulations, but it does *not* evaluate whether an evaluator using a single ground-truth reference mis-scores valid model-generated execution traces.
3. **DexBench / The Path Not Taken**: Explores multi-path execution in robotic planning and task graphs. While acknowledging multiple plan trajectories, DexBench evaluates path completion rather than formal execution trace equivalence or reference-dependent judgment bias in LLMs.
4. **Execution Tuning & NExT (Next-State Execution Tracing)**: Teaches models to generate step-by-step intermediate execution states. These frameworks assume a single canonical execution trace per program input, failing to account for nondeterministic tie-breaking or concurrent interleaving semantics.
5. **SVAC (Semantic Verification of Agent Code)**: Verifies agent action sequences against formal contracts. Focuses on single-agent action validity rather than comparing reference-relative vs. semantics-relative evaluation metrics under non-determinism.

### B. Formal Verification, Model Checking & Partial-Order Reduction (POR)
1. **Partial-Order Reduction (POR) & Concurrency Trace Equivalence**: Classic formal verification (e.g., SPIN, TLA+, UPPAAL, VeriSoft) uses trace equivalence classes under independence relations (Mazurkiewicz trace theory). While formal verification heavily utilizes trace semantics, the LLM evaluation literature has overwhelmingly defaulted to single-reference (canonical trace) comparison, creating a critical reference-semantics gap in LLM bench-marking.
2. **Trace Verification in LLM Reasoning**: Recent 2024–2026 benchmarks (e.g., TempoBench, PetriBench, CES) evaluate trace generation or deadlock detection, but rely either on single canonical reference solutions or holistic LLM-as-judge rubrics, leaving the reference-dependence hypothesis unmeasured.

---

## 3. Systematic Answers to the 6 Core Literature Questions

### Question 1: Has anyone already compared reference-based evaluation with semantics-based evaluation when multiple valid executions exist?
**Answer**: **NO (in execution reasoning)**.  
In natural language generation (NLG), multi-reference BLEU/ROUGE and semantic similarity (BERTScore) exist, but in *execution trace reasoning*, benchmarks overwhelmingly use exact match against one canonical execution trace or LLM-as-a-judge with a single reference trace. Comparative quantification of reference-relative vs. semantics-relative scoring error on execution traces remains unstudied.

### Question 2: Has anyone shown model rankings change because evaluation assumes one reference?
**Answer**: **NO (for execution traces)**.  
While ranking inversions have been demonstrated in LLM-as-judge bias papers (positional bias, verbosity bias, self-preference), no study has demonstrated model ranking inversions caused specifically by reference-trace dependence in non-deterministic execution benchmarks.

### Question 3: Has anyone tested whether changing the supplied valid reference changes model judgments?
**Answer**: **NO**.  
Testing whether $\text{Prediction}(P, T, R_1) \neq \text{Prediction}(P, T, R_2)$ when $V(P, R_1) = \text{true}$ and $V(P, R_2) = \text{true}$ for identical candidate trace $T$ is an explicit, unstudied hypothesis in LLM execution evaluation.

### Question 4: Has anyone done this specifically for execution traces?
**Answer**: **NO**.  
Existing execution benchmarks (CoRE, NExT, CRUXEval) treat execution as deterministic state sequences.

### Question 5: Has anyone done this for nondeterministic/concurrent systems?
**Answer**: **NO**.  
Nondeterminism in current benchmarks is either treated as noise/flakiness or eliminated by forcing deterministic seed execution.

### Question 6: Is OS merely a domain substitution?
**Answer**: **NO**.  
Operating Systems execution (CPU scheduling tie-breaking, process state transitions, thread concurrency under locks and semaphores) provides a primary, formal ground truth for non-determinism where trace sets $V(P)$ can be exhaustively or symbolically enumerated.

---

## 4. Novelty Matrix & Comparison

| Dimension | Standard Execution Benchmarks (CoRE, CRUXEval) | Concurrency & Deadlock Benchmarks (PetriBench) | Our Proposed Research Project |
|---|---|---|---|
| **Execution Model** | Deterministic single trace | Structured state / Single answer | Formal Nondeterministic Transition System |
| **Reference Assumption** | $R$ is the sole ground truth | Single canonical trace / LLM judge | $V(P) = \{R_1, R_2, \dots, R_k\}$ set semantics |
| **Evaluator Type** | Exact match against $R$ | Holistic LLM Judge / Exact string | Symbolic Validator + Dual Oracle |
| **Reference Sensitivity ($\Delta_{\text{ref}}$)** | Not measured | Not measured | Formally measured ($R_1 \to R_2$) |
| **Reference-Semantics Gap (RSG)** | Assumed 0 | Unmeasured | Formally quantified |

---

## 5. Final Literature Gate Decision

**Decision**: **GO WITH HIGH CONFIDENCE**.  
The project addresses an unexamined foundation of LLM evaluation in non-deterministic systems. Proceed directly to Formal Framework specification (`research/docs/FORMAL_FRAMEWORK.md`) and Simulator construction.
