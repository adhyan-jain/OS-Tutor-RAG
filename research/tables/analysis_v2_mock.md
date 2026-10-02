# Results tables (analysis_v2_mock.md)

Provenance: prereg sha256 `7855a8e3ae6839919eaf9e6f3ad75ee8ada6572827e6ec5702589cf34241d360`, git `8462ba27e4`, generated 2026-10-02T01:19:52

## E1 generation (all splits)

| model | parse | Acc_ref | Acc_multi | Acc_sem | RSG | canonical among valid |
|---|---|---|---|---|---|---|
| exact_match | 1.000 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.0 |
| oracle | 1.000 | 0.097 [0.075, 0.121] | 0.283 [0.246, 0.317] | 1.000 [1.000, 1.000] | 0.903 [0.879, 0.925] | 0.09682539682539683 |
| random | 1.000 | 0.325 [0.289, 0.363] | 0.675 [0.638, 0.710] | 0.675 [0.638, 0.710] | 0.349 [0.311, 0.386] | 0.4823529411764706 |

## E2 judging: acceptance rate by condition (all splits)

| model | parse fail | E2|R2|none | E2|R2|R1 | E2|R2|R3 | E2|R2|self | E2|I|none | E2|I|R1 |
|---|---|---|---|---|---|---|---|
| exact_match | 0.000 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| oracle | 0.000 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| random | 0.000 | 0.538 [0.500, 0.575] | 0.471 [0.433, 0.508] | 0.484 [0.444, 0.525] | 0.478 [0.440, 0.517] | 0.544 [0.506, 0.583] | 0.492 [0.452, 0.532] |

## Primary tests

Balanced accuracy (R2 vs I) uses scheduling only; concurrency failed the leakage audit (prereg D2).

| model | AI (self − R1) | H2 p | R1↔R3 flip | noise flip | H3 p | bal.acc none | bal.acc ref=R1 |
|---|---|---|---|---|---|---|---|
| exact_match | 1.000 [1.000, 1.000] | 2.2e-190 | 0.000 | 0.0 | 1 | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] |
| oracle | 0.000 [0.000, 0.000] | 1 | 0.000 | 0.0 | 1 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| random | 0.006 [-0.049, 0.063] | 0.43 | 0.511 | 0.5403726708074534 | 0.85 | 0.494 [0.461, 0.526] | 0.493 [0.461, 0.524] |

## H2b context controls (id): accept(R2|ctrl) − accept(R2|R1)

| model | none | irrelevant | R1 reworded | invalid ref |
|---|---|---|---|---|
| exact_match | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| oracle | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| random | 0.033 [-0.080, 0.147] | 0.007 [-0.107, 0.120] | 0.027 [-0.087, 0.133] | -0.080 [-0.193, 0.027] |

## Anchoring index by split

| model | high_branching | id | lexical_ood | long_trace | rr_primitive | struct_mutex | struct_semaphore |
|---|---|---|---|---|---|---|---|
| exact_match | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| oracle | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| random | -0.013 [-0.150, 0.138] | -0.053 [-0.160, 0.053] | -0.025 [-0.188, 0.138] | 0.037 [-0.125, 0.200] | 0.062 [-0.087, 0.225] | 0.062 [-0.113, 0.225] | 0.025 [-0.138, 0.175] |

## E3 ranking: Acc_ref vs Acc_sem

Kendall τ = 0.0, P(τ<1) under bootstrap = 1.0, inversions = 1

| model | Acc_ref | rank | Acc_sem | rank |
|---|---|---|---|---|
| exact_match | 1.000 | 1 | 1.000 | 1 |
| oracle | 0.097 | 3 | 1.000 | 2 |
| random | 0.325 | 2 | 0.675 | 3 |

## Preregistered decision rules

```
{
 "H2_significant_models": [
  "exact_match"
 ],
 "H2_majority": false,
 "H2b_pass_models": [],
 "H2b_majority": false,
 "H3_significant_models": [],
 "H3_majority": false,
 "H4_rankings_change": true,
 "H4_tau_observed": 0.0,
 "ood_splits_where_anchoring_ci_includes_0": {
  "exact_match": []
 },
 "verdict_rule": "KILL"
}
```
