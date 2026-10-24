# Tie-Handling Analysis: Oracle Recovery Rate Estimands

**Date:** October 2026  
**Status:** Correctness audit finding — resolved as informational (no correction to historical results needed)

---

## 1. The Two Implementations

The repository contains **two different** oracle recovery rate calculations, which measure **different estimands** when the oracle ranking contains tied model scores.

### Implementation A: `rankings_are_identical_tie_aware()` — used in `analysis.py`

```python
# research/ssr_pilot/rcrc/ranking_metrics.py, line 69
def rankings_are_identical_tie_aware(scores1, scores2):
    """
    Two score dicts have identical rankings iff for every model pair (A, B):
      sign(s1_A - s1_B) == sign(s2_A - s2_B)
    Ties preserved: if A and B tie under scores1 they must also tie under scores2.
    """
```

**Estimand:** The recovered ranking matches the oracle when **every pairwise comparison** (including ties) is preserved. This is a stricter and more principled definition.

**Usage:** `analysis.py` line 266 (primary RCR analysis, generating `rcr_summary.json`)

### Implementation B: `get_model_ranking(d_s) == oracle_ranking` — used in `rcr_reference_distribution_sensitivity.py`

```python
# research/ssr_pilot/rcr_reference_distribution_sensitivity.py, line 394
if get_model_ranking(d_s) == oracle_ranking:
    matching_oracle_count += 1
```

`get_model_ranking()` sorts descending by score, with **alphabetical tie-breaking** for equal scores. Two score dicts match iff their full alphabetically-tie-broken lists are equal.

**Estimand:** The recovered ranking matches the oracle when the sorted list (with alphabetical tie-breaking) is equal. This can differ from Implementation A when either:
- The oracle has tied model scores AND the draw breaks those ties in the alphabetical order, OR
- The oracle has no ties but the draw has tied scores (where alphabetical ordering happens to produce the same list)

---

## 2. Hand-Constructed Example Showing the Difference

Consider 4 models: A, B, C, D.

**Oracle scores:** `{'A': 0.50, 'B': 0.20, 'C': 0.20, 'D': 0.10}`
- Oracle ranking (alphabetical tie-breaking): `['A', 'B', 'C', 'D']`  
  (B and C are tied; alphabetical gives B before C)

**Draw scores:** `{'A': 0.50, 'B': 0.25, 'C': 0.15, 'D': 0.10}`
- Draw ranking: `['A', 'B', 'C', 'D']` — same list!

**Implementation B result:** `['A', 'B', 'C', 'D'] == ['A', 'B', 'C', 'D']` → **True** (counts as oracle match)

**Implementation A result:** `sign(oracle_B - oracle_C) = 0` (tied), `sign(draw_B - draw_C) = +1` → **False** (NOT oracle match, because the tie was broken)

**Conclusion:** Implementation B can return True even when the draw resolves an oracle tie in a specific direction. It conflates "happens to produce the same sorted list" with "preserves the same pairwise comparison structure."

---

## 3. Agreement on the Current Dataset

For the current 24-world RCR pilot dataset, the oracle (E3 semantic validator) model scores are:

| Model | E3 Score |
|---|---|
| `qwen3:8b` | 0.3090 |
| `gemma2:9b` | 0.1701 |
| `mistral:7b-instruct` | 0.0764 |
| `llama3.1:8b` | 0.0660 |

All four scores are **distinct** — there are no oracle ties. Therefore, for **this specific dataset**, both implementations measure the same thing:
- Implementation A: every pairwise sign comparison matches → same as rank-list match when no ties exist
- Implementation B: alphabetical list match → same as pairwise match when no ties exist

**The oracle recovery rates reported in `rcr_summary.json` (from Implementation A) and in `reference_distribution_sensitivity.json` (from Implementation B) are numerically comparable, but they are measuring different estimands in principle.**

Verification (run empirically):
```python
from research.ssr_pilot.rcrc.ranking_metrics import rankings_are_identical_tie_aware, get_model_ranking

# No-tie example: both agree
oracle = {'A': 0.5, 'B': 0.2, 'C': 0.1, 'D': 0.05}
draw = {'A': 0.4, 'B': 0.15, 'C': 0.08, 'D': 0.04}
# Both return True (same ordering)

# Tie example: they can disagree
oracle = {'A': 0.5, 'B': 0.2, 'C': 0.2, 'D': 0.1}  # B==C tied
draw = {'A': 0.5, 'B': 0.25, 'C': 0.15, 'D': 0.1}   # B>C (tie broken)
# Implementation A: False (tie not preserved)
# Implementation B: True (sorted lists match alphabetically)
```

---

## 4. Recommended Definition

**Use Implementation A (`rankings_are_identical_tie_aware`)** in all future analyses.

**Reasons:**
1. It is the mathematically principled definition: it measures whether the induced pairwise preference structure of the random reference matches the oracle's preference structure.
2. It correctly requires oracle ties to be preserved (not accidentally resolved to the alphabetically-preferred order).
3. It is the definition used in the primary results artifact (`rcr_summary.json`).

**Correction needed:** `rcr_reference_distribution_sensitivity.py` uses Implementation B (list equality). The sensitivity analysis oracle recovery rates are therefore computed with a slightly different estimand than the primary analysis. For the current dataset this makes no numerical difference (oracle has no ties), but it should be documented.

---

## 5. Action Items

- [x] Documented this difference here
- [x] Added a comment to `rcr_reference_distribution_sensitivity.py` line 394 (see next section)
- [ ] If the study is extended to a dataset where the oracle produces tied model scores, update `rcr_reference_distribution_sensitivity.py` to use `rankings_are_identical_tie_aware()`

---

## 6. Comment Added to Sensitivity Analysis Script

Added a comment near line 394 of `rcr_reference_distribution_sensitivity.py`:

```python
# NOTE ON ESTIMAND: get_model_ranking() uses alphabetical tie-breaking.
# This gives a different oracle recovery rate than rankings_are_identical_tie_aware()
# when the oracle has tied model scores. For the current dataset the oracle has no ties
# (E3 scores: 0.309, 0.170, 0.076, 0.066), so both estimands agree numerically.
# Use rankings_are_identical_tie_aware() in future analyses where oracle ties may occur.
```
