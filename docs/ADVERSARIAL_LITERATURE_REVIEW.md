# Adversarial Literature Review (Phase 2)

Date: 2026-09-30. Purpose: attack the Phase 1 recommendation (a measurement-validity study of LLM explanations of OS mechanisms). We assume our first framing is already published and try to kill it and every variant.

Evidence rules for this document:
- **FULL** means the paper was read end to end from pdftotext output, including appendices. Two papers (MechSim, FAX) were read by me; ten were read by two subagents instructed to read every section.
- Venue-sweep results (§3) come from two further subagents and are marked with their read depth.
- The per-paper fields for the close set are in `research/closest_prior_art_verified.csv`.

## 1. Headline result of the attack

**Our Phase 1 framing is largely pre-empted as a measurement design. It survives only in a narrower form.**

| Phase 1 component | Status after full reads | Killer paper(s) |
|---|---|---|
| "Compare a deterministic checker with LLM judges, per error class, against known labels" | **Done** (formal LP/MILP models) | 2607.16646: recall/FPR per class, blind-set theory, McNemar tests |
| "LLM verifier accuracy on LLM prose explanations vs human labels, with injected error types" | **Done** (XAI narration) | 2604.12543 (WCCI 2026): confusion matrix vs author labels; 6 mutation operators |
| "Correct trace, wrong causal explanation" | **Done** (state machines; code) | TempoBench 2510.27544 (SIM 75-96% vs MIN+ 21-33%); CES 2510.15079 (ICSE 2026) |
| "Explanations checked against a simulator / by execution" | **Done as frameworks** | MechSim 2606.04505; FAX 2605.27879 |
| "Solver/simulator-grounded reasoning on deadlock / replacement" | **Done** (final answers; holistic rubric) | PetriBench 2609.19883; CacheMind 2602.12422 |
| "OS domain" alone | Not done, but a **domain transfer** is not a contribution by itself | -- |

**Verified gaps that none of the 12 fully-read papers fills** (each checked against the CSV fields):
1. **Verifier accuracy against independent expert claim-level labels** with reported agreement. 2607.16646 uses labels known by construction; 2604.12543 uses author labels without agreement; MechSim and FAX report no verifier accuracy at all. MechSim's judge prompt also names the methods (A = Causal-Copilot … D = MechSim), so its explanation scores are not blinded.
2. **An error budget for executable verification of *prose*.** How much verification failure comes from (a) turning prose claims into checkable form, (b) claims the checker cannot express (coverage / blind set), and (c) checker error. 2607.16646 found 76.8% of its flags were *extraction noise* on formal models. Nobody has measured this for free-text explanations.
3. **Residual risk after verification.** Are LLM errors *concentrated* in the claims a checker cannot check (causal "because", generalizations, conditions)? If so, "verified" explanations keep a biased residue of errors. TempoBench shows that causal attribution is where models fail, and FAX warns that verification is local, but neither measures the residual error rate of *passed* explanations.
4. **RAG faithfulness vs refusal, measured.** RAGAS's |S| = 0 case is undefined and its validation (50 pairs) contains no refusals. Sufficient Context scores abstention separately and never computes RAGAS faithfulness. The effect is plausible from the definition, so a reviewer would call it definitional unless it is measured on real partial and hedged answers against expert correctness labels.

## 2. Closest prior art: full-read summary
Full fields are in `research/closest_prior_art_verified.csv`. Only the parts that decide novelty are repeated here.

