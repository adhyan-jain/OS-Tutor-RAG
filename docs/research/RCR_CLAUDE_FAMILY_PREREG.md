# RCR follow-up: Claude-family capability ladder — analysis plan (frozen before generation)

Date written: 2026-10-24, before any Claude generation was run. Internal hash-stamped freeze (the runner records this file's SHA-256 in its manifest); recommended to upload verbatim to OSF/AsPredicted before the paper is submitted. It is NOT an external registration.

## Motivation
The original four-model run was at the capability floor (valid 6.6-30.9%), so most pairs were oracle-non-separated and reversal mass was dominated by near-ties. This follow-up re-runs the identical 24-world benchmark (288 prompts per model: 24 worlds x 3 variants x 4 repeats) on stronger models to test whether the reference-matching findings hold where many pairs are well separated.

## Design (fixed)
- Models: claude-haiku-4-5, claude-sonnet-4-5, claude-haiku-5-5, claude-sonnet-5-5 via headless `claude -p`, no tools, minimal system prompt, thinking disabled (MAX_THINKING_TOKENS=0), no hooks/settings/MCP, empty working directory.
- Prompts, worlds, scorer, oracle and RCR analysis modules are the frozen originals. Nothing in them is edited.
- Deviations from the original protocol, declared now: temperature/top_p/max-tokens are not controllable through the CLI (provider defaults); "seed" is a repeat index, not a sampling seed; the CLI adds a fixed Agent-SDK preamble and the account email to the context.
- Analysis units: world (N=24). Same evaluators E1 (exact), E2 (normalized match), E3 (semantic validator).

## Hypotheses (confirmatory unless marked)
- H1 (floor). At least 3 of the 4 Claude models reach E3 validity >= 30%.
- H2 (detection loss). Among model pairs that E3 separates (world-level paired sign-flip, Holm over all pairs, alpha 0.05), uniform-reference E2 detects the E3 difference (same direction, Holm-significant) in less than 50% of 50,000 reference draws, pooled over separated pairs.
- H3 (canonical inflation). Define for model m the canonical inflation factor CIF_m = observed canonical-matching valid outputs / sum over valid outputs of 1/|V(x)|, i.e. the count expected if the model chose uniformly from V(x). Prediction: CIF_m > 1 for every model whose valid-output count is >= 20, and CIF differs between models (world-level bootstrap CI of the max-min CIF spread excludes 0).
- H4 (ranking distortion). Under the canonical reference, the E2 score ratio between the best and second-best model differs from the E3 ratio by more than a factor of 1.5 for at least one adjacent pair. A reference-vector Kendall tau_b distribution (50,000 draws) is reported as in the original paper.
- Exploratory (labeled as such): per-family breakdowns, version effects (4.5 -> 5.5), k-reference power curve.

## Decision rules
- If H1 fails, report the floor and make no reversal-in-separated-pairs claim.
- If H3 fails (CIF ~ 1 or homogeneous), canonical bias is reported as NOT supported and the paper stays a detection-loss/attenuation study.
- All results are reported whichever way they fall; no model is dropped after seeing results. Failed calls are retried and any permanent failures are reported.
