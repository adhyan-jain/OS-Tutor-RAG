# Top 5 Research Directions

Five fundamentally different programs drawn from `research/candidate_ideas.json`, chosen after the kill attempts in `docs/IDEA_KILL_LOG.md`. **None is confirmed novel**: the search was partial (Semantic Scholar, ACM DL, IEEE, EDM/AIED/LAK proceedings not effectively covered). Each is a *conditionally viable* program with an explicit kill test. Risk tiers: **boring/low**, **medium**, **high-risk/high-upside**.

Shared assumptions and unknowns (apply to all): (a) the course corpus is now 37 files covering processes, memory management and concurrency (`data/raw`, index rebuild in progress); (b) whether **student response data** exist and can be used with ethics approval is UNKNOWN; (c) whether an **API budget** for frontier or cross-family judges exists is UNKNOWN (local hardware: one 8 GB GPU with Ollama); (d) at least two annotators (teachers or advanced students) are assumed.

---

## D1. Measurement validity for course-grounded tutor evaluation *(boring / low risk; candidates C06, C07)*
- **Problem:** automated scores (LLM judges, RAGAS-style metrics) are used to certify tutors; their validity on OS answers is unmeasured.
- **Why it matters:** RAG-tutor claims (including this project's earlier ones) rest on these scores.
- **Existing work solves:** judge/human agreement on chat preference (MT-Bench), bias documentation (self-preference, length, position), metric stress-tests on summarization.
- **It does not establish:** judge and metric validity on claim-level correctness of OS/tutoring answers against teacher labels, or how much abstention inflates faithfulness.
- **Y is important because:** wrong tutor answers propagate to learners; decisions on model selection use these scores.
- **Experiment E:** ~150 human-authored OS questions x 3 generators, ~2,000 claims labelled by two teachers; score with same-family judge, cross-family judge, RAGAS faithfulness/correctness; forced-abstain vs forced-answer variants.
- **Hypotheses:** H1 judge-teacher agreement is lower for state-dependent than definitional claims; H2 forced abstention raises faithfulness with no correctness gain.
- **Strongest baseline:** human-human agreement; a rubric-prompted strongest available judge.
- **Metrics/protocol:** kappa and AUROC vs teacher labels by claim type; clustered bootstrap CIs (Miller 2024); paired comparisons; generator and judge from different families.
- **Data / compute:** new question set + labels; local generation, judges local or API (budget UNKNOWN).
- **Hard-novelty statement:** Existing work solves judge validity for chat preference. Our work would instead investigate claim-level judge validity on OS tutoring answers with expert labels and the abstention confound. It is scientifically important because tutor evaluations are used to certify learner-facing systems. The minimum experiment is E above on a pilot of about 500 claims. If Sufficient Context / TRUST-SCORE-style refusal-aware evaluation were extended with expert labels in education, our abstention sub-result would disappear, but the OS claim-level validity result would not.
- **KILL TEST:** if a cross-family judge's agreement with teachers is within the confidence interval of teacher-teacher agreement for every claim type, and forced abstention does not move faithfulness, abandon.
- **Main risk:** generic novelty; judge studies are abundant. **Abandon if** RAGAS or a similar paper already reports expert claim-level validation in an educational corpus (unchecked).
- **Reviewer objections and answers:** *novelty* — restrict the claim to domain + claim-level labels + abstention; *small annotator pool* — report kappa and adjudicate; *model-specific* — three generators, three judges; *benchmark size* — power analysis first; *circularity* — different-family generator and judge; *reproducibility* — release labels and seeds.
- **Venues:** BEA workshop, EDM, L@S, AIED, Computers & Education: AI, EMNLP Findings (evaluation track).

## D2. What do executable checks detect that LLM judges and NLI miss? *(medium risk; candidates C03, C04, C02)*
- **Existing work solves:** claim decomposition plus tool or simulator checks in other domains (MechSim, FAX), theorem-prover checks of NL explanations, tool-based self-correction (CRITIC).
- **It does not establish:** claim-level recall and false-accept against independent ground truth, nor coverage (the fraction of real claims that are checkable); FAX itself warns that "verified" is local.
- **Important because:** a "verified" badge on a tutor answer is meaningful only if we know what it can miss.
- **Experiment E (staged):** Stage 0 coverage audit on ~60 questions x 3 models; Stage 1 expert-labelled natural errors plus rule-injected errors of five types (wrong order, wrong state, wrong cause, over-generalization, off-by-one quantity); Stage 2 run four verifier families (simulator execution, cross-family judge, NLI, RAGAS) with paired tests.
- **Ground truth must be independent of the simulators** (expert labels), otherwise the evaluation is circular. Injected errors are generated by rules that could favor the simulator, so natural errors must be reported separately.
- **Strongest baseline:** cross-family judge with a rubric and access to the correct textbook definition.
- **Hard-novelty statement:** Existing work solves execution-grounded claim checking in other domains. Our work would instead investigate its claim-level accuracy and coverage against expert labels on OS mechanisms. That is important because a partial verifier can give false assurance. The minimum experiment is Stage 0 plus a 100-claim injected-error pilot. If MechSim is extended with claim-level ground truth in an OS domain, our novelty largely disappears; if MechSim already reports claim-level recall, it disappears entirely (must read it in full first).
- **KILL TEST:** coverage below about 30% of real claims, or a cross-family judge matching the simulator's recall on state-dependent errors within the CI -> abandon executable verification as a general safeguard.
- **Main risk:** close prior art (MechSim 2606.04505, FAX 2605.27879) and simulator fidelity (they must match real OS semantics; validate against textbook worked examples).
- **Reviewer objections:** *novelty* (an application of known pattern) — our contribution is the evaluation, coverage and independent labels; *triviality* (simulators trivially check traces) — coverage result quantifies limits; *simulator validity* — cross-check against textbook examples and real traces; *injected-error bias* — report natural errors separately; *domain-specific* — state scope.
- **Venues:** EMNLP/ACL Findings (evaluation/NLP for education), L@S, AIED, ITiCSE (if framed for CS education).
- **Reuse from repo:** `src/verification/*` (needs rewrite to accept structured claims), pipeline for generation.

## D3. A validated operating-systems misconception inventory *(high risk / high upside; candidate C01)*
- **Existing work solves:** small qualitative OS misconception studies (9 and 78 students) and a 10-item unvalidated 2014 inventory; validated inventories exist in other CS topics.
- **It does not establish:** a psychometrically validated OS item bank across processes, memory and concurrency.
- **Important because:** a validated instrument enables measuring tutors, LLM explanations and simulated students (C11, C12, C21) on real misconceptions; the field lacks one.
- **Experiment E:** develop 30-40 items with expert review; run in >= 2 cohorts (a few hundred responses); classical test theory + IRT; distractor analysis; test-retest if possible.
- **Baseline:** Webb and Taylor items; exam questions.
- **Hard-novelty statement:** Existing work identifies OS misconceptions in small samples. Our work would establish a validated instrument. That is important because measurement precedes intervention. Minimum experiment: pilot 20 items with about 100 responses to check reliability. If a validation of the 2014 inventory exists, our novelty shrinks to extension.
- **KILL TEST:** fewer than about 150 usable responses obtainable, or reliability below about 0.6 after two revisions, or an existing validated OS inventory found -> abandon.
- **Main risk:** data access, ethics, time. **Evidence required before committing:** confirmation of cohort access and a literature check of SIGCSE/ITiCSE/ICER 2015-2026.
- **Objections:** *sample size*; *single institution*; *validity vs reliability*; *shortcut answering*. Answer with multi-cohort design and distractor analysis.
- **Venues:** SIGCSE/ITiCSE, ICER, TOCE, Koli Calling.

## D4. OS-state reasoning: does a correct trace imply a correct explanation? *(medium risk; candidates C22, C05)*
- **Existing work solves:** code-execution reasoning benchmarks (Python), causal attribution on synthetic machines (TempoBench), state-space reasoning (PetriBench, snippet).
- **It does not establish:** accuracy on scheduler, paging and lock state over time on human-authored problems, or the gap between trace and stated-cause correctness in OS mechanisms.
- **Experiment E:** ~150 human-authored textbook and exam-style problems with simulator ground truth; models give trace and cause; score both; error taxonomy.
- **Baselines:** several LLMs; tool-augmented variants.
- **Hard-novelty statement:** Existing work measures execution and causal attribution separately in code and synthetic systems. Our work would measure both on OS mechanisms. That matters because tutors explain "why". Minimum: 50 problems, three models. If PetriBench or CacheMind already covers scheduler/paging traces, novelty largely disappears (unread).
- **KILL TEST:** frontier models above about 95% on both trace and cause -> nothing to study; or gap within noise -> abandon.
- **Objections:** *template benchmark* — use human-authored problems, not generated templates (the project's earlier benchmark failed this test); *ground-truth validity* — simulator checked on worked examples; *contamination* — fresh problems.
- **Venues:** ITiCSE/SIGCSE, EDM, EMNLP Findings, L@S.

## D5. Chunker x expansion x reranker x generator interactions at fixed budget *(boring / low risk; candidate C09)*
- **Existing work solves:** single-factor studies (semantic chunking, expansion failure, long-context RAG).
- **It does not establish:** the interaction structure with noise controlled. The project's own A16/A20 findings (reranking helps single-query retrieval and hurts multi-query; noise floor about 0.027) point at interactions being real but within noise at n = 26.
- **Experiment E:** full factorial on the 37-file corpus with a larger, independently reviewed question set, repeated runs, paired tests with clustered SEs.
- **Hard-novelty statement:** Existing work varies one factor at a time. Our work would investigate joint effects under a controlled noise floor. That matters because signs flip with retriever strength. Minimum: 2 x 2 x 2 pilot with 5 seeds. If a factorial RAG study on educational corpora exists, novelty disappears (arXiv API failed here, so this is unchecked).
- **KILL TEST:** all interactions within the measured noise floor -> report a null result only; do not pursue as a main paper.
- **Objections:** *incremental*, *benchmark size*, *model-specific*, *engineering-only*. Answer with a design contribution, released protocol and power analysis.
- **Venues:** SIGIR resource/reproducibility track, ECIR, EDM/BEA, Computers & Education: AI.

---

## Ranking summary (ordinal, no acceptance predictions)
| Direction | Gap strength | Prior-art collision | Evaluation clarity | Feasibility | Tier |
|---|---|---|---|---|---|
| D1 | Medium | Medium | High | High | Boring / low risk |
| D2 | Medium-high | **High** (MechSim, FAX) | High if labels independent | Medium | Medium risk |
| D3 | High (missing dataset) | Low-medium | High | **Low** (data access) | High risk / high upside |
| D4 | Medium | Medium-high | High | Medium | Medium risk |
| D5 | Low-medium | Medium | High | High | Boring / low risk |

No direction is a confirmed strong survivor; D1, D2 and D4 share the same expert-labelled OS claim set and can be run as one staged program (see `docs/RECOMMENDED_RESEARCH_PROGRAM.md`).