- **2607.16646, Falsification-based verification of LLM optimization models.** The most dangerous paper: same measurement design as ours, different artifact. It compares a solver-based battery with LLM judges on 6,947 mutants, reports recall and FPR per error class, and gives a formal blind set. It also has value-correct-but-wrong cases (23.8% execution-blind mutants). It differs from us in three ways: it checks formal models, not prose; its labels are known by construction; it has no NLI/RAGAS arm. **Consequence:** any claim of ours that "we compare executable checking with LLM judges per error type" is not novel. Our novelty must come from the *prose* layer and the *expert labels*.
- **2604.12543, Two-stage verified XAI explanations (WCCI 2026).** An LLM verifier checks LLM prose against author labels, with injected error types and false-negative counts (e.g. 18 of 209 errors pass). Missing: a deterministic checker, per-type recall, coverage, independent annotators with agreement, and mechanisms.
- **MechSim 2606.04505 (read by me).** The verification agent is an LLM prompt that checks structure, evidence and empirical support. Only sensitivity analysis is executed. Explanation quality is a 1-5 LLM judge score over 5 rounds with method names visible. No human labels. Domains: epidemiology and supply chain.
- **FAX 2605.27879 (read by me).** Claims are tested by re-running the explained ML model. Faithfulness is measured by an LLM simulator predicting that model's behaviour, over 40 scenarios. Verifier verdicts (refuted / corroborated / inconclusive) are never checked against independent labels. The authors say explicitly that "verified" is local.
- **TempoBench, CES, PetriBench, CacheMind.** These establish trace-vs-cause gaps, execution-checked incoherence, and solver-grounded deadlock/replacement reasoning, all on structured outputs, final answers, or one holistic rubric. None decomposes prose into claims or compares verifiers.
- **RAGAS, Sufficient Context.** See gap 4.
- **2605.12748, 2606.01375.** Education context and annotation-reporting precedent (Fleiss κ = .896 with 3 raters). Neither verifies explanations.

## 3. Venue sweep (NLP/IR/SE and education venues)
*Pending; filled from the two sweep reports when they arrive. See the addendum at the end of this file.*

## 4. Adversarial formulations
Each formulation assumes our first framing is already published and asks what would remain. A = scientifically interesting; B = empirically testable with our means; C = plausibly novel **on full-read evidence only**. A and B are never used as evidence for C.

| # | Formulation | A | B | C | Verdict |
|---|---|---|---|---|---|
| F1 | LLM-judge validity for OS explanations vs expert labels | Med | High | **Low**: domain transfer of 2604.12543 / judge-validity work | Killed as headline |
| F2 | Executable checker vs judge vs NLI, per error type, on OS explanations | Med | High | **Low**: 2607.16646 design, new artifact | Killed as headline; kept as an instrument |
| F3 | Trace-vs-cause gap on OS scheduling/paging | Med | High | **Low**: TempoBench / CES | Killed |
| F4 | RAGAS faithfulness rewards refusal on a course corpus | Med | High | **Low-Med**: definitional per RAGAS formula; only a measured magnitude on real hedged answers is new | Side result only |
| F5 | **Error budget of executable verification of prose explanations**: extraction vs coverage vs checker error, against expert labels | High | Med | **Med**: not in the 12 full reads; 2607.16646 measures extraction noise only for formal models | **Survives (pending sweep)** |
| F6 | **Residual-risk hypothesis**: LLM errors concentrate in checker-uncheckable claims, so verified explanations keep a biased error residue | High | Med | **Med**: implied by FAX's caveat and TempoBench, measured by none | **Survives (pending sweep)** |
| F7 | Selective verification: does abstaining on uncheckable claims improve precision at acceptable coverage? | Med | Med | Low-Med: selective-generation work (Sufficient Context) is close | Weak |
| F8 | Checkability as a property of question types (definitional / procedural / trace / causal / counterfactual) | Med | High | Low-Med: descriptive; feeds F5/F6 | Component |
| F9 | Judges vs checker under **lexical-preserving state errors** (wrong transition, same vocabulary) vs lexical errors | Med | High | Low-Med: 2411.16638-style stress tests exist for summarization | Component of F5 |
| F10 | Cross-domain replication: OS mechanisms + a second executable domain (e.g. data structures) to rule out domain-specificity | Med | Med | Adds robustness, not novelty | Component |
| F11 | Simulator fidelity as the object of study: human-simulator disagreements | Med | Med | Low | Threat to validity, not a paper |
| F12 | Leakage: does placing course slides in the judge's context inflate agreement with the tutor? | Med | High | Low-Med: close to self-preference and context-leak work | Side analysis |
| F13 | Does claim-decomposition granularity change verifier recall? (atomic vs sentence) | Med | High | Low: FActScore-style granularity studies | Component |

