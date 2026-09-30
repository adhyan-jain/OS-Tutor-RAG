# Novelty Kill List (full-paper audit)

Upgraded 2026-09-30. The earlier version relied on search snippets; this one is based on the papers themselves.

**How each paper was read (be aware of the difference):**
- **FULL-TEXT:** the paper's full text was extracted from the PDF and read end to end by an auditing subagent: 2506.22303, 2501.12300, 2509.07846, 2509.16780, 2604.04036, 2511.01182. Quotes come from that reading; several numeric discrepancies inside those papers were noted by the reader.
- **FETCH-SUMMARY:** the full open-access page was fetched and summarized by a small model against a fixed question list, not read by me line by line: TutorLLM, DeepTutor, KITE, Frontiers 2026, LPITutor. These are reliable for design and evaluation type but numbers should be re-checked against the paper before being quoted in a manuscript.
- **README-ONLY:** `misconception_aware_rag` (a GitHub repository, not a peer-reviewed paper).

This audit covers 12 sources for 3 ideas. It says nothing about the field beyond them. DOIs are given where the source page stated one; arXiv ids otherwise.

---

## IDEA 1: "Adaptive RAG tutor" (learner state + RAG + tutoring)

**Final status: KILLED as a system or architecture contribution.** The remaining gaps are evaluation gaps, listed below, and are not claimed as survivors until tested against a wider search.

