# AirLLM feasibility test for a 27–32B model (competence mini-pilot)

**Date:** 2026-10-04. **Requested by the user:** use AirLLM, no 70B+ model, pick a practical ~27–32B instruction model, run a feasibility test first, and **stop and report if the projected full run is not reasonable**, rather than downloading or running a huge model.

## Decision: STOP. The planned 32B pilot was judged impractical on measured download and storage limits.

**AirLLM itself was never successfully run.** It was installed only with `--no-deps` into a throwaway environment, where `import airllm` fails with `ModuleNotFoundError: No module named 'tqdm'` (a consequence of that choice). No model was loaded and no generation completed. This document therefore does **not** show that AirLLM fails on this machine, nor that it works: it shows that the specific 288-generation, 32B plan is impractical because the weights cannot be obtained in reasonable time and would not fit on disk with their layer split. Nothing was downloaded beyond metadata and speed probes. The phase was closed as Decision C on 2026-10-04 (see `REPORT.md`).

## Criteria fixed before measuring ("reasonable")
1. **Weights obtainable:** the fp16 HuggingFace checkpoint downloads in ≤ 12 h.
2. **Disk fits:** peak disk need ≤ free space − 10 GB.
3. **Generation time:** all 288 generations finish in ≤ 12 h of wall-clock time.

## Model chosen
**Qwen/Qwen2.5-32B-Instruct** — general instruction model, Apache-2.0, not gated, 32.8B parameters, 64 layers, 17 safetensors shards, **65.5 GB** in fp16. AirLLM 4.0.0 has a dedicated Qwen2 class (`airllm_qwen2.py`) and a generic fallback for newer architectures, so the architecture is supported. Alternatives rejected: `google/gemma-3-27b-it` (gated, needs a licence click-through, 54.9 GB) and Qwen3-32B (same 65.5 GB, no dedicated AirLLM class).

## Measurements (all on this machine, 2026-10-04)
| Quantity | Measured | How |
|---|---|---|
| SSD sequential read | **3.2 GB/s** (4.2 GB in 1.3 s, cold) | `dd iflag=direct` on an 8 GB Ollama blob (bypasses the page cache) |
| HuggingFace CDN download | **0.01–0.04 MB/s**, one read timeout | HTTP Range probes (3 runs, 40–79 s) on a 3.1 GB and a 65 GB-model shard |
| hf-mirror.com | 0.48 MB/s | 25 s probe |
| ModelScope | 0.05 MB/s | 26 s probe |
| Ollama registry (for reference) | ~1–1.8 MB/s average | the earlier real pulls (gemma3:12b: 8.1 GB in ~75 min) |
| Real generation length | mean **67** output tokens (median 54, p90 142, max 600); mean prompt 337 | the 1,152 existing stated-convention outputs |
| Free disk | **71 GB** | `df` |
| Free RAM / VRAM | ~3–5 GB / ~2.4 GB | the other project holds ~5.8 GB VRAM and is running at ~97% GPU |

## Projection
**Per-token cost.** Layer-streaming reads every weight once per forward pass, and a decode step is one pass. So time per pass ≥ (bytes of weights) ÷ (SSD bandwidth): 4-bit (~17.5 GB) ≥ 5.5 s, 8-bit (~32.8 GB) ≥ 10.2 s. These are lower bounds: they ignore dequantisation, host-to-GPU copies, and compute.

**Batching amortises the passes** (one pass serves the whole batch, which runs until its longest output ends). Using the real output-length distribution:

| batch size | 4-bit, hours for 288 calls | 8-bit, hours | KV cache (GB) |
|---|---|---|---|
| 1 | 29.5 | 56.6 | 0.1 |
| 8 | 9.7 | 17.7 | 1.1 |
| 16 | **6.5** | 12.0 | 2.4 |
| 32 | 4.1 | 7.9 | 5.3 |

So **decoding speed alone does not rule it out**, provided AirLLM's batched sampling works (not tested: no weights could be obtained).

## Verdict per criterion
| Criterion | Need | Result | Pass |
|---|---|---|---|
| 1. Weights obtainable | ≤ 12 h | 65.5 GB at 0.48 MB/s (best mirror) = **38 h**; at the HuggingFace CDN speed (0.04 MB/s) = **19 days** | **fails** |
| 2. Disk | ≤ 61 GB | fp16 shards 65.5 GB + 4-bit layer split ~17.5 GB = **~83 GB** peak, against 71 GB free (88 GB even after deleting the 17 GB of partial Ollama downloads) | **fails** |
| 3. Generation time | ≤ 12 h | batched 4-bit lower bound 6.5 h (batch 16) | passes in principle, unmeasured |

Two of three criteria fail on measured numbers (download time and disk), so the planned run is **not reasonable**. The criterion that passes (generation time) rests on a projection, not a measurement, so AirLLM's actual speed remains unknown.

## What was and was not done
- **Done:** read the AirLLM 4.0.0 source (supported architectures, `compression='4bit'|'8bit'`, requirements); measured SSD, download and memory; projected runtime with real token counts.
- **Not done:** AirLLM was **not installed into the project environment**. It needs `transformers>=4.49,<6` while the project pins 4.48.0; it was unpacked with `--no-deps` into a throwaway environment for inspection only. No model weights were loaded, so AirLLM's own per-layer overhead and its batched-generation behaviour are **unmeasured**.
- **Not an option:** the fast Ollama registry serves GGUF files, and AirLLM's documentation lists HuggingFace safetensors checkpoints only (GGUF is not mentioned as supported; not tested); converting a quantised GGUF back to HuggingFace weights would change the model and was not attempted.

## Measured versus untested (explicit)
**Measured:** SSD sequential read (3.2 GB/s); download speeds from three hosts; HuggingFace model sizes; free disk, RAM and VRAM at the time; real output-token distribution (mean 67); the AirLLM 4.0.0 package metadata and file list; the exact import error above.

**Untested (nothing was run):**
1. AirLLM **runtime and tokens-per-second** on this machine. The 5.5 s/token and 6.5 h (batch 16, 4-bit) figures are disk-bound lower-bound projections.
2. AirLLM **compatibility with Qwen2.5-32B-Instruct** (a Qwen2 class exists in the source; no load was attempted).
3. **Peak VRAM/RAM** of any AirLLM run (nothing was loaded).
4. **Batched generation and sampling** (temperature/top_p) under AirLLM.
5. Whether a **working install** is possible: a dry run lists 57 packages including a CUDA 13 stack, and the project environment cannot host it (`transformers 4.48.0` is pinned, AirLLM needs ≥ 4.49); the dependency download size was not measured.

## What this leaves for the competence phase
No model materially stronger than the existing four can be run here. The only fallbacks are (a) `gemma3:12b`, already installed (the user asked not to use it unless nothing stronger is practical, and it is only slightly larger than the baseline models), (b) a hosted API model, or (c) recording the phase as not run. See `model_selection.md` (status update) and the decision rubric: with no new outputs the competence gate cannot pass, which maps to decision **C**.
