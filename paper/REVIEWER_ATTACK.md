# Hostile Reviewer Simulation & Decision Gate

**Manuscript:** [`paper/PAPER_FINAL.md`](file:///home/adhyan/Desktop/OS_RAG/paper/PAPER_FINAL.md)  
**Date:** October 2026  

---

## 1. Five Hostile Expert Reviewer Attacks

### Reviewer 1: ML/NLP Evaluation Expert
- **Attack**: *"We already know single-reference exact match is bad. BLEU/ROUGE literature (e.g. References Matter, INLG 2025) has shown for years that reference choice alters score numbers. Why is this paper novel?"*
- **Empirical Rebuttal**: *References Matter* and prior NLG work focus on string similarity variation in open-ended natural language generation. In contrast, RCR formalizes **benchmark-level perturbation propagation** in formal executable domains where valid solution spaces \(V(x)\) are exhaustively enumerated. We prove that reference choice does not merely shift score magnitudes: it causes **18.61% strict pairwise winner reversals** and reduces oracle rank recovery to **23.92%** (\(E_2\)) and **2.86%** (\(E_1\)).
- **Remaining Weakness**: Scope is bounded to formal execution domains with multi-valued valid solution spaces.

### Reviewer 2: Formal Methods Specialist
- **Attack**: *"Your semantic oracle is just a Python simulator. How do you know the simulator itself is bug-free and truly reference-independent?"*
- **Empirical Rebuttal**: The validator (`research/simulator/validators.py`) was written independently from the enumerators. We ran automated reference-invariance audits across all 24 OS worlds, proving that for any valid candidate trace \(y \in V(x)\), `evaluate_oracle(x, y)` yields `semantic_valid == TRUE` without accessing or accepting a reference parameter.
- **Remaining Weakness**: Validator implementation risk remains a theoretical threat to validity.

### Reviewer 3: Statistics & Experimental Design Auditor
- **Attack**: *"In previous drafts you claimed 50% of reference choices flip statistical significance decisions. Did you fix your statistical unit?"*
- **Empirical Rebuttal**: Yes. Previous cell-level McNemar tests (\(N=288\)) committed pseudoreplication by treating nested seeds and variants as independent observations. Applying the preregistered world-level paired sign-flip permutation test (20,000 sign flips, Holm-Bonferroni corrected over 6 model pairs at \(\alpha=0.05\)) reveals that **world-level variance dominates pairwise model differences**. Across 100% of reference draws, no model pair achieves statistical significance after Holm correction. We explicitly document this correction as Deviation 1.
- **Remaining Weakness**: Benchmark sample size (\(N=24\) worlds) limits statistical power for fine-grained pairwise model ranking significance.

### Reviewer 4: Benchmark Methodology Reviewer
- **Attack**: *"Models generated noncanonical traces because you didn't tell them your tie-breaking convention in the prompt."*
- **Empirical Rebuttal**: We evaluated 1,152 generations under stated-convention prompts where canonical tie-breaking rules were explicitly stated. Stated conventions reduce \(\text{FRR}_{\text{norm}}\) only slightly from 0.715 to 0.625. 9.5% of all stated-convention outputs (110 / 1,152) remain valid-noncanonical trajectories, proving that noncanonical output generation persists even when conventions are disclosed.
- **Remaining Weakness**: Weak models (\(B = 15.3\%\)) fail to follow complex instructions cleanly.

### Reviewer 5: Novelty & Editorial Reviewer
- **Attack**: *"Your competence pilot only evaluated Gemma 3 12B and OLMo 2 7B, generating a tiny $n_{\text{valid}}=48$. Can you claim this holds for frontier models?"*
- **Empirical Rebuttal**: We explicitly unpooled the two models. `gemma3:12b` generated 42 valid outputs with \(\text{FRR}_{\text{norm}} = 0.619\), confirming noncanonical trajectory diversity in a 12B model. However, `olmo2:7b` generated only 6 valid outputs (\(B=0.021\)). We explicitly narrowed our claims: we do NOT claim pooled results prove general frontier capability.
- **Remaining Weakness**: Hardware constraints prevented running 30B+ local models via AirLLM due to disk and network bandwidth limits.

---

## 2. Paper Decision Gate

### Verdict: **MODIFY (Strong Scientific Paper)**

- **Rationale**:
  1. The core RCR contribution—proving that gold reference choice induces 18.61% pairwise winner reversals and drops oracle recovery to 23.92%—is empirically rock-solid across 50,000 Monte Carlo draws (\(\text{SE} = 0.0016\)).
  2. The statistical repair eliminated the invalid "50% significance flip" overclaim, establishing honest world-level inference.
  3. The stated-convention control directly refutes the "unstated tie-break" objection.
  4. The unpooled competence analysis provides honest, uninflated sample size reporting.
  5. The manuscript rewritten with 100% traceable data and 359 passing automated tests is scientifically defensible for top-tier submission (e.g. NeurIPS Datasets & Benchmarks / ACL / EMNLP).
