# Novelty Gap Report

Date: 2026-09-30. Read with `docs/LITERATURE_SEARCH_LOG.md` (coverage limits), `docs/KILL_LIST.md` (full-paper audit of three crowded ideas), `docs/CONTRADICTION_MAP.md`, `docs/EVALUATION_BLIND_SPOTS.md`, `docs/IDEA_KILL_LOG.md`, and `research/literature_database.csv` (73 rows).

## 1. Executive summary
- The project's MGEV numbers (70% vs 90%, 100% corruption detection, 300-question benchmark) are hard-coded or synthetic and are not evidence (`docs/CURRENT_PROJECT_AUDIT.md`). The MGEV *method* has close prior art (MechSim 2606.04505, FAX 2605.27879, Explanation-Refiner, CRITIC).
- Architecture-level ideas (adaptive RAG tutor, GraphRAG for tutoring, misconception-aware RAG) are crowded; five tutors and four GraphRAG-in-education papers were read.
- The least-crowded, evaluable gaps concern **measurement**: whether automated scorers and "verified" explanations are valid for OS correctness, with an independent expert-labelled claim set; and a **missing validated OS misconception inventory**.
- **No strong survivor is confirmed as novel.** The survivors are conditionally viable and gated by kill tests and by student-data access.

## 2. Search methodology
Six area-specific reviews (RAG/IR; factuality and judges; executable/causal reasoning; LLM tutoring; CS/OS education; benchmark science), plus a full-text audit of 12 sources for three ideas and targeted follow-up searches. Every candidate got a kill attempt against what was found. Contradictions and blind spots were extracted per area.

## 3. Search coverage
See the search log. About 150 items retrieved; roughly a third read past the abstract; six read end to end. **Not effectively covered:** Semantic Scholar, ACL Anthology, Google Scholar, IEEE, Springer, ScienceDirect, ACM DL beyond abstracts, EDM/LAK/AIED/ITS proceedings. About 40 arXiv queries came back empty (unsearched, not negative).

## 4. Current state of the literature (within what was read)
LLM tutors are widely built; rigorous learning-outcome evidence is thin and mixed; RAG evaluation depends heavily on LLM judges and similarity metrics with limited validation; execution- or tool-based verification of model claims is an active 2026 topic; OS-specific evidence is sparse.

## 5. Mature / crowded areas
Learner-state and KT-conditioned RAG tutors; GraphRAG vs vector RAG comparisons; misconception-aware RAG (math); LLM-judge bias (self-preference, position, length); benchmark-contamination surveys; code-execution reasoning benchmarks (Python).

## 6. Emerging areas
Execution- and simulator-grounded explanation verification (2026); sycophancy as educational safety risk; simulated-student validity; RLVR verifier noise; statistical practice for evals (error bars, power).

## 7. Contradictory findings
Thirteen sets in `docs/CONTRADICTION_MAP.md`. Notable: self-verification helps vs hurts; self-preference real vs overstated; LLM tutors improve vs harm learning; RAGAS reports high agreement with humans on WikiEval while the project's own small data found faithfulness nearly independent of correctness (unresolved).

## 8. Evaluation blind spots
Sixteen in `docs/EVALUATION_BLIND_SPOTS.md`; most actionable: judge validity for pedagogical correctness; abstention inflating faithfulness; "verified" without coverage; simulated-student validity; benchmark score vs learning.

## 9. Underexplored technical questions
Claim-level accuracy and coverage of execution-based verification (MechSim/FAX report neither); trace correctness vs causal attribution outside synthetic machines; OS-state reasoning (scheduler, paging, locks); interactions among retrieval components under controlled noise.

## 10. Underexplored educational questions
A validated OS misconception inventory; LLM tutors in systems courses (no outcome study found); which guardrail component prevents dependency; whether tutor benchmark scores predict learning.

