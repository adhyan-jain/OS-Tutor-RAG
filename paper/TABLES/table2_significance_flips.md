# Table 2: Statistical Significance Decision Stability Across Reference Choices (\(\alpha = 0.05\))

| Model Pair | Evaluator | Significant (\(p < 0.05\)) Proporation | Non-Significant (\(p \ge 0.05\)) Proportion | Decision Constant Across References? | Mean \(p\)-value |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `gemma2:9b` vs `qwen3:8b` | \(E_2\) Normalized | **50.0%** (Significant B Wins) | **50.0%** (Non-significant) | **NO** (Flips) | 0.1737 ± 0.286 |
| `llama3.1:8b` vs `qwen3:8b` | \(E_2\) Normalized | **50.0%** (Significant B Wins) | **50.0%** (Non-significant) | **NO** (Flips) | 0.1684 ± 0.285 |
| `mistral:7b-instruct` vs `qwen3:8b` | \(E_2\) Normalized | **50.0%** (Significant B Wins) | **50.0%** (Non-significant) | **NO** (Flips) | 0.1737 ± 0.286 |
| `gemma2:9b` vs `qwen3:8b` | \(E_3\) Semantic Oracle | **100.0%** (Significant B Wins) | **0.0%** | **YES** (100% Stable) | 0.0001 ± 0.000 |
