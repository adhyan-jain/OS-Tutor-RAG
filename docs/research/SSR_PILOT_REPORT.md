# SSR pilot report — does the choice of evaluator change conclusions about LLM execution reasoning?

**Date:** 2026-10-03. **Branch:** `ssr-pilot` (uncommitted). **Pre-registration:** `docs/research/SSR_PILOT_PREREG.md`. **Decision:** `docs/research/SSR_PILOT_DECISION.md`.
**Scope:** a pilot to decide whether a larger study is worth building. It makes no novelty claim and is not a benchmark.

## 1. Bottom line

- **Question.** If model-generated OS execution traces are scored by an independent, reference-free semantic oracle instead of by matching a canonical reference trace, does a substantive conclusion about the models change?
- **Mechanical result of the pre-registered rules: CONDITIONAL.** K0, K1, K2, K3 and K5 pass; **K4 (a model-level conclusion changes) fails**, and the data cannot show "no change" with adequate precision.
- **What the data show.** The evaluators disagree a lot: the oracle accepts 15.5% of outputs, reference matching accepts 4.4%, and **71.5% of the semantically valid outputs are rejected by reference matching.** That survives surface normalisation, all three renderings and all three mechanism families, and cheap proxies do not reproduce the oracle.
- **What the data do not show.** No model ranking changed (Kendall τ = 1.0), no pairwise comparison changed significance in a stable way, and the reference-based evaluator is *mostly right* about what is wrong: only 11.6% of the outputs it calls wrong are actually valid. The evaluator changes the **size** of measured gaps (it roughly doubles the qwen3:8b lead over llama3.1:8b and mistral:7b), not their **direction**.
- **Why the pilot is limited.** Four 7–9B models solve only 15.5% of the worlds, so most error is genuine invalidity that both evaluators catch. Reference matching can only matter in the thin valid slice (179 of 1,152 outputs).

## 2. Audit: which artifacts exist, and which are valid for this experiment

| Artifact | Status | Reason |
|---|---|---|
| MGEV prototype (`docs/PAPER_DRAFT.md`, `docs/archive/`) | **Invalid, not used** | Hard-coded and synthetic evaluation; archived by the earlier audit. |
| AGY RSG project (`research/archive_agy/`, `docs/FINAL_RESEARCH_DECISION.md`, `docs/PREREGISTRATION.md`) | **Invalid, not used** | No LLM was run; the oracle rejected every trace (reported RSG −0.94, not +0.94); "FCFS" was preemptive; 38/50 "invalid" traces were valid. |
| `rsg-audit` v2 (`research/simulator/*`, `research/benchmark/benchmark_v2.json`, `research/evaluation/*`) | **Valid code, wrong experiment** | It judges VALID/INVALID *given a reference*. Its R1/R2/R3 are defined relative to a reference, and its concurrency splits fail their own leakage audit (D2/D3). Code reused; dataset **not** reused. The RSG Phase B remains pending and untouched. |
| `research/ssr_bench/` | **Not in this repo** | It lives in `/home/adhyan/Desktop/StoryTrace` (a story-state benchmark; untracked there). Not reused. |

**Reused unchanged:** `research/simulator/{traces,cpu_scheduler,concurrency_interleaver}.py` and `research/evaluation/metrics.py`. **Reused with one fix:** `research/simulator/validators.py` (see D3a). Old results in `research/results/` and `research/tables/` are not overwritten.

**Hard-coded, synthetic or reference-dependent elements of the *new* design, stated up front:**
- The reference R is **defined by the world's own order** (listed order, arrivals before requeued, lowest-index thread or safe process) among task-valid traces. The prompt does **not** state this convention; it says any valid trace is accepted. Rejecting a valid non-canonical trace is therefore an error *relative to the stated rules*, but a real course may state its tie-break (§8).
- Worlds are synthetic specs from seeded generators (plus textbook cases), not exam questions.

## 3. Design

**Worlds (24; the statistical unit).** 8 scheduling (FCFS, SJF, Priority, RR; non-preemptive except RR; ties and the RR requeue ambiguity), 8 synchronisation (mutex, semaphore), 8 Banker's safe sequences. Every second world carries one task constraint that excludes part of the rule-valid set (found by search, so it bites). Textbook cases: `sched_01` (P1=24, P2=3, P3=3, FCFS), `sched_07` (same, RR q=4), `sync_01` (3 threads, 1 mutex), `bank_01` (Silberschatz 5-process example).

