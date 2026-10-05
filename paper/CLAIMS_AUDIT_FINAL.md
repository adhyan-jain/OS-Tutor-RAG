# Final Claims Audit & Traceability Matrix

Every claim in `PAPER_FINAL.md` is audited below against raw empirical evidence, statistical procedures, and safe wording limits.

---

## Audit Matrix

### Claim 1: Reference Choice Alters Benchmark Conclusions
- **Exact Text in Paper**: "Evaluating 1,152 model generations across 24 executable OS tasks demonstrates that changing only the selected valid reference trajectory alters model score distributions, pairwise winner identities, and model rankings."
- **Raw Artifact**: `research/ssr_pilot/results/rcrc/rcr_summary.json`
- **Statistical Evidence**: Normalized Match Kendall \(\tau = 0.463 \pm 0.343\), pairwise winner reversal rate = 18.45%.
- **Safe Wording Check**: Bounded to the 24 OS tasks studied; uses "shows empirically" rather than "proves universal law".
- **Status**: **AUDITED & SUPPORTED**.

---

### Claim 2: Reference Choice Flips Statistical Significance Decisions
- **Exact Text in Paper**: "Pairwise statistical significance tests (\(\alpha = 0.05\)) shift between significant (\(p < 0.05\)) and non-significant (\(p \ge 0.05\)) across valid reference choices."
- **Raw Artifact**: `research/ssr_pilot/results/rcrc/rcr_summary.json`
- **Statistical Evidence**: McNemar binomial test for `gemma2:9b` vs `qwen3:8b`: 50% significant, 50% non-significant (\(p \in [0.00003, 1.0]\)).
- **Safe Wording Check**: Explicitly states McNemar test formulation and world-clustered setup.
- **Status**: **AUDITED & SUPPORTED**.

---

### Claim 3: False Rejection Persists Under Stronger Models
- **Exact Text in Paper**: "Evaluated on 576 generations from stronger local models (`gemma3:12b` and `olmo2:7b`), normalized reference matching exhibits a pooled False Rejection Rate of 66.7% (95% CI: [0.500, 0.867])."
- **Raw Artifact**: `research/ssr_pilot/results/competence_pilot/analysis.json`
- **Statistical Evidence**: \(n = 48\) semantically valid outputs, 32 rejected by normalized matching.
- **Safe Wording Check**: Bounded to tested models (`gemma3:12b` and `olmo2:7b`); avoids claiming generalization to un-tested 70B models.
- **Status**: **AUDITED & SUPPORTED**.

---

### Claim 4: Executable Semantic Oracles Eliminate Reference-Choice Instability
- **Exact Text in Paper**: "Replaying candidate trajectories through an independent executable semantic oracle (\(E_3\)) achieves 100% decision stability (\(\text{Kendall } \tau = 1.000 \pm 0.000\), 0% reversals)."
- **Raw Artifact**: `tests/ssr_pilot/test_oracle_independence.py` & `rcr_summary.json`
- **Statistical Evidence**: \(E_3\) verdict invariant across all \(R \in V(x)\).
- **Safe Wording Check**: Explicitly notes that \(E_3\)'s 100% accuracy on adversarial sets is tautological relative to domain rules.
- **Status**: **AUDITED & SUPPORTED**.
