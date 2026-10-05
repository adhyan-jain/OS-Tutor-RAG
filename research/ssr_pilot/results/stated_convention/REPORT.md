# SSR Pilot Stated-Convention Arm Results & Comparison

## Summary & Decision Note

**Decision Note:** **A) phenomenon survives convention disclosure**

- **Pooled FRR (original baseline):** 0.715 [0.511, 0.891]
- **Pooled FRR (stated-convention arm):** 0.625 [0.443, 0.816]
- **Change in Pooled FRR:** -0.090
- **Newly Canonical-Accepted outputs ($A_{norm}$):** 33 / 1152
  - Of which were already semantically valid ($B$) under original pilot: 10
- **Newly Semantically Accepted outputs ($B$):** 58 / 1152

## Mechanical Criteria (K0-K5) Comparison

| Criterion | Original Pilot | Stated-Convention Arm |
|---|---|---|
| **K0** | PASS | PASS |
| **K1** | PASS | PASS |
| **K2** | PASS | PASS |
| **K3** | PASS | PASS |
| **K4** | FAIL | PASS |
| **K5** | PASS | PASS |

## Per-Model Metrics (Original vs Stated-Convention)

| Model | Arm | B (Semantic) | A_norm | A_strict | C | FRR_norm | UNVERIF |
|---|---|---|---|---|---|---|---|
| **gemma2:9b** | Original | 0.170 [0.080, 0.281] | 0.024 [0.000, 0.073] | 0.010 [0.000, 0.031] | 0.125 [0.038, 0.233] | 0.857 [0.611, 1.000] | 0.045 |
| | Stated-Conv | 0.222 [0.111, 0.347] | 0.066 [0.017, 0.122] | 0.035 [0.010, 0.066] | 0.156 [0.062, 0.267] | 0.703 [0.491, 0.894] | 0.021 |
| **llama3.1:8b** | Original | 0.066 [0.035, 0.104] | 0.003 [0.000, 0.010] | 0.003 [0.000, 0.010] | 0.052 [0.024, 0.083] | 0.947 [0.800, 1.000] | 0.104 |
| | Stated-Conv | 0.090 [0.052, 0.132] | 0.003 [0.000, 0.010] | 0.000 [0.000, 0.000] | 0.059 [0.031, 0.090] | 0.962 [0.863, 1.000] | 0.080 |
| **mistral:7b-instruct** | Original | 0.076 [0.031, 0.132] | 0.017 [0.000, 0.042] | 0.007 [0.000, 0.017] | 0.066 [0.021, 0.118] | 0.773 [0.429, 0.971] | 0.194 |
| | Stated-Conv | 0.031 [0.007, 0.066] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.031 [0.007, 0.066] | 1.000 [1.000, 1.000] | 0.167 |
| **qwen3:8b** | Original | 0.309 [0.181, 0.441] | 0.132 [0.049, 0.229] | 0.090 [0.028, 0.160] | 0.219 [0.108, 0.340] | 0.573 [0.348, 0.807] | 0.049 |
| | Stated-Conv | 0.267 [0.149, 0.403] | 0.160 [0.066, 0.271] | 0.090 [0.021, 0.174] | 0.208 [0.101, 0.340] | 0.403 [0.228, 0.625] | 0.056 |
| **Pooled** | Original | 0.155 [0.102, 0.215] | 0.044 [0.016, 0.078] | 0.028 [0.010, 0.049] | 0.115 [0.065, 0.174] | 0.715 [0.511, 0.891] | 0.098 |
| | Stated-Conv | 0.153 [0.095, 0.217] | 0.057 [0.022, 0.099] | 0.031 [0.011, 0.055] | 0.114 [0.060, 0.176] | 0.625 [0.443, 0.816] | 0.081 |

## FRR_norm by Mechanism Family

| Family | Original | Stated-Convention |
|---|---|---|
| **banker** | 0.954 [0.800, 0.991] | 0.837 [0.719, 1.000] |
| **scheduling** | 0.417 [0.167, 0.750] | 0.423 [0.190, 0.789] |
| **sync** | 0.622 [0.300, 0.914] | 0.574 [0.322, 0.870] |

## FRR_norm by Surface Variant

| Variant | Original | Stated-Convention |
|---|---|---|
| **v0** | 0.686 [0.395, 0.930] | 0.543 [0.294, 0.793] |
| **v1** | 0.667 [0.345, 0.921] | 0.702 [0.489, 0.909] |
| **v2** | 0.756 [0.524, 0.956] | 0.627 [0.375, 0.897] |

## Failure Taxonomy Shift

Share of outputs by classification category:

| Category | Original Baseline | Stated-Convention |
|---|---|---|
| constraint:before | 0.005 | 0.003 |
| constraint:deadline | 0.003 | 0.007 |
| rule:idle_after_completion | 0.001 | 0.001 |
| rule:idle_while_ready | 0.071 | 0.071 |
| rule:incomplete | 0.004 | 0.008 |
| rule:mutual_exclusion_violation | 0.068 | 0.064 |
| rule:need_exceeds_work | 0.267 | 0.287 |
| rule:overlapping_segments | 0.143 | 0.135 |
| rule:policy_violation | 0.053 | 0.053 |
| rule:preempted_partial_burst | 0.004 | 0.007 |
| rule:preemption_or_rerun | 0.003 | 0.000 |
| rule:program_order_violation | 0.049 | 0.052 |
| rule:queue_order_violation | 0.028 | 0.026 |
| rule:ran_past_quantum_or_burst | 0.000 | 0.003 |
| rule:repeated_process | 0.002 | 0.001 |
| rule:started_before_arrival | 0.001 | 0.001 |
| rule:wait_on_zero_semaphore | 0.043 | 0.046 |
| rule:wrong_burst_length | 0.000 | 0.002 |
| unknown_entity | 0.056 | 0.049 |
| unparseable | 0.043 | 0.031 |
| valid_canonical | 0.044 | 0.057 |
| valid_noncanonical | 0.111 | 0.095 |
