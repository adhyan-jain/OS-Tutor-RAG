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
