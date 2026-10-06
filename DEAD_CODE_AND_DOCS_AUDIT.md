# Dead Code and Documentation Audit Log

**Date:** October 2026  
**Repository:** OS-Tutor-RAG  

---

## 1. Audit Overview & Rules

In accordance with Section 0 & 23 operating rules:
- **Provenance Retention**: All historical research artifacts, raw generation outputs, trace banks, and invalid experiment logs are preserved to maintain research evolution provenance.
- **Archive Classification**: Superseded AGY/RSG code, early pilot reports, and legacy manuscript drafts are categorized as `ARCHIVAL / HISTORICAL`.
- **Zero-Trust Canonical Artifacts**: Only active, independently verified, and newly recomputed artifacts are linked in the main `README.md`.

---

## 2. Itemized Inventory & Status

| Item / Path | Classification | Retained / Archived / Removed | Justification & Provenance Value |
|---|---|---|---|
| `src/`, `api/`, `frontend/` | ORIGINAL_PRODUCT | **RETAINED** | Core RAG application code. Must remain intact and unmutated. |
| `research/ssr_pilot/core/` | RESEARCH_CORE | **RETAINED** | Reference-independent oracle, validators, schema, valid-space enumeration. |
| `research/ssr_pilot/rcrc/` | RESEARCH_ANALYSIS | **RETAINED & FIXED** | Recomputed 50,000 Monte Carlo draw RCR protocol, world-level sign-flip statistics, tie-aware Kendall $\tau_b$. |
| `research/ssr_pilot/runs/*.jsonl` | RAW_DATA | **RETAINED** | Raw generation outputs for 1,152 baseline runs across 4 models, 24 worlds. |
| `research/ssr_pilot/runs_stated_convention/*.jsonl` | RAW_DATA | **RETAINED** | Raw generation outputs for 1,152 stated-convention control runs. |
| `research/ssr_pilot/results/competence_pilot/records.jsonl` | RAW_DATA | **RETAINED** | Raw generation outputs for 576 competence pilot runs (`gemma3:12b`, `olmo2:7b`). |
| `research/archive_agy/` | HISTORICAL_ARCHIVE | **ARCHIVED** | Legacy AGY prototype dataset and baseline runner. Preserved for provenance. |
| `research/evaluation/` | HISTORICAL_ARCHIVE | **ARCHIVED** | Pre-SSR pilot prompt and metric evaluation helpers. Kept for historical trace lookup. |
| `paper/PAPER_FINAL.md` | CANONICAL_MANUSCRIPT | **REBUILT** | Canonical journal manuscript rebuilt from scratch with 50k recomputed RCR data. |
| `paper/REPRODUCIBILITY.md` | CANONICAL_GUIDE | **REBUILT** | Contains non-truncated 64-character SHA-256 digests and environment specs. |
| `paper/CLAIMS_AUDIT_FINAL.md` | CANONICAL_AUDIT | **REBUILT** | Exhaustive claims matrix mapping every manuscript statement to raw JSON evidence. |
| `paper/REVIEWER_ATTACK.md` | CANONICAL_SIM | **REBUILT** | 5-reviewer simulation with hostile counter-arguments and empirical rebuttals. |
| `paper/NOVELTY_POSITIONING_FINAL.md` | CANONICAL_AUDIT | **REBUILT** | Prior art comparison against *References Matter*, *TRACE*, *OTAP*, *LogicGraph*, *TIER*. |
| `paper/PAPER_DRAFT_V1.md` | HISTORICAL_DRAFT | **ARCHIVED** | Superseded early draft. Marked as HISTORICAL. |
| `paper/CLAIMS_AUDIT_V1.md` | HISTORICAL_AUDIT | **ARCHIVED** | Superseded claims audit. Marked as HISTORICAL. |

---

## 3. Summary of Cleanup Actions

- No core product code or valid research provenance was deleted.
- Legacy draft files were updated with `SUPERSEDED / HISTORICAL` header banners.
- Top-level `README.md` was streamlined to point exclusively to current canonical artifacts.

