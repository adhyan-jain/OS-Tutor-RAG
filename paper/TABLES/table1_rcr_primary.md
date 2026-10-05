# Table 1: Primary Reference-Choice Robustness Metrics (Baseline 1,152 Generations)

| Evaluator Class | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b-instruct` Score | `llama3.1:8b` Score | Kendall \(\tau\) Stability | Pairwise Reversal Prob | Oracle Recovery Rate \(RCR(E)\) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Canonical Exact** | 4.86% (14/288) | 0.69% (2/288) | 0.00% (0/288) | 0.00% (0/288) | 0.820 ± 0.396 | 5.39% | **4.0%** (4/100) |
| **\(E_2\) Normalized Match** | 13.19% (38/288) | 2.43% (7/288) | 3.47% (10/288) | 0.35% (1/288) | 0.463 ± 0.343 | **18.45%** | **28.0%** (28/100) |
| **\(E_3\) Semantic Oracle** | 30.90% (89/288) | 17.01% (49/288) | 7.64% (22/288) | 6.60% (19/288) | **1.000 ± 0.000** | **0.00%** | **100.0%** (100/100) |
