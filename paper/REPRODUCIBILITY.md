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

| File Path | Full SHA-256 Checksum |
|---|---|
| `paper/PAPER_FINAL.md` | `e5fe6e7b9ed90c3f2dd8fa2ba4908ae09c1a0df462d01fcb691172e13b7c9f1f` |
| `paper/CLAIMS_AUDIT_FINAL.md` | `b19c56b25c5f0805e55dfc6b53b6932a35da3b0af047694da0300b506e5d3213` |
| `docs/PREREGISTRATION_V2.md` | `d7b59abdb01c623fd4ed2b2f9537ca0c4ef8400d13d0ef5f036b63bfcc755bdd` |
| `docs/research/SSR_PILOT_PREREG.md` | `0a2714b04126bbea4b974abb6e4f604c01d05628b02e1bb361159ff2034c27d1` |
| `research/ssr_pilot/results/rcrc/rcr_summary.json` | `23bc59f385274447e530bdcc0fd7165bf450cc2f604852bee322780c7eaf5b71` |
| `research/ssr_pilot/results/stated_convention/REPORT.md` | `3e066a1532892939788a533e73e4659708f92b699c3a61632ff21cbc2c5eb524` |
| `research/ssr_pilot/results/competence_pilot/analysis.json` | `ca4d5b11f5b0e4c92ac0ec38e216f4c9b4260958edfbd03f259ee7abbd5794cf` |
| `research/ssr_pilot/results/adversarial/evaluator_meta_results.json` | `d486835a35d780fc45e9e1f0c02e9ebdd8387d9e98d504709dee5522c4bba284` |
| `research/ssr_pilot/runs/gemma2_9b.jsonl` | `e09be2ef399ac04902a844e119aad73af2a0640bbae7db22fade1d5bd956dd75` |
| `research/ssr_pilot/runs/llama3.1_8b.jsonl` | `38a2ac8b9c6a82dcfe4a9e6f63de6b53b5b04dc80fb7398f9d3d465fdd1d217a` |
| `research/ssr_pilot/runs/mistral_7b-instruct.jsonl` | `320267aa897fd26237a70702f28b55ccc1e34d06dcd409b9f5253c4fa3727d9a` |
| `research/ssr_pilot/runs/qwen3_8b.jsonl` | `1f00104a7c27f245270845f1a53d8d775bf02231ba31f40e3f39b6bd5b645497` |
| `research/ssr_pilot/results/competence_pilot/records.jsonl` | `92958e30514da248cef5ca440c7b21840ec12ffdabe8dfea2f110c0ba269c242` |