## 11. Underexplored cross-disciplinary questions
Psychometrics (IRT, reliability) applied to LLM explanation evaluation; formal-methods and simulation viewpoint on what "verified" can mean for prose; benchmark-science standards (construct validity) applied to educational RAG.

## 12. Candidate research gaps
Twenty-three candidates (`research/candidate_ideas.json`), 15 non-RAG (65%), 21 literature-derived.

## 13. Evidence supporting each gap (strength)
| Gap | Evidence | Strength |
|---|---|---|
| No validated OS inventory | Webb and Taylor 2014 (unvalidated, 10 items); small qualitative studies | Moderate (thin search) |
| No OS-explanation correctness audit | Only a TA system without evaluation and a 6-question grading study found | Weak-moderate (absence claim) |
| Judge/metric validity in tutoring | Judge literature general; no tutoring/OS claim-level study found | Moderate |
| Claim-level accuracy/coverage of execution-based verification | MechSim/FAX limitations | Moderate |
| Trace vs cause on OS mechanisms | TempoBench (synthetic) | Moderate |
| Retrieval interactions under noise | Single-factor papers; project noise-floor evidence | Weak-moderate |

## 14. Closest prior art (for the survivors)
MechSim (2606.04505), FAX (2605.27879), Explanation-Refiner (EMNLP 2024), CRITIC (2305.11738), TempoBench (2510.27544), CES (2510.15079), Webb and Taylor 2014, MT-Bench, MRBench, Sufficient Context, Chunk-cliff, Expansion-failure.

## 15. Gaps that survived aggressive prior-art search
C01, C02, C03 (narrowly), C04, C06, C09, C22 (with risk). "Survived" means no close prior art found in a partial search. Extra searches required per item are in the kill log.

## 16. Ideas we should NOT pursue
Adaptive RAG tutor as an architecture; GraphRAG for OS tutoring as a headline; misconception-aware RAG without validated misconceptions; MGEV as a new method; simulated-student fidelity (crowded 2026); duplicate-document handling; length/position bias for judges; any contribution built on the earlier synthetic benchmark.

## 17. Top research opportunities
D1 (scorer validity), D2 (what executable checks catch), D3 (OS inventory), D4 (trace vs cause), D5 (retrieval interactions): see `docs/TOP_5_RESEARCH_DIRECTIONS.md`.

## 18. Recommended direction
Option C (keep components, drop the original thesis): a measurement program on a shared expert-labelled OS claim set, staged D1 -> D2 -> D4, with D3 as a parallel opportunistic effort if student data exist. Details in `docs/RECOMMENDED_RESEARCH_PROGRAM.md`.

## 19. Why the direction is defensible
It rests on gaps stated in the limitations of the closest papers (FAX's local verification, MechSim's judge-based evaluation, Python-only execution benchmarks, unvalidated OS inventory), each has a clean, independent-label evaluation and a strict kill test, and it uses assets we hold (corpus, pipeline, simulators, measurement experience).

## 20. What evidence is still needed
(a) Full reads of MechSim, FAX, PetriBench, CacheMind, RAGAS validation, 2605.12748, 2603.15547; (b) searches of SIGCSE/ITiCSE/ICER and EDM/AIED proceedings; (c) confirmation of student-data access, annotator availability and API budget; (d) a pilot to check that LLM claim-error rates are high enough to study.

## 21. Threats to novelty
Fast-moving 2026 literature (competing papers appeared during this review); executable-verification framing is close to two 2026 papers; general judge-validity work is abundant; the search was partial.

## 22. Exact next experiments
1. Author ~60 OS questions from exams and lectures (human-written), generate answers with 3 models with and without retrieval.
2. Two annotators label claims; measure kappa; count checkable claims (coverage).
3. Kill checks: LLM claim-error rate (must be non-trivial), coverage (>= ~30%), judge-teacher agreement vs teacher-teacher.
4. Only if these pass: scale to ~150 questions and build claim-to-contract translation for the simulators.
