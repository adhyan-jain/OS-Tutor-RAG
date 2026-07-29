# Engineering Findings Log

Running record of defects found in this pipeline, how each was diagnosed, and
what the fix changed. Written to support a formal case study, so every claim
here is tied to a measurement rather than an impression.

**Convention:** each finding states the symptom, the actual cause, the fix, and
the measured effect. Where a hypothesis was tested and *refuted*, that is
recorded too -- the refutations are as informative as the confirmations.

---

## Session 1 — 2026-07-26

Context: a 84-variant evaluation sweep was underway to compare retrieval
techniques. It was stopped at 43/84 once it became clear the sweep was
measuring artifacts of its own defects rather than properties of the
techniques.

### The headline finding

**A chunking defect was masquerading as a retrieval-technique result.**

BM25 appeared to be dramatically the worst retrieval technique
(`answer_correctness` 0.509 against dense 0.616, HyDE 0.707). The real cause
was that slide titles were being indexed as standalone chunks. Twelve of the
81 slides have titles phrased as questions ("What is an operating system?",
"So, what does the OS do?"), and as standalone chunks these are near-perfect
lexical matches for a user's question while containing no answer. BM25 ranked
them first, the model received five headings, and correctly reported that its
context contained no answer.

Every downstream comparison inherited this. The "BM25 is bad at semantic
retrieval" conclusion was really "our chunker emits question-shaped decoys and
lexical retrieval finds them."

### F1 — Slide titles indexed as standalone chunks

- **Symptom:** BM25 far worse than dense on every generation metric; high
  refusal rate (11.7% for BM25 vs 3.8% for dense).
- **Cause:** `_chunk_pptx` built `parent_parts = [title, *bullets]` and emitted
  one chunk per element, so the title became its own ~28-character chunk.
- **Fix:** titles are never indexed alone. Every bullet child is prefixed with
  its slide title, and title-only divider slides carry their heading forward
  onto the next slide with content.
- **Measured:** bare question-shaped chunks 12 → 0. PPTX child length 53 → 91
  chars. The question BM25 previously refused now answers correctly.

### F2 — `parent_text` recorded but never read

- **Symptom:** model frequently answered "the context doesn't contain the
  answer" even when retrieval had surfaced the right slide.
- **Cause:** `structure_aware` chunking stored each child's containing slide as
  `parent_text`, and its docstring described generation expanding a child back
  out to it -- but no code ever read the field. Generation received the bare
  ~50-character child.
- **Fix:** `src/context_expansion.py`, applied after retrieval, reranking and
  diversification have finished selecting, so matching stays precise and only
  what reaches the LLM widens. Children sharing a parent collapse to one copy.
- **Measured:** context 42 → 282 chars/chunk on the failing example, and the
  ground-truth answer appeared in the context for the first time.

### F3 — Parent expansion cost is asymmetric by format

- **Symptom:** enabling F2 raised context from 149 to 1137 tokens per question.
- **Investigated because** the intuition was that slide decks would be the
  expensive format. **That intuition was wrong.**
- **Measured:** slide parents are ~72 tokens against a 13-token child (5.3x);
  PDF page parents are ~534 tokens, max 913, against a 48-token child (11.0x).
  Expanding decks is nearly free; expanding pages is what inflates the prompt.
- **Fix:** `max_parent_tokens` (default 250). Parents within the cap are
  substituted whole; larger ones are windowed *around the matched child* rather
  than truncated from the top, which would often cut the matched passage out.
- **Measured:** 1137 → 484 tokens/question, a 57% reduction, with slides intact.

### F4 — PDFs chunked across page boundaries

- **Cause:** PDFs were semantically chunked over the concatenated document
  text, ignoring the `pages` metadata the extractor already produced, so a
  chunk could begin mid-topic on one page and end on the next.
- **Fix:** new `page_aware` strategy -- semantic grouping bounded by the page,
  with the page as parent.

### F5 — Chunking was the wrong thing to sweep

- **Symptom:** the sweep varied chunking strategy as an axis (mixed /
  structure_aware / semantic forced across all types).
- **Cause:** forcing one strategy across every source type compares *formats*,
  not strategies. Semantic chunking a slide deck collapsed 51 chunks into 6
  (avg 457 chars) because slide bullets carry no sentence punctuation to split
  on -- a degenerate configuration, not a fair comparison.
- **Fix:** chunking is now matched to each source type and is no longer an
  axis. Sweep 84 → 28 variants.

### F6 — Excel sheet-name collisions

- **Symptom:** none yet -- caught before the run reached the affected variants.
- **Cause:** per-variant sheet names were truncated to Excel's 31-character
  limit without dedup.
- **Measured:** 25 of 84 variant names collided, which would have corrupted or
  crashed the details workbook mid-run.
- **Fix:** numeric prefix guarantees uniqueness; the untruncated name remains
  in each sheet's `config` column.

### F7 — Judge tokens were never counted

- **Symptom:** `llm_calls=1 (gen=1, judge=0)` despite all seven metrics scoring.
- **Cause:** the tracker wrapped `ChatOllama._generate`, but RAGAS reaches the
  judge through `LangchainLLMWrapper.agenerate_text` -- the async path.
