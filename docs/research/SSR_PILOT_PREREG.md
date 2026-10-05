# SSR pilot — preregistration

**Frozen:** 2026-10-02, before any language-model output exists and before any attacker result has been looked at. **Freeze mechanism:** SHA-256 of this file is stamped into every manifest and results file (as in the RSG study). Edits after the freeze must be appended to §9 with date and reason, which changes the hash.

## 1. Question

Does replacing reference-trajectory matching with a reference-independent semantic oracle change a *substantive scientific conclusion* about LLM execution reasoning on OS mechanisms (a model ranking, a pairwise model comparison, or a model's failure profile)? The finding "valid traces differ from the reference" is not a result: it is forced by |V| > 1 and is reported only as context.

## 2. Design (fixed)

- **Worlds:** 24 = 8 each of scheduling, synchronisation, Banker's safe sequences, generated from seeded parametric specs (`research/ssr_pilot/worlds.py`). The world is the statistical unit.
- **Surface variants:** v0 plain, v1 renamed entities + paraphrased narration, v2 reordered narration/rows + table output format. Variants and seeds are nested inside worlds and are **never treated as independent observations**.
- **Models:** qwen3:8b (think off), llama3.1:8b, gemma2:9b, mistral:7b-instruct. Temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600, seeds 0–3.
- **Volume:** 24 × 3 × 4 × 4 = 1,152 generations.
- **Evaluators:** A_strict (exact string match to R), A_norm (exact match of the parsed, normalised trajectory), B (`semantic_valid == TRUE`), C (B and outcome-equivalent to R). UNVERIFIABLE counts as *not valid* in primary rates; the sensitivity bound counts it as valid.
- **Reference R:** the first trace, in canonical enumeration order (listed order / arrivals before the requeued process / lowest-index enabled thread / lowest-index safe process), among traces that satisfy the task constraints. The prompt does **not** state this convention. It says that any valid trace is acceptable.

## 3. Quantities

- **FRR_norm** = P(A_norm rejects | B accepts), pooled over models and outputs, with a world-clustered bootstrap CI (2,000 resamples, seed 0). Also reported per model, per family and per variant.
- **Agreement of a cheap proxy** with the oracle on model outputs = balanced agreement: (P(proxy accepts | B accepts) + P(proxy rejects | B rejects)) / 2.
- **Model scores** per world: the mean over that world's outputs (3 variants × 4 seeds) of the evaluator's accept indicator.

## 4. Kill criteria (thresholds fixed here)

| # | Test | Passes if |
|---|---|---|
| **K0** | Benchmark integrity | For each surface classifier (length/token counts, character n-grams, lexical overlap, distance to R), the balanced accuracy on valid-vs-invalid (balanced per world, grouped by world, and leave-one-structure-out) has a world-bootstrap 95% CI lower bound ≤ 0.55 **and** a point estimate ≤ 0.65 |
| **K1** | Disagreement is non-trivial | Pooled FRR_norm ≥ 0.10 and the CI lower bound > 0.05. (The mechanical floor 1 − E[1/\|V\|] of a uniformly random valid generator is reported as context, **not** a gate.) |
| **K2** | Survives surface normalisation | The K1 criterion holds for FRR_norm in **each** of the three variants separately |
| **K3** | Survives attacker baselines | The trajectory-distance proxy **and** the final-state-only proxy each have balanced agreement < 0.95 with the oracle on model outputs. Otherwise a cheap proxy reproduces the oracle and the oracle adds little. |
| **K4** | Changes a model-level conclusion | At least one of (i)–(iii) holds, and is stable in ≥ 70% of 500 world-level bootstrap resamples (below) |
| **K5** | More than one mechanism family | The K1 criterion holds separately in ≥ 2 of the 3 families |

**K4 definitions** (4 models, 6 pairs, scores per world as in §3):
- **(i) Ranking reversal.** For some pair, the sign of the mean per-world difference is opposite under A_norm and under B. Stable if the observed signs are reproduced in ≥ 70% of resamples.
- **(ii) Significance change.** For some pair, the paired sign-flip test (20,000 flips, seed 0, Holm correction over the 6 pairs, α = 0.05) is significant under exactly one of A_norm and B. Stable if, in ≥ 70% of resamples, |mean difference| / standard error > 2.0 under exactly that evaluator and not the other.
- **(iii) Failure-profile shift.** For some model, **a majority (≥ 50%) of the outputs that A_norm calls wrong are semantically valid**, i.e. reference-based evaluation would attribute mostly non-errors to that model. Stable if this holds in ≥ 70% of resamples.

## 5. Decision rule (mechanical; judgement is added as notes only)

- **GREENLIGHT** iff K0, K1, K2, K3, K4 and K5 all pass.
- **CONDITIONAL** iff K0–K3 pass and K4 and/or K5 fail or are inconclusive *because of power*. The report states the number of worlds that would be needed.
- **KILL** otherwise: K0 fails and cannot be repaired; or K1, K2 or K3 fails; or K4 fails with adequate precision (the 95% CI of the per-pair mean difference excludes any reversal).
- If K0 fails, the trace banks are redesigned **before any LLM spend**. The threshold is not changed.

## 6. Oracle contract

`evaluate_candidate(world, raw_text, truncated)` has no reference argument.
- **TRUE** only after a complete replay that satisfies the rules and constraints.
- **FALSE** only with a named witness (a violated rule, a violated constraint, or an incomplete trace that was not truncated).
- **UNVERIFIABLE** when validity cannot be established: nothing parseable, unknown entity names, or a truncated output whose visible prefix has no violation.

Outcome equivalence and reference match are computed by a *separate* function that takes the reference.

## 7. Clarifications of the approved plan (made before any run)

1. K1 as approved said "above the random-valid floor in ≥ 1 comparison". That clause is ambiguous, so the floor is reported as context only.
2. The plan's taxonomy criterion ("a ≥ 0.15 share shift") would merely restate FRR. It is replaced by K4(iii), which asks whether a *majority* of a model's reference-based "errors" are not errors.
3. The oracle for scheduling and synchronisation delegates its transition replay to `research/simulator/validators.py`, which is reference-independent and was written separately from the enumerators. The independence check is validator vs enumerator (and brute-force permutations for Banker's), not a third implementation.

## 8. Reporting rules

- No novelty claims. Negative results are reported in full.
- Sample size is not inflated: 24 worlds, and the CIs will be wide.
- Every number is recomputed from raw JSONL.

## 9. Deviations

Each deviation is appended here with date and reason, which changes the hash.

- **D1 (2026-10-02, before any LLM output).** K0 **failed** on the first bank. The distance-to-R classifier separated valid alternatives from invalid traces at 0.663 [0.616, 0.711] under grouped CV, above the 0.65 limit. Per structure, invalid traces sat farther from R than valid alternatives in sync and Banker's worlds (mean normalised distance 0.71 vs 0.56 in Banker's, 0.74 vs 0.53 for semaphores). The bank was redesigned as §5 requires; **the K0 threshold was not changed.** Each valid alternative is now paired with the unused invalid trace whose similarity profile to R (normalised edit distance, first-divergence position, same first step, same last step) is closest, and K0 is evaluated on these matched pairs. The leak is real, so this is a design repair, not a threshold change. Selection effect: matching favours invalid traces that look like valid ones, so specificity measured on the bank is harder than on unmatched invalid traces.
- **D2 (2026-10-02, before any LLM output).** Two operational definitions the approved plan left open.
  - **K3 distance proxy:** its threshold is fitted to the *oracle's verdicts on model outputs of the other mechanism families* (leave-one-family-out), which gives the strongest cheap proxy, rather than to bank traces. If even this proxy fails to reproduce the oracle on the held-out family, K3 passes.
  - **D3 (2026-10-03, after the first LLM outputs were generated and first scored).** Two defects found by reading real outputs, both fixed in code with regression tests. Neither changes a criterion, a threshold or a decision rule. (a) `research/simulator/validators.py` raised `ValueError` on a schedule that ends with an `IDLE` segment after every process has finished; it now returns FALSE (`idle_after_completion`). The RSG benchmark never contained such a trace, so no earlier result changes. (b) A_norm counted "reference + a token outside the world" as an exact match, because the parser drops out-of-world tokens; 5 of 1,152 outputs (0.4%, all mistral:7b-instruct) were affected and now count as non-matches. The K-criteria outcomes are compared before and after this fix in the report.
  - **"Adequate precision" for the KILL branch of K4:** the world-bootstrap 95% CI of the evaluator effect on the pairwise gap, mean(Δ_A_norm − Δ_B), lies within ±0.05 for **every** one of the 6 pairs.
