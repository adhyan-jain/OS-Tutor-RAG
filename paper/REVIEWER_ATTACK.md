# Hostile Reviewer Simulation & Decision Gate (revised 2026-10-12)

**Manuscript:** [`paper/PAPER_FINAL.md`](PAPER_FINAL.md)
**Supersedes** the 2026-10-06 version, whose rebuttals to Reviewers 1, 3 and 5 relied on claims that the 2026-10-12 verification pass contradicted (see "What changed" at the end).

---

## 1. Nine Hostile Reviewer Attacks

### Reviewer 1: ML/NLP Evaluation Expert — "this is known"

**Attack:** *"Reference choice changing metric values and even system rankings is established (Casola et al., 2025; Jeong et al., 2026). OTAP and LogicGraph already evaluate against sets of valid solutions. What is new?"*

**Response (concede, then narrow):** Agreed, and the manuscript says so (§1, §8): ranking-level instability under reference variation is **not** claimed as new. The contribution is methodological and scoped: because V(x) is enumerated exhaustively and a reference-independent validator exists, the *entire* reference-vector distribution and the ground-truth ranking are known exactly, which lets us measure what the human-reference studies cannot—**detection loss** (§4.4: reference matching misses the two oracle-significant differences in ≥99.99% of draws and retains 12–18% of true gaps, an exact 1/|V(x)| attenuation, §4.7) and the **location of instability** (§4.5–4.6). The novelty ratings in `NOVELTY_POSITIONING_FINAL.md` were downgraded accordingly.

### Reviewer 2: Formal Methods Specialist — "circular oracle"

**Attack:** *"The Banker's enumerator and the semantic validator may share logic; you verified the family against itself."*

**Response:** The Banker's family uses `BankerSolver` (`research/simulator/banker.py`) and an independent step-by-step `validate_banker` (`research/simulator/validators.py`), cross-validated against exhaustive brute-force permutation search for all 8 specifications. Residual risk: E3 is still a simulator, not a human gold standard (§10.4).

### Reviewer 3: Statistics & Experimental Design Auditor

**Attack 3a (previous version, now withdrawn):** *"Significance used only 200 of 50,000 draws."* → **Accepted and fixed.** Deviation 7: the sign-flip analysis now covers all 50,000 draws for each evaluator, with a cross-check of the new sampler against the legacy loop (§4.1).

**Attack 3b:** *"The earlier text said no pair is significant, but your own output shows two pairs significant under E3."* → **Accepted.** That summary was correct only for E1/E2; it is replaced by Table 3 and Deviation 7.

**Attack 3c:** *"A significant result under one evaluator and a non-significant one under another is not evidence of an evaluator effect."* → **Addressed.** §4.4 / Table 4 tests the effect on each gap directly with a world-level paired bootstrap; the interval excludes zero for 5 of 6 pairs (gap retained: 12–18% for those pairs).

**Attack 3d:** *"86 draws excluded as degenerate."* → Excluded because τ_b is undefined when exactly one vector is constant (0.17%; including them as 0.0 changes the mean by 0.0008; Deviation 5).

### Reviewer 4: Benchmark Methodology Reviewer

**Attack:** *"Stated conventions only reduced FRR from 0.715 to 0.625; Gemma n_valid=42, OLMo n_valid=6; no frontier models."* → The partial reduction shows disclosure does not eliminate noncanonical outputs (110/1,152 remain valid-noncanonical). Small n is reported with CIs and no pooled capability claim is made. Frontier models were not run (disk: ~83 GB needed vs 78 GB free, `airllm_feasibility.md`); this is Limitation 6.

### Reviewer 5: Novelty / Editorial Reviewer — "E3 is a tautology"

**Attack:** *"E3 is reference-independent by construction; τ_b = 1.000 is not a finding."* → **Conceded.** The abstract now states "removes reference dependence by construction"; the empirical content is the cost of *not* using E3, measured in §4.1–4.6.

### Reviewer 6: Curator / Distributional Assumptions Specialist

**Attack:** *"Curators pick the canonical reference with high probability; instability disappears."* → Tested (§4.3, 11 distributions × 50,000 draws): E2 reversal is 12.14% at p=0.50, 7.35% at p=0.80, 2.30% at p=0.95, and vanishes only as p→1. The adversarial row is a **single** draw (n=1) and is labeled as a point value, not a distribution.

### Reviewer 7 (new): "It is just near-ties and a floor effect"