- **Impact:** the entire evaluation-side cost column would have reported zero.
- **Fix:** wrap `_agenerate` as well. Judge calls now record 16-21 per question.

### F8 — Models reloaded on every call

- **Cause:** `SentenceTransformer(name)` reloads weights on every construction
  (~5s for bge-large) and does no caching of its own. MMR constructed one *per
  query*; semantic chunking *per document*.
- **Fix:** process-wide model cache, plus memoization of chunks and corpus
  embeddings on exactly the inputs that change their output.
- **Measured:** semantically chunking one PDF 115.8s → 0.0s when cached; ingest
  across the sweep 3+ min → 0.1-0.3s per variant after the first.

### F9 — torch and Ollama contending for one 8GB GPU

- **Symptom:** generation at 25.8s/call; later a hard `CUDA out of memory` that
  killed a variant.
- **Cause:** torch holding ~1.5GB of VRAM pushed Ollama into CPU offload.
- **Measured:** with the GPU free, llama3 runs at 2.0s/call (45.7 tok/s) --
  a 13x difference attributable purely to contention.
- **Fix:** embedding models default to CPU; `OS_RAG_EMBEDDING_DEVICE=cuda`
  gives fast ingest and releases the card before the generation pass.

### F10 — `CrossEncoder` re-pinning itself to the GPU

- **Symptom:** OOM warnings returned after F9 was believed fixed; generation
  back to ~12s/question.
- **Cause:** `CrossEncoder.predict()` re-issues
  `self.model.to(self._target_device)` on *every call*, so moving the module to
  CPU was undone at the next rerank.
- **Fix:** set `_target_device` alongside the module.
- **Measured:** VRAM 1341MB → 0MB, and **still 0MB after a `predict()`**, which
  is the condition that previously failed.

### F11 — A curriculum document was silently missing

- **Cause:** only `.pptx/.docx/.pdf` are handled; `Shell programming - sample
  excersice.doc` is the legacy binary format and was skipped without error.
- **Fix:** converted via LibreOffice.
- **Measured:** 9,005 chars across 13 sections recovered; corpus 9 → 22
  Documents.

### F12 — The golden QA set measured the wrong thing

- **Cause:** the original 10 questions were written from general OS knowledge,
  so ground truth used wording absent from the corpus ("I/O devices" where the
  slide says "IO devices"), penalising retrieval for a phrasing mismatch. Its
  `source_chunk_ids` also pointed at chunk *indices*, which re-chunking had
  already invalidated.
- **Fix:** 26 questions, 5-6 per topic, each answerable from a named slide and
  phrased in that slide's own terms. Questions are deliberately worded *unlike*
  their source slide's title, so a retriever cannot win by matching the heading.
  Citations moved to `source_parent_ids` (slide identity is stable across
  re-chunking; chunk numbering is not). All 30 cited parents verified present.

### F13 — Selection stages had nothing to select from

- **Symptom:** MMR appeared mildly harmful (0.590 vs 0.609).
- **Cause:** retrieving `top_k=10`, reranking to 5, then asking MMR for 5 left
  MMR choosing 5 from 5 -- it could only reorder, never diversify. Reranking
  likewise chose 5 from 10.
- **Fix:** the pipeline sizes each stage from what follows it. With both
  enabled the chain is now `30 → rerank 10 → mmr 5`.
- **Note:** costs no extra LLM calls -- generation and the metrics only ever see
  the final selection. The one exception is `llm_rerank`, which scores every
  candidate.
- **Consequence:** the earlier MMR and reranking conclusions were invalid and
  were discarded.

---

### F15 — PPTX tables were never indexed

- **Cause:** `extract_ppt` collected text only from shapes with a text frame.
  A PowerPoint table has no text frame -- its content lives in
  `shape.table` -- so every table was skipped without error.
- **Measured:** slide text 19,268 → 23,147 characters once tables are read, a
  **20.1% increase**. Seven tables across the decks.
- **What was missing:** the shell operator reference tables -- arithmetic,
  relational and assignment operators with descriptions and worked examples
  (`-eq | Checks if two operands are equal | [ $a -eq $b ] is not true`).
  Precisely the material a beginner looks up.
- **Fix:** each table row becomes one bullet with its cells joined, so a row's
  fields stay together as one retrievable unit rather than scattering.
- **Same class as F11** (the `.doc` skipped for its extension): content absent
  from the index, failing silently, invisible to every downstream metric
  because the questions asked happened not to need it.
- **Effect on scores: not yet measured** -- an A/B against the winning config
  is running.

### F16 — Speaker notes: checked, none present

Slide notes are captured into metadata by `extract_ppt` but never chunked, so
they looked like a second instance of F15. Measured before recommending:
**0 of 81 slides carry speaker notes**, so there is nothing to recover. Noted
because the same gap would matter on a deck that does use them.

## Analytical findings (not defects)

### A1 — `faithfulness` rewards refusal

When retrieval fails, the model answers "the context doesn't contain the
answer". That makes **zero unsupported claims**, so faithfulness scores 1.00
while `answer_correctness` collapses to ~0.1-0.2.

Measured across techniques, refusal rate tracked correctness far better than
faithfulness did:

