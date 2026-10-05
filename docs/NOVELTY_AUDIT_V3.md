# Novelty audit V3 — does the SSR question already have an answer in the literature?

**Date:** 2026-10-03. **Status:** uncommitted working document. **Scope:** the working question only: *does replacing canonical-reference matching with independently executable semantic evaluation materially change conclusions about LLM execution reasoning?*

**Method and limits.** Web search and abstract/page fetches on 2026-10-03 (queries listed in §6). Only the abstract or landing page was read for most papers, not full texts, so "does not report X" below means "X is not in the abstract/page I read", not "X is absent from the paper". One source (SVAC-Concurrency) is a GitHub repository with a paper draft, not a peer-reviewed publication. Search results are US-only and incomplete; a miss is not proof of absence. Items I could not verify are marked **UNVERIFIED** and are not relied upon.

## 1. Verdict in one paragraph

The **broad thesis** (reference matching penalises valid-but-different outputs; executable/semantic checking is better) is **established** in several domains, and the **narrow phenomenon in OS execution traces has a near neighbour**: SVAC-Concurrency reports that strict positional trace matching scores far below an equivalence-aware verifier on Banker's and wait-for-graph tasks (Banker's step accuracy 41.5% → 74.3%, WFG 31.2% → 95.6% for one model). No source I found (i) enumerates the complete valid-solution space with an exact oracle in order to *measure* a false-rejection rate per evaluator, **and** (ii) tests whether evaluator choice changes *model-level* conclusions with ranking and significance statistics, in an execution-trace domain. That is a **residual gap, not a demonstrated novelty**: it rests on a limited search, and our own model-level result is currently inconclusive (see `SSR_CONCLUSION_IMPACT_ANALYSIS.md`). "Absolute scores change, rankings do not" is the most likely finding in this literature; a paper whose headline is a ranking reversal would need data we do not have.

## 2. Paper records

Columns: multi-valid = multiple valid outputs exist in the task; ref-free = evaluator needs no canonical reference; exact exec = exact executable semantics; model-level = model conclusions compared across evaluators; distortion = ranking/significance distortion measured.

