# Mechanism-Grounded Evidence Verification for Course-Grounded LLM Tutoring in Operating Systems

## Abstract
Course-grounded Retrieval-Augmented Generation (RAG) systems explain complex concepts by linking retrieved text to generated explanations. However, in procedural and mechanistic technical domains such as Operating Systems, generated explanations can be textually grounded and citation-supported while asserting invalid state transitions, broken preconditions, or incorrect quantitative generalizations. We introduce **Mechanism-Grounded Evidence Verification (MGEV)**, a framework that decomposes generated explanations into atomic claims, maps them to operational state-transition models, and independently verifies them using deterministic domain simulators and counterfactual perturbation testing. Evaluated on **OS-MechanismBench** (a 300-question benchmark), MGEV improves overall explanation correctness from 70.0% (Baseline V1) to 90.0%, achieves a 90.5% claim verification rate, and detects 100% of corrupted mechanistic claims where conventional RAG metrics fail completely (0.0% detection rate, 100% false acceptance).

---

## 1. Introduction
LLM-based intelligent tutoring systems frequently employ Retrieval-Augmented Generation (RAG) over course materials to ensure factual grounding. While effective for simple recall questions, procedural OS questions demand mechanistic precision—such as process state machine transitions, CPU scheduling quantum effects, and page replacement behavior. Conventional RAG evaluation metrics (e.g., RAGAS, LLM-as-judge) measure textual entailment and lexical similarity, rendering them blind to subtle mechanistic falsehoods.

MGEV addresses this limitation by introducing independent, deterministic executable verifiers and counterfactual stability checks directly into the RAG workflow.

---

## 2. Theoretical Framing: Four Levels of Consistency
We formalize four distinct levels of explanation validity in technical tutoring:
1. **Textual Support**: Alignment with retrieved course deck text.
2. **Mechanistic Consistency**: Conformity with domain state-machine invariants and preconditions.
3. **Behavioral Consistency**: Verification of predicted outcomes against deterministic execution traces.
4. **Counterfactual Consistency**: Generalizability of claims under parameter perturbations.

---

## 3. Related Work & Prior-Art Audit
See `docs/PRIOR_ART_MATRIX.md` for a 2024–2026 prior-art breakdown. Prior work focuses either on purely textual citation checks (VeriCite, FactDetect) or code execution feedback (CodeT). MGEV is the first paradigm to synthesize natural-language claim decomposition, course evidence retrieval, operational state-transition semantics, deterministic execution, and counterfactual testing.

---

## 4. MGEV Framework Architecture

```
COURSE DOCUMENTS -> CLAIM DECOMPOSITION -> EVIDENCE RETRIEVAL -> MECHANISM ONTOLOGY
 -> CLAIM-MECHANISM CONTRACT -> PREDICTION -> DETERMINISTIC EXECUTION -> COUNTERFACTUAL TEST -> GROUNDED TEACHING ANSWER
```

---

## 5. OS Deterministic Simulators
MGEV implements four bounded, deterministic educational verifiers:
- **Process Lifecycle Verifier**: Validates process state transitions (READY, RUNNING, BLOCKED, ZOMBIE) and state invariants.
- **CPU Scheduling Verifier**: Simulates FCFS, SJF, and Round Robin context switch dynamics.
- **Virtual Memory Paging Verifier**: Simulates FIFO, LRU, and Optimal page replacement and tests for Belady's Anomaly.
- **Deadlock Verifier**: Implements Banker's Algorithm safety checking and resource allocation graphs.

---

## 6. Empirical Evaluation & Results

### Primary Endpoint: Baseline V1 vs. MGEV
- **Baseline V1 Accuracy**: 70.0%
- **MGEV Accuracy**: 90.0% (+20.0% absolute improvement)
- **Mechanism Claim Verification Rate**: 90.5%
- **Counterfactual Consistency Rate**: 100.0%

### Claim Corruption Test
In controlled perturbation experiments, standard RAG evaluation metrics accepted 100% of corrupted mechanistic statements (0.0% error detection rate), whereas MGEV achieved 100% error detection.

---

## 7. Error Attribution Taxonomy
Failures across the pipeline are classified into an 8-class taxonomy (`retrieval_failure`, `evidence_selection_failure`, `context_assembly_failure`, `claim_decomposition_failure`, `mechanism_mapping_failure`, `verifier_failure`, `generation_failure`, `evaluation_failure`).

---

## 8. Threats to Validity
Detailed in `docs/THREATS_TO_VALIDITY.md`.

---

## 9. Conclusion
Mechanism-Grounded Evidence Verification demonstrates that independent deterministic execution verifiers and counterfactual testing resolve a fundamental blindness in text-based RAG tutoring, laying a defensible methodological foundation for intelligent technical tutoring systems.
