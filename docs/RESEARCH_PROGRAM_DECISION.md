# Research Program Decision (Phase 2)

Date: 2026-09-30. Basis: `docs/ADVERSARIAL_LITERATURE_REVIEW.md`, `research/closest_prior_art_verified.csv` (15 papers, 14 read in full or near full), the Phase 1 audit, and `docs/CORPUS_VERSIONS.md`. No title is proposed, and no "first / novel / state-of-the-art" claim is made. Everything below is conditional on the checks listed in §5.

## 1. What the adversarial attack established
- **The Phase 1 recommendation (D1/D2) does not survive as stated.** Comparing a deterministic checker with LLM judges per error class is done (2607.16646; VeriFin 2608.10213). LLM-verifier accuracy on LLM prose explanations with injected errors is done (2604.12543). Trace-vs-cause gaps are done (TempoBench, CES). "Faithfulness rewards abstention" is done with a complete oracle (2606.09376). "LLM verifiers miss non-salient errors" is done (2604.10990).
- **An OS domain transfer of any of these would read as incremental.** That is exactly the objection the user wants to avoid.
- **One formulation survived both rounds: F14.** It asks whether executable (neurosymbolic) verification of prose explanations inherits the salience bias of the LLM that extracts the claims. Its components exist separately (salience in LLM verifiers; extraction omission; executable-vs-judge comparisons). The combined causal test (salience manipulated + executable arm + gold-extraction ablation) was not found in the papers read. OS mechanisms are chosen for a methodological reason: deterministic simulators give a **complete oracle**, so salience can be varied while holding checkability at 100%.

## 2. The three options

### Option 1: KEEP CURRENT PROJECT AS INSTRUMENT
- **What:** keep OS-Tutor-RAG as a tutor and evaluation harness. Publish an empirical account of evaluating a course-grounded RAG tutor on the 37-file corpus. Content: new expert-reviewed question set, re-measured noise floor, the July measurement lessons (decoy chunks, biased golden set) re-tested on v2.
- **What would actually be published:** a solid experience/case-study paper for an education-technology or CS-education venue, e.g. an experience report or a workshop on educational applications of NLP.
- **Novelty evidence:** low. Its contribution is careful practice, not a new finding. Adjacent evaluation-validity results (2606.09376, RAGAS critiques) already cover the general points.
- **Risk:** low. **Value:** modest. Reviewer objection: "an evaluation of one system on one course".

### Option 2: PARTIAL PIVOT (recommended)
- **What:** keep the corpus, pipeline and (rewritten) simulators as instruments. Pivot the research question to **F14, salience transmission in executable verification of mechanism explanations**. Paired with it:
  - **F6 (residual risk):** a secondary analysis on the same data.
  - **An OS-tutor case study:** natural explanations from the RAG tutor, as the ecological-validity arm. This ties the controlled study to real tutor outputs.
- **What would actually be published:** one empirical paper whose main result is a measured answer to "does LLM-mediated claim extraction transmit salience bias into deterministic verifiers?" It reports:
  - per-arm × per-salience detection;
  - extractor recall of the erroneous constraint;
  - the gold-extraction ablation;
  - prompt-intervention results (does exhaustive decomposition fix it, and at what false-reject cost?);
  - a replication on natural tutor explanations.
  Venue class: NLP evaluation / reasoning venues (ACL/EMNLP/NAACL main or Findings; workshops on logical reasoning or verification) or AI-in-education venues if the tutor arm is strong.
- **Novelty evidence:** plausible, not established. The closest papers are each missing one essential element (see the table in §3).
- **Both outcomes are publishable, which reduces risk.** If transmission exists, neurosymbolic "verified" systems (VeriFin, MechSim, FAX, tutors) have a structural blind spot. If it does not, executable verification genuinely escapes the salience shortcut that 2604.10990 found in LLM verifiers. That is also informative, provided the design has adequate power.
- **Cost:** about 360 constructed items plus about 150 natural tutor explanations. Two annotators: about 12 hours of validation plus about 15 hours for natural-claim labelling. Local generation on the 8 GB GPU. At least one cross-family extractor/judge via API is preferable (budget UNKNOWN).

### Option 3: FULL RESEARCH PIVOT
- **What:** drop the tutor entirely. Run F14 as pure methodology across two or three complete-oracle domains (OS mechanisms plus, e.g., data-structure operations or a formal-methods domain) to show that the effect is general.
- **What would actually be published:** a stronger-generality version of the Option 2 paper, targeted at a main NLP/ML venue.
- **Novelty evidence:** same as Option 2. Generality raises significance, not novelty.
- **Cost / risk:** higher (a second simulator and item set). It discards the educational framing, which is the only ecological-validity anchor we have.