---

## 4. Phase G/I/J/M Forensic Audit Pass Addendum (2026-10-06)

| Action | File | Finding | Resolution |
|---|---|---|---|
| FIXED | `research/ssr_pilot/core/oracle.py` | Fake invariance test: loop over `valid_references` never used `r` | Rewrote to call `compare_to_reference(world, steps, raw_text, r)` per iteration |
| FIXED | `research/ssr_pilot/core/oracle.py` | Missing `Tuple` import (Python 3.14 annotation eval) | Added to typing imports |
| ADDED | `research/ssr_pilot/core/oracle.py` | No architectural check that oracle has no reference parameter | Added `assert_oracle_has_no_reference_parameter()` |
| FIXED | `tests/ssr_pilot/test_valid_space.py` | Placeholder `pass` in test loop | Replaced with oracle roundtrip assertions + metamorphic mutation test |
| FIXED | `research/ssr_pilot/rcrc/ranking_metrics.py` | Degenerate tau: one-constant→0.0, NaN→1.0 (undocumented) | one-constant→NaN; both-constant→1.0 documented; NaN→NaN |
| ADDED | `research/ssr_pilot/rcrc/ranking_metrics.py` | No tie-aware ranking identity check | Added `rankings_are_identical_tie_aware()` |
| FIXED | `research/ssr_pilot/rcrc/analysis.py` | Oracle recovery used `tau==1.0` (wrong under ties); hardcoded n_draws | Fixed to `rankings_are_identical_tie_aware()`; fixed to use variable |
| ADDED | `research/ssr_pilot/rcrc/analysis.py` | No tracking of degenerate-draw count | Added `kendall_tau_n_valid_draws`, `kendall_tau_n_degenerate_draws`, `significance_n_sampled_draws` |
| FIXED | `research/ssr_pilot/core/provenance.py` | Missing `Optional` import; no package version or file hash capture | Fixed imports; added `_package_versions()`, `sha256_file()`, `input_files` |
| ADDED | `tests/ssr_pilot/test_rcrc_statistics.py` | Missing tests for +1 MC correction, Holm monotonicity, N=24 guard | Added 4 synthetic tests |
| REGENERATED | `research/ssr_pilot/results/rcrc/rcr_summary.json` | Stale SHA, τ=0.4893 (included degenerate), missing fields | τ=0.4901, n_valid=49914, n_degen=86, correct provenance |
| REGENERATED | `research/ssr_pilot/results/stated_convention/analysis.json` | Potentially stale | Recomputed from frozen JSONL records |
| REGENERATED | `research/ssr_pilot/results/competence_pilot/analysis.json` | Potentially stale | n_valid=48, FRR_norm=0.667, Decision C |
| UPDATED | `paper/PAPER_FINAL.md` | τ=0.489, no degenerate disclosure, overclaimed scope | τ=0.490, n=49,914, D5/D6 added, scoped conclusion |
| UPDATED | `paper/CLAIMS_AUDIT_FINAL.md` | C3 stale (0.489, N=50,000) | Updated to 0.490, N=49,914 |
| CREATED | `paper/claims_manifest.json` | No machine-readable manifest | 15 claims with JSONPaths, tolerances, SHA-256 hashes |
| UPDATED | `paper/REPRODUCIBILITY.md` | Stale SHA-256 hashes, missing commit SHA | Recomputed hashes; added generating commit `3a99f61e` |
| REBUILT | `paper/NOVELTY_POSITIONING_FINAL.md` | 26-line stub with no adversarial analysis | 12-component overlap matrix, A/B/C/D classification |
| REBUILT | `tests/test_consistency_gate.py` | Hardcoded expected values; manuscript string-matching | Rebuilt to load claims_manifest.json and recompute independently |
| UPDATED | `research/ssr_pilot/results/competence_pilot/airllm_feasibility.md` | No Phase I live re-check | Appended live re-check (2026-10-06): disk still binding, network 4× faster |
