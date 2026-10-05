# SSR pilot results (dry)

## Decision (mechanical)

**GREENLIGHT** — all of K0-K5 passed

| K0 | K1 | K2 | K3 | K4 | K5 |
|---|---|---|---|---|---|
| pass | pass | pass | pass | pass | pass |

## Per model (world-clustered 95% CI; UNVERIFIABLE counts as not valid)

| model | B semantic | A_norm | A_strict | C | FRR_norm | FRR_strict | random-valid floor | UNVERIF |
|---|---|---|---|---|---|---|---|---|
| attacker:always_reference | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.831 | 0.000 |
| attacker:random_invalid | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | — | — | — | 0.000 |
| attacker:random_valid | 1.000 [1.000, 1.000] | 0.149 [0.087, 0.219] | 0.149 [0.087, 0.219] | 0.635 [0.490, 0.774] | 0.851 [0.781, 0.913] | 0.851 [0.781, 0.913] | 0.831 | 0.000 |
| attacker:symbolic_alt | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.417 [0.208, 0.625] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.831 | 0.000 |
| **pooled** | 0.750 [0.750, 0.750] | 0.287 [0.272, 0.305] | 0.287 [0.272, 0.305] | 0.513 [0.428, 0.596] | 0.617 [0.594, 0.638] | 0.617 [0.594, 0.638] | | 0.000 |

## FRR_norm by family and by variant (pooled over models)

| group | FRR_norm |
|---|---|
| family: banker | 0.639 [0.608, 0.667] |
| family: scheduling | 0.573 [0.531, 0.611] |
| family: sync | 0.639 [0.611, 0.660] |
| variant: v0 | 0.615 [0.583, 0.642] |
| variant: v1 | 0.611 [0.580, 0.639] |
| variant: v2 | 0.625 [0.601, 0.646] |

## FRR_norm by family × model

| family | attacker:always_reference | attacker:random_invalid | attacker:random_valid | attacker:symbolic_alt |
|---|---|---|---|---|
| banker | 0.000 [0.000, 0.000] | — | 0.917 [0.823, 1.000] | 1.000 [1.000, 1.000] |
| scheduling | 0.000 [0.000, 0.000] | — | 0.719 [0.594, 0.834] | 1.000 [1.000, 1.000] |
| sync | 0.000 [0.000, 0.000] | — | 0.917 [0.833, 0.979] | 1.000 [1.000, 1.000] |

## Cheap proxies vs the oracle (K3; threshold fitted on other families)

| proxy | balanced agreement [95% CI] | accepts when oracle rejects | accepts when oracle accepts |
|---|---|---|---|
| distance | 0.696 [0.684, 0.707] | 0.000 | 0.391 |
| final_state_only | 0.571 [0.532, 0.614] | 0.542 | 0.684 |

## Do conclusions change? (24 worlds)

| pair | Δ A_norm | Δ B | p(A) Holm | p(B) Holm | reversed | stab | sig changes | stab | CI of evaluator effect on the gap |
|---|---|---|---|---|---|---|---|---|---|
| attacker:always_reference|attacker:random_invalid | +1.000 | +1.000 | 0.0003 | 0.0003 | False | 1.00 | False | 1.00 | [+0.000, +0.000] |
| attacker:always_reference|attacker:random_valid | +0.851 | +0.000 | 0.0003 | 1 | False | 1.00 | True | 1.00 | [+0.788, +0.924] |
| attacker:always_reference|attacker:symbolic_alt | +1.000 | +0.000 | 0.0003 | 1 | False | 1.00 | True | 1.00 | [+1.000, +1.000] |
| attacker:random_invalid|attacker:random_valid | -0.149 | -1.000 | 0.0015 | 0.0003 | False | 1.00 | False | 1.00 | [+0.788, +0.924] |
| attacker:random_invalid|attacker:symbolic_alt | +0.000 | -1.000 | 1 | 0.0003 | False | 1.00 | True | 1.00 | [+1.000, +1.000] |
| attacker:random_valid|attacker:symbolic_alt | +0.149 | +0.000 | 0.0015 | 1 | False | 1.00 | True | 1.00 | [+0.076, +0.212] |

| model | share of A_norm-wrong outputs that are semantically valid | majority | stability |
|---|---|---|---|
| attacker:always_reference | nan | False | 0.00 |
| attacker:random_invalid | 0.000 | False | 0.00 |
| attacker:random_valid | 1.000 | True | 1.00 |
| attacker:symbolic_alt | 1.000 | True | 1.00 |

Ranking by A_norm vs B: Kendall τ = 0.5163977794943223, P(τ<1) = 1.0; A_norm ranks {'attacker:always_reference': 1, 'attacker:random_valid': 2, 'attacker:random_invalid': 3, 'attacker:symbolic_alt': 4}, B ranks {'attacker:always_reference': 1, 'attacker:random_valid': 2, 'attacker:symbolic_alt': 3, 'attacker:random_invalid': 4}

K4(i) reversal False; K4(ii) significance change True; K4(iii) failure profile True; adequate precision of 'no change': False

## Failure taxonomy (share of outputs)

| model | constraint:before | constraint:precedence | rule:mutual_exclusion_violation | rule:need_exceeds_work | rule:policy_violation | rule:preempted_partial_burst | rule:queue_order_violation | rule:wait_on_zero_semaphore | rule:wrong_burst_length | valid_canonical | valid_noncanonical |
|---|---|---|---|---|---|---|---|---|---|---|---|
| attacker:always_reference | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| attacker:random_invalid | 0.174 | 0.017 | 0.104 | 0.274 | 0.021 | 0.132 | 0.066 | 0.115 | 0.097 | 0.000 | 0.000 |
| attacker:random_valid | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.149 | 0.851 |
| attacker:symbolic_alt | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |

## Generators / attackers (not models)

| attacker | B | A_norm | A_strict | C | FRR_norm | random-valid floor | final-state-only accepts |
|---|---|---|---|---|---|---|---|
| attacker:always_reference | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.831 | 1.000 |
| attacker:random_invalid | 0.000 | 0.000 | 0.000 | 0.000 | — | — | 0.542 |
| attacker:random_valid | 1.000 | 0.149 | 0.149 | 0.635 | 0.851 | 0.831 | 0.635 |
| attacker:symbolic_alt | 1.000 | 0.000 | 0.000 | 0.417 | 1.000 | 0.831 | 0.417 |