| # | Citation | Year | Domain / task | Multi-valid | Ref-free evaluator | Exact exec | Model-level across evaluators | Distortion measured | How our question differs |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SVAC-Concurrency, Bethegnt (GitHub, repo with `ieee_paper_draft.md`, framed for ICCCN 2026; not peer-reviewed) https://github.com/Bethegnt/SVAC-Concurrency | 2026 | OS concurrency: Banker's, wait-for graph, buddy allocator, semaphore, mutex; 125 instances; step-level traces | Yes (acknowledged) | Yes (invariant-based verifier) | Partly: preconditions/invariants, **no enumeration of all valid traces** | Compares strict vs equivalence-aware *per prompting strategy*; no Kendall τ or ranking-reversal statistic reported | Only absolute deltas and a prompting-strategy ordering illusion (WFG: strict Few-Shot 85.4% > CoT 7.5%; invariant: all ≈ 93–100%) | **Nearest neighbour.** Same domain and same core observation. We differ by exact tri-state oracle over the enumerated valid set, a measured FRR, 24 independent worlds as the statistical unit, and model-level tests. Their setting: temperature 0, 4–6 instances per cell, 4 models, partial coverage, so model-level inference is weak there too. |
| 2 | Kranti & Vajjala, *LLM Judges Can Be Too Generous When There Is No Reference Answer*, arXiv:2607.12885 | 2026 | Open-ended QA, three languages | Yes | Studies reference-free vs reference | No (human annotation) | Judge decisions only | Reports reference placement flips judge decisions "by as much as 85%" | Judges, not exact execution; does not compare model rankings. |
| 3 | Lee et al., *Judging Against the Reference*, arXiv:2601.07506 | 2026 (rev. Jun 2026) | QA evaluation with swapped references | Not the focus | No | No | Judge reliability | Judge accuracy under swapped references | Reference *deference* by judges, on facts; no valid-alternative oracle. |
| 4 | Yeadon et al., *LLM-as-a-judge validity is strongly task-dependent across physics assessment formats*, arXiv:2603.14732 | 2026 (rev. Sep 2026) | Physics grading | Partly | Compares blind / solution-provided / false-solution / anchored conditions | No | Spearman rank agreement with humans | Reports that false solutions degrade absolute accuracy but preserve ranking order | Evidence that *reference manipulation changes absolute scores but not rank order*, a prior for our ranking question. Not an exact oracle. |
| 5 | Krumdick et al., *No Free Labels*, arXiv:2503.05061 | 2025 (rev. Sep 2026) | Finance QA, 160 questions, 1,200 responses | Not the focus | Compares with and without expert references | No | Judge–human agreement | Agreement with humans; effect of references | Judge calibration, not execution semantics. |
| 6 | Badshah & Sajjad, *Reference-Guided Verdict*, arXiv:2408.09235 (Widening NLP Workshop) | 2024 (rev. Nov 2025) | Free-form QA | Yes | Reference-guided judges vs EM/F1 | No | No | Human agreement of ensemble | EM/F1 inadequate for free-form QA; no model ranking analysis. |
| 7 | Chen et al., *Judging Is Not Enumerating*, arXiv:2608.01000 | 2026 | LLMs authoring acceptable sets/test suites; HumanEval+/MBPP+, finite truths, WordNet | Yes (acceptable sets) | Judging vs authoring | Executable reference in one arm | Not across benchmark evaluators | Omission detection rates (6–7× fewer omissions caught than over-inclusions) | **Relevant as caution:** supports building the valid set by *construction* (our enumerator + independent validator) and not by an LLM; not a model-ranking study. |
| 8 | van der Vleuten et al., *EnvTrace*, arXiv:2511.09964 | 2025 | Beamline control code; trace alignment against a digital twin | Yes (equivalent code) | Reference trace alignment | Simulation-based | 30+ LLMs scored, one evaluator family | Reports a gap between syntactic and trace metrics | Execution-trace semantic evaluation exists, but alignment is to a ground-truth trace, not an independent oracle, and no cross-evaluator ranking analysis was seen on the page. |
| 9 | Dong et al., *CodeScore*, arXiv:2301.09043 (TOSEM) | 2023 (rev. 2024) | Code generation | Yes | Learned metric, can be reference-free | Execution supervision | Kendall/Spearman correlation of metrics with functional correctness | Rank correlations of metrics with execution | Classical **metric meta-evaluation** pattern (we should cite and follow). Program-level, not execution traces. |
| 10 | Gu et al., *CRUXEval*, arXiv:2401.03065 | 2024 | Python I/O prediction, execution-checked | Acknowledged | Yes (assertions) | Yes | No | No | Executable scoring for execution reasoning; unique-output tasks mostly. |
| 11 | Valmeekam et al., *PlanBench*, arXiv:2206.10498 (NeurIPS 2023 D&B) | 2022/2023 | PDDL planning scored by VAL | Yes (many valid plans) | Yes (validator) | Yes | No | No | Validator-based scoring is standard in planning; no comparison against reference matching in the page read. |
| 12 | Kostić et al., *Same Meaning, Different Scores*, arXiv:2602.17316 | 2026 | MMLU/SQuAD/AMEGA prompt perturbations, 23 LLMs | n/a | n/a | No | Leaderboards across *prompt* perturbations | Reports perturbations "destabilize model leaderboards on complex tasks" | Leaderboard instability is a live concern; the perturbation is on the *input*, not the evaluator. |
| 13 | Taherkhani et al., *SWE-Flux*, arXiv:2609.28449 | 2026 | Runtime-behaviour questions on 12 repos, oracle harvested from instrumented runs | Not the focus | n/a | Yes (executed) | No | No | Execution-grounded reasoning benchmark; no evaluator comparison. |

**Not relied upon (UNVERIFIED):** a search snippet reported that "semantic evaluation raised scores for one model from 49.70% to 70.06% while overall model ranking remained consistent" (it appeared next to ReactBench arXiv:2604.15994). I fetched that abstract and it did not contain the claim, so I could not attribute it to a paper. It is evidence only of how common the "ranking unchanged" pattern *may* be.

## 3. The seven questions

**1. Is the broad thesis ("reference matching rejects valid alternatives; executable semantics is better") already established?** Yes in general. Rows 1, 6, 8, 9, 11 and the code-metric literature show it for QA, code, planning and traces. Not novel; present it as background.

