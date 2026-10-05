# Competence mini-pilot — model selection

**Date:** 2026-10-03. **Selection rule (fixed in advance):** up to three models that are materially stronger than the existing 7–9B local models; one per family; general instruction models (no reasoning-mode, no coder-specialised); chosen only by size, family and hardware feasibility, never by results.

## Environment inspected before selection
| Item | Value |
|---|---|
| GPU | NVIDIA RTX 4060 Laptop, 8,188 MiB VRAM |
| System RAM | 15,686 MB total; ~2,900 MB available when inspected (the machine is shared with other work) |
| Disk (`/home`) | 89 GB free |
| Ollama | 0.19.0; installed models: qwen3:8b, llama3.1:8b, gemma2:9b, mistral:7b (= mistral:7b-instruct), phi4-mini, olmo2:7b, qwen2.5:7b, qwen2.5-coder:7b, llama3:latest, llava:7b |
| GPU at inspection | **busy**: another project (`research.ssr_bench.adv.run_llm`) holds ~4.9 GB VRAM at ~45% utilisation through the same Ollama server |

**No installed model is larger than 9B**, so none satisfies "materially stronger"; all selected models must be downloaded.

## Selected models
| Model (Ollama tag) | Family | Parameters | Quantisation | Download size | Installed at selection? | Hardware feasibility |
|---|---|---|---|---|---|---|
| `gemma3:12b` | Google Gemma 3 | 12B | Q4_K_M (default) | 8.1 GB | no | Does not fit 8 GB VRAM with KV cache; needs partial CPU offload (~2–3 GB in RAM). Feasible only once the other project frees VRAM/RAM. |
| `qwen3:14b` | Alibaba Qwen 3 | 14B | Q4_K_M (default) | 9.3 GB | no | Needs ~3–4 GB in system RAM beyond VRAM; run with `think: false` so the 600-token cap is not consumed by reasoning. Feasible only once RAM frees. |
| `phi4:14b` | Microsoft Phi-4 | 14B | Q4_K_M (default) | 9.1 GB | no | Same footprint as qwen3:14b. A non-reasoning instruction model (16K context supported; 4,096 used). |

Sizes and tags were confirmed on `ollama.com/library/{qwen3,phi4,gemma3}/tags` on 2026-10-03. Total download ≈ 26.5 GB (disk is sufficient).

## Reasons for the choices
- **Three distinct families**, none a coder or reasoning variant.
- **12–14B** is the largest class that can run at all on 8 GB VRAM + 15.7 GB RAM; larger models (≥ 27B) cannot.
- **qwen3:14b** also gives a within-family scale contrast with qwen3:8b from the earlier arm.
- **Reasoning models** (deepseek-r1 distills, qwen3 with thinking) are excluded: the fixed `num_predict = 600` would truncate their chain of thought and confound competence with truncation.

## Run order (fixed in advance, smallest first)
`gemma3:12b` → `qwen3:14b` → `phi4:14b`. A time or hardware failure therefore costs the least data. The order is not changed after seeing any output.

## Expected runtime and resource concerns
- **Throughput:** partial CPU offload; estimated 15–40 s per call, so 288 calls take ~1.2–3 h per model, ~4–9 h in total. The earlier qwen3:8b run took ~7–11 s per call when partly CPU-bound.
- **RAM:** the dominant risk. A 9 GB model needs roughly (model size − usable VRAM) + KV cache + 1.5 GB headroom in RAM. The gate in `run_competence_pilot.py` waits until `MemAvailable` ≥ model size + 1.5 GB (so ~10–11 GB) and the GPU is free.
- **Shared server:** the other project uses the same Ollama server; the gate refuses to load while a foreign model is resident or a foreign process holds the GPU.
- **Download speed:** observed 0.6 MB/s at the start of the first pull; each pull may take 1–4 h. Downloads need no GPU and run first.
- **Fallbacks (only if a primary model cannot be pulled or loaded, with the exact reason recorded):** `mistral-nemo:12b` (Mistral, 12B) or `qwen2.5:14b` is not substituted automatically; any substitution would be documented before its first generation and never made after seeing results.

## Status log
- **2026-10-03.** `gemma3:12b` downloaded (8.1 GB, ~75 min at ~1.8 MB/s). `qwen3:14b` failed digest verification after 40 tries (9.28 GB partial left on disk). `phi4:14b` reached only 72 MB. The GPU gate polled 32 times (~2.7 h) and never opened: the other project held ~5.8 GB VRAM at up to 97% utilisation and only 2.8–6.2 GB RAM was free (9.6 GB required). **No competence-pilot generation ran** (`runs_competence_pilot/` is empty). The runner and the downloads were stopped on 2026-10-04; partial downloads are kept and resumable.
- **2026-10-04 (user decision).** The user reported the laptop cannot handle 12–14B models and asked to try AirLLM with a ~27–32B model instead, running a feasibility test first and stopping if the projection is not reasonable. Result in `airllm_feasibility.md`: **stopped**. The 65.5 GB fp16 checkpoint cannot be downloaded (HuggingFace CDN 0.01–0.04 MB/s, mirror 0.48 MB/s) and does not fit on disk with its layer split (~83 GB needed, 71 GB free).
- **Selection change (before any output exists):** `gemma3:12b` is demoted from primary to fallback, per the user's instruction not to use it unless nothing stronger is practical. No model replaced it. Open options are listed in `airllm_feasibility.md`.
- The decision rubric is unchanged. With no new outputs the competence gate cannot pass, which the rubric maps to **C**.
- **2026-10-04 — phase closed by the user as Decision C** (inconclusive due to model/hardware constraints). The 0.5B AirLLM smoke test was declined (it does not answer the competence question). Nothing was run: no competence-pilot generation exists. AirLLM itself was never successfully run, and its runtime and model compatibility remain untested. See `REPORT.md`. Partial downloads, `gemma3:12b` and all earlier results are kept as they were.
