# Prior-Art Matrix: Mechanism-Grounded Evidence Verification (MGEV)

This document provides a comprehensive prior-art audit across educational RAG, citation/claim verification, LLM execution feedback, program verification, and domain-specific intelligent tutoring systems (2024–2026).

---

## 1. Prior-Art Audit Table

| Work / System | Problem | Methodology | Representation | Retrieval | Verification Approach | Textual vs Executable | NL Explanation Verification | State-Transition Semantics | Counterfactual Testing | OS Domain | Exact Overlap with MGEV | Exact Distinction from MGEV |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **VeriCite / FactDetect (2024-2025)** | Citation & claim hallucination in RAG | Atomic claim decomposition + NLI entailment checking against retrieved passages | Textual passages & atomic claim lists | Dense / Hybrid | Passage-level NLI entailment | Textual only | Yes | No | No | No (General QA) | Decomposes answers into atomic claims and checks individual claims against sources | NLI checks text entailment only; fails to verify whether supported text claims are mechanistically sound when executed |
| **CodeT / CodeX Execution Feedback (2024-2025)** | LLM code generation logic errors | Test execution feedback for code synthesis and self-correction | Executable unit tests / ASTs | None / Direct prompt | Deterministic sandbox execution of generated code | Executable | No (Code only) | Partial (Code state) | No | No (Programming) | Uses deterministic verifiers to test execution correctness | Verifies raw executable code, not natural-language educational explanations linked to course materials |
| **RagVerus / Formal Proof RAG (2025)** | Verification of complex domain logic in repository-level RAG | formal verifier (e.g. Lean / Verus) feedback loop on generated specifications | Formal proofs & code context | Graph / Vector | Automated theorem prover | Executable / Formal | No (Formal spec) | Yes (Invariants) | No | No | Integrates formal execution/proof checkers into a RAG pipeline | Requires formal proof definitions; MGEV targets natural language explanations in educational domains via operational state-transition models |
| **MemOS / Schema-Governed Agentic Tutors (2024-2025)** | Uncontrolled agentic state drifts in LLM tutors | Deterministic state machine governing LLM tutor actions | Finite State Machine (FSM) of pedagogical moves | Graph / Structured | State transition validation against pedagogical rules | Mixed | Partial (Tutor action) | Yes (Pedagogical state) | No | No | Models state transitions to constrain system behavior | Governs *tutor interaction state* (hints, turns), whereas MGEV models and verifies *domain subject-matter mechanisms* (OS process/memory state) |
| **GraphRAG in Education (2024-2025)** | Multi-hop conceptual gaps in course materials | Knowledge graph linking concepts, prerequisite relationships | Subject concept graph | Entity Graph RAG | Graph path validation | Textual | Yes | No | No | General STEM | Uses structured graph representation over course materials | Constructs entity/concept relations rather than operational state-transition-event semantics with executable verifiers |
| **Conventional Course-Grounded OS Tutors (Baseline)** | Student Q&A over OS course decks & textbooks | Standard RAG (Dense / RRF / HyDE) + LLM synthesis | Text chunks / Parent slides | Dense/BM25 | Textual RAGAS metrics (Faithfulness, Relevancy) | Textual | Yes | No | No | Yes (OS) | Course-grounded retrieval over OS slides/books | Relies on LLM parameter knowledge and textual similarity; accepts textually faithful but mechanistically false explanations |
| **MGEV (Proposed)** | Unchecked mechanistic errors & overgeneralization in OS RAG explanations | Claim–Evidence–Mechanism Contracts + Executable Simulators + Counterfactual Testing | Atomic Claim Contracts + OS Operational Semantics + Simulator Traces | Claim-driven Dense/Parent RAG | Deterministic simulation trace match & counterfactual perturbation testing | Executable & Textual | Yes | Yes (Process, CPU, Memory, Deadlock state transitions) | Yes | Yes (OS) | N/A (Proposed) | Unifies natural language claim decomposition, course evidence retrieval, state-transition mechanism grounding, deterministic execution, and counterfactual testing. |

---

## 2. Literature Audit Conclusion & Novelty Statement

We did **not** identify prior work in the reviewed literature (2024–2026) that combines:
1. Atomic natural-language claim decomposition over course materials,
2. Operational state-transition mechanism representation,
3. Independent deterministic executable verifiers for subject-matter mechanics, and
4. Controlled counterfactual perturbation testing for educational LLM explanations.

### Formal Scope of Claim
"We introduce a mechanism-grounded evidence verification (MGEV) framework for course-grounded LLM tutoring, in which generated natural-language claims are linked to curriculum evidence and operational state-transition representations and, where executable semantics are available, independently verified against deterministic domain models."
