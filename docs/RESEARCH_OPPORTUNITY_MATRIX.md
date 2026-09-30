# Research Opportunity Matrix

Ordinal scores (H / M / L) used **only to organize reasoning**; they do not predict acceptance, and the labels are not probabilities. Source data: `research/opportunity_matrix.csv` (generated from `research/candidate_ideas.json`).

**Score key (in order):** G research-gap strength; I scientific importance; M novel methodological content; C prior-art **collision risk** (H is bad); E evaluation clarity; R reproducibility; D data availability; F implementation feasibility; X cross-domain significance; P potential impact.

**Caveat:** the collision score reflects a partial search. A low collision score means "little found", not "nothing exists". Data availability reflects the corpus we hold; student-response data are UNKNOWN, so C01 and everything blocked on it scores L.

| ID | Candidate (short) | RAG? | Origin | G I M C E R D F X P | Label |
|---|---|---|---|---|---|
| C01 | Validated OS misconception inventory | no | LIT | H H L L H H L L M H | HIGH-RISK/HIGH-REWARD |
| C02 | Correctness audit of LLM OS explanations | no | LIT | M M L L H H M H M M | PROMISING |
| C03 | Executable checks vs judges vs NLI (injected errors) | no | LIT | M H M **H** H M M M M M | PROMISING |
| C04 | Claim-coverage audit | no | LIT | M M L L H H H H L M | PROMISING |
| C05 | Trace vs causal attribution on OS traces | no | LIT | M M M M H M M M M M | PARTIALLY CROWDED |
| C06 | Judge/metric validity on OS answers | no | LIT | M H L M H H M H M M | PROMISING |
| C07 | Faithfulness-abstention confound | yes | PROJECT | L M L M H H H H L L | WEAK |
| C08 | Noise/power audit of RAG-tutor papers | no | LIT | M M L M H H H H H M | WEAK |
| C09 | RAG factorial interaction study | yes | LIT | L M L M H H H H M M | PROMISING |
| C10 | GraphRAG vs vector, matched cost | yes | LIT | L M L **H** H M H M L L | PARTIALLY CROWDED |
| C11 | Misconception-conditioned retrieval (validated) | yes | LIT | M M M M H M L L L M | TOO HARD TO EVALUATE |
| C12 | Simulated students vs real OS distractors | no | LIT | M M M **H** H M L L M M | PARTIALLY CROWDED |
| C13 | Benchmark score vs learning gain | no | LIT | H H M L M L L L H H | TOO HARD TO EVALUATE |
| C14 | Guardrail components + delayed retention RCT | no | LIT | M H M **H** M L L L M H | HIGH-RISK/HIGH-REWARD |
| C15 | Perceived helpfulness vs learning | no | LIT | L M L **H** M L L L L L | TAKEN |
| C16 | Simulator-grounded generation vs post-hoc | yes | LIT | L M M **H** M M M M L L | WEAK |
| C17 | Robustness to plausible wrong passages | yes | LIT | L M L **H** H H H H M L | WEAK |
| C18 | Duplicate lecture versions | yes | PROJECT | L L L **H** H H H H L L | TAKEN |
| C19 | Abstention thresholds for tutors | yes | LIT | L M L **H** H H H M M L | PARTIALLY CROWDED |
| C20 | IRT calibration of LLM-authored items | no | LIT | L L L **H** M M M M L L | WEAK |
| C21 | LLM distractors vs real OS distributions | no | LIT | M M L **H** H M L L L L | PARTIALLY CROWDED |
| C22 | OS-state reasoning benchmark (human-authored) | no | LIT | M M L M H H M M M M | PROMISING |
| C23 | Length/position bias for tutor judges | no | LIT | L L L **H** H H H H M L | TAKEN |

**Counts:** 23 candidates; 15 not RAG-related (65%); 21 literature-derived, 2 project-anchored. Labels: PROMISING 6, PARTIALLY CROWDED 5, WEAK 5, TAKEN 3, HIGH-RISK/HIGH-REWARD 2, TOO HARD TO EVALUATE 2.

**What the matrix shows:**
- The candidates that are not heavily crowded and are evaluable cluster around **expert-labelled correctness of OS explanations** (C02, C04, C06, C03, C22): they share one asset, a human-authored OS question set with claim-level expert labels.
- Method-novelty candidates (a new architecture) all score high on collision risk; the surviving ones are evaluation or dataset contributions (Rule 11, Rule 12).
- The two candidates with the highest importance (C01, C13) have the lowest data availability and feasibility.
