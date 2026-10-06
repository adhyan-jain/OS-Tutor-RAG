# Hostile Reviewer Simulation & Decision Gate

**Manuscript:** [`paper/PAPER_FINAL.md`](paper/PAPER_FINAL.md)
**Date:** 2026-10-06 (rebuilt by Phase P forensic audit; supersedes prior version)

---

## 1. Five Hostile Expert Reviewer Attacks

### Reviewer 1: ML/NLP Evaluation Expert

**Attack:** *"We already know single-reference exact match is bad. Prior work (References Matter, TRACE, OTAP, LogicGraph) has shown that reference choice alters metric values. Your contribution sounds like: 'if you pick a different reference, you get a different score.' That is trivially true and has been known for years."*

**Rebuttal:**
Prior work operates at the **output-score level**: metric values shift when the reference changes. RCR operates at a strictly different level: **benchmark conclusion stability**. We measure whether the scientific conclusions of a benchmark — model rankings, pairwise winner decisions, statistical significance at α=0.05 — are invariant to reference choice.

Under E2 (normalized reference matching), 18.61% of reference-vector pairs produce strictly reversed pairwise winners, and oracle rank recovery is only 23.92%. No prior paper in the verified literature makes or measures this benchmark-level non-identifiability claim.

**Unresolved risk:** The specific papers TIER, Traxgen, PROBE, and ReRef cited in the review were not independently verified in our literature survey (see `NOVELTY_POSITIONING_FINAL.md` Section 5). If any of these measures benchmark-level ranking stability under reference variation, the novelty of C3/C4 would be weakened. This is a genuine open gap requiring targeted literature search before submission.

---

### Reviewer 2: Formal Methods Specialist

**Attack:** *"Your Banker's algorithm oracle is circular. The enumerator that builds V(x) and the semantic validator both use `rules_check`. You have not independently verified anything for the Banker's family — you've verified it against itself."*

**Rebuttal:**
This is accurate and is explicitly disclosed in the manuscript (Section 10, Limitation 2): "For the Banker's deadlock-avoidance family, the enumerator and the semantic validator share the same `rules_check` implementation." For the Banker's family, cross-validation relies on brute-force permutation enumeration rather than an independently implemented validator. The scheduling and synchronization families use a separate validator (`research/simulator/validators.py`) not shared with the enumerator, and have the stronger independence claim.

**Unresolved risk:** 8 of 24 worlds (33%) are affected. An independent Banker's verifier (e.g., direct resource-matrix simulation) would address this. Such a reimplementation was out of scope for this study without rerunning the generation campaign.

---

### Reviewer 3: Statistics & Experimental Design Auditor

**Attack:** *"Your Kendall τ mean is 0.490, but you excluded 86 draws as 'degenerate.' Why not assign 0? And your significance stability analysis uses only 200 of 50,000 draws — 0.4% of the claimed sample. This is a cherry-picked subsample."*

**Rebuttal on degenerate draws:** The 86 excluded draws had one model with a constant score vector (τ-b's denominator is zero; the metric is genuinely undefined). Assigning 0.0 would be incorrect: the fact that one model scores zero across all 24 worlds does not imply any particular rank correlation with the canonical ranking. The correct policy is to exclude and count separately. The 0.17% exclusion rate does not materially affect τ = 0.490 (the prior value with degenerate included as 0.0 was 0.4893; the difference is 0.0008). Deviation D5 documents this explicitly.

**Rebuttal on significance subsampling:** The 200-draw significance stability analysis is a *stability check*, not the primary result. The primary claims — τ = 0.490 ± 0.355 and 18.61% reversal probability — use all 49,914 non-degenerate draws. Sign-flip permutation tests (20,000 flips each) are computationally expensive at n=50,000 scale; the 200-draw subsample measures whether significance decisions are stable. The finding ("no pair achieves significance in any of the 200 sampled reference conditions") is disclosed as deviation D6 with explicit n=200.

**Unresolved risk:** A reviewer could argue that 200 draws is too small to claim strong significance-stability conclusions. The conservative framing — "no pair achieves significance in any of the 200 sampled conditions" — is the honest representation. An expanded analysis (e.g., 2,000 draws) would strengthen this claim but was not run.

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

**Unresolved risk:** Same as Reviewer 1 — novelty overlap with TIER/Traxgen/PROBE/ReRef is not fully resolved. Flagged in `NOVELTY_POSITIONING_FINAL.md`.

---

## 2. Paper Decision Gate

### Verdict: **MODIFY** (two genuine unresolved limitations; statistical and empirical core is sound)

**Confirmed strengths (verified by this forensic audit):**
1. τ = 0.490 ± 0.355 (n=49,914), reversal 18.61%, oracle recovery 23.92%/2.86% — independently recomputed, verified by consistency gate, traceable to frozen JSONL records
2. Statistical method (world-level sign-flip, N=24, Holm-Bonferroni) correctly implemented; verified by 4 new synthetic unit tests
3. Stated-convention control directly refutes the "unstated tie-break" objection with 1,152 additional generations
4. All 6 deviations from preregistration explicitly documented (D1–D6 in manuscript)
5. Oracle invariance test fixed (fake loop → real reference-exercising test); placeholder valid-space test replaced with oracle roundtrip + metamorphic mutation assertions
6. Banker circularity disclosed honestly — not concealed
7. AirLLM infeasibility documented with measured numbers (disk and network), not asserted
8. 366/366 tests pass; claims manifest independently recomputes all headline numbers

**Two genuine unresolved limitations requiring action before submission:**
1. **Novelty gap**: TIER, Traxgen, PROBE, ReRef, OTAP, LogicGraph not independently verified — targeted literature search required to rule out C3/C4 overlap
2. **Banker circularity**: enumerator and validator share `rules_check` for 8/24 worlds — an independent Banker verifier would address this, but requires implementation work

**Recommendation:** Conduct targeted literature search for the five unverified papers before submission. Implement independent Banker verifier if feasible without rerunning generation. Both limitations are disclosed; neither kills the core empirical contribution.