### Detailed cards for the two survivors (the others are summarized above)

**F5: Where does executable verification of prose explanations fail?**
- **RQ:** For LLM explanations of OS mechanisms, how is the verification failure rate, measured against expert claim labels, split among (a) prose-to-contract extraction errors, (b) claims outside the checker's expressible set, and (c) checker errors?
- **Hypothesis:** (a) dominates false flags and (b) dominates misses. The paper's key number is how much of the undetected error comes from coverage and how much from extraction.
- **Independent variables:** verifier family (simulator checker; cross-family LLM judge; NLI/RAGAS); extraction method (LLM extraction vs gold hand-formalization, the key ablation); claim type.
- **Dependent variables:** per-claim true/false-accept and reject rates; error attribution to stage a/b/c; coverage.
- **Minimum viable dataset:** about 80 human-authored OS questions (scheduling, paging, process states, locks/deadlock from the v2 corpus) × 3 LLMs, giving roughly 1,500 atomic claims. Two expert annotators label correctness and checkability; a third adjudicates.
- **Annotation burden:** roughly 1,500 claims × 2 annotators × about 40 s ≈ 35 hours, plus gold formalization of checkable claims (about 10 hours).
- **Cost:** local generation; judges local or small API. Simulators must be rewritten and validated on textbook worked examples.
- **Closest prior work:** 2607.16646 (formal models, labels by construction); 2604.12543 (LLM verifier on prose, author labels).
- **Exact novelty gap:** a verification error budget for free-text explanations against independent expert labels, with gold-extraction ablation. Neither paper can separate extraction error from coverage for prose.
- **Strongest reviewer objection:** "Domain transfer of 2607.16646 to prose; the error split is obvious." Answer: the gold-formalization ablation isolates extraction error causally, and the split is an empirical quantity nobody has reported for prose.
- **Kill condition:** annotator κ < 0.6 after one revision; or checkable coverage < 20% (too little to decompose); or LLM claim-error rate < 3% (nothing to verify); or the venue sweep finds a paper reporting this split for NL explanations.

**F6: Do "verified" explanations keep a biased residue of errors?**
- **RQ:** Among explanations that pass a verifier, is the error rate in unchecked claims higher than the base error rate? Are LLM errors over-represented in uncheckable claim types?
- **Hypothesis:** P(error | uncheckable claim) > P(error | checkable claim), because causal and generalization claims (uncheckable) are where models fail (consistent with TempoBench). A "verified" badge therefore signals less than its coverage suggests.
- **Independent variables:** claim checkability; claim type; model.
- **Dependent variables:** error rate by checkability; residual error rate of verifier-passed explanations vs judge-passed vs unverified.
- **Minimum viable dataset:** same as F5, shared.
- **Annotation burden:** included in F5.
- **Closest prior work:** FAX (caveat only), TempoBench (causal attribution fails in structured tasks), 2607.16646 (blind set is provably non-empty, but error rates by blind-set membership are not given for prose).
- **Exact novelty gap:** a measured residual-risk estimate for verified prose explanations. This is a direct, practical warning for every "verified explanation" system (MechSim, FAX, tutors).
- **Strongest reviewer objection:** "Selection effect, not a property of verification: checkable claims may simply be easier." Answer: stratify by question difficulty and include checkable-vs-uncheckable claims *within the same explanation* (a paired design).
- **Kill condition:** no significant difference in error rate between checkable and uncheckable claims within explanations (paired test with clustered CIs), in which case the residual-risk story disappears.

F5 and F6 share one dataset and one annotation effort, so they form **one paper**: an error-budget and residual-risk study of executable verification for LLM explanations, with OS mechanisms as the testbed and a second domain (F10) if resources allow.

## 5. A / B / C separation (summary)
- **Interesting but not novel:** F1, F2, F3.
- **Testable but weak novelty:** F4, F7, F9, F12, F13.
- **Plausibly novel on full-read evidence:** F5, F6. Their C rating is conditional on the venue sweep (§3) not finding an equivalent study, and is **not** yet a claim of novelty.