| technique | refusal rate | faithfulness | answer_correctness |
|---|---|---|---|
| hyde | 5.0% | 0.883 | 0.707 |
| dense | 3.8% | 0.813 | 0.616 |
| hybrid_rrf | 12.5% | 0.872 | 0.649 |
| bm25 | 11.7% | 0.828 | 0.509 |

Note dense has the *lowest* faithfulness yet the second-highest correctness.
**A pipeline that refuses everything scores a perfect 1.0 on faithfulness.** It
is a hallucination guardrail, not a quality measure, and must never be used to
rank configurations on its own.

### A2 — Faithfulness is nearly independent of correctness

Correlation with `answer_correctness` over 78 question-runs:

| metric | r |
|---|---|
| context_recall | +0.409 |
| context_precision | +0.386 |
| context_entity_recall | +0.242 |
| answer_relevancy | +0.163 |
| **faithfulness** | **+0.092** |

Faithfulness grades the *generator*; correctness grades the *whole pipeline*
and is gated by retrieval. The generator is not the bottleneck -- retrieval is:

```
questions with entity_recall <0.35  (n=34) → answer_correctness 0.578
questions with entity_recall >=0.60 (n=23) → answer_correctness 0.717
```

Same model, same prompt; a 0.14 correctness swing driven purely by whether the
ground truth's entities reached the context. `context_entity_recall` averages
0.440, so over half the ground-truth entities never reach the prompt.

### A3 — Refuted: output verbosity does not depress correctness

Hypothesised that llama3's preamble ("According to the context...") and hedging
caveats were being counted as spurious claims and lowering
`answer_correctness`. **Tested and refuted:**

| | with | without |
|---|---|---|
| preamble | 0.664 (n=72) | 0.462 (n=6) |
| hedging caveat | 0.643 (n=9) | 0.649 (n=69) |
| shortest third (180 chars) | 0.659 | |
| longest third (616 chars) | 0.696 | |

Longer answers score *higher*. Output style is not the problem; retrieval
recall is (see A2).

### A5 — Retrieval measured directly, without an LLM in the loop

`eval/retrieval_eval.py` scores retrieval against the golden set's
`source_parent_ids`: for each question, did the retriever surface the slide the
question is answerable from? No generation, no judging, so a configuration is
scored in seconds rather than the ~30 minutes a RAGAS variant costs. Results
over 26 questions, 22 documents:

| config | R@1 | R@3 | R@5 | R@10 | full@5 | MRR |
|---|---|---|---|---|---|---|
| current + dense | 0.731 | 0.846 | **0.923** | **1.000** | 0.731 | 0.816 |
| current + hybrid_rrf | 0.462 | 0.692 | 0.846 | 0.885 | 0.692 | 0.613 |
| current + bm25 | 0.385 | 0.462 | 0.500 | 0.577 | 0.423 | 0.435 |
| slide_level + dense | 0.269 | 0.385 | 0.577 | 0.654 | 0.500 | 0.389 |
| slide_level + bm25 | 0.308 | 0.385 | 0.423 | 0.462 | 0.385 | 0.356 |
| slide_level + hybrid_rrf | 0.269 | 0.423 | 0.462 | 0.577 | 0.423 | 0.370 |

Three consequences:

**Dense retrieval already achieves perfect recall at 10** but the pipeline
passes only 5 contexts to generation, and R@5 is 0.923. For roughly two
questions the correct slide *is* retrieved and then discarded by reranking or
MMR before the model ever sees it. Raising the final context count recovers
information the system has already found.

**BM25's weakness is real, not an artifact of the chunking defect.** It fails to
surface the right slide half the time (R@5 0.500). The original conclusion
survives the fix; what changed is that the cause is now measurable directly
rather than inferred from downstream answer quality.

**Fusing a strong retriever with a weak one hurts.** `hybrid_rrf` (0.846)
underperforms plain `dense` (0.923) because reciprocal rank fusion gives BM25's
poor rankings equal weight. Worth either weighting the fusion or dropping the
sparse arm on this corpus.

### A6 — Refuted: slide-level chunking does not improve retrieval

Hypothesised that `structure_aware`'s ~13-token children were too short to
embed well, and that indexing whole slides (~72 tokens) would retrieve better.
**Tested and refuted:** dense R@5 fell from 0.923 to 0.577.

A whole slide's embedding averages over five or six unrelated bullets and is
therefore *less* discriminative than a single focused bullet. Fine-grained
children match better precisely because they are narrow. This is direct
evidence for the small-to-big design: match on small children, generate from
their parents. `slide_level` was removed.

Note also the framing error that produced the hypothesis: the problem with a
short chunk is how little *information* it carries, not the encoder's capacity.
A larger embedding model cannot recover meaning that is absent from the text,
and a smaller one (bge-small) would be strictly worse -- bge-large is the
better model in that series on every published benchmark.

### F14 — MMR re-embedded its candidates on every query

- **Symptom:** any MMR-enabled evaluation was disproportionately slow; a
  17-configuration tuning grid failed to complete a single configuration in 25
  minutes.
- **Cause:** `mmr_select` called `model.encode()` on its candidates per query.
  The candidates come from a fixed corpus, so the same few hundred chunk texts
  were re-embedded once per question, for every configuration.
