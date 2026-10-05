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