## 5b. Second-round attack (citation check and targeted searches, same day)

A forward-citation check (Semantic Scholar) plus searches aimed at F5 and F6 surfaced more 2026 work. Read depth for each:

| Paper | Read | What it does | Effect on our formulations |
|---|---|---|---|
| **VeriFin** 2608.10213 (Stevens) | FULL (me) | SMT verifier vs LLM judge / judge+formula / PoT on LLM financial numeric claims; false accepts, abstention, **coverage–false-accept trade-off** (98.8% vs 80.6% coverage); 6 generator models; UNSAT-core repair | **Weakens F5 further.** The coverage–false-accept trade-off of symbolic vs LLM verification is now shown in finance. Differences from us: single numeric claims, labels by construction, no prose multi-claim explanations, no salience manipulation |
| **When Verification Fails** 2604.10990 (UPenn) | FULL main text (me) | LLM claim verifiers use **salient-constraint checking**; they over-accept claims whose violation sits in a non-salient, compositional constraint (drops up to 26.7 pp); decomposition prompting only moves the operating point on a shared ROC | **Kills** "LLM judges miss non-salient errors" as a finding. **Motivates F14 below** |
| **Precision Is Not Faithfulness** 2606.09376 | abstract + method (grep) | Complete-oracle domains (F1 telemetry, weather): precision-only faithfulness rewards abstention; the most precise model covers 0.46 of relevant facts; 7,253 instances | **Kills F4.** Also shows the complete-oracle design is established |
| Claimify / claim-extraction evaluation (ACL 2025, 2502.10855) | abstract + intro | Framework for extraction coverage and decontextualization | Extraction omission is studied in general fact-checking, not as a cause of executable-verifier false accepts |
| Know Your Limits 2606.16118 | abstract | Legal NLI: LLM vs LLM-formal vs Z3; "implicit constraint blindness", "scope laundering" | Adjacent: omitted constraints in autoformalization, no salience manipulation, not explanations |
| VeriMed 2605.13817 | abstract + error grep | LLM+SMT auditing of requirements; errors include "omitted structural constraints" | Adjacent evidence that extraction drops constraints |
| Signal-Coverage Matrix 2606.28013 (ICML AI4Math WS) | abstract | Stratifies autoformalization errors into cells (type vs semantic) | Design template for an error-stratum decomposition; weakens F5's framing novelty |
| AdmitOR 2608.15565, ClaimReceipt 2609.01992, credit-narrative fidelity audit 2608.08126 | abstract | Label-free admission gates, evidence-sufficiency receipts, sign errors in LLM narratives of SHAP | Confirm the genre is active; none overlaps F14 |

**Updated verdicts:** F4 **killed**. F5 **weakened** to an incremental error-budget study (VeriFin, 2607.16646, Signal-Coverage). F6 **kept**, but must be framed through the salience result below.

