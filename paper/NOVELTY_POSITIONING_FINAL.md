# Novelty Positioning — Verified Prior-Art Audit (revised 2026-10-12)

**What changed.** The previous revision rated five components "A, genuinely new" and relied on papers whose identifiers did not resolve to the cited works (TRACE, OTAP, LogicGraph) or that were unrelated padding (TIER, PROBE). Every work below was re-checked against its primary arXiv page on 2026-10-12 (`paper/references_verified.csv`). Ratings are based on abstracts plus the full-read notes in `research/closest_prior_art_verified.csv` for MechSim, FAX and Falsification-Based Verification; they were **not** re-derived from full texts for the other works, and the search was not exhaustive.

**Dropped from the previous audit.** TRACE (cited ID belongs to an unrelated paper; no matching paper found), TIER (no matching paper found), PROBE (a proactive-agent benchmark, unrelated to reference choice), "Multi-Ref Code" (could not be traced to a specific paper).

---

## 0. RCR 12-Component Decomposition

| ID | Component |
|---|---|
| C1 | Multi-valid-reference awareness |
| C2 | Formal exhaustive enumeration of V(x) |
| C3 | Reference identity as an experimental variable |
| C4 | Benchmark-level conclusion stability (rankings, significance) |
| C5 | Kendall τ_b distribution over reference-vector draws |
| C6 | Pairwise winner-reversal probability |
| C7 | Significance-decision stability / detection analysis |
| C8 | Reference-independent semantic verifier (E3) |
| C9 | Oracle recovery rate |
| C10 | Monte Carlo sampling from ∏ V(x_k) |
| C11 | World-level sign-flip permutation test |
| C12 | OS state machines as the executable domain |

## 1. Closest Verified Works

| Work (verified) | What it does | Overlap with RCR |
|---|---|---|
| **Casola et al., 2025** — *References Matter* (arXiv:2506.14335, INLG 2025) | Varies human reference *sets* in summarization; metrics are unstable and ROUGE-based **model rankings vary with the reference set** | C1, C3, and ranking-level instability (C4 partially). Reference variation changing rankings is established. |
| **Jeong et al., 2026** — *Reporting Practice Matters* / ReRef (arXiv:2609.19093) | Rewrites radiology references along a reporting-practice taxonomy; rewriting can change which system ranks first | C1, C3, ranking change (C4 partially) in a medical NLG setting |
| **Barazandeh et al., 2026** — OTAP (arXiv:2607.17082) | Scores agent trajectories by optimal transport against a **set** of valid solution graphs; notes strict surface metrics do better when a formal verifier exists | C1, C8 (consistent with E3 argument); an evaluator, not a conclusion-stability diagnostic |
| **Wu et al., 2026** — LogicGraph (arXiv:2602.21044) | Solver-verified full sets of minimal proofs; reference-free evaluation of multi-path reasoning | C1, C2 (partial), C8 |
| **Alzahrani et al., 2024** — *When Benchmarks are Targets* (arXiv:2402.01781, ACL 2024) | Minor benchmark perturbations (option order, answer selection) shift LLM leaderboard rankings by several places, measured with Kendall's τ | C4, C5 in a different perturbation axis |
| **Li et al., 2025** — Instance-level Randomization (arXiv:2509.12678, Findings of EMNLP 2025) | Randomizes few-shot and format factors per instance to stabilize LLM evaluation | Evaluation-stability motivation; different factor |
| PetriBench (arXiv:2609.19883), TempoBench (arXiv:2510.27544) | Formal state-space / execution-trace reasoning benchmarks | C12-adjacent; do not vary reference identity |
| MechSim (2606.04505), FAX (2605.27879), Falsification-Based Verification (2607.16646) | Execution- or solver-based reference-free verification in other domains | C8 only |
| CES (arXiv:2510.15079, ICSE 2026) | Intermediate execution-state evaluation of code reasoning | C12-adjacent |

## 2. Revised Classification

Ratings: **Established** = shown by cited prior work; **Novel combination** = components known, the exact-enumeration instantiation is new; **Not found** = not found in the checked works (search not exhaustive).

