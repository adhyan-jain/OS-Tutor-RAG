# Table 1: Primary Reference-Choice Robustness (RCR) Metrics

| Evaluator | `qwen3:8b` Score | `gemma2:9b` Score | `mistral:7b-instruct` Score | `llama3.1:8b` Score | Kendall \(\tau\) Stability | Pairwise Reversal Prob | Oracle Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **\(E_1\) Canonical Exact** | 4.86% | 0.69% | 0.00% | 0.00% | 0.820 ± 0.396 | 5.39% | **4.0%** |
| **\(E_2\) Normalized Match** | 13.19% | 2.43% | 3.47% | 0.35% | 0.463 ± 0.343 | **18.45%** | **28.0%** |
| **\(E_3\) Semantic Oracle** | 30.90% | 17.01% | 7.64% | 6.60% | **1.000 ± 0.000** | **0.00%** | **100.0%** |