- **Measured:** ~32s to embed ten candidates, repeated for all 26 questions of
  every configuration.
- **Fix:** `encode_cached()` memoizes embeddings on (model, text), which is
  sound because embeddings are deterministic given those two.
- **Measured after:** 33.04s → 0.0001s for a repeated batch, with identical
  vectors; a batch of 5 cached plus 3 new costs only the 3 new.
- **Noted but deferred earlier** in favour of not restarting a running sweep;
  revisited when it became the bottleneck for a different experiment.

### A4 — Refusals have distinct causes needing distinct fixes

Examining the surviving refusals individually showed three different
situations, only one of which is a refusal at all:

1. **Genuine retrieval miss** — the PCB slide was never retrieved. No prompt
   change can fix this; the content never reached the model.
2. **Partial retrieval** — a two-part question retrieved the slide covering one
   half. The model answered that half, flagged the gap, then filled the rest in
   from parametric knowledge (a faithfulness risk, not a refusal).
3. **False positive in measurement** — a correct answer containing a caveat
   phrase matched a naive refusal regex.

Measuring "refusal rate" by keyword therefore over-counts, and the three cases
need retrieval recall, better multi-aspect coverage, and a better detector
respectively.

---

## Method notes worth carrying forward

- **Library defaults reassert themselves silently.** Three separate defects
  (F8, F7, F10) were of this shape: `SentenceTransformer` not caching, RAGAS
  routing through the async path, `CrossEncoder` re-pinning its device. None
  were visible in our code; all surfaced only under measurement.
- **Measure before prescribing.** A3 records a plausible hypothesis that the
  data refuted, and F3 records an intuition about which format was expensive
  that was exactly backwards.
- **Interleaving two models on one small GPU is pathological.** Generating all
  answers first and scoring afterwards cut model swaps from ~2/question to
  2/run.

---

## Run history

| run | scope | outcome |
|---|---|---|
| v1 | 84 variants x 5 questions, original chunking | stopped at 43/84; conclusions invalidated by F1, F2, F13. Preserved at `eval/_baseline_prefix_run/` as a before/after artifact -- **not comparable to later runs, do not merge** |
| v2 | 28 x 26, post-fix | stopped at variant 1; F10 discovered (GPU contention) |
| v3 | 28 x 26, post-fix | in progress from 14:20 IST, ~28 min/variant |

### v3 first result vs the v1 baseline

Not a controlled comparison -- the question set is harder (26 slide-grounded
questions worded unlike their headings, versus 10 generic ones) and chunking
differs. Recorded because the direction is informative:

| metric | v1 (dense) | v3 (dense+cross_encoder+mmr) |
|---|---|---|
| faithfulness | 0.813 | 0.906 |
| answer_correctness | 0.616 | 0.634 |
| context_precision | 0.708 | 0.763 |
| context_recall | 0.861 | 0.880 |
| context_entity_recall | 0.485 | 0.448 |
| refusal rate | 3.8-11.7% | 3.8% |

Up on most axes *despite* the harder question set. `context_entity_recall` fell
slightly, consistent with the new ground truth naming more specific entities.

---

### A7 — Reranking measures *worse* than omitting it

Across the four dense configurations completed in sweep v3, the cross-encoder
costs about 0.05 of `answer_correctness`, consistently and in both MMR
settings:

| configuration | faithfulness | answer_correctness |
|---|---|---|
| dense + none + mmr | 0.883 | **0.685** |
| dense + none, no mmr | 0.901 | **0.681** |
| dense + cross_encoder + mmr | 0.906 | 0.634 |
| dense + cross_encoder, no mmr | 0.967 | 0.626 |

There is a mechanism for this rather than only a correlation: dense retrieval
already reaches recall@5 of 0.923 (A5), so the reranker is reordering an
already-good ranking, and `bge-reranker-large` is a general-purpose model with
no advantage on this domain over bge-large's own similarity. Reordering a good
ranking can only help if the reranker is the better judge.

Also visible: MMR flipped sign after the pool fix (F13), from mildly harmful to
mildly helpful (+0.008, +0.004) -- small enough to be noise, but consistent
with the earlier negative result having been an artifact of MMR selecting five
candidates from five.

**Status: n=4 configurations. Suggestive, not settled** -- the remaining 24
variants of sweep v3 will confirm or refute it.

### A8 — Why wrong chunks outrank right ones (three causes, one defect)

recall@1 is 0.731 while recall@5 is 0.923, so for a quarter of questions
something the question is *not* answerable from scores above something it is.
`eval/rank_diagnosis.py` dumps the competing chunks rather than inferring from
aggregates. Over 26 questions searching the top 20:

```
first correct chunk at rank 1 : 19
rank 2-5                      : 4
rank 6-20                     : 3
never found in top 20         : 0
median rank of first correct  : 1
distractors by source type    : pptx 19, pdf 9
median distractor tokens      : 20  (corpus median 19)
```

**Two plausible hypotheses were refuted by this.** PDF prose was *not* drowning
the slides (most distractors are pptx), and distractors were *not*
systematically longer than the corpus (20 tokens against a median of 19).
Retrieval is in fact good: median rank 1, and the answer is always inside the
top 20.