### F14 (new, strongest survivor): does executable verification inherit the salience bias of its LLM claim extractor?
- **Logic:** 2604.10990 shows LLM verifiers check only the salient constraint. Every executable verifier of prose (VeriFin's planner, 2607.16646's slot extraction, FAX's claim identification, MechSim's agents) uses an LLM to decide *which* constraints to formalize. If extraction is itself salience-biased, errors in non-salient constraints never reach the solver. The deterministic checker then "verifies" an explanation whose error it never saw, and executable verification inherits exactly the blind spot it is meant to remove.
- **RQ:** In mechanism explanations with a complete oracle, does the probability that an error is caught drop with its salience, for (a) LLM judges, (b) LLM-extracted + deterministic checking, and (c) gold-extracted + deterministic checking?
- **Hypothesis:** (a) and (b) both degrade on non-salient errors; (c) does not; the (b)–(c) gap is explained by extraction omission of the erroneous constraint.
- **Independent variables:** error salience (salient vs non-salient/compositional), manipulated with a graph-based construction adapted from 2604.10990; verifier arm (a/b/c; also NLI/RAGAS); extraction prompt (plain vs decomposition-forcing vs CWA-style); generator/extractor model family.
- **Dependent variables:** detection rate per arm × salience; extractor recall of the erroneous constraint; false-reject rate on correct explanations; the counterfactual "detected if extracted" rate.
- **Why OS mechanisms:** deterministic simulators give a **complete oracle**: every state, ordering and count claim in a scheduling/paging/lock scenario is decidable, so salience can be varied while checkability is held at 100%. That removes the coverage confound that limits F5 and VeriFin. The domain choice is methodological, not decorative.
- **Minimum viable dataset:** about 60 human-authored scenario templates, instantiated with simulator ground truth (scheduling, page replacement, process state, lock/deadlock). Each correct explanation gets 1 salient and 1 non-salient corrupted variant. Two annotators validate that each corrupted item is unambiguous and has the intended salience: about 360 items, about 12 hours.
- **Closest prior work:** 2604.10990 (salience in LLM verifiers, NLI setting, no executable arm), VeriFin and 2607.16646 (executable vs judge, no salience manipulation), Claimify (extraction coverage, no downstream checker), 2606.16118 (implicit-constraint blindness, no controlled salience).
- **Exact novelty gap:** a controlled test of whether LLM-mediated extraction transmits salience bias into deterministic verification, with the gold-extraction ablation isolating the cause. None of the papers read combines salience manipulation with an executable verifier.
- **A / B / C:** A high (it bears on every neurosymbolic "verified" system); B high (complete oracle, local compute, modest annotation); C **plausible on full-read evidence**, since the components exist separately and the combined causal test was not found. This is **not** a claim of novelty.
- **Strongest reviewer objection:** "An obvious combination of 2604.10990 and known extraction omission." Answer: the result is not obvious in either direction. Deterministic checkers could escape the bias if extractors enumerate exhaustively (the decomposition prompt condition tests this), and a null result would itself matter for neurosymbolic verification claims.
- **Kill condition:** extractor recall on non-salient erroneous constraints is within the CI of salient ones under the plain prompt (no transmission), **or** the effect disappears under decomposition-forcing prompts at no false-reject cost (trivially fixable), **or** the pending venue sweep finds this test already published.

## 6. What this review cannot rule out
- Paywalled ACM/IEEE/Springer/Elsevier papers were read at abstract level at most.
- The 2026 literature moves quickly: two close papers (2607.16646, 2609.19883) appeared within the last three months.
- A citation-graph check (forward citations of 2607.16646, 2604.12543, FAX, MechSim) has not been done. It is the single most efficient remaining test before committing.

## Addendum A: education-venue sweep (subagent, 2026-09-30)

Coverage: AIED, EDM, LAK, ITS, L@S, SIGCSE, ITiCSE, ICER, Koli, CompEd, TOCE, TLT, FIE, C&E, C&E:AI, IJAIED, BEA, BJET, searched via Crossref, OpenAlex, arXiv, venue sites and web search. About 30 relevant papers, 16 read beyond the abstract. **DBLP was blocked; ACM/Elsevier/Springer full texts returned 403 (abstract only).**

**Must be cited, not claimed:**
- LLM-judge vs expert agreement for CS feedback, grading and code: Koutcheme et al. ITiCSE 2024 / SIGCSE 2025; Pathak et al. ICER 2025; Jain et al. 2510.11822 (judges reject invalid outputs poorly, TNR < 25%); Van Mullem et al. 2603.28295 (RAGAS-style metrics found unexplainable; judge calibrated on 100 expert-scored answers, κ = 0.655).
- Judge validated against experts in a systems domain, plus simulator scoring: **QuArch** 2510.22087 (85.48% judge-expert agreement vs 90.75% human-human; answer level).
- Claim-level NLI grounding in a CS1 tutor, with an over-refusal trade-off and an explicit note that code claims need execution: **EduGuard** 2607.15738.
- Sentence-level faithfulness labels validating hallucination detectors on course feedback: **Jia et al. EDM 2024** (1,430 sentences; best F1 ≈ 72%).
- Answer-level LLM correctness on OS: Joshi et al. SIGCSE 2024 (OS 58.4%); Liu et al. 2509.08862 (OS and computer-organization course assistant, 600 labelled responses, 2.17% erroneous).
- Concurrency-bug feedback vs teacher ground truth: Estévez-Ayres et al. IJAIED (about 50%).

