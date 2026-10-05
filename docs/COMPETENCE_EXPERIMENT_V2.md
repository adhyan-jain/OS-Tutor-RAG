# Competence experiment V2 — design only (nothing here has been run, bought or downloaded)

**Date:** 2026-10-04. **Status:** proposal; uncommitted. **No API key exists in this environment, no money has been spent, and no model was run.** The closed local pilot (Decision C, `research/ssr_pilot/results/competence_pilot/`) is untouched; its frozen `decision_rubric.md` is not edited. This document does **not** use the 0.5B AirLLM test as a substitute and does **not** claim AirLLM failed: AirLLM was never successfully run, and its runtime and compatibility remain untested.

## 1. Question this experiment answers (and does not)

*Among clearly more capable models, with the convention stated, does a large share of oracle-valid output stay non-canonical, **and** does evaluator choice then change model-level conclusions?*

It does **not** test whether stronger models are better, and it is not a general benchmark. It exists because (a) the frozen data show a large per-output gap but **no reversal** among four weak models (`SSR_CONCLUSION_IMPACT_ANALYSIS.md` §3, §8), and (b) a ranking reversal is only possible among models of **comparable ability** that the two evaluators order differently.

## 2. Design choices fixed in advance

| Item | Choice |
|---|---|
| Task | The existing stated-convention task, byte-identical prompts: `render.render_variant(world, variant, stated_convention=True)`; prompt template hashes taken from `render.py` (sha256 `c8142b77…`) and recorded in the run manifest |
| Worlds / variants / seeds | 24 worlds × 3 surface variants × 4 samples = **288 generations per model** (full run); **staged screen** = 8 worlds × 3 × 4 = **96 per model** |
| Stage-1 world rule (fixed now, before any output) | From the 16 stratum-D worlds (where the stated convention determines R) sorted by id, take indices 0, 2, 4, …, 14: **bank_01, bank_04, bank_07, sched_02, sched_05, sync_01, sync_05, sync_07**. This excludes the 8 stratum-U worlds on purpose: the screen should not be confounded by an underdetermined R. The full run uses all 24 with the strata reported separately (as in `analyze_competence_pilot.py`) |
| Decoding | temperature 0.7, top_p 0.95, max output 600 tokens, no system prompt beyond the frozen one; "thinking"/reasoning modes disabled or capped so the 600-token cap is not consumed by hidden reasoning. Where an API forbids setting both temperature and top_p, or forbids a seed, that is **recorded as a deviation before the first call**, never adjusted later |
| Samples | 4 independent samples per (world, variant); the sample index plays the role of the seed; idempotent key `(model, world, variant, sample)` so an interrupted run resumes without duplicating |
| Evaluators | Unchanged: A_strict, A_norm, B (UNVERIFIABLE = invalid), C, plus B_ub as sensitivity; analysis per `impact_analysis.py` with its hashed definitions |

## 3. Model selection

**Preference order (yours, kept):** (1) a hosted strong model with an existing key; (2) a stronger machine/cloud instance; (3) a local 12–14B model only if it is feasible (the closed pilot found RAM, not the GPU, was the binding limit on this laptop).

**Candidates are chosen by capability class and family, never by results.** I have not verified provider catalogues or prices for this document; the model IDs for non-Anthropic providers must be read from the provider's own model list at the time of the run. Selection rule:

- **Minimum (answers the competence question):** ≥ 2 models from **different families**, each plausibly far above the 7–9B baseline (baseline pooled valid rate 0.153).
- **Recommended (also gives the ranking question a chance):** **4 models = 2 families × 2 sizes** (a large and a small/medium model per family), because a reversal needs models in a similar ability band. Two very strong models will mostly be ranked identically by every evaluator and cannot test reversal.
- **Families (examples, to be confirmed from live catalogues):** Anthropic (the API names on record in this environment: `claude-sonnet-5-5`, `claude-haiku-4-5-20251001`), plus at least one non-Anthropic hosted family (e.g. an OpenAI or Google model), and optionally a hosted open-weight family (Qwen, Llama, Mistral) through a third-party host.
- **Not used:** reasoning-mode models with uncapped thinking; code-specialised variants; the existing four local models as "strong".
- **Conflict note:** if an Anthropic model is tested, the analysis and write-up must not describe Anthropic models as the evaluator or reference in any other role; they are test subjects only. The oracle is the deterministic code in `oracle.py`, not an LLM.

## 4. Cost, runtime, privacy

**Token arithmetic (measured on the 1,152 existing outputs):** mean prompt 337 tokens, mean output 67 tokens (median 54, p90 142, max 600). Per model, per 288 generations: **97,056 input tokens and 19,296 output tokens**; per 96 generations: ≈ 32,352 input and ≈ 6,432 output. Cost per model = 0.097 × P_in + 0.0193 × P_out dollars, with P_in and P_out the provider's price per million tokens. **I have not looked up current prices; any dollar figure here is a formula, not a quote.** As an *illustration only* (placeholder prices of $3 input and $15 output per million tokens, not a real quote) the cost is ≈ $0.58 per 288-call model and ≈ $0.19 per 96-call screen. Token counts will differ by tokenizer, and models that explain at length will output more (max 600 per call → worst case 172,800 output tokens per model); the plan's cost ceiling uses that worst case. **No spending without your approval of a quoted cost.**

**Runtime:** one hosted call is a few seconds; 288 sequential calls ≈ 10–30 minutes per model with modest concurrency (not measured; depends on rate limits). The local scoring and analysis run in seconds.

**Privacy:** prompts are synthetic OS worlds (process tables, resource matrices); no personal data, no repository code. They would leave the machine to a third party, and some providers retain prompts per their policy. API keys must be supplied by you through an environment variable; they are never written to a file, a log or a manifest.