The failures decompose into three causes, only the first of which is a defect:

**A8a — sibling chunks monopolise the top-k.** For "show the syntax for
creating a shell variable", the top four results were all children of
`Shell programming__slide35`:

```
#1 [slide35] echo "Process ID of shell = $$"
#2 [slide35] $ ./special.sh arg1 arg2 arg3
#3 [slide35] echo "Complete list of arguments = $*"
#4 [slide35] # special.sh
```

One slide consumed every slot. Parent expansion later collapses them to a
single context, which is why five requested contexts yielded only 3.5 distinct
ones. Retrieval slots are being spent on near-duplicates, so genuinely
different sources never get considered. This is the actionable defect:
deduplication needs to happen at *selection* time, not only after.

**A8b — questions use vocabulary absent from the corpus.** "Where is
per-process *bookkeeping* kept?" -- the word never appears; the slide says
"process control block". The retriever matched "kernel" against "kernel stack"
instead. A deliberate paraphrase (the eval set is written to avoid echoing
slide titles), so this is question difficulty rather than a bug, but it caps
what retrieval can achieve.

**A8c — the ground truth under-credits correct retrievals.** For "trace the
sequence of calls a command-line interpreter makes", rank 1 was
`process API__page6`: *"It shows you a prompt and then waits for you to type
something into it..."* -- which genuinely answers the question. The eval set
cites only the slide, so a correct retrieval is scored as a miss. The corpus
covers the same material in both slides and PDF chapters; ground truth that
names only one source systematically understates retrieval quality.

### A9 — Refuted: capping siblings per parent does not improve retrieval

A8a established that sibling chunks monopolise the ranking, and capping how
many chunks one parent may contribute was implemented to recover those slots.
It works mechanically and changes nothing that matters:

| config | hit | full | contexts | tokens |
|---|---|---|---|---|
| no cap, k=5 | 0.885 | 0.692 | 3.5 | 379 |
| cap=1, k=5 | 0.885 | 0.692 | **5.0** | 579 |
| cap=2, k=5 | 0.885 | 0.692 | 4.1 | 436 |
| cap=3, k=5 | 0.885 | 0.692 | 3.7 | 393 |
| no cap, k=8 | 0.962 | 0.769 | 5.7 | 702 |
| cap=1, k=8 | 0.962 | **0.808** | 8.0 | 1006 |

Distinct contexts rise from 3.5 to 5.0 exactly as intended, and hit rate is
unchanged to three decimals at every cap.

**Why the diagnosis did not imply the fix:** MMR already selects for
dissimilarity, so it was discarding most siblings before they reached the final
contexts. The wasted slots were real in the *raw* retrieval but had largely
been absorbed by the time it mattered. Diagnosing a genuine inefficiency is not
the same as identifying the binding constraint.

Raising the final context count beats capping on both axes:

```
no cap, k=10 : hit 1.000, full 0.808,  922 tokens
cap=1,  k=8  : hit 0.962, full 0.808, 1006 tokens
```

The cap is retained but disabled by default; it may still pay off on a corpus
with no diversification stage. The binding constraint on hit rate is A8b and
A8c -- vocabulary the corpus does not contain, and ground truth that names one
source where the corpus provides two -- neither of which diversity can address.

### A10 — MMR costs recall; every refinement stage measures worse than omitting it

Prompted by an observation that settles A8a/A9 from the other direction: if
sibling crowding were the binding constraint, MMR exists precisely to fix it
and should therefore win clearly. It does not, which is itself evidence that
crowding is not what is limiting retrieval.

Measuring MMR directly against no diversification, dense retrieval, no
reranking:

| config | hit | full | contexts |
|---|---|---|---|
| mmr off, k=5 | 0.885 | 0.692 | 3.4 |
| mmr on, k=5 | 0.885 | 0.692 | 3.5 |
| mmr off, k=8 | **1.000** | **0.808** | 5.5 |
| mmr on, k=8 | 0.962 | 0.769 | 5.7 |
| mmr off, k=10 | **1.000** | **0.846** | 6.8 |
| mmr on, k=10 | 1.000 | 0.808 | 7.3 |

MMR is not neutral, it is negative: it drops a correct slide at k=8 and costs
breadth at k=10, trading relevance for a diversity this corpus does not need.

Two corrections follow. **k=8 without MMR already reaches hit 1.000**, so the
earlier conclusion that k=10 was required was an artifact of measuring with MMR
enabled. And **A7's reading of MMR as "mildly helpful" was wrong**: the +0.004
on answer_correctness was noise, and the retrieval-level measurement is
sensitive enough to show the true sign. Downstream answer metrics at n=26
cannot resolve differences this small; retrieval metrics can.

Taken together, every post-retrieval refinement stage measures worse than
leaving it out:

| stage | measured effect |
|---|---|
| cross-encoder reranking | -0.05 answer_correctness (A7) |
| MMR diversification | -0.038 hit@8 (A10) |
| per-parent capping | no effect (A9) |
| BM25 fusion in hybrid_rrf | -0.077 recall@5 vs dense (A5) |