**Attack:** *"Models solve 7–31% of tasks; E2 scores are 0.5–4%. Most pairs are statistically indistinguishable, so reversals are noise. Scheduling has zero reversals."*

**Response (largely concede):** The suspicion is correct and measured: 85.6% of E2 reversal mass is in oracle-non-separated pairs, mean reversal there is 22.1% vs 7.4% in separated pairs; scheduling's zero is uninformative because three models solve none of its worlds (§4.5, §4.6, Limitation 2). The manuscript therefore states that the headline 17.56% / 13.63% figures **must not** be read as the share of well-supported orderings that are overturned, and reframes the finding as *detection loss plus arbitrary near-tie orderings*.

### Reviewer 8 (new): Process / Preregistration Reviewer

**Attack:** *"Your own pilot returned CONDITIONAL and asked for ≥50%-valid models and ≥65 worlds. You ran neither, then redefined the study around metrics invented after seeing the data. 'Preregistered' is also overstated."*

**Response (concede):** §9 now states: the preregistration is an internal hash-stamped freeze (not externally registered; first committed with the runs); the pilot verdict was CONDITIONAL (K4 failed without adequate precision); the competence-floor and world-count conditions were **not** met; the RCR protocol and extended analyses are **post-hoc and exploratory** (Deviation 8). The paper positions itself as a scoped case study, not a confirmatory test.

### Reviewer 9 (new): Reproducibility / Process

**Attack:** *"The headline numbers in this version differ from the previous one (τ_b 0.490 → 0.618, reversal 18.61% → 17.56%, recovery 23.92% → 13.63%). Which is right, and what else could be wrong?"*

**Response:** The earlier numbers came from a bug: the RCR modules omitted the preregistered rule D3(b) that the pilot scorer applies (outputs that mention entities outside the world never count as a normalized match), so 7 `mistral:7b-instruct` outputs were counted as E2 matches. All RCR artifacts were regenerated; an independent vectorized implementation agrees with the corrected loop within Monte Carlo error; the canonical reference now reproduces the E3 ordering, consistent with the pilot report (τ = 1.0). Deviation 9 in the manuscript lists every before/after value, and the test suite pins the corrected values (the claims manifest plus a checksum-sync test). The qualitative conclusions (detection loss ≥99.99%, near-tie concentration, attenuation) are unchanged. Residual risk: any further divergence between the pilot scorer and the RCR modules would shift E2 results (Limitation 10).

---

## 2. Paper Decision Gate

### Verdict: **READY AS A SCOPED CASE STUDY / WORKSHOP-LEVEL SUBMISSION** (not a main-track confirmatory claim)

**Strengths (verified by the test suite and 44-claim manifest):**
1. Headline numbers independently recomputed from frozen JSONL records; the vectorized re-implementation agrees with the legacy loop within Monte Carlo error.
2. Detection-loss result is large, direction-consistent and computed on all 50,000 draws with an exactly reference-invariant oracle.
3. Statistical unit (world, N=24) is respected; the evaluator-effect claim is tested directly rather than inferred from a significance contrast.
4. Bibliography re-verified against primary sources; a gate test blocks mismatched identifiers.
5. All deviations (D1–D8) and the pilot's CONDITIONAL verdict are disclosed.

**Remaining weaknesses (cannot be repaired without new data):**
1. One benchmark, 24 worlds, four sub-10B models at low accuracy.
2. No second domain; the family breakdown is not independent replication.
3. Post-hoc framing relative to the preregistered pilot.

## 3. What changed vs the 2026-10-06 version

| Item | 2026-10-06 | 2026-10-12 |
|---|---|---|
| Novelty claim | "no prior paper measures benchmark-level conclusion non-identifiability" | Ranking-level instability acknowledged as known; contribution narrowed to exact-enumeration + detection analysis |
| Significance | "no pair significant; world-level variance dominates" (200 draws, evaluators pooled) | Per-evaluator, all 50,000 draws; E3 separates two pairs that E1/E2 never detect |
| Bibliography | three IDs resolving to unrelated papers; wrong titles/authors | primary-source verified; gate test added |
| E3 stability | "restores 100% decision stability" | "by construction"; cost of not using it is the finding |
| Preregistration | "preregistered" | pre-specified (internal freeze); pilot verdict CONDITIONAL disclosed |
| Verdict | GREENLIGHT / FREEZE PASS COMPLETE | Scoped case study; exploratory post-hoc analyses flagged |
