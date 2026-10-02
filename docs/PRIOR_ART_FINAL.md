# Prior art — hostile re-review (replaces AGY's version)

**Date:** 2026-10-02. **AGY's version:** `docs/archive/PRIOR_ART_FINAL_AGY.md`.

**Method.** Web search on 2026-10-02 for every work AGY named, plus the closest threats AGY did not name. This is a targeted adversarial search, not a systematic review: a skeptical reviewer could still surface something closer, and that limitation is stated in the audit.

## 1. Verification of AGY's citations

| AGY citation | Exists? | What it actually is | AGY's description |
|---|---|---|---|
| CoRE | Yes. arXiv [2507.05269](https://arxiv.org/abs/2507.05269), NeurIPS 2025 D&B | Static-analysis tasks (data/control dependency, information flow) on C/C++/Java/Python, 12,553 instances | Roughly right ("deterministic") |
| EquiBench | Yes. arXiv [2502.12466](https://arxiv.org/abs/2502.12466) | Program-pair equivalence checking, 2,400 pairs | Roughly right |
| DexBench ("The Path Not Taken") | Yes. arXiv [2604.20917](https://arxiv.org/abs/2604.20917), ACL 2026 | Forward coverage prediction plus backward counterfactual input mutation on **Python programs**, 445 instances | **Wrong.** AGY called it "robotic planning and task graphs". |
| SVAC ("Semantic Verification of Agent Code") | **Not found** under that name | — | Cited with no URL or ID. Treat it as unverified or fabricated and remove it. |
| TempoBench, PetriBench, CES | TempoBench is in the committed literature DB (arXiv 2510.27544). PetriBench and CES were not re-verified. | — | Unverified; remove them unless an ID is found. |

## 2. "Has somebody already done this experiment under another name?"

| AGY claim | Closest prior work | Verdict |
|---|---|---|
| A gap exists between exact-match-to-reference scoring and semantic scoring when many outputs are valid (the "RSG") | **Functional-correctness evaluation** of code: Kulal et al. 2019 (SPoC); Chen et al. 2021 (Codex/HumanEval, pass@k), which argued explicitly that match-based metrics miss functionally correct programs; CodeBLEU (2020). Planning evaluation with a plan validator rather than a reference plan (PlanBench / VAL). Multi-reference BLEU in machine translation. | **KILLED as a contribution.** Exact match against one of k > 1 valid outputs under-counts by construction (RSG ≥ 0 because R1 ∈ V(P)). It is a known, mathematically forced effect. Its *magnitude* on this benchmark can be reported as context only. |
| Reference sensitivity: a judge changes its verdict when given a reference | Yeadon et al. 2026, *LLM-as-a-judge validity is strongly task-dependent across physics assessment formats* ([arXiv 2603.14732](https://arxiv.org/abs/2603.14732)): blind vs official-solution vs false-solution vs anchored conditions; "models defer to provided references". *Judging Against the Reference* ([arXiv 2601.07506](https://arxiv.org/abs/2601.07506)): swapping the reference entity sharply drops judge accuracy, and judges even reject candidates that match the swapped reference. Kranti & Vajjala 2026 ([arXiv 2607.12885](https://arxiv.org/abs/2607.12885)): adding or removing the reference flips verdicts by up to 85%. Krumdick et al. 2025, *No Free Labels* ([arXiv 2503.05061](https://arxiv.org/abs/2503.05061)): judges succeed where they could answer themselves, and references help. Reference-Guided Verdict ([arXiv 2408.09235](https://arxiv.org/abs/2408.09235)). | **Heavily NARROWED.** "Judges are sensitive to the supplied reference" is established in QA, physics and math grading. AGY's "unstudied hypothesis" claim is false. |
| A *valid but different* reference makes judges reject *valid* candidates | None of the works above, as far as their abstracts and summaries show, supplies a correct-but-different reference for a candidate whose validity is **formally decidable**. Yeadon et al. use false solutions; 2601.07506 uses swapped (wrong) entities; 2607.12885 varies presence and position. | **SURVIVES, narrowly, and must be stated as a gap in *this* search.** The surviving contribution is a *controlled measurement* in a domain with an exact oracle, with no-reference, irrelevant-reference and reworded-reference controls. It is not a new phenomenon. |
| Model rankings change under single-reference evaluation | Yeadon et al. report that false references degrade accuracy "but leave rank-ordering intact". In code generation, ranking changes between match metrics and pass@k were part of the Codex/CodeBLEU motivation. | **Open, low prior.** Prior evidence suggests rankings are robust. The claim may be made only if H4 passes. |
| Nondeterministic / concurrent execution traces specifically | DexBench (multiple *input-dependent* paths, still deterministic per input). CONCUR ([arXiv 2603.03683](https://arxiv.org/html/2603.03683v1)): concurrent code generation validated by exploring all interleavings with Java PathFinder. Execution-trace benchmarks (CRUXEval, CodeMind, REval, CoRE) assume one trace per input. | **Survives as a domain choice, not as novelty.** Applying a known judge bias to a new domain is exactly the "same domain difference" the brief says not to accept. The defensible value is that the domain gives an **exact validity oracle** and **controllable |V(P)|**, which none of the reference-bias papers had. |
| "OS is not merely domain substitution" | — | **REJECTED as stated.** For the *phenomenon*, OS is a domain substitution. For the *measurement*, the OS domain is useful because V(P) is enumerable, and that is how the claim should be phrased. |

## 3. Educational-practice threat (a construct-validity threat AGY missed)

Standard OS course material resolves scheduling ties by **convention**: "the process with the smaller ID goes first", or FCFS order for SJF ties. Examples: Silberschatz practice exercises; GATE-style problem sets ([gatevidyalay](https://www.gatevidyalay.com/cpu-scheduling-practice-problems-numericals/)).

So in real course grading, R1 often *is* the specification, and a grader who rejects R2 is following course rules, not showing bias. Our prompts state explicitly that ties may be broken in any order, which makes rejecting R2 an error *relative to the stated rules*. But any claim about **educational grading in practice** must be dropped or heavily qualified.

## 4. Strongest prior-art threat

**Yeadon et al. 2026 and *Judging Against the Reference* (2601.07506) together.** They already show that LLM judges defer to a supplied reference, including against correct answers. A reviewer can argue that our result, whichever way it comes out, is a domain instance of this known bias. Our only answers are:
- (a) **valid** alternative references rather than false or swapped ones,
- (b) an exact oracle with |V(P)| control,
- (c) context controls (none, irrelevant, reworded) that separate anchoring from generic context effects.

If (c) shows the effect is generic, the reviewer wins.

## 5. Decision

The surviving novelty is a narrow, measurement-type contribution. "GO WITH HIGH CONFIDENCE" is withdrawn. See `docs/CLAUDE_FINAL_RESEARCH_AUDIT.md`.
