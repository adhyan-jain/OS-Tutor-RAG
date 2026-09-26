# Formalization of the Research Gap: Mechanism-Grounded Evidence Verification (MGEV)

## 1. Problem Statement

Conventional course-grounded Retrieval-Augmented Generation (RAG) systems evaluate explanation quality primarily through text-level metrics:
- **Retrieval Recall / Precision** (Did we fetch relevant text?)
- **Faithfulness / Grounding** (Is the text supported by the retrieved context?)
- **Answer Relevance / Correctness** (Does the output sound reasonable to an LLM judge?)

However, in procedural and mechanistic technical domains such as Operating Systems, an explanation can be:
1. Lexically grounded in course slides,
2. Citation-supported by textbook passages,
3. Coherent and plausible in natural language, and
4. Rated as highly faithful by conventional LLM judges,

**while still asserting a wrong state transition, illegal precondition, broken invariant, or incorrect quantitative/causal relationship.**

---

## 2. Theoretical Framing: Four Levels of Consistency

To address this gap, we formalize four distinct levels of explanation validity:

```
[ A. Textual Support ]
       │
       ▼
[ B. Mechanistic Consistency ]
       │
       ▼
[ C. Behavioral Consistency ]
       │
       ▼
[ D. Counterfactual Consistency ]
```

### Level A: Textual Support
*Definition*: Does the retrieved course evidence explicitly mention the concepts, terms, or definitions contained in the generated explanation?
*Failure Mode*: Hallucination of course terminology or citing irrelevant slide pages.

### Level B: Mechanistic Consistency
*Definition*: Do the claims align with the theoretical state-transition model, invariants, and preconditions defined by the operating system domain ontology?
*Failure Mode*: Asserting that a blocked process can be directly scheduled by the CPU without an intervening interrupt/unblock event.

### Level C: Behavioral Consistency
*Definition*: When the generated claim's parameters, initial state, and event sequences are executed on a deterministic verifier/simulator, does the observed trace match the predicted outcome?
*Failure Mode*: Claiming that a specific process sequence with SJF scheduling yields 3 context switches when the execution trace proves it yields 5.

### Level D: Counterfactual Consistency
*Definition*: Does the explanation hold up under controlled perturbations of parameters, or does it overgeneralize local behavior into an incorrect universal rule?
*Failure Mode*: Stating "Reducing Round Robin quantum always increases context switches" without accounting for process arrival times, CPU burst patterns, or completion boundaries.

---

## 3. Central Research Question

> **"Can mechanism-grounded independent verification detect and reduce errors in course-grounded RAG explanations that conventional text-based RAG evaluation fails to detect?"**

---

## 4. Key Failure Cases Ignored by Standard RAG Evaluation

| Error Type | Example Statement | Standard RAG Judgment | MGEV Judgment |
| :--- | :--- | :--- | :--- |
| **Flawed Causal Conclusion** | "Because Round Robin uses time slices, process priority increases with each quantum expiry." | **PASS** (High textual similarity to scheduling terms) | **FAIL** (Priority queue mechanism violated) |
| **Invalid Precondition** | "When a process issues a read() system call, it enters the RUNNING state to await disk IO." | **PASS** (Text contains read, system call, process state) | **FAIL** (Blocked state transition invariant violated) |
| **Overgeneralization** | "Adding more physical frames always reduces page faults." | **PASS** (Matches general virtual memory context) | **FAIL** (Fails Belady's Anomaly counterfactual check) |
| **Quantitative Error** | "With FIFO replacement on ref string [1,2,3,1,4] and 3 frames, 3 page faults occur." | **PASS** (Plausible numerical statement) | **FAIL** (Deterministic paging simulator observes 4 faults) |
