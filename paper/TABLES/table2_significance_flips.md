# SUPERSEDED — do not cite

This table previously reported "50% significance flips" from cell-level McNemar tests. Those tests treated nested seeds and variants as independent observations (pseudoreplication) and were retracted (manuscript §4.2, Deviation 1).

A later 200-draw subsample analysis pooled the evaluators and was also superseded (Deviation 6 -> 7).

Use instead, all generated from `research/ssr_pilot/results/rcrc/extended_analysis.json` by `python paper/build_tables.py`:

- `table3_significance_detection.md` — world-level significance per evaluator over all 50,000 draws
- `table4_evaluator_effect.md` — evaluator effect on each pairwise gap (world-level bootstrap)
- `table5_near_tie.md` — reversals by oracle separation
- `table6_by_family.md` — reversal by mechanism family