| world | structure | size | \|V_rules\| | \|V_task\| | constraint | matched valid/invalid pairs |
|---|---|---|---|---|---|---|
| sched_01 (textbook) | fcfs | 3 | 6 | 6 | — | 5 |
| sched_02 | fcfs | 4 | 6 | 3 | precedence | 2 |
| sched_03 | sjf | 5 | 6 | 6 | — | 5 |
| sched_04 | sjf | 5 | 4 | 2 | precedence | 1 |
| sched_05 | priority | 5 | 4 | 4 | — | 3 |
| sched_06 | priority | 4 | 6 | 2 | deadline | 1 |
| sched_07 (textbook) | rr | 3 | 6 | 6 | — | 5 |
| sched_08 | rr | 4 | 12 | 6 | precedence | 5 |
| sync_01 (textbook) | mutex | 3 | 6 | 6 | — | 5 |
| sync_02 | mutex | 3 | 210 | 114 | before | 20 |
| sync_03 | mutex | 3 | 168 | 168 | — | 20 |
| sync_04 | mutex | 2 | 5 | 4 | before | 3 |
| sync_05 | semaphore | 3 | 18 | 18 | — | 17 |
| sync_06 | semaphore | 3 | 384 | 192 | before | 20 |
| sync_07 | semaphore | 3 | 5 | 5 | — | 4 |
| sync_08 | semaphore | 3 | 384 | 192 | before | 20 |
| bank_01 (textbook) | banker | 5 | 16 | 16 | — | 15 |
| bank_02 | banker | 6 | 48 | 12 | before | 11 |
| bank_03 | banker | 5 | 48 | 48 | — | 47 |
| bank_04 | banker | 5 | 6 | 3 | before | 2 |
| bank_05 | banker | 6 | 90 | 90 | — | 20 |
| bank_06 | banker | 5 | 4 | 2 | before | 1 |
| bank_07 | banker | 6 | 54 | 54 | — | 53 |
| bank_08 | banker | 5 | 24 | 12 | before | 11 |

**Traces derived from the semantics, never by perturbing the reference.**
- **Reference:** the first task-valid trace in canonical enumeration order.
- **Valid alternatives:** the rest of the task-valid set, enumerated.
- **Invalid:** sampled from the same transition system with **one rule relaxed** (e.g. ignore arrival, drop mutual exclusion, skip `need ≤ work`) and kept only if the oracle rejects them; plus rule-valid traces that violate the task constraint.

**Oracle (`research/ssr_pilot/oracle.py`).** `evaluate_candidate(world, raw_text, truncated)` has no reference argument. TRUE only after a full replay satisfying rules and constraints; FALSE only with a named witness; UNVERIFIABLE when validity cannot be established (nothing parseable, entities outside the world, truncated with no visible violation). Observational equivalence and reference match come from a separate function that takes the reference. Scheduling and sync replay delegate to the independently written `validators.py`; Banker's replay is new.

