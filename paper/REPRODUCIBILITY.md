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

### Step 6: Re-run Reference-Distribution Sensitivity Analysis
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_reference_distribution_sensitivity
```
*Output*: Updates `research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.json` and `.csv`.

### Step 7: Re-run Extended Analysis (all 50,000 draws; detection, near-tie, per-family, evaluator effect)
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_extended_analysis
```
*Output*: Writes `research/ssr_pilot/results/rcrc/extended_analysis.json` (about 2.5 minutes; seeds 20261016 for reference draws, 20261017 for the shared 20,000-flip sign matrix and the 5,000-resample world bootstrap). The artifact's embedded provenance records the git SHA of the checkout it was run in; re-run it after committing so that the recorded commit contains `rcr_extended_analysis.py`.

### Step 8: Regenerate Tables 3–6 and the LaTeX/PDF Manuscript
```bash
bash paper/build/build.sh
```
*Output*: `paper/TABLES/table3_*.md` … `table6_*.md`, `paper/build/PAPER_FINAL.tex`, `paper/build/PAPER_FINAL.pdf`. Requires `latexmk` and `pdflatex`.

### Step 9: Bibliography Check
`tests/test_references_verified.py` checks that every arXiv identifier and title in the manuscript References appears in `paper/references_verified.csv` (identifiers and titles were compared with the arXiv abstract pages on 2026-10-12).

---

### Claude-family follow-up (Section 4.8)

```bash
# generation (resumable; headless claude CLI, subscription auth)
.venv/bin/python -m research.ssr_pilot.run_claude --workers 6
# preregistered analysis H1-H4 (seed 20261024; 50,000 draws; 5,000 bootstrap resamples)
.venv/bin/python -m research.ssr_pilot.rcr_claude_analysis
```
Outputs: `research/ssr_pilot/results/rcrc_claude/`. Provider-default sampling; model-version drift may change a rerun.

## 3. Complete SHA-256 Artifact Checksums

**Experiment-Generating Commit:** `e2a60d30fb4acd6b6311f88ade9972f647c806ee` (the clean commit at which the 50,000-draw RCR Monte Carlo protocol and auxiliary analyses were executed and recorded in `research/ssr_pilot/results/rcrc/rcr_summary.json`).  
**Final Submission Package Commit (previous freeze):** `a3d727a1faef49f9667d968264ee336b3ef0cd38` (independent Banker solver, bibliography, extended consistency gate). The experiment results in `rcr_summary.json`, `reference_distribution_sensitivity.json`, `stated_convention/analysis.json`, `competence_pilot/analysis.json` and `adversarial/evaluator_meta_results.json` are unchanged since that freeze.

**Post-audit revision (2026-10-12):** built on `81b9c7056464aa6d4049b6645201242d18fcba78`. It adds `extended_analysis.json` (generated from the working tree containing the then-uncommitted `rcr_extended_analysis.py`, so its embedded git SHA is the parent commit), the verified bibliography, rewritten manuscript sections 1, 4.2, 4.4–4.6, 8–11, and the LaTeX build. The manuscript, claims audit, novelty and reviewer documents, and claims manifest hashes below therefore differ from the previous freeze. The "frozen" label of the earlier package no longer applies to those files.

| File Path | Full SHA-256 Checksum |
|---|---|
| `paper/PAPER_FINAL.md` | `c11bfeb218a031e65bd3659c6f43c9d7f63e8859af0f4dc653b43b20a302e751` |
| `paper/CLAIMS_AUDIT_FINAL.md` | `5952e2f6008fb9cd4f051cde0f52ce621f23d01395b214576e4cdc1f5a4a06d5` |
| `paper/claims_manifest.json` | `11af34aefe44bba2cd2e3bc18dbae1e781a186fa193d1469526f8786abc9633a` |
| `paper/NOVELTY_POSITIONING_FINAL.md` | `d2a58b8dc4c62932da85a5de4aa305bce0804806330230b51fb365b5c249d74b` |
| `paper/REVIEWER_ATTACK.md` | `cbdd6803fb34b0f8a6dbc62d98b843f1198da12432e41e0c207943c53af2248e` |
| `paper/references_verified.csv` | `d66e886b45f32bcc198fb572293093de4630b618e39b88e347e3b16d0ac9b573` |
| `research/ssr_pilot/results/rcrc/extended_analysis.json` | `5228943a2ce011ee961a779f94615d05c4ff7f0f6d6c58f26c4792868afdcf31` |
| `docs/research/SSR_PILOT_PREREG.md` | `0a2714b04126bbea4b974abb6e4f604c01d05628b02e1bb361159ff2034c27d1` |
| `research/ssr_pilot/results/rcrc/rcr_summary.json` | `956ebd4b86fdbf1764205d19f96dfd16be692b3af1eddf9b779ed8fbd093641b` |
| `research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.json` | `607393fe070b404ad24c3a3820843c7bfd6b6d2bb0fffdc81b6193f50990862c` |
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
| `docs/research/RCR_CLAUDE_FAMILY_PREREG.md` | `8d61178e12fe2749da3e2b2ef4f16cd914fd363c26e79570dc0eecae9980f9ce` |
| `research/ssr_pilot/results/rcrc_claude/hypotheses.json` | `64fa18b103573827e79d3fc9e2ac3e8f0f3cb10c7ad71e7cde83e2bdf856af18` |
| `research/ssr_pilot/results/rcrc_claude/extended_analysis.json` | `1b127acdbb27b7ec190ac082cac2337d7d44e461ea2602d57777c7e15a866671` |
| `research/ssr_pilot/results/rcrc_claude/kref_attenuation.json` | `07c3b0380ebecd2d27cb160252bfb2c146a45a788046f2017486b2d040fcad7c` |
| `research/ssr_pilot/runs_claude/claude-haiku-4-5.jsonl` | `9c4d80d3ec6359f95414f743e98c381ab749a60c7f2c68f514ebeec09ee6980a` |
| `research/ssr_pilot/runs_claude/claude-haiku-5-5.jsonl` | `2cb15a6f3324d069339673d8c41e74596e48bd7b30b3d59a4a4c7d33347f1c1e` |
| `research/ssr_pilot/runs_claude/claude-sonnet-4-5.jsonl` | `cded81739dc8f4a9e5f2f29f7343be57e2edc3f433bd8fe70f06f88a3c593025` |
| `research/ssr_pilot/runs_claude/claude-sonnet-5-5.jsonl` | `021fa53424d401f8a29840b3516f2fb6ad0b029ad6bf57eb0c6c5d88eff97076` |