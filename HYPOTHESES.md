# Open Hypotheses

Standing list of things believed but not yet measured, with what would settle
each. Confirmed and refuted entries move to FINDINGS.md; this file is the queue.

Written 2026-07-26 from the trends visible after six of eight focused-sweep
variants. Status values: **open**, **testing**, **confirmed**, **refuted**.

---

## Tier 1 — targets the metrics that are actually weak

### H1. Multi-query's advantage grows with more variants
**status: open**

Multi-query is the single largest gain measured (+0.032 composite, +0.033
answer_correctness) and it works by covering more phrasings of the question.
`num_query_variants` is 3. If the mechanism is coverage, 5 should beat 3, with
diminishing returns after.

*Test:* retrieval harness at 3 / 5 / 7 variants, then RAGAS on the best.
*Falsified if:* recall and full_recall are flat or fall from 3 to 5, which
would mean the gain comes from something other than coverage.

### H2. HyDE and multi-query stack
**status: testing** (variants 7-8 of the focused sweep)

They contribute independently (+0.012 and +0.032) through different mechanisms
-- breadth against precision -- so their gains may add.
*Falsified if:* the combination scores at or below the better parent, meaning
the two query transformations interfere.

### H3. Query decomposition beats reformulation on multi-part questions
**status: open**

17 of 26 questions are multi-part. Multi-query *reformulates* the whole
question; decomposition would *split* it and retrieve per sub-question. For
"what is X, and what does Y do", reformulation still embeds both halves
together and biases toward whichever dominates.

*Test:* implement decomposition as a retriever wrapper, compare full_recall
against multi-query on the 17 multi-part questions specifically.
*Falsified if:* full_recall does not improve on that subset.

### H4. Prompting for part-coverage converts partial retrieval into partial credit
**status: open**

The prompt currently offers a binary: answer, or say the context does not
contain the answer. A4 case 2 found the model going off-script -- answering the
half it had, flagging the gap, then filling the rest from its own knowledge,
which is a faithfulness risk. An explicit instruction to address each part and
name what is missing should raise answer_correctness on multi-part questions
without costing faithfulness.

*Test:* A/B the prompt on the current best config.
*Falsified if:* answer_correctness is flat, or faithfulness drops.

---

## Tier 2 — measurement quality

### H5. Ground truth is systematically less complete than the corpus
**status: open, and the largest single correctness lever**

Two worked cases: an answer scoring 0.61 listed process states (zombie,
terminated) that the corpus teaches and the reference omitted, and one scoring
0.56 was content-identical to its reference but split one bullet in two. Both
lose points as false positives.

*Test:* rewrite ground-truth answers from the cited sources, then re-measure.
*Caution:* this changes the benchmark, so it must not be compared across the
boundary (see A11's method note). Do it once, deliberately, and re-baseline.
*Falsified if:* answer_correctness does not move after references are completed.

### H6. A stronger judge tightens every number
**status: open**

`qwen2.5:7b` performs statement-level entailment for answer_correctness and
entity extraction for context_entity_recall, and A15 showed the latter failing
outright. A larger judge should reduce variance and correct systematic
strictness.

*Test:* re-judge stored answers with a different local model, or GPT-4o-mini
(~$0.26 by this project's own token accounting).
*Falsified if:* scores shift uniformly rather than differentially -- that would
mean the judge is a constant offset, not a source of error.

### H7. `context_entity_recall` should leave the composite
**status: effectively confirmed by A15, not yet acted on**

Half of the `completeness` composite is a metric that scored 0/7 on a question
whose context contained all seven entities. Replacing it with `full_recall`
from the retrieval harness -- which is exactly measured, not LLM-extracted --
would make the composite mean what it claims.

---

## Tier 3 — worth trying, weaker priors

### H8. Blending reranker scores beats replacing them
**status: open** (`eval/reranker_eval.py` written, never run)

Reranking now measures positive (A14 correction), but it discards the
retriever's scores entirely. Dense reaches recall@5 1.000, so its ranking
carries real signal; a weighted blend should beat either alone.
*Test:* the blend weights already implemented in `reranker_eval.py`.

### H9. A newer reranker beats bge-reranker-large
**status: open** (`bge-reranker-v2-m3`, `ms-marco-MiniLM-L-6-v2` downloaded)

### H10. Adjacent-slide expansion helps topics that span slides
**status: open**

Several multi-part questions cite consecutive slides (`slide10` + `slide11`).
Expansion currently returns the matched slide only; including its neighbour
would cover the pair from a single hit.
*Falsified if:* full_recall does not improve, or the added tokens cost more
than the coverage gains.

### H11. Generation temperature affects correctness
**status: open**

Currently 0.2. Lower would make answers more deterministic and possibly closer
to reference phrasing; the F1-style metric may reward that. Cheap to test,
weak prior.

---

## Explicitly not pursuing

- **Prompting for terser answers.** It would raise answer_correctness by
  suppressing correct extra facts (A13's mechanism in reverse). That optimises
  the metric against the student's interest.
- **A different embedding model.** recall@5 is saturated at 1.000; there is
  nothing to win.
- **Further chunking changes.** Refuted twice (A6, A9); the current design is
  validated.
- **`llm_rerank`.** Pointwise scoring per candidate, and the cheaper
  cross-encoder already covers the stage.
