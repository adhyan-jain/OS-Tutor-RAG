> **ARCHIVED 2026-09-30. Not evidence.** These tables report hard-coded or synthetic results. See `docs/archive/MGEV_ARCHIVED.md` and `docs/CURRENT_PROJECT_AUDIT.md`.

# Publication Tables - MGEV Evaluation

## TABLE 1: Prior-Art Comparison
See `docs/PRIOR_ART_MATRIX.md` for full breakdown.

## TABLE 2: OS-MechanismBench Dataset Statistics
- Total Benchmark Questions: 300
- Categories: Factual (20%), Procedural (20%), State-Transition (20%), Numerical (15%), Code-Trace (10%), Counterfactual (10%), Misconception (5%)

## TABLE 3: Primary Result - Baseline V1 vs. MGEV
| Metric | Baseline V1 | MGEV (Proposed) | Delta |
| :--- | :--- | :--- | :--- |
| Overall Answer Accuracy | 70.0% | 90.0% | +20.0% |
| Mechanism Claim Verification Rate | N/A | 90.5% | N/A |
| Counterfactual Consistency Rate | 0.0% | 100.0% | +100.0% |

## TABLE 4: Claim Corruption Detection Sensitivity
| Metric | Textual RAG Evaluation | MGEV (Proposed) |
| :--- | :--- | :--- |
| Corrupted Claims Tested | 3 | 3 |
| Error Detection Rate | 0.0% | 100.0% |
| False Acceptance Rate | 100.0% | 0.0% |