| Paper | What it implements | Data | Evaluation | Learning outcomes? | Human/expert? | Actually adaptive? |
|---|---|---|---|---|---|---|
| **TutorLLM** (arXiv 2502.15709, https://arxiv.org/abs/2502.15709) [FETCH-SUMMARY] | Knowledge tracing (MLFBK, BERT-based) + Jina scraper + GPT-4 RAG, as a Chrome plugin | Linear algebra course; 30 first-year students | Two-week crossover field study, 3 groups, 15 daily tests, SUS = 76.35 | Measured, **not significant**: 74.48 vs 71.97, ANOVA p = 0.462 | Questionnaires only, no expert content review | Yes, responses tailored to KT-predicted state; update frequency not stated |
| **LPITutor** (Liu et al., PeerJ Comput Sci 11:e2991, 2025, doi 10.7717/peerj-cs.2991, https://peerj.com/articles/cs-2991/) [FETCH-SUMMARY] | Sentence-transformer RAG + two-layer prompt (static pedagogical template + dynamic learner metadata) | 300 queries at beginner/intermediate/advanced levels, undergraduate CS lectures | Rubric scores (accuracy, completeness, clarity, difficulty alignment, coherence, relevance) plus BLEU/ROUGE; baselines: plain LLM, plain RAG | **Not measured** (authors say real-world testing is required) | Two subject experts plus a rater pool; disagreements adjudicated | Per-query only, no persistent learner model |
| **Frontiers in Education 2026** (Adenuga, doi 10.3389/feduc.2026.1896839, https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1896839/full) [FETCH-SUMMARY] | Learner-state-aware RAG tutor with pedagogical response modes (incl. misconception correction) vs prompt-only tutor | Algebra; 24 tasks; small curated corpus | 8 expert raters, 192 rating cells per condition, Wilcoxon + BH correction | **No students, no outcomes** (stated) | Yes, 8 experts, imperfect blinding | Scripted follow-ups only; "cannot show authentic adaptivity" |
| **DeepTutor** (arXiv 2604.26962, https://arxiv.org/abs/2604.26962) [FETCH-SUMMARY] | Agentic tutor with a trace-forest memory and profile-driven question generation | TutorBench: 30 knowledge bases, 90 learner profiles, 270 tasks | LLM student simulator + LLM judge (Claude Sonnet 4.6), 10 rubric dimensions | **No real students** (stated as future work) | Human review only for benchmark construction | Yes, in simulation |
| **KITE** (arXiv 2605.12988, https://arxiv.org/abs/2605.12988) [FETCH-SUMMARY] | Intent-aware RAG tutor (dense + BM25 + MMR, GPT-5) for AI course | 109 course questions with instructor-verified answers | RAGAS metrics (e.g. factual correctness 0.4483), 44 simulated student interactions rated by experts (Cohen's kappa 0.88) | **No real students** (simulated only) | Yes, expert rubric | Intent classification and session state; no learner-knowledge model |

**Overlap with our idea:** methodological. All five combine retrieval with some learner-state or intent conditioning over course material, and two (LPITutor, KITE) are in CS courses.

**Remaining gaps visible from these papers (not yet confirmed as gaps across the field):**
- The only study with real students (TutorLLM, n = 30) found no significant learning effect; the others measure none.
- No ablation separating retrieval from learner-state from pedagogy: the Frontiers paper says its condition "changed several components at once."
- Frontiers found **more** unsupported content in the RAG condition (13/192 vs 1/192), and its authors ask for rubrics that separate failure types.
- None checks the correctness of explanations by computation. Correctness rests on LLM judges, similarity to reference text, or expert ratings.

## IDEA 2: "GraphRAG for OS tutoring"

**Final status: PARTIALLY CROWDED.** The generic comparison "GraphRAG vs vector RAG on course material" has been done, with mixed results. What has not been shown for OS content is listed below.

| Paper | What it implements | Data | Evaluation | Outcomes / human? | Key limits |
|---|---|---|---|---|---|
| **KnowLP / EDU-GraphRAG** (arXiv 2506.22303v2, https://arxiv.org/abs/2506.22303) [FULL-TEXT] | GraphRAG builds a concept graph from LLM-written explanations of concept **names**; a PPO multi-agent recommender sequences concepts; explanations via community summaries | Junyi, MOOCCubeX-Computer (443 concepts), ASSISTments09 | Simulated environment (DKT/DIMKT); baselines KNN, GRU4Rec, RL-Tutor etc.; t-test vs DLPR | No real learners ("cannot be directly validated"); no human/expert evaluation; explanation quality shown only as a qualitative figure | It is a **path recommender**, not question answering. The graph comes from LLM text, not a course corpus. No limitations section, no future work |
| **LLM-Assisted KG Completion** (arXiv 2501.12300, IEEE EDUCON 2025, https://arxiv.org/abs/2501.12300) [FULL-TEXT] | Ontology + GPT-4o concept extraction from lecture slides, manuscripts and Whisper transcripts + teacher validation | Two Siegen modules: Embedded Systems, FPGA design (9 sessions each) | Expert precision/recall/F1 (e.g. topic P/R/F1 0.99/0.94/0.96), 3 evaluators, no baselines or statistics | No students; recommender not built | **Not GraphRAG**; RAG only suggested as future use. Structure metrics barely moved (modularity 0.769 to 0.767) |
| **"Aligning LLMs for the Classroom…"** (Jain, Cui, Chen, arXiv 2509.07846, https://arxiv.org/abs/2509.07846) [FULL-TEXT] | OpenAI vector search vs Microsoft GraphRAG (Local/Global) + a router prototype | EduScopeQA: 3,176 QA pairs over History, Literature, Science, Computer Science (arXiv monographs; **no OS text**); KnowShiftQA: 3,005 MCQs | GPT-4.1-Nano pairwise judge, win rates; GraphRAG Global wins comprehensiveness (e.g. CS 0.879 specific), vector wins directness; GraphRAG costs 10-20x more | No learners, no human check of the judge | No statistics; some prose numbers disagree with Table II; no BM25/hybrid baseline; ground truth is LLM-generated |
| **"Comparing RAG and GraphRAG for Page-Level Retrieval…"** (Chen et al., arXiv 2509.16780v3, https://arxiv.org/abs/2509.16780) [FULL-TEXT] | 5 embedding models, BM25, GraphRAG (gpt-4o-mini, o3-mini) | One undergraduate pure-math textbook, 628 pages, 477 curated QA pairs | Page-hit accuracy (voyage-3-large top-1 .686, GraphRAG .914 with o3-mini but ~47K tokens per query), word-overlap F1, bootstrap CIs | No learners; authors filtered QA pairs, did not grade outputs | 72% unigram overlap questions-to-pages; F1 is a weak proxy; **cross-concept questions, where GraphRAG is hypothesized to help, are not tested** |

**Overlap with our idea:** methodological only for 2509.07846 and 2509.16780 (vector vs GraphRAG on educational text). 2506.22303 and 2501.12300 share vocabulary but are a simulated recommender and a KG-construction pipeline.

**What is still open (from these papers):** OS or systems content; multi-hop or cross-concept questions with an expert or executable correctness check; a matched-cost comparison, since GraphRAG's context is a confound; real-student evidence. Because GraphRAG already looks costly and mixed on these tasks, this is not a strong standalone headline, and "GraphRAG for OS" alone would read as an application of a known comparison.

## IDEA 3: "RAG + misconception detection"

**Final status: PARTIALLY CROWDED.** The architecture exists for K-12 math. For an OS domain the question is UNKNOWN: no validated OS-misconception dataset was found in these sources, and that search has not been done.

| Source | What it implements | Data | Evaluation | Key limits |
|---|---|---|---|---|
| **MisEdu-RAG** (Guo, Lu, Lin, arXiv 2604.04036v2, https://arxiv.org/abs/2604.04036) [FULL-TEXT] | Dual hypergraph RAG (concept hypergraph from pedagogy texts + case hypergraph from MisstepMath); two-stage retrieval; **teacher-facing** advice | MisstepMath, "semi-synthetic", 12,000 K-8 mistake cases; a 221-questionnaire pilot and 6 interviews | Cosine/F1 vs gold text, unnamed LLM judge, 100-question sample; F1 0.3437 vs 0.2801 for HypergraphRAG (GPT-4o-mini) | No learners; no expert rating of outputs; misconceptions come from dataset labels, no diagnosis accuracy; single-run means; text and table disagree in the ablation |
| **MiRAGE** (Van Duc et al., arXiv 2511.01182v1, https://arxiv.org/abs/2511.01182) [FULL-TEXT] | Offline **classifier**: kNN-style label retrieval + CoT reasoner + reranker + fusion | MAP misconception dataset (Kaggle); size and split not stated | MAP@1/3/5 = 0.82/0.92/0.93; only self-ablations | Not a tutor; "retrieval" is label lookup; no external baselines; no human evaluation |
| **misconception_aware_rag** (https://github.com/devissaputra/misconception_aware_rag) [README-ONLY] | BM25 + wrong-answer query expansion + pedagogical reranking + abstention | SciQ (1,000 test questions) | MRR 0.9472 to 0.9433 with wrong-answer conditioning; CI spans zero | **A null result:** conditioning on wrong answers gave no clear content-specific benefit; distractors are not validated misconceptions; unpublished working paper |
| **Frontiers 2026** (see Idea 1) [FETCH-SUMMARY] | Includes a misconception-correction response mode and "misconception notes" in the corpus | Algebra | Expert ratings | No learners |

**Overlap with our idea:** methodological for the "concept corpus + misconception cases" architecture (MisEdu-RAG); the detection formulation (MiRAGE) is transplantable but needs a labelled dataset.

**What is still open:** whether misconception-aware retrieval helps at all beyond generic query expansion (the only controlled test found is null); any OS or systems misconception dataset with validated labels; misconception evidence tied to learner responses instead of teacher queries. Whether such OS datasets exist is **UNKNOWN**.

---

## Cross-cutting observations (from these 12 sources only)
1. No source verifies explanation correctness by computation or simulation; correctness is judged by an LLM, by similarity to LLM-generated reference text, or by expert rating.
2. Of the tutors, only TutorLLM ran a real-student study, and its learning effect was not significant (n = 30).
3. Several papers contain internal numeric inconsistencies (2509.07846 prose vs tables; MisEdu-RAG ablation text vs table; MiRAGE text vs table). Weak statistical reporting is common: no seeds, CIs or significance tests in several.
4. None uses OS course material. LPITutor and KITE are CS or AI courses; 2501.12300 is embedded systems.

These are observations of a small sample, not field-wide findings, and none is yet a confirmed research gap.

## Not yet checked
- Leads from search results, not read: EduGuard (arXiv 2607.15738), a prompt-engineering personalization paper (arXiv 2609.03402), Wiley Computer Applications in Engineering Education doi 10.1002/cae.70153, a ScienceDirect systematic survey of RAG for education (pii S2666920X25000578), and "LLM Intelligent Agent Tutoring in Higher Education Courses using a RAG Approach."
- The project's own idea (mechanism-grounded verification, simulator-based checking of explanations) and its neighbors (program verification, execution-based feedback, causal/counterfactual tests). This is in the broader search, not here.
