# Threats to Validity: Mechanism-Grounded Evidence Verification (MGEV)

This document explicitly outlines the potential internal, external, construct, and statistical validity threats associated with MGEV.

---

## 1. Internal Validity

### A. Simulator Fidelity & Bounded Mechanics
- *Threat*: Educational simulators for CPU scheduling, paging, process lifecycle, and deadlock model idealized operational semantics rather than hardware-level corner cases (e.g. TLB misses, cache pollution, interrupts).
- *Mitigation*: Simulators were validated against standard OS textbook definitions (OSTEP, Silberschatz) and verified with rigorous unit tests.

### B. LLM Claim Decomposition Accuracy
- *Threat*: The claim decomposer might misidentify preconditions, target mechanisms, or expected state variables from student questions.
- *Mitigation*: Structured claim schema validation and fallback to textual RAG for unmapped mechanisms prevent broken contracts.

---

## 2. External Validity & Generalization

### A. Domain Specificity to Operating Systems
- *Threat*: Results obtained on OS course materials may not immediately generalize to soft or non-mechanistic domains (e.g. history, literature).
- *Mitigation*: MGEV is explicitly scoped to procedural technical domains with deterministic operational semantics (OS, Networking, Compilers, DB Internals).

### B. Corpus Bounds
- *Threat*: Course corpus coverage is limited to lecture slides and OSTEP textbook chapters.
- *Mitigation*: All claims preserve strict citation provenance back to slide titles and textbook section headings.

---

## 3. Construct Validity

### A. Synthetic Corrupted Answer Benchmark
- *Threat*: Manually constructed claim corruptions might introduce artificial distribution shifts compared to real student misconception queries.
- *Mitigation*: Corruption patterns were modeled after documented OS student misconceptions (e.g., Belady's Anomaly overgeneralization, invalid state transition directly from BLOCKED to RUNNING).

---

## 4. Statistical Validity

### A. Paired Evaluation Design
- *Threat*: Variance in LLM output generation across non-deterministic runs.
- *Mitigation*: Experiments used fixed random seeds and paired evaluation across identical question sets in OS-MechanismBench.
