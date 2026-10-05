# Competence-filter mini-pilot — REPORT

Date: 2026-10-03. Stated-convention generation arm only; same 24 worlds, prompts, settings, oracle and statistics as the stated-convention arm. Rules: `decision_rubric.md` (frozen before any output).

## A. Purpose

The stated-convention arm kept the evaluator discrepancy high (pooled FRR_norm 0.625) but its four local models are weak (pooled semantic validity 0.153). This phase asks whether the discrepancy survives when clearly more capable models are used: *among semantically valid outputs, does a large share remain non-canonical under the stated convention?* It does not ask whether stronger models are better.

## B. Selected models

| model | family | size | installed | outputs scored | run status |
|---|---|---|---|---|---|
| gemma3:12b | Google Gemma 3 (12B) | 2.0 GB (Q4_K_M) | yes | 288 / 288 | not run |
| olmo2:7b | Allen Institute OLMo 2 (7B) | 2.0 GB (Q4_K_M) | yes | 167 / 288 | not run |

Full reasoning and hardware feasibility: `model_selection.md`.

## C. Experimental design

24 worlds × 3 surface variants (v0, v1, v2) × 4 seeds = 288 generations per model; stated-convention prompts; temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600; evaluators A_strict, A_norm, B, C unchanged; world-clustered bootstrap (2,000 resamples, seed 0). One model at a time. Baseline = the 4 local models of the stated-convention arm (recomputed; pooled FRR_norm 0.625).

## D. Resource use

GPU-gate polls that found the GPU or RAM busy: **35** (every 5 minutes; see `resource_log.md`).

| model | calls | s/call | minutes |
|---|---|---|---|
| gemma3:12b | 279 | 5.4 | 25 |

Key events:

- `2026-10-05T01:26:36` [gemma3:12b] START smoke: 9 to run, 0 cached — VRAM 15/8188 MiB, util 0%, RAM avail 5.3 GB, ollama ps -
- `2026-10-05T01:27:13` [gemma3:12b] END smoke: 9 calls, 4.1s/call, 1 min — VRAM 7259/8188 MiB, util 43%, RAM avail 2.3 GB, ollama ps ['gemma3:12b']
- `2026-10-05T01:28:05` [olmo2:7b] START smoke: 9 to run, 0 cached — VRAM 15/8188 MiB, util 0%, RAM avail 5.1 GB, ollama ps -
- `2026-10-05T01:28:28` [olmo2:7b] END smoke: 9 calls, 2.5s/call, 0 min — VRAM 6459/8188 MiB, util 95%, RAM avail 4.9 GB, ollama ps ['olmo2:7b']
- `2026-10-05T01:28:28` STATUS {"gemma3:12b": "done", "olmo2:7b": "done"} — VRAM 6459/8188 MiB, util 54%, RAM avail 4.9 GB, ollama ps ['olmo2:7b']
- `2026-10-05T01:28:39` [gemma3:12b] START full: 279 to run, 9 cached — VRAM 15/8188 MiB, util 0%, RAM avail 5.2 GB, ollama ps -
- `2026-10-05T01:53:47` [gemma3:12b] END full: 279 calls, 5.4s/call, 25 min — VRAM 7257/8188 MiB, util 53%, RAM avail 3.0 GB, ollama ps ['gemma3:12b']
- `2026-10-05T01:53:53` [olmo2:7b] START full: 279 to run, 9 cached — VRAM 15/8188 MiB, util 0%, RAM avail 5.9 GB, ollama ps -

## E. Overall validity (world-clustered 95% CI; UNVERIFIABLE counted as not valid)

| model | n | B semantic | A_norm | A_strict | C | UNVERIF |
|---|---|---|---|---|---|---|
| gemma3:12b | 288 | 0.146 [0.062, 0.240] | 0.056 [0.014, 0.108] | 0.042 [0.003, 0.087] | 0.118 [0.049, 0.208] | 0.000 |
| olmo2:7b | 167 | 0.006 [0.000, 0.018] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.287 |
| **new models pooled** | 455 | 0.095 [0.042, 0.156] | 0.035 [0.008, 0.068] | 0.026 [0.002, 0.056] | 0.075 [0.030, 0.136] | 0.105 |
| *baseline (4 local) pooled* | 1152 | 0.153 [0.095, 0.217] | 0.057 [0.022, 0.099] | 0.031 [0.011, 0.055] | 0.114 [0.060, 0.176] | 0.081 |

## F. Competence-conditioned disagreement (among semantically valid outputs)

| model | semantically valid | canonical accepted | canonical rejected | **FRR_norm** | FRR_strict | FRR_norm, UNVERIF as valid | valid-but-reference-wrong (share of all outputs) |
|---|---|---|---|---|---|---|---|
| gemma3:12b | 42 | 16 | 26 | 0.619 [0.440, 0.839] | 0.714 [0.578, 0.912] | 0.619 [0.440, 0.839] | 0.090 |
| olmo2:7b | 1 | 0 | 1 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.006 |
| **new models pooled** | 43 | 16 | 27 | **0.628 [0.462, 0.833]** | 0.721 [0.582, 0.914] | 0.824 [0.732, 0.943] | 0.059 |
| *baseline pooled* | 176 | 66 | 110 | 0.625 [0.443, 0.816] | 0.795 [0.676, 0.911] | 0.755 [0.636, 0.876] | 0.095 |

