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

**Experiment-Generating Commit:** `e2a60d30fb4acd6b6311f88ade9972f647c806ee` (the clean commit at which the 50,000-draw RCR Monte Carlo protocol and auxiliary analyses were executed and recorded in `research/ssr_pilot/results/rcrc/rcr_summary.json`).  
**Final Submission Package Commit:** `a3d727a1faef49f9667d968264ee336b3ef0cd38` (incorporating independent Banker solver, scholarly bibliography, and extended consistency gate). The artifact hashes below reflect the current clean repository state.

| File Path | Full SHA-256 Checksum |
|---|---|
| `paper/PAPER_FINAL.md` | `ab1a224696f404cbd60dd8935c09885e0d655efe7bdb5be70b8782f0fedac7d8` |
| `paper/CLAIMS_AUDIT_FINAL.md` | `2ad11694c476390abf9e868fb99f77aa703dde9ba29928905327756895d1163a` |
| `paper/claims_manifest.json` | `edbb9fdf9533aaa9906b9a4a02b2bb0304005da8c7e815875a33ab5217e82f57` |
| `paper/NOVELTY_POSITIONING_FINAL.md` | `6db384eafd704a3a1feb9049768d76fc2c25a4bedd88553fc4fb55e76e5af8d1` |
| `docs/research/SSR_PILOT_PREREG.md` | `0a2714b04126bbea4b974abb6e4f604c01d05628b02e1bb361159ff2034c27d1` |
| `research/ssr_pilot/results/rcrc/rcr_summary.json` | `c6824c09b78f06668eab84e4639a02a491ac9a2df7bf1dd0a3a9b365444423f7` |
| `research/ssr_pilot/results/stated_convention/analysis.json` | `f9901318ebf6aac58ee35a9a3a84b66a065f5d6b9c5bcd0a03d57a66e37a0772` |
| `research/ssr_pilot/results/stated_convention/REPORT.md` | `55373a622df56ba223688069f36242b5ec71e84b6eae1c2424efc7d0ad09a01a` |
| `research/ssr_pilot/results/competence_pilot/analysis.json` | `f06397607da4cb1a5a44a803e1b39c50dfb5b8542c6f8e77d7262b48d22867fa` |
| `research/ssr_pilot/results/competence_pilot/airllm_feasibility.md` | `60b6593c3a80e13d9495ab6677cbe15f36487a103d33e9323db1e3cf76720d98` |
| `research/ssr_pilot/results/adversarial/evaluator_meta_results.json` | `d486835a35d780fc45e9e1f0c02e9ebdd8387d9e98d504709dee5522c4bba284` |
| `research/ssr_pilot/runs/gemma2_9b.jsonl` | `e09be2ef399ac04902a844e119aad73af2a0640bbae7db22fade1d5bd956dd75` |
| `research/ssr_pilot/runs/llama3.1_8b.jsonl` | `38a2ac8b9c6a82dcfe4a9e6f63de6b53b5b04dc80fb7398f9d3d465fdd1d217a` |
| `research/ssr_pilot/runs/mistral_7b-instruct.jsonl` | `320267aa897fd26237a70702f28b55ccc1e34d06dcd409b9f5253c4fa3727d9a` |
| `research/ssr_pilot/runs/qwen3_8b.jsonl` | `1f00104a7c27f245270845f1a53d8d775bf02231ba31f40e3f39b6bd5b645497` |
| `research/ssr_pilot/results/competence_pilot/records.jsonl` | `92958e30514da248cef5ca440c7b21840ec12ffdabe8dfea2f110c0ba269c242` |
