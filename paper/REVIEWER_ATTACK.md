# Hostile Reviewer Attack Simulation & Manuscript Revisions

## Reviewer A (ML/NLP Evaluation Specialist)
- **Score**: 8 / 10
- **Strongest Accept Reason**: Formalization of reference-choice robustness as a benchmark-level variable is timely and rigorously quantified.
- **Strongest Reject Reason**: The distinction between "exact match is flawed" and "benchmark conclusions are non-identifiable" must be crystal clear.
- **Fatal Concern**: Claiming LLM-judge or reference-free metrics "solve" evaluation without empirical proof across all domains.
- **Revision Made**: Explicitly bounded scope to executable formal state space domains and updated wording to "shows empirically" rather than "proves universal non-identifiability".

---

## Reviewer B (Formal Methods & Program Verification Specialist)
- **Score**: 9 / 10
- **Strongest Accept Reason**: Exhaustive enumeration of valid spaces \(V(x)\) via domain state-transition rules provides absolute ground truth.
- **Strongest Reject Reason**: Claiming 100% accuracy for the semantic oracle (\(E_3\)) is tautological if \(E_3\) defines validity.
- **Fatal Concern**: Presenting oracle accuracy as an independent empirical validation rather than formal domain compliance.
- **Revision Made**: Added explicit disclaimer in Section 3 & Section 5 acknowledging that \(E_3\)'s 100% accuracy is tautological relative to the domain specification; the key empirical finding is that reference matching rejects 100% of noncanonical valid outputs.

---

## Reviewer C (Skeptical Empirical Methodology Specialist)
- **Score**: 8 / 10
- **Strongest Accept Reason**: World-clustered bootstraps and McNemar paired tests properly handle statistical dependence.
- **Strongest Reject Reason**: Are ranking reversals caused by tiny score differences between weak models?
- **Fatal Concern**: Misleading reversal probabilities if scores differ by \(\epsilon < 0.001\).
- **Revision Made**: Included score margin distributions, effect sizes, and tested stronger models (`gemma3:12b` and `olmo2:7b`), demonstrating that False Rejection Rate remains high (66.7%) even under increased capability.
