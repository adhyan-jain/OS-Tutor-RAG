# SSR pilot decision

**Date:** 2026-10-03. **Evidence:** `docs/research/SSR_PILOT_REPORT.md`. **Rules:** `docs/research/SSR_PILOT_PREREG.md` (fixed before any model output).
**Question tested:** does replacing reference-trajectory matching with an independent semantic oracle materially change conclusions about LLM execution reasoning on OS mechanisms?

## What the pilot established

1. **The evaluators disagree a lot, and the disagreement is not an artifact of formatting, rendering or one mechanism.** Of the 1,152 outputs, the oracle accepts 15.5% and reference matching 4.4%. Of the outputs that are semantically valid, **71.5% [51.1%, 89.1%] are rejected by reference matching** (80.8% if unverifiable outputs are counted as valid). This holds under all three renderings (0.67–0.76) and in all three families (Banker's 0.95, synchronisation 0.62, scheduling 0.42), and strict string matching adds only about 10 points over the normalised trajectory match.
2. **Cheap proxies do not stand in for the oracle.** A distance-to-reference proxy and a final-state-only proxy agree with the oracle at 0.70 and 0.64 (balanced). The final-state-only proxy accepts 46% of the outputs the oracle rejects.
3. **The benchmark's integrity gate passed only after a repair.** The first bank leaked a canonical-path artifact (distance to the reference separated valid from invalid at 0.663); it was redesigned, with the threshold unchanged, and now passes with a small residual (0.563).
4. **The oracle is trustworthy for these rules.** It has no reference argument, agrees with exhaustive enumeration and an independent brute force, and 9 worlds (3 per family) were verified by hand.

## What the pilot did not establish

1. **No model-level conclusion changed.** Rankings are identical under both evaluators (Kendall τ = 1.0). Two qwen3 comparisons are significant under the oracle and not under reference matching, but that pattern does not hold in repeated resampling (stability 0.10 and 0.13 against a 0.70 requirement). Among the outputs reference matching calls wrong, only 11.6% are actually valid, so its error attribution is mostly right.
2. **What does change is the size of the measured gaps.** The oracle roughly doubles qwen3:8b's lead over llama3.1:8b and mistral:7b (0.128 → 0.243 and 0.115 → 0.233), because reference matching compresses every model toward zero. The direction of every difference is unchanged.
3. **"No change" is not established either.** The evaluator effect on five of six pairwise gaps has a confidence interval wider than ±0.05, so K4 failed *without* adequate precision.
4. **The only apparent ranking reversal in the first scoring came from a defect.** A scoring bug affecting 5 of 1,152 outputs (0.4%) briefly made mistral rank above gemma2 under reference matching. It is fixed, with a regression test; all K outcomes are identical before and after. At this sample size a "the evaluator reverses the ranking" finding can be manufactured by a handful of outputs.

## Why the pilot cannot settle K4

- **Competence floor.** Four 7–9B models solve only 15.5% of the worlds; three of the four produced no valid scheduling trace at all. Evaluator choice can only matter in the valid slice (179 outputs), and the scheduling result rests on 24 outputs from one model.
- **Power.** 24 worlds and 4 models; the evaluator-effect confidence intervals have a half-width of about 0.08 (roughly 65 worlds would be needed to bring it to ±0.05).
- **The reference convention was not stated in the prompt**, so part of the disagreement is models not knowing a tie-break nobody gave them. The pilot did not test a "convention stated" arm.

## Mechanical result of the pre-registered rules

| K0 | K1 | K2 | K3 | K4 | K5 |
|---|---|---|---|---|---|
| pass | pass | pass | pass | **fail (inconclusive)** | pass (thinly: scheduling rests on one model) |

K0–K3 pass and K4 fails without adequate precision, so the pre-registered decision rule gives **CONDITIONAL**. No threshold, criterion or decision rule was changed after outputs existed; three deviations (D1–D3) are recorded in the pre-registration and the report.

## Recommendation

- **Do not build a large benchmark.** The pilot shows a real, robust disagreement but not a changed conclusion, and a large build would spend most of its cost on worlds that these models cannot solve.
- **If the idea is pursued, run one targeted follow-up before any scaling**, with conditions fixed in advance:
  1. include models that clear a competence floor (for example ≥ 50% semantic-valid on each family), so that evaluator choice can matter among competent models;
  2. use at least ~65 worlds;
  3. add an arm in which the tie-break convention is stated in the prompt, to separate "unspecified convention" from genuine reference dependence;
  4. keep the K4 definitions as pre-registered, or revise them in writing beforehand.
- **Stop (KILL) if** that follow-up fails K4 with adequate precision (the evaluator effect within ±0.05 for every pair), because the disagreement would then be shown to be real but inconsequential for the conclusions it was meant to change.
- **Proceed (GREENLIGHT) only if** K0–K5 all pass in that follow-up.

CONDITIONAL