**Not found (in the sources above):** RAGAS faithfulness validated against claim-level instructor labels; a claim-labelled OS explanation dataset; an LLM tutor coupled to an OS simulator; a validated OS concept inventory after 2014; a measured executable-coverage rate of tutor claims (EduGuard states it only qualitatively). **Nothing in the sweep tests F14** (salience transmission through extraction into an executable verifier).

**New threat to validity for any OS labelling:** Liu et al. marked as wrong an effective-access-time answer that uses the standard parallel-access convention. The "gold" answer depended on the course's convention. Expert labels on OS explanations must record the convention (e.g., hierarchical vs parallel memory access; counting of context switches; tie-breaking in scheduling), and the simulators must be parameterized by it. This favors F14's constructed complete-oracle items, where the convention is fixed per item, over labelling natural explanations only.

**Impact on the decision:** none on the recommendation. The survivor list is unchanged, and F1/F4-style framings are now even more crowded in education venues. The NLP/IR/SE sweep is still pending.

## Addendum B: NLP/IR/SE venue sweep (subagent, 2026-09-30)

Coverage: arXiv API, OpenAlex (partial; rate-limited), Crossref, web search restricted to aclanthology.org, dl.acm.org and ieeexplore.ieee.org. **DBLP was blocked and Semantic Scholar was rate-limited: effectively not searched.** 27 close papers; read at PARTIAL depth (abstract + method + annotation + results) or abstract only; none in full.

**Must be cited, not claimed:**
- **Kang, Milliken, Yoo 2024, "Identifying Inaccurate Descriptions in LLM-generated Code Comments via Test Execution"** (2406.14836): the most dangerous paper. Execution-based verification of LLM natural-language descriptions against human accuracy labels (540 comments). Consistency detectors, similarity metrics and an LLM detector fail; "document testing" works. It gives a coarse **testable vs untestable** split of error types. Any claim-coverage or executable-vs-judge result must be positioned as an extension of this paper.
- Claim or segment-level human labels on code explanations with per-type verifier accuracy: **ReFEree** 2604.10520 (α = 0.74, 4 error types, G-Eval/FactScore baselines), **ETF** (ACL 2025, about 10K entity labels).
- Verifier meta-evaluation against segment or step labels by error type: **FELM** (NeurIPS 2023 D&B), **REVEAL** (ACL 2024), **ReaLMistake** (COLM 2024), **FBI** (EMNLP 2024, judges miss >50% of injected degradations).
- RAGAS vs LLM judges under graded error injection: **Can We Trust the Judges?** 2609.15561 (RAGAS tracks degradation better on NQ).
- Oracle-graded mechanism explanations: model checking as the oracle for LLM explanations of MDP policies (2608.30581), with no human labels and no judge comparison.
- Judge validity on causal failure explanations: 2604.18309 (EASE 2026), explanation-level ratings only.

**Not found (in the sources above):** a three-way comparison of judge, NLI/RAGAS and executable checks on the same claim-labelled explanations; any claim-labelled OS mechanism explanation data; a measured claim-coverage rate; trace-vs-causal claims as an axis of verifier validity; faithfulness vs correctness on mechanism explanations with human labels. **Nothing in the sweep manipulates error salience against an executable verifier or ablates extraction with gold formalizations. F14 is not pre-empted by anything this sweep found.**

**Impact:** F14 stands. Kang et al. 2024, ReFEree and ETF join 2604.10990, VeriFin and 2607.16646 in the closest-prior-art set of any F14 paper. The claim-coverage piece (F4-style) must now be framed explicitly as a refinement of Kang et al.'s testable/untestable split, not as new.
