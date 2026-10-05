# Reproducibility Guide & Artifact Checksums

This document provides exact instructions, environment specifications, random seeds, and artifact checksums to reproduce all experimental findings.

---

## 1. System & Environment Specifications

- **OS Platform**: Linux x86_64 (Kernel 7.2.4)
- **Python Version**: Python 3.14.7
- **PyTest Version**: PyTest 9.1.1
- **Random Seeds**:
  - World Generation Seed: `20261003`
  - Trace Bank Seed: `20261004`
  - Reference Sampling & RCR Bootstrap Seed: `20261005`

---

## 2. Reproduction Steps

### Step 1: Run Full PyTest Suite
```bash
PYTHONPATH=. .venv/bin/pytest tests/ssr_pilot/ tests/research/ tests/test_verifiers.py
```
*Expected Output*: 354 passed.

### Step 2: Re-run RCR Core Analysis (1,152 Baseline Generations)
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION
```
*Expected Output*: Updates `research/ssr_pilot/results/rcrc/rcr_summary.json`.

### Step 3: Re-run Stronger-Model Competence Analysis (576 Generations)
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_competence_pilot
```
*Expected Output*: Updates `research/ssr_pilot/results/competence_pilot/analysis.json`.

### Step 4: Re-run Adversarial Contrast Evaluation
```bash
PYTHONPATH=. .venv/bin/python -c "from research.ssr_pilot.adversarial.construction import build_adversarial_dataset, evaluate_evaluators_on_adversarial; evaluate_evaluators_on_adversarial(build_adversarial_dataset())"
```
*Expected Output*: Updates `research/ssr_pilot/results/adversarial/evaluator_meta_results.json`.

---

## 3. Key Artifact SHA-256 Checksums

- `research/ssr_pilot/results/rcrc/rcr_summary.json`: `a4f912c9b20e...`
- `research/ssr_pilot/results/competence_pilot/analysis.json`: `c81b37ef10d...`
- `research/ssr_pilot/results/adversarial/evaluator_meta_results.json`: `e712a4b9981...`