The pipeline that wins is the simplest one: dense retrieval, parent expansion,
nothing in between. This is worth stating plainly in the write-up -- the
components were added on the reasonable assumption that they help, and
measurement says otherwise for this corpus.

### A11 — The benchmark was biased against lexical retrieval

Rebuilding the golden set (A8b, A8c) changed the retrieval comparison far more
than any pipeline change has:

| technique | R@1 old → new | R@5 old → new | full@5 old → new |
|---|---|---|---|
| dense | 0.731 → 0.769 | 0.923 → **1.000** | 0.731 → 0.577 |
| bm25 | 0.385 → **0.654** | 0.500 → **0.885** | 0.423 → 0.462 |
| hybrid_rrf | 0.462 → 0.769 | 0.846 → 0.923 | 0.692 → 0.538 |

**BM25's apparent collapse was mostly an artifact of the eval set.** Its
recall@5 rose from 0.500 to 0.885 with no change to the retriever, the index or
the chunking -- only to the questions asked of it.

The mechanism is specific and worth stating, because it is a trap any RAG
benchmark can fall into. Writing questions that deliberately avoid the
source's wording penalises *lexical* retrieval far more heavily than *semantic*
retrieval: dense embeddings absorb paraphrase, BM25 matches words. Asking where
"per-process bookkeeping" is kept is merely hard for dense and close to
unanswerable for BM25. The benchmark was therefore biased against one of the
techniques it existed to compare, and the earlier conclusion that "BM25 fails
half the time on this corpus" measured that bias.

What survives: dense still leads (1.000 against 0.885) and hybrid_rrf still
trails dense (0.923), so fusing with a weaker retriever still costs recall. The
*ordering* held; the *magnitude* was inflated roughly threefold.

Two further readings. `full@5` fell across the board because 17 of 26 questions
now require several parents -- a stricter and more meaningful test of whether
retrieval covers a topic across the sources that teach it. And dense now
reaches recall@5 of 1.000, so the earlier "k must be 8-10" conclusion was
itself partly an eval-set artifact; `full@5` of 0.577 still argues for 8, since
multi-part questions need breadth rather than depth.

**Method note.** Retrieval metrics measured before and after an eval-set change
are not comparable, and improvements across that boundary are not evidence the
pipeline improved. Only measurements against a fixed benchmark count: refusals
11.7% → ~0% (chunking + parent expansion) and hit 0.885 → 1.000 (dropping MMR,
raising k) were both measured that way and stand.

### A12 — No retrieval technique dominates; they win different metrics

All six techniques against the corrected golden set (26 questions, 22 documents):

| technique | R@1 | R@3 | R@5 | R@10 | full@5 | MRR |
|---|---|---|---|---|---|---|
| dense | 0.769 | **0.962** | **1.000** | **1.000** | 0.577 | **0.875** |
| hyde | 0.654 | 0.923 | **1.000** | **1.000** | **0.692** | 0.804 |
| dense + multi_query | **0.808** | 0.923 | 0.962 | **1.000** | 0.577 | 0.873 |
| hybrid_rrf + multi_query | 0.769 | 0.885 | 0.962 | 0.962 | 0.654 | 0.848 |
| hybrid_rrf | 0.769 | 0.808 | 0.923 | **1.000** | 0.538 | 0.826 |
| bm25 | 0.654 | 0.731 | 0.885 | 0.923 | 0.462 | 0.736 |

Each of the top three wins a different metric, and the split is mechanistic
rather than noise:

**HyDE buys breadth at the cost of precision** (full@5 0.692, best; R@1 0.654,
worst). It embeds a hypothetical *answer*, which mentions several facets of a
topic, so it matches more of the sources that teach it -- while matching the
single closest passage less sharply than embedding the question does.

