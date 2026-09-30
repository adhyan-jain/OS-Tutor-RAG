# Current Project Audit

Audit date: 2026-09-30, commit `f1d4943`. This is not a novelty analysis. It establishes which results and resources are real. It does not defend the project.

**Method:** read the scoring and generation code, reran `eval/mgev_eval.py` and `eval/corruption_eval.py` to scratch paths (tracked result files untouched), and cross-checked FINDINGS.md numbers against `eval/pipeline_runs.xlsx` (sheet "Final Analysis"). Not yet done: re-execution of the RAGAS sweeps (needs local Ollama and GPU) and a review of the untracked notes.

**Labels:** experimentally verified / reproducibly computed / derived / hard-coded / synthetic / unsupported.
**Status:** SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED / UNKNOWN.

---

## Part A: MGEV claims (commit `f1d4943`, 2026-09-26)

**Bottom line: none of the MGEV headline numbers is evidence of anything about LLMs, RAG or tutoring. No LLM, retriever or baseline pipeline runs in either MGEV evaluation.** They must not appear in any paper recommendation.

### A1. OS-MechanismBench, 300 questions
- **Source:** `eval/benchmark_builder.py:8-110`; output `eval/OS_MechanismBench.json`.
- **Evidence:** every question comes from a `for i in range(...)` loop over a fixed template, e.g. "What is the definition of operating system mechanism concept #{i}…", ground truth "Concept #{i} defines core OS abstraction…". Counterfactual: "…in scenario #1?". Numerical: "Calculate the total number of context switches or page faults for workload #1." with no workload given. The 300 strings are distinct only because of the counter.
- **Reproducibility:** deterministic regeneration.
- **Label: SYNTHETIC.** Questions carry no answerable content. The numerical and code-trace items reference workloads and code snippets that do not exist.
- **Status: UNSUPPORTED as a benchmark.** It has no ground truth an LLM could be scored against.

### A2. "70% baseline" and "90% MGEV"
- **Source:** `eval/mgev_eval.py`; output `eval/mgev_results.json`.
- **Evidence:**
  - Questions with `requires_mgev=False` (factual 60, procedural 60, state_transition 60 = 180) are added to both `baseline_v1_correct` and `mgev_correct` unconditionally. No system is run on them.
  - For the remaining questions, baseline correctness is set by `q_type`: fail if counterfactual, misconception or numerical, else pass. It is a function of the label, not of any model output.
  - MGEV correctness is `all_passed` from the verifier run on **hard-coded** `verification_input` / `predicted_observation` values (RR quantum 2; RUNNING to BLOCKED; a fixed two-process case).
  - Runtime 0.0047 s: no model call is possible in that time.
- **Reproducibility:** rerun today reproduces exactly (70.0 / 90.0). Reproducible does not mean valid: the numbers are fixed by the code.
- **Label: HARD-CODED.** The 70% is almost entirely the auto-pass of 180 questions plus a rule assigning "pass" to code_trace; it is not a measured baseline.
- **Status: UNSUPPORTED** as a comparison of systems.

### A3. "Mechanism claim verification rate 90.5%" and "counterfactual consistency 100%"
- **Source:** `eval/mgev_eval.py`, `src/verification/counterfactual.py`.
- **Evidence:** the counterfactual check runs the same verifier on a baseline input and a perturbed input and reports CONDITIONAL if they differ. Both inputs are constants. Nothing an LLM said is examined. "Baseline counterfactual consistency 0.0%" in `docs/PAPER_TABLES.md` has no computation behind it in `mgev_eval.py`.
- **Label: DERIVED / hard-coded.** Simulator self-consistency, not model consistency.
- **Status: UNSUPPORTED** as evidence about explanation quality; **SUPPORTED** only as "the simulators run and are self-consistent on their inputs" (see `tests/test_verifiers.py`).

### A4. "100% corruption detection" and "100% textual-RAG false acceptance"
- **Source:** `eval/corruption_eval.py:75-124`; output `eval/corruption_results.json`.
- **Evidence:** 3 corrupted claims total (`corp_01`… ). `is_textual_accepted = True` is a **literal** assignment with the comment that textual RAG "accepts corrupted claim because it contains keywords and valid citations". No RAGAS metric, LLM judge or retriever is called. The MGEV arm (`corruption_eval.py:14-100`) does not parse the claim text: each item carries a hand-written `verification_input` and a hand-encoded `predicted_corrupted` observation (e.g. `{"asserts_always_fewer_faults_with_more_frames": True}`), and the simulator checks that structured prediction. So "detection" tests the simulators against a human's translation of the claim into structured form. It does not test whether an LLM's claim, or an automatic claim-to-contract translation, is verified. The natural-language-to-contract step, which is the hard part of the proposed method, is not exercised at all.
- **Reproducibility:** deterministic, and the textual arm is fixed by construction.
- **Label: HARD-CODED and SYNTHETIC; n = 3.**
- **Status: UNSUPPORTED.** The 100% textual false acceptance is an assumption written in code, not a measurement. It is also the paper's core claim.

