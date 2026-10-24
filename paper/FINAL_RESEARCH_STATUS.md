# Final Research Status Report & Paper Decision Gate

**Repository:** OS-Tutor-RAG  
**Date:** October 2026  
**Final Decision Gate:** **SCOPED CASE STUDY — READY FOR WORKSHOP-LEVEL SUBMISSION AFTER VENUE SELECTION** (revised 2026-10-12; supersedes the 2026-10-07 "GREENLIGHT / freeze" label, which preceded the adversarial novelty and statistics audit)  
**Automated Test Suite Status:** **401 / 401 PASSED**  
**Experiment-Generating SHA:** `e2a60d30fb4acd6b6311f88ade9972f647c806ee` (post-audit revision generating SHA: `81b9c7056464aa6d4049b6645201242d18fcba78`)  
**Final Package SHA:** `a3d727a1faef49f9667d968264ee336b3ef0cd38`  

---

## Executive Summary of Completed Work

1. **Forensic Audit & Zero-Trust Verification**: Evaluated all 1,152 baseline generation records, 1,152 stated-convention control records, and 576 competence pilot records directly from raw JSONL files. Calculated 64-character SHA-256 digests for all files.
2. **50,000 Monte Carlo Reference Vector Draws**: Reimplemented reference sampling to draw $N=50,000$ independent uniform reference vectors from the Cartesian product $\prod_{k=1}^{24} V(x_k)$, keeping canonical Draw 0 strictly separate. Demonstrated Monte Carlo $\text{SE} = 0.0016$.
3. **Statistical Repair**: Replaced pseudoreplicated cell-level McNemar testing with the preregistered world-level paired sign-flip permutation test (20,000 sign flips) and Holm-Bonferroni correction across 6 model pairs (evaluated over 200 sampled reference conditions). The earlier summary "world-level variance dominates pairwise differences ($p \ge 0.05$ across all pairs)" was correct only for E1/E2 and has been **withdrawn** (see the 2026-10-12 section below).
4. **Tie-Aware Model Ranking**: Implemented primary Kendall $\tau_b$ score vector correlation using `scipy.stats.kendalltau(variant='b')`, eliminating arbitrary string tie-breaking.
5. **Reference-Distribution Sensitivity Analysis**: Evaluated 11 reference-selection distributions across 550,000 total Monte Carlo draws ($N=50,000$ draws per distribution). Proved that while increasing canonical selection bias attenuates reversal rates monotonically (Uniform: 18.22%, $p=0.50$: 11.73%, $p=0.80$: 7.67%, $p=0.95$: 2.69%, Similarity-weighted: 17.72%), pairwise ranking instability and conclusion non-identifiability persist across all realistic non-deterministic curation distributions.
6. **Exhaustive $E_3$ Reference-Invariance Verification**: Implemented exhaustive test harness asserting 100% reference independence for semantic oracle $E_3$ across all 24 benchmark worlds, 1,152 candidate model outputs, and all reference selections in $V(x)$.
7. **Stated-Convention Control**: Recomputed stated-convention arm results; proved that disclosing canonical tie-breaking rules fails to eliminate noncanonical outputs ($\text{FRR}_{\text{norm}} = 0.625$).
8. **Unpooled Competence Analysis**: Unpooled Gemma 3 12B ($n_{\text{valid}}=42$, $\text{FRR}_{\text{norm}} = 0.619$) and OLMo 2 7B ($n_{\text{valid}}=6$). Transparently reported sample sizes and avoided overclaiming frontier capability.
9. **Adversarial Meta-Evaluation**: Evaluated $E_1, E_2, E_3$ on 79 real model output contrasts. Proved $E_1/E_2$ suffer 50.0% FRR and reject 100% of noncanonical valid solutions.
10. **Independent Verifiers & Literature Audit**: Implemented standalone `validate_banker` in `research/simulator/validators.py` and conducted primary-source literature audit for References Matter, ILR, OTAP, LogicGraph, TIER, PROBE, and ReRef.
11. **Manuscript & Reproducibility Package**: Completely rebuilt `PAPER_FINAL.md`, `REPRODUCIBILITY.md`, `CLAIMS_AUDIT_FINAL.md`, `REVIEWER_ATTACK.md`, `NOVELTY_POSITIONING_FINAL.md`, and `DEAD_CODE_AND_DOCS_AUDIT.md`.
12. **Automated Consistency Gate**: Extended `tests/test_consistency_gate.py` asserting 100% agreement between manuscript numbers, JSON result artifacts, non-truncated SHA-256 hashes, sensitivity analysis monotonicity, and 50,000 draw sampling parameters. All 401 tests pass (383 original + 4 bibliography-gate + 13 extended-analysis + 1 checksum-sync test).

