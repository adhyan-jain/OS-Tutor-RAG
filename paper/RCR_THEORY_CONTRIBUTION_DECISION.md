# Publication Verdict Memo: Theory-Backed RCR Paper

**Date:** October 2026  
**Status:** Architectural Decision Memo  
**Verdict:** **NO-GO** (for a theory-backed paper)

---

## Executive Summary

This memorandum evaluates whether to pivot or position the Reference-Choice Robustness (RCR) project as a **theory-backed contribution** incorporating exact dynamic programming (DP) margin convolutions and total-variation (TV) robustness certificates.

Based on rigorous mathematical derivations, empirical validation on the frozen 1,152 generation pilot dataset, and prior-art search, the verdict is **NO-GO for a theory-backed paper**. The mathematical formulations are elementary, the TV certificate is empirically vacuous on realistic distribution shifts, and the exact DP provides no qualitative insights beyond standard Monte Carlo estimation.

---

## 1. What Exact DP Adds vs. Monte Carlo Estimation

### Analysis
- At $M = 50,000$ Monte Carlo draws, the standard error of pairwise reversal probability estimates is:
  $$\mathrm{SE} \approx \sqrt{\frac{p (1 - p)}{M}} \le \sqrt{\frac{0.25}{50000}} \approx 0.0022$$
  For our empirical pairwise reversal probabilities ($p \in [0.068, 0.278]$), the standard error is $\sim 0.0011 - 0.0016$.
- Our exact DP convolution computes the margin distribution to floating-point precision ($\sim 10^{-15}$). For E2 normalized matching, the exact DP mean pairwise reversal probability across all 6 pairs is:
  $$p_{\mathrm{exact}} = 0.171518$$
  Comparing to existing Monte Carlo artifacts:
  - `extended_analysis.json` (seed 20261016): $0.171770$ ($\Delta = 0.00025$)
  - `reference_distribution_sensitivity.json` (seed 20261007): $0.172348$ ($\Delta = 0.00083$)
  Both differences are well within $1 \times \mathrm{SE}$.

### Verdict on DP Contribution
Is there any qualitative scientific finding that MC at 50k draws cannot establish?
**Answer: No.**
In extreme tail-risk or rare-event estimation (e.g., reversal probabilities of $10^{-6}$), exact DP or large-deviations theory would be essential. However, in RCR the reversal probabilities are large ($6.8\% - 27.8\%$). Monte Carlo at 50k samples already nails the point estimates and confidence intervals. Exact DP is computationally elegant and fast ($<2$ ms), but it is a numerical optimization, not a theoretical finding that changes any scientific conclusion.

---

## 2. Informativeness of the TV Robustness Certificate

### Analysis
The TV robustness certificate provides a Lipschitz upper bound on the shift in expected pairwise margin $\mu_{AB} = \mathbb{E}[M_{AB}]$:
$$|\mu_{AB}(q) - \mu_{AB}(q^0)| \le \frac{2}{N} \sum_{i=1}^N \mathrm{TV}(q_i, q_i^0)$$
To certify that the sign of $\mu_{AB}(q)$ remains positive under distribution shift, the expected margin under the baseline distribution must exceed the TV bound:
$$|\mu_{AB}(q^0)| > \frac{2}{N} \sum_{i=1}^N \mathrm{TV}(q_i, q_i^0)$$

### Quantitative Audit on the Pilot Dataset
1. **Empirical expected margins:**
   Across all 6 pairs under uniform reference distribution:
   - `gemma2:9b` vs `llama3.1:8b`: $\mu = +0.0122$
   - `gemma2:9b` vs `mistral:7b-instruct`: $\mu = +0.0124$
   - `gemma2:9b` vs `qwen3:8b`: $\mu = -0.0243$
   - `llama3.1:8b` vs `mistral:7b-instruct`: $\mu = +0.0002$
   - `llama3.1:8b` vs `qwen3:8b`: $\mu = -0.0366$
   - `mistral:7b-instruct` vs `qwen3:8b`: $\mu = -0.0368$
   The maximum expected margin across any pair is $0.0368$.