### A5. Prior-art and novelty claims (`docs/PRIOR_ART_MATRIX.md`, `RESEARCH_GAP.md`)
- **Evidence:** 30- and 68-line documents naming VeriCite, CodeT, RagVerus, MemOS and "GraphRAG in Education". No claim checked against full texts in this audit.
- **Label: unsupported (Tier 4).** Status UNKNOWN pending the literature audit.

### A6. Simulators (paging, scheduler, deadlock, process)
- **Source:** `src/verification/*.py`, `tests/test_verifiers.py`.
- **Evidence:** deterministic implementations (FIFO/LRU/optimal, FCFS/SJF/RR, Banker's algorithm, process states). Unit tests exist; not run in this audit.
- **Label: real code, reproducibly computed on their inputs.**
- **Status: PARTIALLY SUPPORTED** (works on tested inputs; fidelity beyond them unverified). **Corpus mismatch:** `data/raw` has no paging, scheduling or deadlock lectures.

---

## Part B: Pre-MGEV RAG work (2026-07-24 to 2026-07-31)

These are real measured experiments with a local LLM stack. They are small and noisy, as their own caveats state.

| Claim (FINDINGS.md) | Evidence checked | Label | Status |
|---|---|---|---|
| Chunking defect (slide titles as standalone chunks) made BM25 look worst (F1, "headline finding") | Narrative and fix-effect numbers. Not re-run | derived from T2 runs | PARTIALLY SUPPORTED (plausible mechanism, not independently rerun) |
| Golden set v1 was biased; v2 rebuilt in course vocabulary (A11/F12) | `eval/eval_set.json` (26 q, each with `source_parent_ids`), backups present | experimentally verified structure | SUPPORTED that v2 exists and is sourced; whether it is unbiased is UNKNOWN (author-written, 26 items) |
| A20: few_shot 0.748, CoT 0.689, temp 0.0 0.7343 answer_correctness | Matches the "Final Analysis" sheet in `eval/pipeline_runs.xlsx` (0.748 / 0.689 / 0.734) | experimentally verified against workbook | SUPPORTED as recorded values |
| Run-to-run noise floor about 0.027 answer_correctness (A20) | Two runs of the same config: 0.7752 vs 0.7478, from FINDINGS. Workbook shows 0.775 for `dense+multi_query+cross_encoder` | experimentally verified (n = 1 pair) | PARTIALLY SUPPORTED (one pair only) |
| Defect fixes +0.111, prompt +0.092 outweigh retrieval technique choice (A17, A20 table) | FINDINGS.md tables | derived | PARTIALLY SUPPORTED; the differences that exceed noise are prompting and defect fixes |
| Retrieval technique differences (reranking, multi-query) are not established | FINDINGS A20 concedes this | derived | SUPPORTED as a negative result: differences are inside noise |
| A16 table (dense+multi_query composite 0.772 etc.) | Values differ from the "Final Analysis" sheet (e.g. 0.746 vs 0.662 answer_correctness for dense+multi_query); different run generation (`num_query_variants=3`, older config) | derived from older run | UNKNOWN: no single workbook sheet was matched; treat as superseded |
| A1/A2: faithfulness rewards refusal and is nearly independent of correctness | Analysis in FINDINGS; not re-run | derived | PARTIALLY SUPPORTED; this is the one finding with likely wider interest (metric blind spot) but n = 26 |
| Judge model (qwen2.5:7b) differs from generator (llama3) | Stated in FINDINGS and README; not confirmed in code | derived | PARTIALLY SUPPORTED |
| USD costs | FINDINGS states they are hypothetical GPT-4.1/4o-mini pricing on local token counts | derived | SUPPORTED as hypothetical; never a measured cost |
| "22-document corpus" | `data/raw` has 11 files | unsupported | UNKNOWN (discrepancy; see inventory) |

**Sample-size caveat carried over from the project's own notes:** 26 questions, single run per config, no significance testing, 7B local judge.

---

## Part C: Resources actually available

**Real assets**
- An 11-file OS course corpus (processes and shell only) plus the authored 26-question golden set with slide citations.
- A working local RAG pipeline (dense, BM25, hybrid RRF, HyDE, multi-query, cross-encoder rerank) and a RAGAS-based eval harness with per-question rows in xlsx.
- Recorded measurement practice: refutations, a noise-floor estimate, defect discoveries.
- Four deterministic OS simulators and their tests.
- Compute: a single 8 GB GPU with local Ollama (per FINDINGS F9); no cloud API results.

**Not assets**
- Any MGEV headline number; OS-MechanismBench as a benchmark; the corruption experiment.

## Part D: What this means for the research decision
1. The project has **no evidence yet** for the MGEV thesis. The idea remains a hypothesis (T4), to be judged from the literature and a properly designed experiment.
2. The **strongest empirical material** is the pre-MGEV work: a careful case study of RAG evaluation artifacts (decoy chunks, biased golden set, refusal-rewarding faithfulness, noise-floor). It is small but honestly measured.
3. Any MGEV-style claim needs a real benchmark with ground truth, a real baseline (an actual LLM/RAG run), a real judge, and n larger than 3 before it can enter a paper recommendation.
