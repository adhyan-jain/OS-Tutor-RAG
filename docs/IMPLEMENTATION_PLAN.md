# Comprehensive Research Implementation Plan: Mechanism-Grounded Evidence Verification (MGEV)

## System Architecture Blueprint

```
                          ┌───────────────────────────┐
                          │    Student Question       │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │ Mechanism-Aware Parser    │
                          │ & Question Classifier     │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┴───────────────────────────┐
           │                                                        │
           ▼ (Mechanism-Sensitive Question)                          ▼ (Factual / Conceptual)
 ┌───────────────────────────┐                            ┌───────────────────────────┐
 │ Atomic Claim Decomposition│                            │ Standard Dense/HyDE RAG   │
 └─────────────┬─────────────┘                            │ (Baseline V1 Pipeline)    │
               │                                          └─────────────┬─────────────┘
               ▼                                                        │
 ┌───────────────────────────┐                                          │
 │ Claim-Driven Retrieval    │                                          │
 │ & Course Evidence Mapping │                                          │
 └─────────────┬─────────────┘                                          │
               │                                                        │
               ▼                                                        │
 ┌───────────────────────────┐                                          │
 │ Mechanism Contract Engine │                                          │
 │ (State/Event/Precondition)│                                          │
 └─────────────┬─────────────┘                                          │
               │                                                        │
               ▼                                                        │
 ┌───────────────────────────┐                                          │
 │ Executable Verifiers      │                                          │
 │ & Counterfactual Engine   │                                          │
 └─────────────┬─────────────┘                                          │
               │                                                        │
               ▼                                                        │
 ┌───────────────────────────┐                                          │
 │ Verification Synthesis    │                                          │
 │ (Pass/Conditional/Fail)   │                                          │
 └─────────────┬─────────────┘                                          │
               │                                                        │
               └────────────────────────────┬───────────────────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │ Final Grounded Answer     │
                              │ & Verification Report     │
                              └───────────────────────────┘
```

---

## Phases & Deliverables

### Phase 0: Literature & Research Gap Formalization
- **Objective**: Complete prior-art audit and formalize theoretical research gap.
- **Files**:
  - `docs/PRIOR_ART_MATRIX.md`
  - `docs/RESEARCH_GAP.md`
- **Success Criteria**: Clear distinction from existing work established and documented.

### Phase 1: Baseline Freeze & Repository Alignment
- **Objective**: Freeze existing `OS-Tutor-RAG` pipeline components as Baseline V1.
- **Files**:
  - `src/config.py` (Preserve default baseline configs)
  - `src/pipeline.py` (Ensure baseline pipeline execution remains unimpaired)
- **Success Criteria**: Existing retrieval and RAGAS evaluations run reproducibly.

### Phase 2: Mechanism Representation & Schema Definition
- **Objective**: Implement ontology, schemas, and contract models for OS mechanisms.
- **Files**:
  - `src/mechanism/schema.py` (Claim–Evidence–Mechanism Contract Dataclasses)
  - `src/mechanism/ontology.py` (States, Events, Transitions, Invariants)
  - `src/mechanism/provenance.py` (Evidence citation linkage)
  - `src/mechanism/validator.py` (Semantic structure validator)
- **Success Criteria**: Strong typing and validation for claims, states, events, and evidence.

### Phase 3: Deterministic Executable Educational Simulators
- **Objective**: Implement safe, bounded, deterministic simulators for 4 core OS domains.
- **Files**:
  - `src/verification/base.py` (Base Verifier Interface)
  - `src/verification/process.py` (Process Lifecycle & State Machine Verifier)
  - `src/verification/scheduler.py` (CPU Scheduling: FCFS, SJF, Round Robin Verifier)
  - `src/verification/paging.py` (Paging & Page Replacement Algorithms: FIFO, LRU, Optimal)
  - `src/verification/deadlock.py` (Banker's Algorithm & Resource Allocation Graph Verifier)
  - `tests/test_verifiers.py` (Unit tests for all simulators)
- **Success Criteria**: 100% deterministic, exact execution traces for verified operational semantics.

### Phase 4: Mechanism-Aware Query Parsing & Claim Decomposition
- **Objective**: Classify questions and decompose mechanism queries into atomic claims.
- **Files**:
  - `src/query/question_classifier.py` (Classify factual vs. mechanism/procedural/counterfactual)
  - `src/query/claim_decomposer.py` (Extract atomic claims, preconditions, and expected outcomes)
  - `src/query/mechanism_parser.py` (Map queries to target OS mechanisms)
- **Success Criteria**: Reliable extraction of structured claims without hallucinating execution targets.

### Phase 5: Claim-Driven Evidence Retrieval & Contract Synthesis
- **Objective**: Perform claim-level retrieval and construct Claim–Evidence–Mechanism Contracts.
- **Files**:
  - `src/retrieval/claim_retriever.py` (Per-claim retrieval and coverage scoring)
  - `src/mechanism/contract_builder.py` (Synthesize structured contracts for verification)
- **Success Criteria**: Quantifiable claim coverage metric and citation tracking per claim.

### Phase 6: Verification Engine & Counterfactual Perturbation
- **Objective**: Execute verifiers against contracts and test counterfactual variations.
- **Files**:
  - `src/verification/engine.py` (Orchestrate prediction vs observation matching)
  - `src/verification/counterfactual.py` (Generate parameter perturbations and evaluate stability)
- **Success Criteria**: Structured outputs (`PASS`, `CONDITIONAL`, `FAIL`, `UNVERIFIABLE`) with exact reasons.

### Phase 7: OS-MechanismBench Benchmark & Corruption Corpus
- **Objective**: Construct a benchmark focused on OS mechanism reasoning and corruption detection.
- **Files**:
  - `eval/OS_MechanismBench.json` (Annotated question set across 7 categories)
  - `eval/corrupted_answers.json` (Controlled answer perturbations for detection sensitivity tests)
  - `eval/benchmark_builder.py` (Benchmark loading, validation, and splitting)
- **Success Criteria**: High-quality, verified benchmark covering factual, procedural, counterfactual, and misconception cases.

### Phase 8: Comprehensive Evaluation Harness & Error Attribution
- **Objective**: Execute multi-dimensional evaluations comparing Baseline V1 vs. MGEV.
- **Files**:
  - `eval/mgev_eval.py` (Primary MGEV evaluation suite)
  - `eval/corruption_eval.py` (Claim corruption sensitivity test harness)
  - `eval/ablation_eval.py` (Systematic ablation study harness)
  - `eval/error_attribution.py` (8-class error taxonomy classifier)
- **Success Criteria**: Full reproducibility of baseline vs MGEV tables and failure taxonomies.

### Phase 9: Scientific Artifacts & Draft Paper Synthesis
- **Objective**: Generate publication-ready tables, figures, threats to validity, and draft manuscript.
- **Files**:
  - `docs/THREATS_TO_VALIDITY.md`
  - `docs/PAPER_DRAFT.md`
  - `scripts/generate_paper_tables.py`
- **Success Criteria**: Complete reproducible publication draft with clean empirical grounding.