**2. Is the narrower "conclusion distortion" question already studied?** *Partly.* Metric meta-evaluation by rank correlation with a gold standard is routine (row 9). A reference-manipulation study reports absolute-accuracy change with preserved ranking in a judge setting (row 4). I found no paper that specifically asks, for execution traces, whether switching from canonical-reference matching to an executable oracle changes *model* rankings or significance decisions. This is an absence in a limited search.

**3. Is the "complete executable valid-solution space" design already used for evaluator meta-evaluation?** I did not find it. SVAC's own text says it does not enumerate valid traces (row 1); row 7 argues enumeration is hard for LLM-authored sets, which supports our construction-by-enumeration but is not itself an evaluator comparison. Residual novelty candidate, unproven.

**4. Is the OS execution-trace setting novel?** No. SVAC-Concurrency already uses Banker's, WFG and other OS algorithms with deterministic reference solvers and reports strict vs equivalence-aware scoring. The setting cannot be the contribution.

**5. Nearest prior paper?** SVAC-Concurrency (row 1), with rows 4 and 9 as the nearest methodological neighbours. If SVAC matures into a peer-reviewed paper with a ranking analysis, our overlap would increase.

**6. What contribution could still be novel?** Only the *combination*: an exact tri-state oracle plus enumerated valid-set evaluation, used to (a) measure per-evaluator false-rejection/acceptance and (b) test with world-clustered statistics whether evaluator choice alters model-level conclusions. This is a **measurement/methodology** contribution, and its strength depends entirely on (b) showing an effect. A pooled FRR of 0.6–0.7 with weak models, on its own, repeats SVAC's observation with a cleaner oracle; I would not call it a new finding.

**7. Cheapest experiment to falsify the novelty claim?** (i) Read the full SVAC draft and repository for any ranking/significance analysis (zero cost; the draft summary I fetched reported none); (ii) re-search arXiv/ACL Anthology for "evaluator-induced ranking change" in code/trace/planning with different keywords; (iii) check whether our own frozen data show *any* model-level change (done in Phase 2). If the data show no decisive ranking or significance change, the remaining claim is "absolute scores shift, conclusions are stable", which is already the dominant pattern (row 4; unverified snippet) and is a weak paper.

## 4. Consequence for the program

- Do **not** claim first/novel for "reference matching underestimates valid outputs", nor for the OS setting.
- A paper would need the model-level effect to be real and measured; the broad-FRR story alone is background.
- Cite SVAC-Concurrency and state clearly how the oracle and the statistical unit differ.

## 5. Uncertainty

Search coverage is limited to what the search tool returned and the pages I fetched; I did not read full texts or search ACL Anthology, PMLR or OpenReview directly. Several 2026 arXiv items have revision dates after submission; I recorded the dates shown on the pages.

## 6. Search log (2026-10-03)

1. evaluator choice changes model ranking reference-based vs executable verification multiple valid solutions LLM 2026
2. LLM judge anchored to reference answer rejects valid alternative solutions reference-guided evaluation bias
3. planning plan validator VAL executable verification versus plan matching metric LLM planning evaluation valid alternative plans
4. system-level meta-evaluation metric rank correlation benchmark evaluator sensitivity ranking instability LLM benchmarks
5. LLM operating system scheduling concurrency execution trace reasoning benchmark process scheduling deadlock Banker's algorithm evaluation
6. CodeBLEU exact match vs execution-based evaluation model ranking correlation functional correctness multiple correct programs
7. exact-match scoring undercounts correct answers LLM benchmark rankings change with semantic equivalence checker reevaluation
8. reference-based metric false negatives valid outputs rejected enumerate all valid solutions oracle meta-evaluation of LLM judges
9. strict positional trace matching vs semantic equivalence-aware verifier LLM execution trace model ranking unchanged benchmark 2026
10. "valid but different" reference solution LLM evaluation false rejection rate reference-based scorer independent verifier ranking Kendall tau

Fetched pages: SVAC-Concurrency repo and draft; arXiv 2603.14732, 2602.17316, 2609.28449, 2608.01000, 2511.09964, 2601.07506, 2607.12885, 2503.05061, 2408.09235, 2604.15994, 2206.10498, 2301.09043, 2401.03065.
