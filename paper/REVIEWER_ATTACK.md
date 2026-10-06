# Hostile Reviewer Simulation & Decision Gate

**Manuscript:** [`paper/PAPER_FINAL.md`](paper/PAPER_FINAL.md)
**Date:** 2026-10-06 (rebuilt by Phase P forensic audit; supersedes prior version)

---

## 1. Five Hostile Expert Reviewer Attacks

#### Reviewer 1: ML/NLP Evaluation Expert

**Attack:** *"We already know single-reference exact match is bad. Prior work (References Matter, TRACE, OTAP, LogicGraph, ReRef) has shown that reference choice alters metric values. Your contribution sounds like: 'if you pick a different reference, you get a different score.' That is trivially true and has been known for years."*

**Rebuttal:**
Prior work operates at the **output-score level**: metric values shift when the reference changes (e.g., Casola et al. 2025 on summarization metrics, ReRef on radiology report style variation, ILR on prompt formatting). RCR operates at a strictly different level: **benchmark conclusion stability**. We measure whether the scientific conclusions of a benchmark — model rankings, pairwise winner decisions, statistical significance at α=0.05 — are invariant to reference choice.

Under E2 (normalized reference matching), 18.61% of reference-vector pairs produce strictly reversed pairwise winners, and oracle rank recovery is only 23.92%. A fresh targeted primary-source literature audit confirms that no prior paper in the literature measures benchmark-level conclusion non-identifiability under formal reference vector perturbation in multi-valued executable domains.

---

### Reviewer 2: Formal Methods Specialist

**Attack:** *"Your Banker's algorithm oracle is circular. The enumerator that builds V(x) and the semantic validator both use `rules_check`. You have not independently verified anything for the Banker's family — you've verified it against itself."*

**Rebuttal:**
In the final submission-freeze pass, an independent Banker semantic verifier (`validate_banker` in `research/simulator/validators.py`) was implemented and integrated into the validator module without requiring new generation runs. All 24 worlds across CPU scheduling, concurrency synchronization, and Banker's deadlock avoidance now execute through independent trace validators in `validators.py`, fully resolving the shared implementation seam.

---

### Reviewer 3: Statistics & Experimental Design Auditor

**Attack:** *"Your Kendall τ mean is 0.490, but you excluded 86 draws as 'degenerate.' Why not assign 0? And your significance stability analysis uses only 200 of 50,000 draws — 0.4% of the claimed sample. This is a cherry-picked subsample."*

**Rebuttal on degenerate draws:** The 86 excluded draws had one model with a constant score vector (τ-b's denominator is zero; the metric is genuinely undefined). Assigning 0.0 would be incorrect: the fact that one model scores zero across all 24 worlds does not imply any particular rank correlation with the canonical ranking. The correct policy is to exclude and count separately. The 0.17% exclusion rate does not materially affect τ = 0.490 (the prior value with degenerate included as 0.0 was 0.4893; the difference is 0.0008). Deviation D5 documents this explicitly.

**Rebuttal on significance subsampling:** The 200-draw significance stability analysis is a *stability check*, not the primary result. The primary claims — τ = 0.490 ± 0.355 and 18.61% reversal probability — use all 49,914 non-degenerate draws. Sign-flip permutation tests (20,000 flips each) are computationally expensive at n=50,000 scale; the 200-draw subsample measures whether significance decisions are stable. The finding ("no pair achieves significance in any of the 200 sampled reference conditions") is disclosed as deviation D6 with explicit n=200.

---

### Reviewer 4: Benchmark Methodology Reviewer

**Attack:** *"Your stated-convention arm only reduces FRR_norm from 0.715 to 0.625. That's barely anything. Also, Gemma 3 12B n_valid=42 and OLMo2 7B n_valid=6. You cannot generalize from these numbers. And why didn't you test frontier 30B+ models?"*

**Rebuttal on stated conventions:** The partial reduction (0.715 → 0.625) confirms that disclosure of tie-breaking conventions reduces but does not eliminate noncanonical outputs. 9.5% of all stated-convention outputs (110/1,152) remain valid-noncanonical. Reference-matching evaluators reject these semantically correct outputs under any reference selection — the problem is structural, not instruction-following.

**Rebuttal on small n:** n_valid = 42 (Gemma3 12B) and n_valid = 6 (OLMo2 7B) are explicitly reported with uncertainty (95% CIs). We make no pooled population claim. The competence gate (Decision C: gain −0.069 vs required ≥ 0.15) is conservative precisely because of low n. We do not claim generality to frontier models; we claim noncanonical output persistence is not eliminated at the 12B scale.

**Rebuttal on frontier models:** AirLLM feasibility was re-checked live on 2026-10-06 (see `airllm_feasibility.md`). Disk is the binding constraint: peak storage need ~83 GB vs 78 GB free. This is a real measured infrastructure limitation, not a refusal. It is disclosed in the manuscript as Limitation 5.

---

### Reviewer 5: Novelty / Editorial Reviewer

**Attack:** *"Your claim that E3 restores '100% decision stability' is a tautology. E3 is reference-independent by construction. Of course τ=1.000 under a reference-free oracle."*

**Rebuttal:** The contribution is not that E3 is reference-free (trivially true by design). The contribution is the **quantification of the cost** of using reference-dependent evaluators instead. Under E2, oracle recovery is 23.92% — meaning 76.08% of reference draws fail to recover the oracle ranking. Under E1, 97.14% fail. This is measured by comparing E1/E2 outcomes across 49,914 reference-draw distributions to the E3 ground truth. The diagnostic value: "how well does canonical-reference matching approximate reference-independent evaluation?" Answer: poorly.

The "100% decision stability" language in Section 11 was updated in this forensic pass to: "0% winner reversals and 100% oracle recovery across all sampled reference conditions (scoped to the 50,000-draw Monte Carlo distribution over the 24-world OS benchmark reported here)."

---

## 2. Paper Decision Gate

### Verdict: **GREENLIGHT / FREEZE PASS COMPLETE** (Statistical and empirical core fully sound; verifiers unified and literature verified)

**Confirmed strengths (verified by this forensic audit):**
1. τ = 0.490 ± 0.355 (n=49,914), reversal 18.61%, oracle recovery 23.92%/2.86% — independently recomputed, verified by consistency gate, traceable to frozen JSONL records
2. Statistical method (world-level sign-flip, N=24, Holm-Bonferroni) correctly implemented and evaluated over 200 sampled reference conditions
3. Stated-convention control directly refutes the "unstated tie-break" objection with 1,152 additional generations
4. All 6 deviations from preregistration explicitly documented (D1–D6 in manuscript)
5. Oracle invariance test fixed (fake loop → real reference-exercising test); placeholder valid-space test replaced with oracle roundtrip + metamorphic mutation assertions
6. Independent Banker verifier (`validate_banker` in `validators.py`) implemented and integrated cleanly
7. Primary-source literature audit completed for References Matter, ILR, OTAP, LogicGraph, TIER, PROBE, ReRef, confirming narrow novelty boundaries
8. 376/376 tests pass; claims manifest independently recomputes all headline numbers and SHA-256 digests

