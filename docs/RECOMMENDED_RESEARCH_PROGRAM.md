# Recommended Research Program

> **Superseded in part (2026-09-30, Phase 2).** An adversarial full-paper review found the D1/D2 framings below largely pre-empted (2607.16646, 2604.12543, VeriFin, 2606.09376, 2604.10990). The current recommendation is in `docs/RESEARCH_PROGRAM_DECISION.md`: a partial pivot to F14, salience transmission in executable verification. The asset mapping and audit conclusions below still stand.

Date: 2026-09-30. Basis: `docs/SOURCE_OF_TRUTH_INVENTORY.md`, `docs/CURRENT_PROJECT_AUDIT.md`, `docs/KILL_LIST.md`, `docs/NOVELTY_GAP_REPORT.md`, `docs/IDEA_KILL_LOG.md`, `docs/TOP_5_RESEARCH_DIRECTIONS.md`.

## Decision: **C. Keep only some components and abandon the original thesis.**

Not "continue improving OS-Tutor-RAG". The original thesis (mechanism-grounded verification as a method, with a 70% vs 90% result) is dropped: its numbers are hard-coded or synthetic, and the method has close 2026 prior art (MechSim, FAX). What is kept is the instrument: the corpus, a working retrieval and generation pipeline as a *system under test*, the evaluation harness, the measurement discipline, and the OS simulators (after rewriting) as candidate verifiers.

## The central question
*If we started from zero today, what research problem gives the strongest combination of genuine unresolved gap, importance, defensible novelty, feasible evaluation and publication value?*

**Answer, with its confidence:** a **measurement-validity program for LLM explanations of operating-systems mechanisms**, built on one shared asset (a human-authored OS question set with expert claim-level correctness labels). It asks: (1) how often and where do LLM explanations go wrong; (2) do automated scorers (LLM judges, RAGAS-style metrics) detect those errors; (3) what do execution-based checks catch that judges miss, and on what fraction of claims do they apply. The contribution is an evaluation result and a released labelled set, not a new architecture.

**This is not a confirmed strong survivor.** Evidence quality is moderate: the search was partial, the closest prior art (MechSim, FAX) was read only in part, and success depends on annotator access and on LLM error rates being non-trivial. If the first pilot fails its kill checks, the honest conclusion is that no strong survivor exists among the candidates with data we can obtain, except possibly D3 which needs student data.

## Three tiers (as requested)
| Tier | Direction | Why | Kill test |
|---|---|---|---|
| Boring / low risk | **D1** Validity of automated scorers for OS tutoring answers (with D5 as a fallback methodological study) | Clean, reproducible, clear gap in domain-specific claim-level validation | Cross-family judge within CI of teacher-teacher agreement on every claim type, and no abstention effect |
| Medium risk | **D2** What executable checks catch vs judges/NLI (with D4 OS-state trace-vs-cause) | Narrow but real gap in claim-level accuracy and coverage | Coverage < ~30% of real claims, or judge recall equals simulator recall within the CI |
| High risk / high upside | **D3** Validated OS misconception inventory | Missing dataset with lasting value; enables later tutor/LLM/simulated-student evaluation | < ~150 usable responses, reliability < ~0.6 after two revisions, or an existing validated OS inventory is found |

## Why this order
D1, D2 and D4 all consume the same labelled claim set, so one annotation effort supports three papers. D3 is independent and high-value but blocked on student-data access (UNKNOWN). D5 is an inexpensive methodological fallback that reuses the pipeline and the project's real noise-floor evidence.