| Component | Classification | Justification |
|---|---|---|
| C1 multi-valid-reference | Established | Casola, Jeong, OTAP, LogicGraph |
| C2 formal V(x) enumeration | Novel combination | Exhaustive enumeration is standard in verification; LogicGraph provides solver-verified full proof sets in logic |
| C3 reference identity as variable | Novel combination | Reference-set variation is established (Casola, Jeong); *exact* variation over the full valid space is new here |
| C4 benchmark-level conclusion stability | Established (setting-specific) | Ranking change under reference variation shown in summarization and radiology; leaderboard fragility shown by Alzahrani et al. |
| C5 τ_b distribution over Cartesian-product draws | Novel combination | τ-based stability is standard; the product-space distribution is new |
| C6 winner-reversal probability | Novel combination | Reversal under reference change is documented informally; the closed-form pairwise statistic is ours |
| C7 detection / significance stability | Not found | Detection analysis (false negatives, gap attenuation) and its exploratory status are described in Sections 4.4 and 9 of the paper |
| C8 reference-independent verifier | Established | OTAP, LogicGraph, FAX, Falsification, planning/constraint validators |
| C9 oracle recovery rate | Novel combination | Descriptive; not statistically supported pairwise structure (paper §4.5) |
| C10 Monte Carlo over ∏V(x_k) | Novel combination | Uniform and biased reference-vector samplers |
| C11 world-level sign-flip permutation test | Established | Standard method |
| C12 OS executable domain | Novel combination | Scheduling, synchronization, Banker's as an enumerable benchmark |

No component is rated "genuinely new" in isolation. The contribution is the **combination**: exact enumeration, reference-independent ground truth, conclusion-level metrics, and the decomposition of where instability lives (detection loss, near-ties, family heterogeneity).

## 3. Defensible Claim (matches paper §8)

> In multi-valued executable domains with exhaustively enumerable V(x), swapping the gold reference while holding tasks, outputs and evaluators fixed measurably degrades benchmark conclusions—chiefly by hiding real differences (reference matching retains 12–18% of true pairwise gaps, an exact attenuation of 1/|V(x)|, and detects the two oracle-significant differences in at most 5 of 50,000 draws) and by making near-tie orderings arbitrary (85.6% of E2 reversal mass lies in pairs the oracle cannot separate)—on the 24-world benchmark studied here. Matching against many references (k ≈ 25) restores about 85% detection; an inverse-|V| correction removes bias but not variance.

## 4. Claims Removed

- "First measurement of benchmark-level conclusion stability" (contradicted by ranking-change results in Casola et al. and Jeong et al.).
- "Genuinely new" ratings for C4–C7 and C9.
- "Reference-matching evaluators render benchmarks non-identifiable" as a general statement.
- "Restores 100% decision stability" without qualification: E3 is reference-independent by construction.
- Universal or cross-domain generalization.

## 5. Residual Novelty Risks

1. Reviewers may regard the effect as expected from |V(x)| > 1 (the pilot preregistration itself states this).
2. The search covered arXiv/ACL-style venues and was not exhaustive; planning-validator, program-equivalence and multi-reference code-evaluation literatures were not surveyed in depth.
3. Single benchmark, low-accuracy models; replication on a second domain is the main step that would strengthen the novelty case.

*Revised after primary-source verification, 2026-10-12.*

## Addendum (2026-10-24): Claude-family follow-up and crowded-area check

- Closest new work found: HypoSpace (set-valued hypothesis evaluation), VTC-Bench (valid-trace diversity), Shi et al. (ICLR 2026) and Dristi and Dwyer; PROBE (2607.13820) was verified from its arXiv abstract page only. The area is more crowded than the earlier novelty note assumed. The surviving claim is the combination: exhaustive V(x) enumeration, Cartesian reference-vector Monte Carlo, detection loss against an oracle, and the exact attenuation identity E[E2] = E3/|V(x)|.
- Not novel: the idea that more references help (k-reference/match-any).
- Unverified and the largest outstanding risk: how prevalent single-reference matching actually is in planning or executable benchmarks, where validators (for example VAL) are standard. A prevalence audit has not been done.
- Empirical evidence added: Section 4.8 (H1-H3 supported, H4 not supported; the H3 spread criterion is weak by construction).
- Paper type: empirical measurement and methodology study with a thin analytic part (the attenuation identity). Not conceptual. Realistic targets: workshop, or TMLR.