2. **TV budget under canonical bias:**
   Consider a modest canonical bias distribution where the canonical reference receives probability $p = 0.50$ (and remaining valid references share the remaining $0.50$).
   - Across the 24 worlds (where $|V_i|$ ranges from 1 to 24), the mean TV distance is $\overline{\mathrm{TV}} = 0.3308$.
   - The Lipschitz TV bound is:
     $$\text{Bound} = 2 \times \overline{\mathrm{TV}} = 2 \times 0.3308 = 0.6616$$
   - Even for a mild bias $p = 0.25$, $\overline{\mathrm{TV}} = 0.1572$, giving a TV bound of $0.3144$.

3. **Comparison:**
   $$\text{Max } |\mu| = 0.0368 \ll 0.3144 \ll 0.6616$$
   The TV bound is **18 times larger** than the largest expected margin on the benchmark!

### Verdict on TV Certificate
**The certificate fails to certify sign invariance for realistic distribution shifts due to bound conservatism.**
- The certifiable TV budget under this sufficient condition is bounded by $\overline{\mathrm{TV}} < \frac{|\mu|}{2} \le 0.0184$. This means the certificate can only guarantee stability for perturbations of less than $1.8\%$ probability mass per world.
- Crucially, **failure of the sufficient certificate does NOT prove that the expected margin flips sign.** In fact, empirical evaluation across canonical bias distributions ($p \in [0.25, 0.99]$ in `reference_distribution_sensitivity.json`) shows that the actual expected margins for all pairs retain their signs!
- Because TV distance is an $L_1$ worst-case Lipschitz bound assuming adversarial alignment of differences ($D_i = -1.0$), it is drastically too conservative for multi-reference benchmarking where differences do not span $[-1, 1]$ adversarially. Theory or statistics reviewers would immediately recognize that this bound is uninformative in practice.

---

## 3. Prior Art and Direct Overlap Risk

### arXiv:2610.03825
- **Paper:** *Same Output, Different Gold: Measuring How Reference Choice Moves a Multilingual Benchmark Score*  
- **Authors:** Parth Kulshreshtha, Shivali Dalmia, Abhishek Mukherji (arXiv:2610.03825, cs.CL, submitted October 2026).  
- **Abstract & Scope:** Examines how variations in reference ("gold") standards shift benchmark scores, alter system rankings, and impact comparative evaluation when system outputs remain identical.
- **Overlap:** This represents a direct conceptual overlap with the core premise of RCR: that reference choice is an unmodeled experimental variable that destabilizes benchmark rankings.

### Broader Landscape
- Multiple 2025–2026 papers already document reference-induced ranking instability:
  - Casola et al. (arXiv:2506.14335, INLG 2025): Reference sets vary ROUGE-based rankings.
  - Jeong et al. (arXiv:2609.19093): Reference variation flips model ranks in radiology NLG.
  - Alzahrani et al. (ACL 2024): Leaderboard fragility under benchmark perturbation.

---

## 4. Honest Verdict and Final Recommendation

### Verdict: **NO-GO for a Theory-Backed Paper**

### Justification:
1. **Zero Mathematical Novelty:**
   - The TV bound is textbook coupling (Levin & Peres, Lemma 4.2).
   - The convolution is standard discrete DP.
   - The reversal identity $2 p_+ p_-$ is a two-line elementary probability identity.
   Calling this a "theoretical framework" or "theory contribution" invites instant rejection from theory reviewers.
2. **Empirical Vacuity of the Certificate:**
   The TV certificate certifies no realistic distribution shift because worst-case Lipschitz bounds are vastly too loose when individual task margins are on the order of $10^{-2}$.
3. **No Added Scientific Value over Monte Carlo:**
   Exact DP corroborates the 50k MC numbers to 4 decimal places, but uncovers no new phenomenon.
4. **Prior Art Density:**
   With Kulshreshtha et al. (arXiv:2610.03825) appearing in October 2026, claiming general evaluation theory on reference variation is exposed to high prior-art friction.

### Path Forward: Empirical Systems / Benchmark Positioning
If the OS-Tutor-RAG / SSR pilot work is to be published, it should **NOT** be submitted as a theoretical paper. Instead, its defensible positioning is:
- **An empirical systems/benchmarking study:** Demonstrating how formal state-space verification (scheduling, synchronization, deadlock avoidance) enables exact identification of valid spaces $V(x)$, and quantifying the resulting conclusion instability in LLM-generated code/plans.
- The DP algorithm and $2 p_+ p_-$ identity should be included in the **methods appendix** as compact, clean calculation tools, without claiming mathematical novelty.
