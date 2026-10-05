# Paper Claims Audit & Empirical Traceability Matrix

This document audits every major scientific claim presented in the manuscript against empirical artifacts, code implementations, statistical evidence, and test suites.

## Claim 1: Executable Reasoning Benchmarks exhibit Reference-Choice Instability
- **Claim**: When evaluating executable model outputs against a gold reference trajectory selected from the valid solution space \(V(x)\), changing only the chosen valid reference alters model score distributions, model rank order, and pairwise winner identity.
- **Empirical Artifact**: `research/ssr_pilot/results/rcrc/rcr_summary.json`
- **Supporting Evidence**:
  - Normalized Matching Kendall \(\tau = 0.463 \pm 0.343\) across valid reference vector draws.
  - Pairwise winner reversal probability = 18.45%.
- **Status**: **SUPPORTED**.

---

## Claim 2: Reference Choice Flips Statistical Significance Decisions
- **Claim**: The statistical significance of pairwise model comparisons (\(p < 0.05\) vs \(p \ge 0.05\)) changes depending on which valid reference trajectory is selected from \(V(x)\).
- **Empirical Artifact**: `research/ssr_pilot/results/rcrc/rcr_summary.json` (`significance_stability` field)
- **Supporting Evidence**:
  - McNemar / Binomial test for `gemma2:9b` vs `qwen3:8b`: 50% of valid reference draws yield \(p < 0.05\) ("SIGNIFICANT_B_WINS"), while 50% yield \(p \ge 0.05\) ("NON_SIGNIFICANT").
  - `llama3.1:8b` vs `qwen3:8b`: 50% significant, 50% non-significant.
- **Status**: **SUPPORTED**.

---

## Claim 3: Reference Matching Evaluators Underestimate True Model Competence
- **Claim**: Exact string match and normalized trajectory match evaluators reject semantically valid model solutions that diverge from the single arbitrary canonical reference.
- **Empirical Artifact**: `research/ssr_pilot/results/adversarial/evaluator_meta_results.json` & `rcr_summary.json`
- **Supporting Evidence**:
  - `qwen3:8b` achieves 30.90% accuracy under the reference-independent semantic oracle, but only 4.86% under exact matching ($E_1$) and 13.19% under normalized matching ($E_2$).
  - On the adversarial contrast dataset, $E_1$ and $E_2$ yield a False Rejection Rate (FRR) of 50.0% and accept 0.0% of noncanonical valid solutions.
- **Status**: **SUPPORTED**.

---

## Claim 4: The Executable Semantic Oracle is Reference-Invariant and Eliminates Instability
- **Claim**: Replaying candidate outputs through the formal state transition system and checking task constraints directly yields a verdict that is strictly invariant to reference selection, recovering 100% decision stability.
- **Empirical Artifact**: `tests/ssr_pilot/test_oracle_independence.py` & `rcr_summary.json`
- **Supporting Evidence**:
  - $E_3$ Kendall \(\tau = 1.000 \pm 0.000\), 0.00% winner reversals, 100.0% oracle recovery rate.
  - Unit tests prove $E_3$ verdict is strictly identical for all $R \in V(x)$.
- **Status**: **SUPPORTED**.

---

## Prohibited Claims Check
- "First" / "World's First": **EXCLUDED**. (Differentiated via novelty matrix relative to TRACE, OTAP, and LogicGraph).
- "All LLMs" / "Frontier Models": **EXCLUDED**. (Scope bounded strictly to tested models `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`, `llama3.1:8b`, `gemma3:12b`, `olmo2:7b`).
- "Oracle is Objectively Correct": **EXCLUDED**. (Formally stated as reference-invariant relative to the formal task specification, not philosophically absolute).