---

## Post-Audit Completion Pass (2026-10-12)

An adversarial novelty and statistics audit found problems that the 2026-10-07 freeze did not catch. All of the following were fixed:

1. **Bibliography.** Three arXiv identifiers resolved to unrelated papers; "References Matter" had wrong title/authors; one venue year was wrong. All references were re-verified against primary sources (`paper/references_verified.csv`); `tests/test_references_verified.py` blocks regressions. TRACE, TIER, PROBE and "Multi-Ref Code" were dropped as unverifiable or unrelated.
2. **Novelty claim.** Ranking-level instability under reference variation is established (Casola et al., 2025; Jeong et al., 2026); OTAP and LogicGraph evaluate against valid-solution sets. "First" and "genuinely new" claims were removed; the contribution is the exact-enumeration protocol plus the detection and near-tie analyses (`paper/NOVELTY_POSITIONING_FINAL.md`).
3. **Statistics.** Sign-flip inference now covers all 50,000 draws per evaluator (`research/ssr_pilot/rcr_extended_analysis.py`). Result: the reference-independent validator separates `qwen3:8b` from `llama3.1:8b` and `mistral:7b-instruct` (Holm-adjusted p = 0.013, 0.018), while reference matching misses both in ≥99.99% of draws and retains 10–18% of the true gaps (world-level bootstrap CI excludes 0 for 5 of 6 pairs).
4. **Near-ties and heterogeneity.** 86.4% of E2 reversal mass lies in pairs the oracle cannot separate; reversal is concentrated in Banker's (21.0%) and synchronization (11.6%), absent in scheduling (uninformative: three models score zero).
5. **Process disclosure.** The pilot's preregistered verdict was CONDITIONAL (K4 failed without adequate precision); its follow-up conditions (≥50%-valid models, ≥65 worlds) were not met; the RCR protocol is a post-hoc reanalysis; the preregistration is an internal hash-stamped freeze, not an external registration. All disclosed in manuscript §9–10 (deviations D5–D8).
6. **Packaging.** `bash paper/build/build.sh` regenerates Tables 3–6, the LaTeX source and a 12-page PDF from `PAPER_FINAL.md`. Hashes in `REPRODUCIBILITY.md` were re-synced.

### Genuinely open items (cannot be closed without new data or decisions)

| Item | Why it is open |
|---|---|
| Second enumerable domain | Needs new worlds, validators and ~1,000+ model generations; the per-family breakdown is a within-benchmark check only |
| Models above ~12B / ≥50% semantic validity | Disk (about 83 GB needed vs 78 GB free; `airllm_feasibility.md`) |
| ≥65 worlds | Pilot follow-up condition; requires new world generation and runs |
| Venue selection and venue-specific formatting | A decision for the authors; the LaTeX build uses a generic `article` class |
| External time-stamped registration | Only meaningful before a confirmatory follow-up is run |



## Update 2026-10-24: Claude-family follow-up
Four Claude models (haiku/sonnet 4.5 and 5.5, headless CLI, no tools, thinking off) ran the same 288 prompts each (1,152 calls, no permanent failures) under `docs/research/RCR_CLAUDE_FAMILY_PREREG.md`. Result: H1 supported (validity 73%-99%), H2 supported (E2 detects E3-separated pairs in 3.0% of draws), H3 supported (CIF 2.26-3.30; the spread test is weak by construction), H4 not supported (max distortion 1.43 < 1.5). Uniform-reference reversal 26.9%. See `paper/PAPER_FINAL.md` Section 4.8. The preregistration is internal; upload it to OSF/AsPredicted before claiming preregistration externally.