## 3. Why Option 2 and not the others

| Closest paper | Has | Lacks (relative to F14) |
|---|---|---|
| 2604.10990 When Verification Fails | Salience manipulation; LLM verifiers over-accept non-salient errors | No executable verifier; no extraction-to-solver pipeline; not mechanisms |
| VeriFin 2608.10213 | Symbolic vs LLM verifiers; false accepts; coverage trade-off | No salience manipulation; single numeric claims; no gold-plan ablation |
| 2607.16646 | Solver battery vs LLM judges per error class; extraction noise (76.8% of flags) | Formal models, not prose; no salience manipulation |
| 2604.12543 | LLM verifier on prose explanations with injected errors | No executable arm; author labels without agreement |
| Claimify (ACL 2025) | Extraction coverage evaluation | No downstream verifier; no salience manipulation |
| 2606.09376 | Complete-oracle design | No verifier comparison; no salience manipulation |
| MechSim / FAX | Executable verification frameworks for explanations | No verifier accuracy measured at all |

Option 1 is safe but weak on novelty. Option 3 adds generality at high cost and loses the only real-world anchor. Option 2 keeps what the project actually built (corpus, pipeline, simulators, measurement discipline) and aims it at the one question that survived.

## 4. Separation of claims for F14 (as required)
- **A. Scientifically interesting: yes.** It bears on the reliability claims of every neurosymbolic verifier of free text.
- **B. Empirically testable: yes.** A complete oracle, manipulable salience, a gold-extraction ablation, and local compute.
- **C. Plausibly novel: plausible only.** The support is that none of the 15 closely read papers, and none of the second-round search results, combines the three elements. A and B are **not** evidence for C.

## 5. Conditions that must hold before committing (in order)
1. **Venue sweeps: DONE (2026-09-30).** Neither the education sweep nor the NLP/IR/SE sweep found a study that tests F14 (review Addenda A and B). Caveats: DBLP was blocked and Semantic Scholar rate-limited in both sweeps, and ACM/IEEE/Elsevier full texts were abstract-only. New must-cite neighbours: Kang, Milliken & Yoo 2024 (execution-based verification of LLM code descriptions; testable vs untestable error split), ReFEree, ETF, QuArch, EduGuard.
2. **Read in full:** Kang, Milliken & Yoo 2024 (2406.14836), the 2604.10990 appendices (annotation protocol, rubric validation), Claimify (ACL 2025), "Decomposition Dilemmas" (NAACL 2025), 2606.16118 (implicit constraint blindness), 2605.13817 (VeriMed error analysis).
3. **Pilot (before building anything large):** 20 scenario templates × salient/non-salient corruption, 2 extractor models, plain vs decomposition-forcing prompts.
   - **Go** if the plain-prompt extractor recall differs between salient and non-salient erroneous constraints by more than the 95% CI, **and** a nontrivial gap persists under decomposition prompting or closes only at a measurable false-reject cost.
   - **Stop** otherwise.
4. **Annotation feasibility:** two annotators available; κ ≥ 0.6 on item validity in the pilot.
5. **Simulator validity:** each rewritten simulator reproduces textbook worked examples (scheduling Gantt charts, FIFO/LRU/OPT fault counts incl. Belady's case, Banker's algorithm) before use.

## 6. What happens to the existing project under Option 2
| Asset | Action |
|---|---|
| Corpus v2, ingestion, retrieval/generation pipeline | **Keep**: produces the natural tutor explanations (ecological arm) |
| `eval/` RAGAS harness, workbooks | **Keep**: RAGAS/NLI is one verifier arm |
| `src/verification/*` simulators | **Rewrite**: complete-oracle generators and deterministic checkers with a structured claim interface; validate against worked examples |
| `src/query/claim_decomposer.py`, `src/mechanism/*` | **Rewrite**: the LLM extractor becomes an experimental variable, with a gold-extraction path |
| MGEV benchmark, eval scripts, results, paper draft | **Archived** (`docs/archive/MGEV_ARCHIVED.md`); not reused |
| Frontend, API, auth, Docker | Irrelevant to the paper |

## 7. If the conditions fail
If the sweep finds an equivalent study or the pilot shows no transmission effect, the honest fallback is Option 1 (a careful evaluation case study) or the null-result version of F14, if it is adequately powered. A stronger survivor is not available in the literature examined so far, and none should be manufactured.
