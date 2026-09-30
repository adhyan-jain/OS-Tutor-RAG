# Paper Concepts

One-page concepts for the five directions in `docs/TOP_5_RESEARCH_DIRECTIONS.md`. Titles are provisional. No result is claimed: every "primary result needed" is a target that experiments may refute. Numbers from the project's earlier MGEV evaluation (70%, 90%, 100%, 300-question benchmark) must not appear in any of these papers (`docs/CURRENT_PROJECT_AUDIT.md`).

## Concept 1: Are Automated Scorers Valid for Course-Grounded OS Tutoring? (D1)
- **One-sentence contribution:** a claim-level, expert-labelled test of whether LLM judges and RAGAS-style metrics detect wrong OS explanations, and how much abstention inflates faithfulness.
- **Problem:** tutor quality is certified by automated scores of unknown validity in this domain.
- **Gap:** judge validity is shown for chat preference; no OS/tutoring claim-level validation, and self-preference evidence is contested.
- **RQ:** Do same- and cross-family judges and RAGAS metrics agree with teacher claim-level labels, and does agreement depend on claim type?
- **Hypotheses:** H1 agreement is lower for state-dependent than definitional claims. H2 forced abstention raises faithfulness without correctness.
- **Method:** decompose answers into claims; two teachers label; score with judges/metrics; forced-abstain vs forced-answer manipulation.
- **Dataset:** ~150 human-authored questions (exams and lecture-derived), ~2,000 labelled claims; released with labels.
- **Baselines:** teacher-teacher agreement; rubric-prompted strongest judge.
- **Experiments:** agreement by claim type; abstention manipulation; sensitivity to judge family and prompt.
- **Primary result needed:** a significant, interpretable gap between judge-teacher and teacher-teacher agreement for at least one claim type (with clustered CIs).
- **Secondary:** effect of answer length; noise across repeated generations.
- **Failure condition:** cross-family judge indistinguishable from human agreement on all types and no abstention effect.
- **Threats:** small annotator pool; single course; three generators only; labels reflect one syllabus.
- **Expected contribution:** a released labelled set and a validity protocol for educational RAG evaluation.

## Concept 2: What Do Executable Checks Catch That LLM Judges Miss? (D2)
- **One-sentence contribution:** claim-level recall, false-accept and coverage of simulator-based verification vs judges and NLI on OS explanations with independent expert labels.
- **Problem:** "verified" explanations are promoted (MechSim, FAX) without reporting what verification misses.
- **Gap:** no claim-level accuracy against independent ground truth; coverage unreported; FAX warns verification is local.
- **RQ:** On state-dependent and definitional OS claims, which error types does each verifier family catch?
- **Hypothesis:** simulator checks catch state-dependent errors judges miss but cover a minority of claims.
- **Method:** Stage 0 coverage audit; Stage 1 natural + rule-injected errors; Stage 2 four verifier families, paired tests.
- **Dataset:** the Concept 1 set plus injected variants; simulators rewritten to consume structured claims.
- **Baselines:** cross-family judge with textbook definition; NLI; RAGAS.
- **Primary result needed:** simulator recall exceeds judge recall on state-dependent errors by a margin outside the CI, with coverage reported.
- **Failure condition:** coverage under ~30% or judge matches simulator recall.
- **Threats:** circularity (ground truth must be expert-labelled, not simulator-derived); injected-error bias; simulator fidelity to real OS semantics.
- **Expected contribution:** an honest account of the reach and limits of execution-based verification; not a new architecture.

## Concept 3: A Validated Operating-Systems Misconception Inventory (D3)
- **One-sentence contribution:** a psychometrically validated item bank on processes, memory and concurrency with distractor-level misconception data.
- **Problem:** no validated OS instrument exists in what we found; qualitative studies are small.
- **RQ:** Can items reach acceptable reliability and identify dominant misconceptions replicating across cohorts?
- **Method:** item writing with expert review, multi-cohort administration, CTT and IRT, distractor analysis.
- **Data:** student responses from >= 2 cohorts (availability UNKNOWN).
- **Primary result needed:** reliability >= ~0.7 and stable distractor rankings across cohorts.
- **Failure:** < ~150 usable responses or reliability < ~0.6 after revision.
- **Threats:** single institution; test-taking behaviour; distractor coverage.
- **Contribution:** shared instrument enabling later LLM and tutor evaluation.

## Concept 4: Correct Traces, Wrong Reasons? Reasoning About OS State (D4)
- **One-sentence contribution:** a human-authored benchmark of scheduler, paging and lock scenarios scoring both the trace and the stated cause.
- **Gap:** code-execution benchmarks are Python-centric (their own limitation); OS-state reasoning and trace-vs-cause gaps are untested.
- **RQ:** How large is the gap between trace accuracy and causal-explanation accuracy on OS mechanisms?
- **Method:** textbook-style problem variants authored by people (not templates); simulator ground truth checked on worked examples.
- **Primary result needed:** a trace-minus-cause gap outside noise across several models.
- **Failure:** models near ceiling on both.
- **Threats:** contamination of textbook problems; simulator validity; small n.

## Concept 5: Interactions in Course-Grounded Retrieval Pipelines Under a Controlled Noise Floor (D5)
- **One-sentence contribution:** a factorial, repeated-run study of chunker, expansion, reranker and generator interactions with paired significance.
- **Gap:** single-factor studies; effect signs flip with retriever strength.
- **Method:** full factorial on the 37-file corpus, larger independently reviewed question set, repeated seeds, clustered SEs.
- **Primary result needed:** at least one interaction exceeding the measured noise floor.
- **Failure:** all interactions inside the noise floor -> a null-result note only.
- **Threats:** one corpus; local models; incremental contribution.