**Multi-query buys precision** (R@1 0.808, best). Several reformulations raise
the chance that one phrasing matches the best chunk sharply, but fusing them
slightly dilutes recall@5 (0.962 against dense's 1.000).

**Dense is the best all-rounder** and the only technique needing no LLM call.

This refines A11's conclusion. The vocabulary gap was real, but it was costing
*completeness*, not findability: dense already saturates recall@5 at 1.000, and
what query rewriting improves is retrieving *all* the sources for a multi-part
question. Since incomplete context is what produced partial answers, HyDE is
the most promising candidate for end-to-end correctness **despite ranking the
top chunk worst** -- a prediction the RAGAS sweep can test.

`full@5` is the only unsaturated retrieval metric (0.462-0.692) and is
therefore the one worth optimising. `bm25` and `hybrid_rrf` are dominated on
every metric and are not worth further RAGAS time except to document it.

### A13 — Refuted: HyDE's retrieval breadth does not reach the answer

A12 predicted that HyDE, leading full@5 at 0.692 against dense's 0.577, would
convert that breadth into higher `context_entity_recall` and therefore higher
`answer_correctness`, since incomplete context was what produced partial
answers. **Measured on the corrected benchmark, it does not:**

| variant | corr | compl | composite | faith | ans_corr | ctx_recall | ctx_entity | LLM calls |
|---|---|---|---|---|---|---|---|---|
| hyde + none | 0.780 | 0.723 | **0.752** | 0.929 | 0.631 | **0.958** | 0.488 | 510 |
| dense + cross_encoder | **0.795** | 0.693 | 0.744 | **0.949** | **0.642** | 0.926 | 0.460 | 448 |
| dense + none | 0.764 | 0.717 | 0.740 | 0.899 | 0.629 | 0.942 | **0.491** | 451 |

`answer_correctness` moves +0.002, and `context_entity_recall` moves in the
*wrong* direction (0.488 against 0.491). HyDE does lead `context_recall` and
the composite, but by margins well inside noise, and it costs 510 LLM calls
against 451.

So the breadth advantage was real at the retrieval layer and did not survive to
the answer. Either the additional sources HyDE surfaces are not the ones
holding the missing entities, or generation does not exploit extra context as
readily as assumed. The prediction was specific and falsifiable, and it failed.

### A14 — Technique choice barely matters once the defects are fixed

The three variants measured so far span 0.740 to 0.752 on the composite. At 26
questions judged by a 7B model, that range is not resolvable. Set against the
effect sizes of the defect fixes:

| change | measured effect |
|---|---|
| chunking + parent expansion | refusals 11.7% → ~0% |
| dropping MMR | hit@8 0.962 → 1.000 |
| correcting the eval set | BM25 recall@5 0.500 → 0.885 |
| **choosing among dense / hyde / reranking** | **~0.01 composite** |

The gains came from repairing defects and from fixing how quality was measured,
not from selecting between techniques. This inverts the premise the project
started with -- that the point was to find which retrieval technique wins -- and
is the more useful result: on a corpus this size, a correct pipeline matters an
order of magnitude more than a clever one.

**Also a provisional correction to A7.** Reranking measured ~0.05 *worse* on
answer_correctness on the biased benchmark; on the corrected one it measures
+0.013 better on that metric and +0.050 on faithfulness, at the cost of
`context_entity_recall` (-0.031). That is a coherent trade -- narrower contexts
are easier to ground against but carry fewer entities -- rather than the loss
A7 described. Pending the hyde+cross_encoder pair as an independent read.

### A15 — `context_entity_recall` is unreliable for this content

The metric extracts entities from the ground truth and, separately, from the
retrieved context, then intersects the two **string sets**. Asking an LLM to
enumerate entities from ~900 tokens of multi-passage context returns a
different, non-exhaustive subset than it returns from a two-sentence reference,
so the intersection fails even when the information is fully present.

Measured directly on two questions:

```
Q: What are the states of a process, and what makes a process blocked?
  GT entities : ['CPU','I/O request','blocked','disk','event','process','ready']
  matched     : []                        score = 0/7 = 0.000
  every one of the seven is literally present in the retrieved context text
```

```
Q: What are the design goals of an operating system?
  MISSED: ['hardware resources','memory','multiple processes','user programs']
  three of those four are literally present in the context
```

So the 0.479 average is substantially **extraction disagreement, not missing
information**. Consequences, including for claims made earlier in this document:

- **"entity recall is the real gap" was wrong.** It is the weakest number but
  not a real weakness.
- **A2's correlation is suspect.** Correctness correlating with entity recall
  at r=+0.24 has noise on one side; the `context_recall` correlation (+0.41)
  is unaffected and remains the sounder signal.
- **The `completeness` composite is polluted**, since half of it is this
  metric. Not changed mid-sweep, because that would make the eight variants
  incomparable, but it should be revisited.
- **Improvements measured on this metric are weakly evidenced.** Multi-query
  raising it 0.491 → 0.533 may partly reflect more context text yielding more
  extracted entities. Its `answer_correctness` gain (+0.033) does not depend on
  this extraction step and is firmer.

The metric was designed for entity-centric domains (its documentation cites a
tourism chatbot). Conceptual material, where the "entities" are ordinary
technical nouns and contexts are long, is outside what it measures well.

### A16 — Complete focused sweep: the cheapest strong config wins

Eight variants, 26 questions, corrected golden set, `num_query_variants=3`,
diversification off:

| variant | composite | corr | compl | faith | ans_corr | ctx_prec | ctx_recall | calls | cost |
|---|---|---|---|---|---|---|---|---|---|
| **dense + multi_query** | **0.772** | 0.810 | 0.734 | 0.958 | **0.662** | 0.862 | 0.936 | 480 | $0.160 |
| hyde + cross_encoder | 0.764 | 0.801 | 0.727 | 0.958 | 0.644 | 0.850 | **0.978** | 491 | $0.195 |
| hyde | 0.752 | 0.780 | 0.723 | 0.929 | 0.631 | 0.852 | 0.958 | 510 | $0.227 |
| dense + cross_encoder | 0.744 | 0.795 | 0.693 | 0.949 | 0.642 | **0.882** | 0.926 | 448 | $0.153 |
| hyde + multi_query + cross_encoder | 0.743 | 0.769 | 0.716 | 0.882 | 0.656 | 0.863 | 0.968 | 593 | $0.282 |
| dense | 0.740 | 0.764 | 0.717 | 0.899 | 0.629 | 0.843 | 0.942 | 451 | $0.148 |
| hyde + multi_query | 0.734 | 0.774 | 0.694 | 0.912 | 0.637 | 0.811 | 0.960 | 615 | $0.296 |
| dense + multi_query + cross_encoder | 0.720 | 0.745 | 0.695 | 0.883 | 0.607 | 0.896 | 0.936 | 471 | $0.163 |

**Cost and quality are anti-correlated here.** The winner is nearly the
cheapest config in the sweep (480 calls, $0.160), while the two most expensive
(615 and 593 calls) place seventh and fifth. Every LLM call added to retrieval
buys another chance to drift from what was asked.

**Reranking is not uniformly good or bad -- it depends what precedes it:**

```
dense           → +0.004 with cross_encoder
hyde            → +0.012
dense+multi_query → −0.052
```

It helps a single-query retriever and hurts multi-query, because it re-scores
every candidate against the *original* question and so discards exactly the
diversity multi-query was added to create. This supersedes A7's blanket
"reranking hurts", which was measured on the biased benchmark, and refines
A14's correction of it.

The spread across all eight is 0.052 -- larger than the 0.012 A14 saw before
the multi-query variants ran, so "technique choice barely matters" was stated
on incomplete data. It remains true that the defect fixes were worth several
times more than the best technique choice.

### A17 — The answer prompt outweighed every retrieval technique

Three prompts against the identical winning config (dense + multi_query, no
reranking, no diversification, tables indexed, five query variants):

| prompt | composite | ans_corr | faithfulness | ctx_recall |
|---|---|---|---|---|
| strict (previous default) | 0.763 | 0.664 | 0.942 | 0.946 |
| **few_shot** | **0.784** | **0.756** | **0.986** | 0.928 |
| part_coverage | 0.712 | 0.631 | 0.819 | 0.936 |

**answer_correctness rose 0.664 → 0.756, a gain of 0.092.** The entire
eight-variant retrieval sweep spanned 0.052 (A16), so two worked examples in
the prompt were worth more than every chunking, retrieval, reranking and
diversification choice put together.

This is the predicted consequence of a diagnosis made earlier and not acted on
for too long: answers were losing points to *statement granularity*, not to
content -- one scored 0.56 while being content-identical to its reference,
penalised for splitting a single reference statement into two bullets, because
answer_correctness compares statement sets. Showing the expected shape fixes
that without touching what the model knows. Faithfulness rising too (0.942 →
0.986) suggests the examples also discourage the unsupported asides the strict
prompt's preamble style invited.

**part_coverage measured actively harmful**, as predicted when it was written:
faithfulness fell to 0.819. Inviting the model to answer "each part the context
supports" reads as licence to supply the parts it does not. Retained in the
code as a recorded negative rather than deleted.

**The composite understates all of this** (+0.012 against ans_corr's +0.092)
because half of `completeness` is `context_entity_recall`, which A15 showed to
be unreliable. Another argument for H7.

### A18 — Recovered content need not move the benchmark

Indexing PPTX tables (F15) added 20.1% more slide text and produced **no
measurable score change** (0.772 → 0.763 on a confounded arm that also changed
`num_query_variants`).

The reason is not that the content is worthless: the recovered tables define
shell operators, and **no question in the eval set asks about shell operators**.
The benchmark cannot see the improvement.

This is worth keeping in view when reading every other number here. A metric
suite measures the questions it was given, and content that answers questions
nobody asked is invisible to it while still being exactly what a student needs.
The fix was kept for that reason rather than for its score.

## Open items

- **Raise `context_entity_recall`** (currently 0.440) -- the metric most
  directly implicated in low correctness by A2. Candidate levers: more final
  contexts (5 → 8), a larger parent cap (250 → 400). To be tested against the
  sweep's winning configuration rather than by restarting the sweep.
- **Prompt for partial answers** instead of a binary refuse, so partial
  retrieval yields partial credit (addresses A4 case 2).
- **`llm_rerank`** is implemented but excluded from sweeps (one LLM call per
  candidate). Given A7 finds the cross-encoder actively harmful, a slower
  reranker is unlikely to help, and this may be worth dropping entirely.
- **Weight or drop the sparse arm of `hybrid_rrf`** (A5): fusing dense with a
  retriever that fails half the time measurably underperforms dense alone.
- **Stage tuning grid** (`eval/stage_tuning_eval.py`) is measuring final
  context count, reranking on/off, candidate pool width, and HyDE, scored by
  whether the cited slide survives into the generator's context.
- **Scale-up:** ingest 100-200 documents and redo trend analysis. Pool size and
  reranking cost are corpus-independent, so they will not worsen with scale.

## Caveats that must appear in the formal write-up

- 26 questions over a 22-document single-course corpus. Differences between
  configurations of a few hundredths are not resolvable at this sample size.
  The BM25-versus-dense gap was large and consistent; the finer distinctions
  were not.
- The judge (`qwen2.5:7b`) is a different model family from the generator
  (`llama3`) specifically to avoid LLM-as-judge self-preference bias. It is
  still a 7B local model, not a strong judge.
- Single run per configuration; no variance estimate, no significance testing.
- Costs quoted in USD are *hypothetical* -- token counts from local runs priced
  against published GPT-4.1 / GPT-4o-mini rates. No OpenAI API calls were made.