## Mapping onto current assets (done after the literature-first ideation)
| Asset | Action | Reason |
|---|---|---|
| `data/raw` (37 files after merging Theory.zip) and the ingestion, chunking, retrieval, reranking, generation code | **KEEP** | The pipeline is a legitimate system under test; the corpus is the real OS material |
| `scripts/reindex.py`, `src/build_index.py` | **KEEP, fix note** | Re-embedding after a chunker change appended stale vectors (see index note below); rebuild from scratch when chunking changes |
| `eval/ragas_eval.py`, `retrieval_eval.py`, `rank_diagnosis.py`, xlsx workbooks | **KEEP / MODIFY** | Harness and per-question rows are reusable; the 26-question set must be replaced by a larger, independently reviewed one |
| `FINDINGS.md` measurement practice (decoy chunks, biased golden set, refusal-rewarding faithfulness, noise floor) | **KEEP as prior work** | Real but small; re-measure on the new corpus before citing |
| `src/verification/*` simulators, `tests/test_verifiers.py` | **REWRITE** | Must accept structured claims and be validated against textbook worked examples; currently tested on hard-coded inputs |
| `src/query/claim_decomposer.py`, `mechanism_parser.py`, `src/mechanism/*` | **REWRITE** | The natural-language-to-contract step (the hard part) was never exercised |
| `eval/OS_MechanismBench.json`, `benchmark_builder.py` | **DELETE** | Template-generated, no ground truth |
| `eval/mgev_eval.py`, `corruption_eval.py`, `mgev_results.json`, `corruption_results.json` | **DELETE** | Hard-coded scoring, a literal `True` for the textual baseline, n = 3 |
| `docs/PAPER_DRAFT.md`, `PAPER_TABLES.md`, `PRIOR_ART_MATRIX.md`, `RESEARCH_GAP.md` | **DELETE / ARCHIVE** | Claims unsupported; prior-art table unverified and now known to miss MechSim and FAX |
| `graphify-out/` | **IGNORE** | Not a research input; semantic extraction stays paused as instructed (note: the semantic merge had already run before that instruction; the graph contains 40 doc-derived nodes from a partial-read subagent) |
| `api/`, `frontend/`, Docker, auth | **KEEP but irrelevant** | No research value |

## Executive decision (the 10 requested items)
1. **Five strongest gaps:** (a) no claim-level correctness audit of LLM explanations for OS mechanisms; (b) judge/metric validity for tutoring answers is unmeasured; (c) claim-level accuracy and coverage of execution-based verification are unreported; (d) no validated OS misconception inventory found; (e) trace correctness vs causal explanation is untested outside synthetic machines.
2. **Five strongest directions:** D1 scorer validity; D2 executable checks vs judges; D3 OS inventory; D4 trace-vs-cause on OS state; D5 retrieval-interaction study.
3. **Three ideas that looked novel and were killed or crowded:** adaptive/learner-state RAG tutor (five implemented systems); MGEV as a new method (MechSim, FAX, Explanation-Refiner); simulated-student fidelity for OS misconceptions (2026 competitors). Also partially crowded: GraphRAG for OS tutoring, misconception-aware RAG.
4. **Clearest defensible gap:** claim-level, expert-labelled validity of automated scorers for OS explanations (D1).
5. **Highest-risk / highest-upside:** D3, the validated OS misconception inventory.
6. **Safest / cleanest publication-oriented:** D1 (with D5 as a fallback).
7. **Reusable:** corpus, ingestion and retrieval/generation pipeline, evaluation harness and workbooks, measurement discipline, simulators after rewrite.
8. **Discard:** OS-MechanismBench, the MGEV/corruption evaluation scripts and results, the MGEV paper draft and tables, the unverified prior-art matrix.
9. **First experiment, before implementing anything:** a pilot on ~60 human-authored OS questions x 3 models with and without retrieval; two annotators label claim-level correctness and mark which claims are simulator-checkable. It answers three go/no-go questions at once: are LLM claim-error rates non-trivial, is annotator agreement acceptable (kappa >= ~0.6), and is coverage at least ~30%.
10. **Evidence that would make us abandon the chosen direction:** claim-error rate near zero on strong models; kappa below 0.6 after guideline revision; coverage under ~30%; a cross-family judge matching teachers (D1) or matching simulator recall (D2) within CIs; full reads showing MechSim or FAX already report claim-level recall/false-accept with independent labels; no annotators or budget.

## Preconditions and unknowns to resolve first
1. Annotator availability (two teachers or advanced students) and effort budget.
2. API budget for a genuinely cross-family or frontier judge (local hardware: one 8 GB GPU with Ollama).
3. Whether student responses exist and may be used (gates D3).
4. Full reads of MechSim and FAX, and the searches listed in the kill log.

## Note on data changes made during this review
`data/raw` now holds 37 files (26 added from `Theory.zip`; the 11 existing files were preserved, including four not in the zip: Shell programming.pptx, its exercise .doc/.docx, and Linux commands (1).pdf). The first incremental re-index re-chunked all files (the chunker had changed since July) but appended vectors onto the old index, leaving 1,110 stale vectors and a dense/BM25 mismatch; the faulty index was moved aside to `data/_index_dup_bug_20260930/` and a clean rebuild from scratch completed and was verified: 3,646 chunks in the dense index, FAISS and BM25 with identical chunk ids, 36 of 37 raw files indexed (the legacy `.doc` is skipped by design; its `.docx` twin is indexed). **All July evaluation results were measured on the 11-file corpus and a different index; they are not comparable with anything run on the merged corpus.** Backups are in `data/_backup_20260930/`.
