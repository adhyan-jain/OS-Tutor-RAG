# SSR pilot results (llm)

## Decision (mechanical)

**CONDITIONAL** — K0-K3 passed; K4 and/or K5 inconclusive at this sample size

| K0 | K1 | K2 | K3 | K4 | K5 |
|---|---|---|---|---|---|
| pass | pass | pass | pass | FAIL | pass |

## Per model (world-clustered 95% CI; UNVERIFIABLE counts as not valid)

| model | B semantic | A_norm | A_strict | C | FRR_norm | FRR_strict | random-valid floor | UNVERIF |
|---|---|---|---|---|---|---|---|---|
| gemma2:9b | 0.170 [0.080, 0.281] | 0.024 [0.000, 0.073] | 0.010 [0.000, 0.031] | 0.125 [0.038, 0.233] | 0.857 [0.611, 1.000] | 0.939 [0.833, 1.000] | 0.900 | 0.045 |
| llama3.1:8b | 0.066 [0.035, 0.104] | 0.003 [0.000, 0.010] | 0.003 [0.000, 0.010] | 0.052 [0.024, 0.083] | 0.947 [0.800, 1.000] | 0.947 [0.800, 1.000] | 0.926 | 0.104 |
| mistral:7b-instruct | 0.076 [0.031, 0.132] | 0.017 [0.000, 0.042] | 0.007 [0.000, 0.017] | 0.066 [0.021, 0.118] | 0.773 [0.429, 0.971] | 0.909 [0.714, 1.000] | 0.939 | 0.194 |
| qwen3:8b | 0.309 [0.181, 0.441] | 0.132 [0.049, 0.229] | 0.090 [0.028, 0.160] | 0.219 [0.108, 0.340] | 0.573 [0.348, 0.807] | 0.708 [0.535, 0.882] | 0.866 | 0.049 |
| **pooled** | 0.155 [0.102, 0.215] | 0.044 [0.016, 0.078] | 0.028 [0.010, 0.049] | 0.115 [0.065, 0.174] | 0.715 [0.511, 0.891] | 0.821 [0.684, 0.928] | | 0.098 |

## FRR_norm by family and by variant (pooled over models)

| group | FRR_norm |
|---|---|
| family: banker | 0.954 [0.800, 0.991] |
| family: scheduling | 0.417 [0.167, 0.750] |
| family: sync | 0.622 [0.300, 0.914] |
| variant: v0 | 0.686 [0.395, 0.930] |
| variant: v1 | 0.667 [0.345, 0.921] |
| variant: v2 | 0.756 [0.524, 0.956] |

## FRR_norm by family × model

| family | gemma2:9b | llama3.1:8b | mistral:7b-instruct | qwen3:8b |
|---|---|---|---|---|
| banker | 1.000 [1.000, 1.000] | 0.917 [0.667, 1.000] | 0.875 [0.556, 1.000] | 1.000 [1.000, 1.000] |
| scheduling | — | — | — | 0.417 [0.167, 0.750] |
| sync | 0.767 [0.417, 1.000] | 1.000 [1.000, 1.000] | 0.500 [0.000, 1.000] | 0.489 [0.200, 0.818] |

## Semantic-validity rate B (and n valid outputs) by family × model

| family | gemma2:9b | llama3.1:8b | mistral:7b-instruct | qwen3:8b |
|---|---|---|---|---|
| banker | 0.198 (n=19/96) | 0.125 (n=12/96) | 0.167 (n=16/96) | 0.188 (n=18/96) |
| scheduling | 0.000 (n=0/96) | 0.000 (n=0/96) | 0.000 (n=0/96) | 0.250 (n=24/96) |
| sync | 0.312 (n=30/96) | 0.073 (n=7/96) | 0.062 (n=6/96) | 0.490 (n=47/96) |

## Sensitivity: UNVERIFIABLE counted as valid

| model | B_ub | FRR_norm_ub |
|---|---|---|
| gemma2:9b | 0.215 [0.111, 0.330] | 0.887 [0.682, 1.000] |
| llama3.1:8b | 0.170 [0.104, 0.240] | 0.980 [0.923, 1.000] |
| mistral:7b-instruct | 0.271 [0.160, 0.399] | 0.936 [0.843, 1.000] |
| qwen3:8b | 0.358 [0.219, 0.503] | 0.631 [0.448, 0.828] |
| **pooled** | 0.253 [0.172, 0.346] | 0.825 [0.718, 0.924] |

## Cheap proxies vs the oracle (K3; threshold fitted on other families)

| proxy | balanced agreement [95% CI] | accepts when oracle rejects | accepts when oracle accepts |
|---|---|---|---|
| distance | 0.703 [0.613, 0.797] | 0.131 | 0.536 |
| final_state_only | 0.643 [0.526, 0.748] | 0.457 | 0.743 |

