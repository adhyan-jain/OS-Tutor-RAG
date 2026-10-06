# Reproducibility Guide & Artifact Checksums

This document provides exact environment specifications, random seeds, execution commands, and complete 64-character SHA-256 digests to reproduce all experimental findings.

---

## 1. System & Environment Specifications

- **OS Platform**: Linux x86_64 (Kernel 7.2.4)
- **Python Version**: Python 3.14.7
- **PyTest Version**: PyTest 9.1.1
- **Random Seeds**:
  - World Generation Seed: `20261003`
  - Trace Bank Seed: `20261004`
  - Reference Sampling & 50k RCR Monte Carlo Seed: `20261005`

---

## 2. Reproduction Commands

### Step 1: Run Full PyTest Suite & Consistency Gate
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

### Step 2: Re-run RCR Protocol (50,000 Monte Carlo Reference Vector Draws)
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION
```
*Output*: Updates `research/ssr_pilot/results/rcrc/rcr_summary.json`.

### Step 3: Re-run Stated-Convention Control Analysis
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_stated_convention
```
*Output*: Updates `research/ssr_pilot/results/stated_convention/REPORT.md`.

### Step 4: Re-run Competence Pilot Analysis (Gemma 3 12B & OLMo 2 7B)
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_competence_pilot
```
*Output*: Updates `research/ssr_pilot/results/competence_pilot/analysis.json`.

### Step 5: Re-run Adversarial Meta-Evaluation
```bash
PYTHONPATH=. .venv/bin/python -c "from research.ssr_pilot.adversarial.construction import build_adversarial_dataset, evaluate_evaluators_on_adversarial; evaluate_evaluators_on_adversarial(build_adversarial_dataset())"
```
*Output*: Updates `research/ssr_pilot/results/adversarial/evaluator_meta_results.json`.

---

## 3. Complete SHA-256 Artifact Checksums

**Generating commit:** `3a99f61e4d308b6d5d021afc853ea2cf4b6cb156` (branch `main`, 2026-10-06 forensic audit recompute). The prior session's hashes for `rcr_summary.json`, `CLAIMS_AUDIT_FINAL.md`, `PAPER_FINAL.md`, and `competence_pilot/analysis.json` are replaced below with recomputed values.

| File Path | Full SHA-256 Checksum |
|---|---|
| `paper/PAPER_FINAL.md` | `480c22a6c8b1d76770434fcfbc86d6f6235c0abc0d8b220683f6e1c8f5aa99b5` |
| `paper/CLAIMS_AUDIT_FINAL.md` | `8a3e4bfc6b3bc3c5ac25ca668f3237f6710470b33863546f53884ea0eafa4b30` |
| `paper/claims_manifest.json` | `b3ca7660ffb9b1459a19a802d848437fb5c56605126ca589d4ec4630d0197ae6` |
| `paper/NOVELTY_POSITIONING_FINAL.md` | `d7ef5d89b7ed16a8bbb1f741f78aa17ebbd4647acdf22f93e7320015dbe7f00c` |
| `docs/research/SSR_PILOT_PREREG.md` | `0a2714b04126bbea4b974abb6e4f604c01d05628b02e1bb361159ff2034c27d1` |
| `research/ssr_pilot/results/rcrc/rcr_summary.json` | `54574db93fc819c0d2d57976b68f068b53733063e30b82b0196d24d2db2dba1d` |
| `research/ssr_pilot/results/stated_convention/analysis.json` | `9859f64bf1de436842a8ad3e3c8a9a341e86b459971cc47ee5d8ca2e458354e6` |
| `research/ssr_pilot/results/stated_convention/REPORT.md` | `3792bf8bb225bffc81a0bad8010a8fc031faca120bac4dab673c5ec42cb04e27` |
| `research/ssr_pilot/results/competence_pilot/analysis.json` | `529eb507e34f03f47896aaa54931a23cb70b5240d72f56d8c7606747b7c4b6b2` |
| `research/ssr_pilot/results/competence_pilot/airllm_feasibility.md` | `60b6593c3a80e13d9495ab6677cbe15f36487a103d33e9323db1e3cf76720d98` |
| `research/ssr_pilot/results/adversarial/evaluator_meta_results.json` | `d486835a35d780fc45e9e1f0c02e9ebdd8387d9e98d504709dee5522c4bba284` |
| `research/ssr_pilot/runs/gemma2_9b.jsonl` | `e09be2ef399ac04902a844e119aad73af2a0640bbae7db22fade1d5bd956dd75` |
| `research/ssr_pilot/runs/llama3.1_8b.jsonl` | `38a2ac8b9c6a82dcfe4a9e6f63de6b53b5b04dc80fb7398f9d3d465fdd1d217a` |
| `research/ssr_pilot/runs/mistral_7b-instruct.jsonl` | `320267aa897fd26237a70702f28b55ccc1e34d06dcd409b9f5253c4fa3727d9a` |
| `research/ssr_pilot/runs/qwen3_8b.jsonl` | `1f00104a7c27f245270845f1a53d8d775bf02231ba31f40e3f39b6bd5b645497` |
| `research/ssr_pilot/results/competence_pilot/records.jsonl` | `92958e30514da248cef5ca440c7b21840ec12ffdabe8dfea2f110c0ba269c242` |