**Evaluators.** A_strict (whitespace-collapsed string match to R), A_norm (parsed, normalised trajectory equals R), B (oracle says TRUE; UNVERIFIABLE counts as not valid), C (B and outcome-equivalent to R's outcome).

**Surface variants (matched renderings of the same world, never independent observations).** v0 plain; v1 renamed entities and paraphrased narration; v2 rows/threads listed in reverse, rules after the data, table output.

**Models and settings.** qwen3:8b (think off), llama3.1:8b, gemma2:9b, mistral:7b-instruct (four families, local Ollama). Temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600, seeds 0–3. 24 worlds × 3 variants × 4 seeds × 4 models = **1,152 generations**, all complete. Mean distinct raw responses across the 4 seeds of one (model, world, variant): 3.1, so seeds add some diversity but are not independent observations.

## 4. Integrity of the benchmark and oracle

- **Oracle tests (309 tests, all passing, including the earlier RSG suite).**
  - The verdict is unchanged when a reference field is added, removed or scrambled.
  - The oracle agrees with exhaustive enumeration on every world, with the `Scheduler` / `Interleaver` membership tests, and with an independently formulated brute-force safe-sequence search for Banker's.
  - Textbook cases are pinned, and UNVERIFIABLE is never reported as FALSE.
  - Every stored trace round-trips through format → parse → oracle in all three variants, and no prompt contains its world's reference.
- **Hand audit (3 worlds per family, recomputed by hand against the textbook rules):** `sched_04, 06, 08`, `sync_02, 04, 06`, `bank_04, 06, 08`. All references, alternatives, invalid traces and constraint violations are correct.
- **K0 failed first.** On the first bank, distance-to-reference alone separated valid alternatives from invalid traces (0.663 [0.616, 0.711], above the 0.65 limit), because invalid traces sat farther from R. Per the pre-registration the bank was redesigned before any LLM spend, **not** the threshold: each valid alternative is paired with the unused invalid trace of closest similarity profile to R (deviation D1). K0 now passes:

| classifier / protocol | accuracy [95% CI] | pass |
|---|---|---|
| length_counts / grouped_cv | 0.503 [0.500, 0.513] | pass |
| length_counts / loso | 0.500 [0.500, 0.500] | pass |
| char_ngrams / grouped_cv | 0.520 [0.482, 0.565] | pass |
| char_ngrams / loso | 0.495 [0.476, 0.511] | pass |
| listing_order / grouped_cv | 0.528 [0.471, 0.589] | pass |
| listing_order / loso | 0.468 [0.428, 0.507] | pass |
| distance_to_R / grouped_cv | 0.563 [0.524, 0.599] | pass |
| distance_to_R / loso | 0.547 [0.507, 0.585] | pass |

  592 rows (296 valid / 296 invalid pairs). A modest residual remains for distance-to-R (0.563 grouped CV); matching also means the invalid traces are harder than unmatched ones. The classifiers see only the bank, not model outputs; with 24 worlds the CIs are wide.
- **Dry-run identities (attackers scored by the full stack):**

| attacker | B | A_norm | A_strict | C | FRR_norm | random-valid floor | final-state-only accepts |
|---|---|---|---|---|---|---|---|
| always_reference | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.831 | 1.000 |
| random_valid | 1.000 | 0.149 | 0.149 | 0.635 | 0.851 | 0.831 | 0.635 |
| symbolic_alt (perfect solver, other tie-break) | 1.000 | 0.000 | 0.000 | 0.417 | 1.000 | 0.831 | 0.417 |
| random_invalid | 0.000 | 0.000 | 0.000 | 0.000 | — | — | 0.542 |

  A solver that is correct on every world scores **zero** under reference matching. The "random-valid floor" 1 − E[1/|V|] = 0.83 is the disagreement that is purely mechanical (what a model would show if it chose uniformly among valid traces).

## 5. Results (1,152 outputs; world-clustered 95% CIs; UNVERIFIABLE counts as not valid)

### 5.1 Per model

| model | B semantic | A_norm | A_strict | C | FRR_norm | FRR_strict | floor | UNVERIF |
|---|---|---|---|---|---|---|---|---|
| gemma2:9b | 0.170 [0.080, 0.281] | 0.024 [0.000, 0.073] | 0.010 [0.000, 0.031] | 0.125 [0.038, 0.233] | 0.857 [0.611, 1.000] | 0.939 [0.833, 1.000] | 0.900 | 0.045 |
| llama3.1:8b | 0.066 [0.035, 0.104] | 0.003 [0.000, 0.010] | 0.003 [0.000, 0.010] | 0.052 [0.024, 0.083] | 0.947 [0.800, 1.000] | 0.947 [0.800, 1.000] | 0.926 | 0.104 |
| mistral:7b-instruct | 0.076 [0.031, 0.132] | 0.017 [0.000, 0.042] | 0.007 [0.000, 0.017] | 0.066 [0.021, 0.118] | 0.773 [0.429, 0.971] | 0.909 [0.714, 1.000] | 0.939 | 0.194 |
| qwen3:8b | 0.309 [0.181, 0.441] | 0.132 [0.049, 0.229] | 0.090 [0.028, 0.160] | 0.219 [0.108, 0.340] | 0.573 [0.348, 0.807] | 0.708 [0.535, 0.882] | 0.866 | 0.049 |
| **pooled** | 0.155 [0.102, 0.215] | 0.044 [0.016, 0.078] | 0.028 [0.010, 0.049] | 0.115 [0.065, 0.174] | **0.715 [0.511, 0.891]** | 0.821 [0.684, 0.928] | | 0.098 |

- **Semantic-validity rate** (B) is 15.5% (179 of 1,152 outputs); reference matching (A_norm) sees 4.4%: a factor of about 3.5.
- **Disagreement A_norm vs B** = 0.111 of all outputs, and **all of it is false rejection** (B accepts, A rejects). The false-acceptance rate of reference matching is 0, as it must be (R is valid).
- **Formatting explains little:** FRR is 0.821 under strict string match and 0.715 after normalisation, so about 10 points of strict rejection are formatting; the remaining 0.715 is trajectory.
- **FRR against the floor.** Per model FRR is below the random-valid floor for qwen3 (0.573 vs 0.866) and mistral (0.773 vs 0.939), and close to it for gemma2 and llama. Only qwen3 shows a visible preference for the canonical order; for the others, which valid trace they happen to emit looks near chance.
- **Sensitivity (UNVERIFIABLE counted as valid):** pooled B rises to 0.253 [0.172, 0.346]; FRR_norm is 0.808 [0.688, 0.923]. K1 holds under either convention.
- **UNVERIFIABLE rate 9.8%** (mistral 19.4%: 35 unknown-entity, 21 unparseable; llama 10.4%).

### 5.2 By mechanism family, by variant

| group | B | A_norm | disagreement | FRR_norm [95% CI] | n valid outputs |
|---|---|---|---|---|---|
| Banker's | 0.169 | 0.008 | 0.161 | 0.954 [0.800, 0.991] | 65 |
| Scheduling | 0.062 | 0.036 | 0.026 | 0.417 [0.167, 0.750] | **24 (qwen3 only)** |
| Synchronisation | 0.234 | 0.089 | 0.146 | 0.622 [0.300, 0.914] | 90 |
| v0 plain | 0.133 | 0.042 | 0.091 | 0.686 [0.395, 0.930] | |
| v1 renamed + paraphrase | 0.109 | 0.036 | 0.073 | 0.667 [0.345, 0.921] | |
| v2 reordered + table | 0.224 | 0.055 | 0.169 | 0.756 [0.524, 0.956] | |

- **Scheduling is thin.** gemma2, llama3.1 and mistral produced **zero** valid scheduling traces (typical failures: two processes on the CPU at once, idling while a process is ready). I read the raw outputs to rule out a parser fault; these are genuine failures. The scheduling FRR rests on 24 outputs from one model.
- **The v2 rendering raises both validity (0.224 vs 0.133) and disagreement (0.169 vs 0.091).** A plausible reading, not tested here, is that with rows listed in reverse some models emit a trace that follows the *listed* order, while R follows the *world's* order, so reference matching calls a valid answer wrong. The one case I inspected supports it (`sched_01`, qwen3: P3, P2, P1 is valid but not R). The table output format is a second difference between v2 and v0, so the two effects are confounded.
- **Descriptive quality example (n = 24 valid scheduling outputs, one model, dominated by the textbook P1=24 world).** Average waiting time is 3.1 for valid non-canonical outputs versus 11.2 for valid canonical ones: matching the canonical trace there rewarded the *worse* schedule. This is not a tested claim.

### 5.3 Cheap proxies versus the oracle (K3)

| proxy | balanced agreement [95% CI] | accepts when oracle rejects | accepts when oracle accepts |
|---|---|---|---|
| distance to R (threshold fitted on other families' oracle verdicts) | 0.703 [0.613, 0.797] | 0.131 | 0.536 |
| final-state-only | 0.643 [0.526, 0.748] | 0.457 | 0.743 |

Neither proxy reproduces the oracle (both ≪ 0.95). The final-state-only proxy accepts 45.7% of the outputs the oracle rejects (it is blind to order); the distance proxy rejects 46% of valid ones.

### 5.4 Do conclusions change? (K4; 4 models, 6 pairs, 24 worlds)

| pair | Δ A_norm | Δ B | p(A), Holm | p(B), Holm | reversed | stab | sig. changes | stab | evaluator effect on the gap [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| gemma2 − llama3.1 | +0.021 | +0.104 | 1 | 0.196 | no | 0.66 | no | 0.40 | [−0.163, −0.014] |
| gemma2 − mistral | +0.007 | +0.094 | 1 | 0.196 | no | 0.57 | no | 0.48 | [−0.175, −0.019] |
| gemma2 − qwen3 | −0.108 | −0.139 | 0.078 | 0.196 | no | 0.99 | no | 0.07 | [−0.052, +0.122] |
| llama3.1 − mistral | −0.014 | −0.010 | 1 | 0.795 | no | 0.57 | no | 0.86 | [−0.049, +0.040] |
| llama3.1 − qwen3 | −0.128 | −0.243 | 0.078 | 0.014 | no | 1.00 | **yes** | 0.10 | [+0.024, +0.212] |
| mistral − qwen3 | −0.115 | −0.233 | 0.078 | 0.017 | no | 1.00 | **yes** | 0.13 | [+0.024, +0.215] |

- **(i) Ranking reversal: none.** Both evaluators give qwen3 > gemma2 > mistral > llama3.1 (Kendall τ = 1.0; P(τ<1) = 0.71 under bootstrap).
- **(ii) Significance change: observed but not stable.** For qwen3 vs llama3.1 and vs mistral, the difference is significant under the oracle (Holm p = 0.014, 0.017) and not under reference matching (p = 0.078), but this does not reproduce in ≥ 70% of world bootstraps (stability 0.10, 0.13). The two p-values sit on either side of a Holm threshold; the *difference* between them is not itself shown to be real.
- **(iii) Failure-profile shift: none.** Among the outputs reference matching calls wrong, only 6–20% are semantically valid (pooled 11.6%); no model has a majority.
- **What does change is the magnitude.** For four of six pairs the CI of the evaluator effect on the gap excludes zero: the oracle roughly doubles qwen3's lead over llama3.1 and mistral (0.128 → 0.243; 0.115 → 0.233). Under A_norm all models are compressed near zero (a floor effect), so the oracle gives a wider scale. The direction never changes.
- **Adequate precision of "no change" is not met** (the evaluator-effect CI exceeds ±0.05 for 5 of 6 pairs), so K4 is *failed but inconclusive*, not *failed with precision*. The CIs have a half-width of about 0.08; reaching ±0.05 with the same per-world variance needs roughly 65 worlds.

### 5.5 Failure taxonomy (what reference matching cannot see)

Reference matching has a single "wrong" category. The oracle separates distinct profiles (share of all outputs):

| model | valid canonical | valid non-canonical | dominant failure types |
|---|---|---|---|
| qwen3:8b | 0.132 | 0.177 | need_exceeds_work 0.260, policy_violation 0.139, queue_order 0.069 |
| gemma2:9b | 0.024 | 0.146 | need_exceeds_work 0.267, overlapping_segments 0.194, mutual_exclusion 0.101 |
| llama3.1:8b | 0.003 | 0.062 | need_exceeds_work 0.278, idle_while_ready 0.156, overlapping_segments 0.108, unknown_entity 0.094 |
| mistral:7b-instruct | 0.017 | 0.059 | overlapping_segments 0.267, need_exceeds_work 0.264, unknown_entity 0.122, unparseable 0.073 |

Banker's failures dominate for every model (essentially all Banker's errors are `need_exceeds_work`: the model proposes an unsafe order). These profiles differ by model but, at this scale, they are descriptive, not a pre-registered conclusion.

## 6. Pre-registered kill criteria

| # | Test | Result | Verdict |
|---|---|---|---|
| K0 | Benchmark integrity | all classifiers CI lower bound ≤ 0.55 and point ≤ 0.65 (after bank redesign D1) | **pass** |
| K1 | Disagreement non-trivial | pooled FRR_norm 0.715 [0.511, 0.891] (≥ 0.10, lower bound > 0.05); under the UNVERIFIABLE sensitivity 0.808 | **pass** |
| K2 | Survives surface normalisation | FRR_norm per variant: 0.686 / 0.667 / 0.756, each with lower bound > 0.3 | **pass** |
| K3 | Survives attacker baselines | proxy balanced agreement 0.703 and 0.643 (< 0.95) | **pass** |
| K4 | Changes a model-level conclusion | no stable reversal, no stable significance change, no majority-wrong-are-valid | **FAIL** (inconclusive) |
| K5 | More than one mechanism family | FRR criterion met in all 3 families (Banker's, sync, scheduling) | **pass** (see caveat) |

**K5 caveat.** The scheduling estimate is 24 valid outputs from one model, and the sync estimate comes mostly from qwen3 and gemma2. K5 passes mechanically, but it is the weakest "pass".

**Mechanical verdict: CONDITIONAL** (K0–K3 pass; K4 failed without adequate precision).

## 7. Deviations and defects found, in order

- **D1 (before any LLM output).** K0 failed; bank redesigned by profile-matching invalid traces; threshold unchanged.
- **D2 (before any LLM output).** Defined the K3 proxy threshold (fitted to the oracle on other families, the strongest cheap proxy) and "adequate precision" (evaluator-effect CI within ±0.05 for every pair).
- **D3a (after the first outputs).** `validators.py` raised `ValueError` on a schedule ending with `IDLE` after all processes finished. It now returns FALSE (`idle_after_completion`), with a regression test. No earlier result is affected.
- **D3b (after the first scoring).** A_norm treated "reference + a token outside the world" as an exact match, because the parser drops out-of-world tokens. 5 of 1,152 outputs (all mistral) were affected. **Before the fix this 0.4% bug produced the only apparent ranking reversal in the data (mistral above gemma2 under A_norm) and made τ = 0.667. After the fix the rankings agree (τ = 1.0).** All K outcomes are identical before and after. Lesson: a result of the form "evaluation choice reverses a ranking" at this sample size can be created by a handful of outputs.
- **Process notes.** The smoke test of 12 qwen3 outputs became part of the final run (identical call keys). No prompt, threshold or decision rule was changed after outputs existed. The K4(ii) stability rule, as pre-registered, compares a Holm-adjusted observed decision against a raw |t| > 2 in resamples, which makes it strict for borderline Holm results; I did not change it.

## 8. Limitations and threats to validity

1. **Competence floor.** Only 15.5% of outputs are valid, and three of four models cannot do scheduling at all. The test of "does the evaluator change conclusions among models that are actually competent" has barely been run.
2. **Power.** 24 worlds and 4 models. The K4 CIs are wide; the pilot cannot show "no change" either.
3. **Unspecified convention.** The prompt does not state R's tie-break, so a large part of FRR is the models not knowing a convention nobody told them. Courses often state it. An arm that states the convention was not run; it would separate "unspecified convention" from "model copies list order".
4. **Synthetic, small worlds** (3–6 entities, |V_task| 2–192, mostly < 20). The floor 1 − 1/|V| is high for small |V|.
5. **Four 7–9B models, quantised, local, one temperature.** Nothing here speaks to frontier or reasoning models.
6. **Seeds are not independent** (mean 3.1 distinct responses per 4 seeds); the unit of analysis is the world.
7. **Residual leakage in the bank** (distance-to-R 0.563), and the matched invalid traces may be harder than natural errors.
8. **Oracle scope.** The oracle is exact for these rules, but UNVERIFIABLE outputs (9.8%) are counted as invalid; the sensitivity bound is reported.
9. **Reference definition.** R follows the world's order, and v2 reverses the listing, so part of the v2 effect is a rendering confound by design.
10. **Single-run, single-author analysis;** the K4 operationalisation was fixed before the data but is one of several reasonable choices.

## 9. What would change the decision

- **Toward GREENLIGHT:** a follow-up that (a) includes models clearing a competence floor (for example ≥ 50% semantic-valid), (b) uses ≥ 65 worlds, (c) adds a "convention stated" arm, and in which K4 passes stably.
- **Toward KILL:** the same follow-up with K4 failing *with* adequate precision (evaluator effect within ±0.05 for every pair).
- **Not recommended:** a large benchmark now. The disagreement is real but, in this pilot, it moves magnitudes and not conclusions.

## 10. Reproducibility

- **Commands**
  - `python -m research.ssr_pilot.worlds` and `python -m research.ssr_pilot.bank` build the 24 worlds and trace banks.
  - `python -m research.ssr_pilot.run_pilot --attackers` and `--models qwen3:8b,llama3.1:8b,gemma2:9b,mistral:7b-instruct` generate outputs.
  - `python -m research.ssr_pilot.analyze --tag llm` (or `--tag dry --dry`) recomputes everything from raw JSONL.
  - `pytest tests/ssr_pilot tests/research` runs the 309 tests.
- **Data and code:** worlds `research/ssr_pilot/worlds/`; banks `data/banks/`; raw outputs `runs/*.jsonl` (1,152 records) and `runs_dry/`; manifests `manifests/`; scored records and tables `results/llm/{records.jsonl,analysis.json,tables.md}`; logs `logs/`.
- **Provenance:** manifest `manifests/llm_20261002T230247.json` (git `f16448ca`, base commit before this branch's changes; worktree dirty). Hashes at launch: prereg `8db9eeaefc54303c…`, worlds index `331d41eb5117a5a1…`. The preregistration was edited after launch only by appending deviation D3 (current hash `0a2714b04126bbea…`). Settings: temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600, seeds 0–3.
- **Nothing is committed.**
