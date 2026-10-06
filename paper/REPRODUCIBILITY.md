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

**Generating commit:** `de6262f74575816b08eab45d6f4c7bae0ab1b532` (branch `main`, 2026-10-06 final freeze pass recompute). The artifact hashes below reflect the current clean HEAD state.

| File Path | Full SHA-256 Checksum |
|---|---|
| `paper/PAPER_FINAL.md` | `8605db6ea2195505a703189bdf271a9672795708ab83d096ff23df3e92208d05` |
| `paper/CLAIMS_AUDIT_FINAL.md` | `2ad11694c476390abf9e868fb99f77aa703dde9ba29928905327756895d1163a` |
| `paper/claims_manifest.json` | `1239f6c7b1d113e6ac6c1130b178aca5a28111af507f2e3615d303bc6631a589` |
| `paper/NOVELTY_POSITIONING_FINAL.md` | `6db384eafd704a3a1feb9049768d76fc2c25a4bedd88553fc4fb55e76e5af8d1` |
| `docs/research/SSR_PILOT_PREREG.md` | `0a2714b04126bbea4b974abb6e4f604c01d05628b02e1bb361159ff2034c27d1` |
| `research/ssr_pilot/results/rcrc/rcr_summary.json` | `f11636309b7fc6b5ee76711b4a4204754950a3e981258ac34a955b6bf335e545` |
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
