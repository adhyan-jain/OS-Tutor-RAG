# AGY's original RSG artifacts — archived, not evidence

These files are kept only as evidence for `docs/CLAUDE_FINAL_RESEARCH_AUDIT.md`. Do not cite any number in them.

| File | Why it is invalid |
|---|---|
| `baseline_runner.py` | No language model is ever called. The three "models" are hand-coded heuristics. `Reference_Sensitive_Judge` accepts any candidate whose first step matches the reference, and its "reference sensitivity" is built into its own code. |
| `baseline_results.json` | Produced by an oracle that compares JSON lists with tuples and rejects every trace, so `mean_semantic_score` is 0.0 for every "model". The reported RSG is **−0.94**, yet `FINAL_RESEARCH_DECISION.md` reports +0.94 to 1.00. |
| `ranking_inversions.json` | Spearman and Kendall correlations over three constant-scored heuristics: both are NaN. `FINAL_RESEARCH_DECISION.md` nevertheless answers "rankings change: YES". |
| `dataset.json` | Built by a simulator that re-schedules every time unit, which makes "FCFS" preemptive. 44/50 R2 traces are invalid under real FCFS. 24/50 "invalid" traces are byte-identical to R1, and 38/50 are members of V(P). The structural OOD split is empty. |

They are replaced by `research/benchmark/benchmark_v2.json`, `research/evaluation/` and `scripts/reproduce_all.py`.