Total canonical (A_norm) outputs, new models: 16 of 455.

## G. Comparison to the stated-convention baseline

- Baseline pooled FRR_norm: **0.625 [0.443, 0.816]** (n valid 176).
- New-model pooled FRR_norm: **0.628 [0.462, 0.833]** (n valid 43).
- Competence gain (pooled B): **-0.058** (0.095 vs 0.153).
- Difference in FRR_norm (new − baseline), world-clustered: **+0.003 [-0.197, +0.205]**

All models, ordered by semantic validity (descriptive; does validity rise together with non-canonical output?):

| model | arm | B | A_norm | n valid | FRR_norm |
|---|---|---|---|---|---|
| olmo2:7b | new | 0.006 | 0.000 | 1 | 1.000 |
| mistral:7b-instruct | baseline | 0.031 | 0.000 | 9 | 1.000 |
| llama3.1:8b | baseline | 0.090 | 0.003 | 26 | 0.962 |
| gemma3:12b | new | 0.146 | 0.056 | 42 | 0.619 |
| gemma2:9b | baseline | 0.222 | 0.066 | 64 | 0.703 |
| qwen3:8b | baseline | 0.267 | 0.160 | 77 | 0.403 |

Spearman correlation between B and FRR_norm across models with ≥ 1 valid output: -0.928 (descriptive; 6 models).

**World strata (fixed in advance; see decision_rubric.md).** Stratum U is the 8 constrained worlds in which a literal reading of the stated tie-break violates the task constraint, so the prompt does not determine R there.

| stratum | arm | n outputs | n valid | B | FRR_norm |
|---|---|---|---|---|---|
| D (R is the literal reading) | new | 299 | 39 | 0.130 | 0.590 [0.417, 0.806] |
| D (R is the literal reading) | baseline | 768 | 142 | 0.185 | 0.542 [0.364, 0.738] |
| U (R underdetermined) | new | 156 | 4 | 0.026 | 1.000 [1.000, 1.000] |
| U (R underdetermined) | baseline | 384 | 34 | 0.089 | 0.971 [0.750, 1.000] |

## H. Family and variant breakdown (new models pooled; baseline alongside)

Cells with fewer than 10 valid outputs are marked *too few to interpret*.

| group | n valid (new) | B (new) | FRR_norm (new) | FRR_norm (baseline) |
|---|---|---|---|---|
| banker | 5 | 0.051 | 1.000 [1.000, 1.000] *too few to interpret* | 0.837 [0.719, 1.000] |
| scheduling | 11 | 0.057 | 0.364 [0.000, 0.571] | 0.423 [0.190, 0.789] |
| sync | 27 | 0.165 | 0.667 [0.500, 0.947] | 0.574 [0.322, 0.870] |
| v0 | 15 | 0.098 | 0.467 [0.111, 1.000] | 0.543 [0.294, 0.793] |
| v1 | 8 | 0.052 | 0.500 [0.000, 1.000] *too few to interpret* | 0.702 [0.489, 0.909] |
| v2 | 20 | 0.134 | 0.800 [0.400, 1.000] | 0.627 [0.375, 0.897] |

## I. Statistical results

All intervals are world-clustered bootstrap 95% CIs (2,000 resamples, seed 0).

Pairwise comparisons among the new models, A_norm vs B (descriptive; no competence-specific threshold):

| pair | Δ A_norm | Δ B | p(A) Holm | p(B) Holm | reversed | evaluator effect on the gap [95% CI] |
|---|---|---|---|---|---|---|
| gemma3:12b|olmo2:7b | +0.067 | +0.156 | 0.122 | 0.0287 | False | [-0.167, -0.017] |

Cheap proxies against the oracle on the new models' outputs (descriptive):

| proxy | balanced agreement [95% CI] | accepts when oracle rejects |
|---|---|---|
| distance | 0.751 [0.600, 0.873] | 0.172 |
| final_state_only | 0.665 [0.497, 0.804] | 0.461 |

## J. Limitations

- **24 worlds and at most 3 new models.** Intervals are wide; per-family and per-variant cells can have few valid outputs.
- **Local, quantised 12–14B models only** (Q4_K_M, partial CPU offload on an 8 GB GPU). Nothing here speaks to frontier or reasoning models, and `think` was off where applicable.
- **The stated convention does not determine R in 8 of the 12 constrained worlds** (stratum U): a literal reading violates the task constraint and the prompt does not say how to resolve it, so non-canonical valid output is partly expected there even from a perfect solver. Stratum D is the cleaner test.
- **Hardware constraints:** the GPU is shared with another project; runs wait for a free GPU and enough RAM (see Section D).
- The competence gate, the 0.50/0.15 survival thresholds and the strata were fixed before any output; no threshold was changed afterwards. The result describes these worlds and models only; no novelty, universality, frontier-model, or publication-readiness claim is made.

- **Incomplete or skipped models:** gemma3:12b, olmo2:7b (see Section B and `resource_log.md`).

## K. Decision

**C) INCONCLUSIVE DUE TO MODEL/POWER LIMITATIONS**

Rule application: competence gate failed (gain -0.058 vs required >= 0.15, n_valid 43 vs required >= 100).

- Competence gate: gain -0.058 (need ≥ 0.15) and n_valid 43 (need ≥ 100) → FAILED.
- Pooled FRR_norm 0.628 [0.462, 0.833] against the 0.625 baseline.

