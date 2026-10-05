# SSR conclusion-impact analysis (frozen data, no new generation)

**Date:** 2026-10-03. **Status:** uncommitted. **Code:** `research/ssr_pilot/impact_analysis.py` (+ `tests/ssr_pilot/test_impact_analysis.py`, 10 tests). **Output:** `research/ssr_pilot/results/impact_analysis/{analysis.json,definitions.txt}` (new folder; frozen result folders were not written). **Question:** does evaluating with an independent executable oracle (B) instead of canonical-reference matching (A_norm) change *model-level conclusions*?

## 0. Integrity report

| Check | Result |
|---|---|
| Branch / HEAD | `ssr-pilot`, `f16448c` (no new commits) |
| Tracked changes | 9 exploration docs deleted (earlier cleanup you requested; restore with `git checkout -- docs/`); `research/simulator/validators.py` +2 lines (the trailing-IDLE fix, D3a, with a regression test) |
| Untracked | `docs/research/`, `research/ssr_pilot/`, `tests/ssr_pilot/`, and now `docs/NOVELTY_AUDIT_V3.md` (this session's new files are listed in §9) |
| Frozen-result checksum | `7ea66402…acddf` recomputed **after** all work this session: **identical** |
| Prereg / code hashes | prereg `0a2714b0…`, oracle `e8107292…`, families `963b174b…`, render `c8142b77…`: identical to the values stamped in the run manifests |
| Stored vs recomputed numbers | 42 values (per-model B, A_norm, A_strict, C, FRR_norm for both arms, plus pooled FRR_norm) recomputed in memory from the records with `analyze.summarize` and compared with the stored `analysis.json`: **0 mismatches** (tolerance 1e-9). Original pooled FRR_norm 0.7151 [0.511, 0.891]; stated 0.625 [0.443, 0.816] |
| Preregistration | Not edited. The original no-convention verdict is CONDITIONAL (K4 failed); see §7 for how the stated arm's K4 result should be read |
| Competence closure | `REPORT.md`, `airllm_feasibility.md` and the handoff each contain "never successfully run"; a grep for "AirLLM failed / cannot work / does not work" found nothing. Decision C, no outputs, is stated |
| Processes | Two idle `ollama serve` processes (no model resident) and one **stale** bash wrapper (pid 3089310: a leftover `until ! pgrep -f …run_pilot` watcher whose own command line matches its pattern). No experiment runner, AirLLM, download, `ssr_bench` or GPU job; GPU 15 MiB / 0%; RAM ~2.8 GB available |
| Tests | `pytest tests/ssr_pilot tests/research -q`: 344 passed |

## 1. Definitions (fixed before any number was computed; sha256 `a64c01acad2d177a…44efb`)

Unit = world (24); per-world score = mean over 12 generations (3 variants × 4 seeds); evaluators B (oracle; UNVERIFIABLE counts as invalid), C, A_norm, A_strict; 95% CIs from 2,000 world bootstraps (seed 0).
1. **Weak ranking reversal** (pair): the gap has opposite non-zero signs under A_norm and B. Not called a reversal by itself.
2. **Decisive ranking reversal**: weak reversal and both CIs exclude 0.
3. **Ranking stability**: bootstrap rank-order stability, paired A_norm/B order agreement, Kendall τ with CI.
4. **Decision reversal**: "a better than b" is decided (CI excludes 0) under one evaluator and not, or oppositely, under the other.
5. **Significance change**: *nominal* if Holm-adjusted sign-flip decisions differ; *supported* if additionally the CI of the evaluator effect on the gap (d_A − d_B) excludes 0.
6. **Relative distortion**: gap ratio d_B/d_A (only when |d_A| ≥ 0.02); spread ratio.
7. **Absolute distortion**: B − A_norm and A_norm/B per model.
8. **Taxonomy distortion**: share of A_norm-"wrong" outputs that are oracle-valid; shares valid-noncanonical / invalid / UNVERIFIABLE.

The word "reversal" below means definition 2 only; "significance change" means the supported version.

## 2. Individual-output level (24 worlds × 12 gens × 4 models, per arm)

| Quantity | Original arm | Stated-convention arm |
|---|---|---|
| Pooled B (oracle-valid) | 0.155 | 0.153 |
| Pooled A_norm | 0.044 | 0.057 |
| Pooled FRR_norm = P(A_norm rejects \| B accepts) | 0.715 [0.511, 0.891] | 0.625 [0.443, 0.816] |
| **Invalid acceptance** (A_norm accepts, oracle rejects) | **0.000 for every model** | **0.000 for every model** |
| UNVERIFIABLE share of outputs | 113/1152 = 9.8% | 93/1152 = 8.1% |

Invalid acceptance is zero by construction here: the reference R is itself task-valid, so A_norm can only be wrong in one direction. This means the asymmetry is real but also **structural**, not a discovered behaviour of the evaluator.

Per model (point [95% CI], original → stated):

| Model | B | A_norm | A_strict | FRR_norm | valid outputs | valid-but-noncanonical rate | B_ub (UNVERIFIABLE valid) |
|---|---|---|---|---|---|---|---|
| gemma2:9b | 0.170 [0.080, 0.281] → 0.222 [0.111, 0.347] | 0.024 → 0.066 | 0.010 → 0.035 | 0.857 → 0.703 | 49 → 64 | 0.146 → 0.156 | 0.215 → 0.243 |
| llama3.1:8b | 0.066 [0.035, 0.104] → 0.090 [0.052, 0.132] | 0.003 → 0.003 | 0.003 → 0.000 | 0.947 → 0.962 | 19 → 26 | 0.062 → 0.087 | 0.170 → 0.170 |
| mistral:7b | 0.076 [0.031, 0.132] → 0.031 [0.007, 0.066] | 0.017 → 0.000 | 0.007 → 0.000 | 0.773 → 1.000 | 22 → 9 | 0.059 → 0.031 | 0.271 → 0.198 |
| qwen3:8b | 0.309 [0.181, 0.441] → 0.267 [0.149, 0.403] | 0.132 → 0.160 | 0.090 → 0.090 | 0.573 → 0.403 | 89 → 77 | 0.177 → 0.108 | 0.358 → 0.323 |

**Reading.** All four models are weak (pooled valid rate ≈ 15%), so FRR for llama and mistral rests on 9–26 valid outputs. UNVERIFIABLE is large for mistral (B_ub 0.27 vs B 0.076): the oracle's undecided cases are concentrated in one model and can matter for the bottom of the ranking.

## 3. Model-level results

**Point rankings are identical under A_norm and B in both arms.** Original order (best → worst): qwen3 > gemma2 > mistral > llama; stated: qwen3 > gemma2 > llama > mistral. Kendall τ(A_norm, B) = 1.0 in both arms. There are **0 weak reversals and 0 decisive reversals** among the 6 pairs in either arm (headline comparison A_norm vs B), and also none against A_strict and C.

**But rankings are statistically unstable under *both* evaluators**, so identical point ranks are weak evidence either way:

| Quantity | Original | Stated |
|---|---|---|
| P(bootstrap order = point order), A_norm / B | 0.45 / 0.61 | 0.63 / 0.76 |
| P(A_norm order = B order, same resample) | 0.32 | 0.51 |
| τ 95% CI | [0.00, 1.00] | [0.55, 1.00] |
| Only the top (qwen3) is separable | yes | yes |

The three weaker models are not reliably ordered by any evaluator with 24 worlds. For example, in the original arm the B-gap CIs for gemma|mistral ([0.000, 0.198]) and llama|mistral ([−0.062, 0.038]) include or touch 0.

**Significance (A_norm vs B, Holm, α = 0.05):**

| Arm | Pair | d_A | d_B | Holm p A / B | Evaluator effect d_A − d_B 95% CI | Label |
|---|---|---|---|---|---|---|
| Original | llama \| qwen3 | −0.128 | −0.243 | 0.078 / 0.014 | [0.028, 0.212] | **supported significance change** (B detects, A_norm does not) |
| Original | mistral \| qwen3 | −0.115 | −0.233 | 0.078 / 0.017 | [0.024, 0.215] | **supported** |
| Stated | gemma \| llama | 0.062 | 0.132 | 0.123 / 0.045 | [−0.142, −0.003] | **supported** |
| Stated | gemma \| mistral | 0.066 | 0.191 | 0.123 / 0.018 | [−0.219, −0.049] | **supported** |
| Stated | llama \| mistral | 0.003 | 0.059 | 1.000 / 0.045 | [−0.097, −0.017] | **supported** |

In all five, the **direction of the gap is the same** under both evaluators; B simply has larger gaps and so more power. No pair flips from "a significantly better" to "b significantly better". The effect is therefore *loss of resolution* by the reference-based evaluator (compressed scores near the floor), not a reversed conclusion. Spread ratio (B range / A_norm range): 1.89 (original), 1.48 (stated).

Caveats on that finding: (i) with six pairs and several nominal tests, some of these are expected by chance at α = 0.05 (the Holm correction covers the test within an evaluator, not the 5-of-12 across-evaluator comparison); (ii) the CI for the evaluator effect is for each pair separately, uncorrected; (iii) the stated arm's pairs involve the two weakest models (valid rates 0.09 and 0.03, mistral having only 9 valid outputs), where A_norm is at zero and cannot resolve anything.

**Relative distortion.** Where defined (|d_A| ≥ 0.02), B gaps are 1.1–5.0× the A_norm gaps (stated gemma|mistral 2.9, original llama|qwen3 1.9, original gemma|llama 5.0 because d_A is only 0.021). One pair is *narrower* under B (stated gemma|qwen3, ratio 0.48). The ratio is undefined for pairs with |d_A| < 0.02 (original gemma|mistral, llama|mistral; stated llama|mistral), which are exactly the floor-level pairs.

**Absolute distortion** is large: B − A_norm per model = 0.146 (gemma), 0.062 (llama), 0.059 (mistral), 0.177 (qwen3) in the original arm; A_norm / B = 0.14, 0.05, 0.22, 0.43. The reference evaluator understates every model, and understates the strongest model *least* in relative terms.

**Taxonomy distortion.** Among outputs A_norm calls wrong, the oracle-valid share is 0.15 (gemma), 0.06, 0.06, 0.20 (qwen3) in the original arm, 0.17, 0.09, 0.03, 0.13 in the stated arm. **No model reaches a majority**, i.e. for these models most "reference-wrong" outputs really are invalid. The prereg K4(iii) is false in both arms. The high FRR coexists with a *low* absolute share because 85% of outputs are simply invalid.

## 4. Robustness

**Family (8 worlds each) and variant.** Pooled τ conceals family structure:
- *Scheduling:* A_norm and B ranks identical (τ = 1.0), but FRR is the lowest (0.42) and only 24–26 valid outputs exist.
- *Banker's (original arm):* A_norm ranks are nearly flat (scores 0.00–0.03, CIs [0, 0.03]) while B differs (τ = −0.55, FRR 0.95). Four **weak** reversals appear; **none is decisive**, since B's CIs span 0 (e.g. gemma|llama: d_B = 0.073 [−0.07, 0.25]). So "reversal" is not claimed. The Banker's result is a floor effect: A_norm is ≈ 0 for every model.
- *Sync:* one weak reversal per arm, not decisive. Stated arm gemma|qwen3: d_A = −0.125 [−0.29, −0.01] (qwen better, A_norm CI excludes 0) vs d_B = +0.104 [−0.10, 0.29] (gemma better, CI spans 0). This is the **closest thing to a reversal in the data**; it is not decisive because B cannot reject equality, and it is a subgroup (8 worlds) finding found after looking at 3 families × 2 arms.
- *Variants (v0, v1, v2):* τ 0.67–0.91 between evaluators within each variant; no decisive reversal tested at variant level (≈ 24 worlds each, sub-sampled generations).

**UNVERIFIABLE handling.** Counting UNVERIFIABLE as valid (B_ub) changes the point ranking (original: ranks [3,4,2,1] vs A_norm [2,4,3,1]; stated: [2,4,3,1] vs [2,3,4,1]) with τ = 0.667 and 1 weak reversal in each arm, **none decisive**, and it shrinks the spread ratio (original 1.46; stated 0.96, so the oracle-based spread is then no larger than A_norm's). So the model-level "B > A_norm in resolution" result depends on how the ~8–10% undecided outputs are treated. This is the largest known threat to B as a gold standard.

**A_strict vs B.** Stated arm: 5 nominal and 5 supported significance changes, 0 reversals, A_strict ranks tie two models (A_strict = 0 for llama and mistral). Mostly floor effect.

**C vs B.** Outcome-equivalence (C) already removes most of the gap with B for the A_norm comparison (supported significance changes 0 in both arms against A_norm), so a *weaker* canonical-outcome check recovers most of the resolution B provides; this is a relevant control for any "oracle is needed" claim.

## 5. Proxy discrimination (does a cheap distance/final-state score reproduce B?)

| Proxy | Balanced agreement with B [95% CI] | Accepts when oracle rejects | Accepts when oracle accepts |
|---|---|---|---|
| Distance to R (threshold fitted on other families) | 0.703 [0.61, 0.80] (original); 0.704 [0.59, 0.80] (stated) | 0.13 / 0.15 | 0.54 / 0.56 |
| Final-state-only | 0.643 [0.53, 0.75]; 0.639 [0.53, 0.75] | 0.46 / 0.47 | 0.74 / 0.74 |

Both are far from the prereg's 0.95 bar, so the cheap proxies do **not** substitute for the oracle on this data. This supports the *need for an exact oracle*, not that A_norm distorts model rankings.

## 6. Convention effect (stated minus original, per model, world-clustered 95% CI)

B: gemma +0.052 [−0.003, 0.111]; llama +0.024 [−0.014, 0.063]; mistral −0.045 [−0.080, −0.014]; qwen3 −0.042 [−0.115, 0.031]. A_norm: gemma +0.042 [0.003, 0.087]; llama 0.000; mistral −0.017 [−0.042, 0.000]; qwen3 +0.028 [−0.028, 0.090]. Only mistral's B drop and gemma's A_norm rise exclude 0 (two of eight intervals, uncorrected). Stating the convention did not materially raise semantic validity and changed A_norm only marginally.

## 7. How to read the stated arm's mechanical K4 PASS

The stated-convention script reports K4 PASS (hence a mechanical GREENLIGHT) through K4(ii), significance change. Using the prereg's own stability criterion, only llama|mistral (stability 0.896) clears the 0.70 threshold (gemma|llama 0.196, gemma|mistral 0.238 do not). That one pair is two models with 26 and 9 valid outputs, where A_norm is ≈ 0. It is real information loss by A_norm, but concerns the least capable models and no ranking. The original, preregistered arm fails K4, and the stated arm was an added arm (deviation), so the project's CONDITIONAL verdict should stand; I do not recommend upgrading it. (No frozen document was edited.)

## 8. Current-state assessment

**Which of A / B / C is supported?** *Neither "a real evaluator-level problem that changes conclusions" nor "just a per-trace artifact"*; the data support an intermediate statement:

1. **Per-output**: reference matching rejects most oracle-valid outputs (FRR 0.63–0.72), and *never* accepts an invalid one. This replicates the SVAC-Concurrency observation (`NOVELTY_AUDIT_V3.md`) with a cleaner oracle, and is not new in kind.
2. **Model-level ranking**: **no reversal, weak or decisive, in the headline comparison; no decisive reversal anywhere.** Point rankings coincide in both arms.
3. **Model-level significance**: the oracle resolves more model differences than reference matching (5 supported pair-level changes, same direction), mostly among models near the floor. This is a *power/resolution* distortion, not a conclusion reversal, and depends on how UNVERIFIABLE is counted.
4. **Power:** with 4 weak models and 24 worlds the study can detect only large effects (per-world SD of gaps: 0.27 under B, 0.17 under A_norm, giving a detectable gap of about 0.15 and 0.10 respectively at 80% power for one unadjusted test; 48 worlds would give about 0.11 and 0.07). The reversal question is **inconclusive for stronger models**, not answered.

**Strength as a paper:** as it stands, a measurement paper reporting "absolute underestimation, stable ranking, resolution loss near the floor" in a setting with a near neighbour. That is a modest contribution, probably workshop or dataset-track level, not a journal paper. A stronger claim requires models capable enough to have many valid outputs and a data pattern where the reference-based ranking actually disagrees. That is unknown, and it is the experiment in `COMPETENCE_EXPERIMENT_V2.md`.

**Uncertainty stated explicitly:** the oracle's UNVERIFIABLE share (8–10%) affects the headline; 24 worlds with 8 per family limit subgroup claims; the family-level analysis involved 6 family-arm comparisons and the near-reversal in stated sync is exploratory; all four models are small local models with ~15% validity.

## 9. Files created or changed this session (all uncommitted)

`docs/NOVELTY_AUDIT_V3.md`, `docs/SSR_CONCLUSION_IMPACT_ANALYSIS.md`, `docs/COMPETENCE_EXPERIMENT_V2.md` (next), `research/ssr_pilot/impact_analysis.py`, `tests/ssr_pilot/test_impact_analysis.py`, `research/ssr_pilot/results/impact_analysis/`. Nothing in the frozen result folders, the preregistration, the original analysis or StoryTrace was modified.