## 5. Sample-size and power justification (from the frozen data, not from the new models)

Per-world SD of pairwise gaps in the stated arm (24 worlds, existing models): **0.265 under B** and **0.170 under A_norm** (averages across the six pairs). The detectable gap for one unadjusted two-sided test at 80% power is ≈ 2.8 × SD/√W:

| Worlds | B gaps | A_norm gaps |
|---|---|---|
| 24 | ≈ 0.15 | ≈ 0.10 |
| 48 | ≈ 0.11 | ≈ 0.07 |
| 8 (the screen) | ≈ 0.26 | ≈ 0.17 |

Consequences: **(i)** the screen (8 worlds) can estimate whether competence is high and FRR among valid outputs stays large, but is **not** powered for model-level conclusions and is never presented as confirmatory; **(ii)** the full run (24 worlds) detects only gaps of about 0.10–0.15, so a reversal between models closer than that cannot be declared; **(iii)** if the screen passes and the ranking question is the target, add worlds (a second world bank of 24 would give 48) before adding models. These variances come from weak models and will differ for strong ones; the screen's own variances replace them for the final sizing. FRR among valid outputs depends on the number of valid outputs: with 8 worlds and ~50% valid, roughly 48 valid outputs per model, clustered in 8 worlds, so its CI will be wide (my estimate is ±0.15–0.25; not computed).

## 6. Stages, GO / NO-GO gates and stopping rules

All thresholds below are **proposed** and will be written into a new `decision_rubric_v2.md` and hashed **before** any call is made; they are never changed afterwards.

**Stage 0 (free, local, no API):** freeze rubric v2; hash prompts and worlds; run the unchanged pipeline end-to-end on mock outputs; confirm the key is available and approve the quoted cost (the approval is a **human decision**).

**Stage 1 (screen, 96 gens/model):**
- *Gate S (competence):* at least one model with **B ≥ 0.30 and ≥ 25 valid outputs** (roughly twice the baseline 0.153, with enough valid outputs for a usable estimate). Fail → stop; the thesis remains "weak-model phenomenon, unproven".
- *Gate P (phenomenon among capable models):* among models passing S, **pooled FRR_norm ≥ 0.40** (lower bound reported, not required). FRR below 0.20 would indicate that the reference gap shrinks with competence.

**Stage 2 (full, 288 gens/model)** only if S and P pass in Stage 1, and only after the cost of the full run is quoted and approved. Predefined analysis: the eight hashed definitions in `impact_analysis.py` plus the strata (D vs U) split.

**Stopping rules (any stage):** stop if (a) > 5% of calls error or return unparseable output for reasons other than the model's own format, (b) realised spend exceeds 1.5× the approved quote, (c) the API silently changes the model identifier mid-run, (d) a mismatch is found between the prompt hash and the frozen one, (e) the key has been rate-limited into a state that makes seeds non-independent. A stop is recorded, not hidden.

## 7. What would strengthen or weaken the thesis (predefined)

| Outcome | Reading |
|---|---|
| FRR_norm stays ≥ 0.40 for capable models **and** at least one supported significance change **or** a decisive reversal with stable rank order among comparable models | Thesis strengthened: the problem survives competence and affects model-level conclusions. Still only an OS result |
| FRR stays high but **no** reversal or supported change, with adequate precision (evaluator-effect CI within ±0.05 for every pair) | "Absolute underestimation, stable conclusions": consistent with the likely literature pattern; a modest measurement paper at best |
| FRR_norm < 0.20 for capable models | Thesis weakened: the phenomenon is mainly a weak-model artifact; **stop or pivot** |
| Stage 1 fails Gate S | Inconclusive; do not scale; the question needs more capable access, not more local runs |

## 8. Entry conditions for the later phases (not executed)

- **Core evaluator comparison / meta-evaluation of LLM judges (Phases 4–5):** only if Stage 2 passes. A reference-free LLM judge would be scored against the exact oracle (agreement, false accept/reject, and whether its model ranking agrees); the judge prompt and model are fixed in the rubric before use.
- **Controlled pairs (Phase 6), predefined here before any result:** **A** canonical valid trace; **B** non-canonical but valid trace; **C** invalid trace minimally perturbed from B; **D** invalid trace minimally perturbed from A; **E** same final state but invalid trajectory; **F** semantically valid but lexically very different; **G** lexically similar but semantically invalid. Purpose: separate surface similarity, final-state similarity, canonical-reference proximity and executable validity. These categories are fixed now and may not be added to after seeing which direction favours the thesis.
- **Second domain (Phase 7):** only if the OS result is strong **at the model-conclusion level**; candidates must have multiple valid solutions, executable semantics, a bounded state space, independently enumerable valid solutions and a deterministic oracle (e.g. Petri-net/concurrency, workflow execution, graph planning). No second benchmark before then.
- **Paper skeleton (Phase 9–10):** only after the science survives; not started.

## 9. Overall GO / NO-GO for the program

**NO-GO (stop, pivot or kill) if any of:** the novelty audit finds essentially the same experiment and conclusion (currently the nearest is SVAC-Concurrency, which reports the per-output effect but, in the draft read, no ranking analysis); no key or budget is approved; Stage 1 fails Gate S; or the outcome is "FRR < 0.20 for capable models".

**GO to Stage 1** only if: you provide a key and approve the quoted cost for the screen, ≥ 2 families are available, and the residual novelty (exact oracle over the enumerated valid set + a model-level test) still stands after re-reading the SVAC draft.

**GO to the full run** only if Stage 1 passes Gates S and P.

**Where the evidence stands now:** the per-output gap is established but not novel; the model-level effect is unproven (zero reversals; five same-direction significance changes among near-floor models); the competence question is open. A journal-grade claim requires the model-level effect to appear with capable models.