## Do conclusions change? (24 worlds)

| pair | Δ A_norm | Δ B | p(A) Holm | p(B) Holm | reversed | stab | sig changes | stab | CI of evaluator effect on the gap |
|---|---|---|---|---|---|---|---|---|---|
| gemma2:9b|llama3.1:8b | +0.021 | +0.104 | 1 | 0.196 | False | 0.66 | False | 0.40 | [-0.163, -0.014] |
| gemma2:9b|mistral:7b-instruct | +0.007 | +0.094 | 1 | 0.196 | False | 0.57 | False | 0.48 | [-0.175, -0.019] |
| gemma2:9b|qwen3:8b | -0.108 | -0.139 | 0.0783 | 0.196 | False | 0.99 | False | 0.07 | [-0.052, +0.122] |
| llama3.1:8b|mistral:7b-instruct | -0.014 | -0.010 | 1 | 0.795 | False | 0.57 | False | 0.86 | [-0.049, +0.040] |
| llama3.1:8b|qwen3:8b | -0.128 | -0.243 | 0.0783 | 0.0138 | False | 1.00 | True | 0.10 | [+0.024, +0.212] |
| mistral:7b-instruct|qwen3:8b | -0.115 | -0.233 | 0.0783 | 0.0167 | False | 1.00 | True | 0.13 | [+0.024, +0.215] |

| model | share of A_norm-wrong outputs that are semantically valid | majority | stability |
|---|---|---|---|
| gemma2:9b | 0.149 | False | 0.00 |
| llama3.1:8b | 0.063 | False | 0.00 |
| mistral:7b-instruct | 0.060 | False | 0.00 |
| qwen3:8b | 0.204 | False | 0.00 |

Ranking by A_norm vs B: Kendall τ = 1.0, P(τ<1) = 0.71; A_norm ranks {'qwen3:8b': 1, 'gemma2:9b': 2, 'mistral:7b-instruct': 3, 'llama3.1:8b': 4}, B ranks {'qwen3:8b': 1, 'gemma2:9b': 2, 'mistral:7b-instruct': 3, 'llama3.1:8b': 4}

K4(i) reversal False; K4(ii) significance change False; K4(iii) failure profile False; adequate precision of 'no change': False

## Failure taxonomy (share of outputs)

| model | constraint:before | constraint:deadline | rule:idle_after_completion | rule:idle_while_ready | rule:incomplete | rule:mutual_exclusion_violation | rule:need_exceeds_work | rule:overlapping_segments | rule:policy_violation | rule:preempted_partial_burst | rule:preemption_or_rerun | rule:program_order_violation | rule:queue_order_violation | rule:repeated_process | rule:started_before_arrival | rule:wait_on_zero_semaphore | unknown_entity | unparseable | valid_canonical | valid_noncanonical |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma2:9b | 0.000 | 0.000 | 0.000 | 0.062 | 0.000 | 0.101 | 0.267 | 0.194 | 0.035 | 0.010 | 0.000 | 0.038 | 0.031 | 0.000 | 0.000 | 0.045 | 0.000 | 0.045 | 0.024 | 0.146 |
| llama3.1:8b | 0.000 | 0.000 | 0.003 | 0.156 | 0.003 | 0.062 | 0.278 | 0.108 | 0.038 | 0.007 | 0.000 | 0.094 | 0.010 | 0.000 | 0.003 | 0.066 | 0.094 | 0.010 | 0.003 | 0.062 |
| mistral:7b-instruct | 0.000 | 0.000 | 0.000 | 0.059 | 0.003 | 0.066 | 0.264 | 0.267 | 0.000 | 0.000 | 0.000 | 0.038 | 0.000 | 0.000 | 0.000 | 0.031 | 0.122 | 0.073 | 0.017 | 0.059 |
| qwen3:8b | 0.021 | 0.014 | 0.000 | 0.007 | 0.010 | 0.042 | 0.260 | 0.003 | 0.139 | 0.000 | 0.014 | 0.024 | 0.069 | 0.007 | 0.000 | 0.031 | 0.007 | 0.042 | 0.132 | 0.177 |

## Generators / attackers (not models)

| attacker | B | A_norm | A_strict | C | FRR_norm | random-valid floor | final-state-only accepts |
|---|---|---|---|---|---|---|---|
| attacker:always_reference | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.831 | 1.000 |
| attacker:random_invalid | 0.000 | 0.000 | 0.000 | 0.000 | — | — | 0.542 |
| attacker:random_valid | 1.000 | 0.149 | 0.149 | 0.635 | 0.851 | 0.831 | 0.635 |
| attacker:symbolic_alt | 1.000 | 0.000 | 0.000 | 0.417 | 1.000 | 0.831 | 0.417 |
