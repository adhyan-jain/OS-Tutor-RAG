# Competence mini-pilot — decision rubric (frozen before any model output)

**Frozen:** 2026-10-03, before any competence-pilot generation. Its SHA-256 is stamped into every manifest of this phase. The rubric may not be edited after the first generation; any later change must be appended under "Deviations" and will change the hash.

**Question.** Among substantially more capable models, with the tie-break convention stated in the prompt, does a large share of semantically valid output remain non-canonical?

**Fixed conditions (identical to the stated-convention arm).** 24 existing worlds × v0/v1/v2 × seeds 0–3 = 288 generations per model; stated-convention prompts; temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600; evaluators A_strict, A_norm, B, C; same oracle and banks; world-clustered bootstrap (2,000 resamples, seed 0).

**Baseline.** The four local 7–9B models in the stated-convention arm: pooled FRR_norm 0.625 [0.443, 0.816], pooled B 0.153, A_norm 0.057. The baseline is recomputed from raw outputs with the current scorer and must reproduce 0.625 before any new number is trusted.

## Quantities
- **FRR_norm** = P(A_norm rejects | B accepts), pooled over the new models, with a world-clustered 95% CI.
- **Competence gain** = pooled B (new models) − pooled B (baseline, 0.153).
- **n_valid** = number of semantically valid outputs among the new models' outputs.

## Decision (exactly one; applied mechanically)

1. **Competence gate (fixed here, new for this phase).** The gate passes only if **competence gain ≥ 0.15 and n_valid ≥ 100**. If it fails, the decision is **C**, whatever FRR_norm shows.
2. If the gate passes:
   - **A) DISCREPANCY SURVIVES COMPETENCE CHECK:** FRR_norm ≥ 0.50, the drop from 0.625 is at most 0.15 (FRR_norm ≥ 0.475 is implied), and the CI lower bound is above 0.10.
   - **B) DISCREPANCY SUBSTANTIALLY SHRINKS:** the CI **upper** bound of FRR_norm is below 0.50 and the drop from 0.625 is at least 0.15.
   - **C) INCONCLUSIVE:** every other case, including a CI that straddles 0.50.

**Provenance of the numbers.** 0.50 and 0.15 come from the decision logic in `research/ssr_pilot/analyze_stated_convention.py` (A: FRR ≥ 0.50 and change > −0.15); 0.10 is the K1 non-triviality bar in `docs/research/SSR_PILOT_PREREG.md`. The competence gate (0.15 gain, 100 valid outputs) is new and is fixed here, before any data, to separate "the phenomenon shrinks" from "the models are still too weak to tell".

## Descriptive only (no thresholds)
Per-model B, A_norm, A_strict, C, FRR_norm, UNVERIFIABLE rate, valid-but-reference-wrong rate, counts; family and variant breakdowns; pairwise model comparisons; the 7-model (B, FRR) table; and the **world strata** below.

**World strata (fixed in advance; applied identically to the baseline).** In 8 of the 12 constrained worlds a model that applies the stated tie-break literally (lowest-index choice at each tie, constraint ignored) violates the task constraint, and the prompt does not say how to resolve the conflict.
- **Stratum D (R is the literal reading), 16 worlds:** all 12 unconstrained worlds, plus the 4 constrained worlds where the literal reading already equals R (sched_02, sync_06, sync_08, bank_04).
- **Stratum U (R underdetermined by the stated convention), 8 worlds:** sched_04, sched_06, sched_08, sync_02, sync_04, bank_02, bank_06, bank_08.
FRR is reported for D and U separately and pooled. The decision above uses the pooled figure, as in the stated-convention arm.

## Failure handling (rules, not discretion)
- Excessive invalid or unparseable output: recorded as data; no evaluator change, no length or temperature change, no manual correction.
- A model that cannot run for hardware reasons: stopped, with the exact reason recorded; remaining models continue.
- No model is removed because its result is inconvenient.
- Ollama crash: completed outputs are preserved; the run resumes without duplicating trials.

## Deviations
(None yet.)
