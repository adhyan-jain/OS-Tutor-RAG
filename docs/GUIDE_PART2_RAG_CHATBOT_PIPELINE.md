# Part 2 of 2: The RAG chatbot's pipeline, end to end (OS Tutor)

> This is **Part 2**, the chatbot: its pipeline, its measurements and its tutoring layer. **Part 1** (`docs/GUIDE_PART1_RESEARCH_PAPER.md`) is the research paper (Reference-Choice Robustness). They are independent; if you are asked about the paper, switch to Part 1.

A guide for learning the chatbot end to end and presenting it. It answers two questions at the level of actual
inputs and actual arithmetic, not summaries:

1. **What exactly is sent at every stage?** (retrieval query, prompt, judge row)
2. **How exactly does each metric get its number?** (the judge's real prompts, what comes back, the formula)

Everything numeric below is copied from a file in this repo or reproduced from a real run, and says which. Where
something is my inference rather than a measurement, it is marked **[inference]**. Where I could not verify
something, it is marked **[unverified]**.

Companion material, so this guide does not repeat it:

- `LEARNING_GUIDE.md` is the conceptual background (embeddings, FAISS, BM25, RRF, RAGAS ideas, reading lists). Read
  its Parts 10, 11 and 15 before presenting.
- `FINDINGS.md` is the evidence log (F1 to F16 defects, A1 to A20 analyses). `HYPOTHESES.md` is the queue.
- The `/research` page in the frontend is a visual summary of the same numbers.

> **Corpus caveat to say out loud.** Every measurement in FINDINGS.md was taken on the July corpus: 22 `Document`
> objects from 10 source files (5 PPTX decks, 4 OSTEP PDF chapters, 1 DOCX of 13 sections). `data/raw/` now holds 37
> files and the index has 46 documents and 3,646 chunks. FINDINGS' own correction note (2026-09-30) says none of the
> numbers transfer to the larger corpus without re-measurement.

---

## 0. How to use this guide

| You have | Do this |
|---|---|
| 2 hours | Read sections 1, 2, 5, 6 (the worked example), 11, then rehearse section 13 |
| An evening | Everything in order, then run the three commands in section 14 |
| 10 minutes before | Section 1 (the five numbers), section 13.1 (the 10-minute track), section 15 (cheat sheet) |

---

## 1. The story in one paragraph, and the five numbers

We built a RAG tutor for an operating-systems course and, instead of simply tuning it, measured it. The measurements
overturned most of our expectations. The gains came from **repairing defects** and from **one prompt's wording**, not
from retrieval cleverness; the retrieval-technique comparison lives mostly **inside the benchmark's own noise**; and
two of our headline "problems" (BM25 being terrible, the metric `faithfulness` being a quality score) turned out to
be artifacts of our own chunker, our own benchmark and the metric's degenerate optimum.

The five numbers to memorise (all `answer_correctness` unless stated; FINDINGS A20 table):

| # | Number | Meaning |
|---|---|---|
| 1 | **+0.111** | gain from fixing defects (chunking, parent expansion, eval set) |
| 2 | **+0.092** | gain from the `few_shot` prompt over the `strict` one (0.664 to 0.756, A17) |
| 3 | **0.027** | run-to-run noise: the same config scored 0.7752 then 0.7478 (A20) |
| 4 | **0.052 / 0.067** | spread across all eight retrieval/rerank variants: composite 0.052 in the first sweep (A16); answer_correctness 0.0670 in the later few_shot sweep (`eval/comparison_results.md`) |
| 5 | **26** | questions in the golden set, so differences of a few hundredths are not resolvable |

If you remember one sentence: *"Technique choice moved the score by about what re-running the same config moves it;
fixing bugs and rewording one prompt moved it three to four times more."*

---

## 2. System map

```
data/raw/*.pptx|pdf|docx
   |  extract (src/ingestion)               -> Document(doc_id, text, metadata: slides | pages | sections)
   |  chunk per format (src/chunking)       -> many small CHILD chunks, each carrying PARENT text (its slide/page)
   |  embed with BAAI/bge-large-en-v1.5     -> normalised float32 vectors
   |  FAISS IndexFlatIP                     -> data/index/dense.faiss + dense_chunks.pkl (+ bm25.pkl)
   v
question --(optional query transform: multi_query | hyde)--> retrieve top-k children (cosine)
   --(optional) cross-encoder rerank --> expand child -> parent (dedupe, cap 400 tokens)
   --> fill answer prompt (few_shot) --> llama3 via Ollama, temperature 0 --> answer

evaluation:
golden set (26 Q + reference answer + cited slide/page ids)
   |- eval/retrieval_eval.py : recall@k, full_recall@k, MRR       (NO LLM; seconds)
   '- eval/ragas_eval.py     : answer + contexts -> RAGAS judge (qwen2.5:7b + bge-small) -> 7 metrics
```

The tutor on top (Socratic questions, follow-up chips) is **section 11**. It is a separate layer and, importantly,
**not** what the RAGAS numbers measure (see Q&A 21).

---

## 3. Stage by stage: what goes in, what comes out

Defaults are from `src/config.py` at the time of writing; the study varied some of them per sweep, and each result
table names its own config.

### 3.1 Ingestion (`src/ingestion/`)
- **In:** files in `data/raw/`. PPTX via python-pptx (title, bullets, table cells, notes), PDF via pypdf (text per
  page), DOCX via python-docx (one Document per heading section).
- **Out:** `Document(doc_id, source_path, text, metadata)`. `metadata["slides"]` or `["pages"]` keeps structure.
- **Defects found here:** `.doc` binary skipped silently (F11, 9,005 chars lost); PPTX tables never read (F15,
  +20.1% slide text recovered); speaker notes checked and found absent (F16).

### 3.2 Chunking (`src/chunking/`): matched to format, not swept
| Format | Strategy | Child | Parent |
|---|---|---|---|
| PPTX | `structure_aware` | one **bullet**, prefixed with its slide title (`"<heading>: <bullet>"`) | the whole slide |
| PDF | `page_aware` | semantic passage, never crossing a page | the page text |
| DOCX | `structure_aware` | overlapping 512-char windows (64 overlap) | the section |

Two rules from the bugs: titles are **never** indexed alone (F1: 12 of 81 slide titles are question-shaped and became
perfect lexical decoys), and children carry `parent_id` / `parent_text` so generation can read more than it matched.
The small-to-big design is **validated** by A6: indexing whole slides dropped dense R@5 from 0.923 to 0.577.

### 3.3 Index (`src/retrieval/dense.py`)
Child texts are encoded with `BAAI/bge-large-en-v1.5` (`normalize_embeddings=True`) into a `faiss.IndexFlatIP`.
Normalised inner product is cosine similarity. Flat means exact search: at ~3.6k vectors there is nothing to
approximate. Corpus embeddings are memoised on `(model, sha256(all chunk texts))` (F8, F14).

### 3.4 Query transforms (optional, `src/retrieval/multi_query.py`, `hyde.py`)
- **multi_query:** one LLM call asks for N reformulations (N = `num_query_variants`, default 5, one per line). The
  original plus the variants are each retrieved, then fused by **Reciprocal Rank Fusion**:
  `score(chunk) = sum over lists of 1 / (60 + rank)`. H1 found an inverted U: 0 variants full@5 0.500, 3: 0.538,
  **5: 0.577**, 7: 0.538.
- **hyde:** one LLM call writes a 2 to 4 sentence hypothetical textbook passage; **that text** is embedded and
  searched instead of the question.
- Both are LLM calls at temperature 0.0 now (A19 found 0.2 made retrieval itself stochastic: only 13 of 26 questions
  retrieved the same contexts across two arms).

### 3.5 Retrieval, selection, expansion (`src/pipeline.py::_retrieve_candidates`)
1. `_stage_sizes()` widens the pool so each filter has something to filter (F13). With the cross-encoder on and MMR
   off: `rerank_n = 8`, `pool_k = max(10, 8 x 3) = 24`. With neither: `pool_k = top_k = 10`.
2. `retriever.retrieve(query, top_k=pool_k)`. (Optional per-parent cap, off by default, A9.)
3. Optional cross-encoder: scores `(original question, child text)` pairs with `BAAI/bge-reranker-large` and keeps the
   top 8. Note it sees the **child**, not the parent.
4. Optional MMR (off; A10 showed it dropping the correct slide).
5. `expand_to_parents`: replace each child by its parent text, **drop duplicate parents** (first child wins), and if a
   parent exceeds `max_parent_tokens = 400`, take a window **around the matched child** rather than the top of the
   parent (F3: slide parents ~72 tokens vs 13 for their child; PDF page parents ~534 vs 48).

Why the final context count varies: 24 candidates can collapse to ~5 distinct parents. The worked example has 5.

### 3.6 Generation (`src/generation/local_llm.py`)
`context_text = "\n\n".join(chunk.text for each final context)`, substituted into the prompt template, sent to Ollama
`/api/generate` with `temperature=0.0`, `num_predict=900`, model `llama3:latest`. The default template is
`few_shot`, **verbatim**:

```
Answer the question using only the context below. If the context doesn't contain the answer, say so.

Answer in continuous prose, stating each fact once. Do not add preamble about the context.

Example question: What does the OS do when it creates a process?
Example answer: The OS allocates memory and creates the memory image, loads the code and data from the executable
on disk, creates the runtime stack and heap, and opens basic files.

Example question: What are user mode and kernel mode?
Example answer: CPU hardware has multiple privilege levels: user mode runs user code, and kernel mode runs OS code
such as system calls.

Context:
{context}

Question: {query}

Answer:
```

Four prompts exist (`strict`, `part_coverage`, `few_shot`, `cot`) so the difference could be measured. `cot` has its
`Reasoning:` section stripped by `_strip_reasoning` before scoring, otherwise reasoning sentences would be scored as
answer statements.

---

## 4. The golden set: how it was built and why it changed

`eval/eval_set.json`: **26 questions**, schema `question, ground_truth_answer, source_parent_ids, topic`.
Topics: process_abstraction 6, os_basics 5, process_api 5, process_execution_mechanism 5, shell_programming 5.
17 of 26 questions are multi-part (A11).

Its history is itself a finding and a good example of the research method:

| Version | Problem | Evidence |
|---|---|---|
| v1: 10 questions from general OS knowledge | Ground truth used wording absent from the corpus ("I/O devices" vs slide "IO devices"); cited chunk **indices**, which re-chunking invalidated | F12 |
| v2: 26 slide-grounded, **deliberately paraphrased** away from slide titles | Asked for "per-process bookkeeping" where the slide says "process control block". Unanswerable for BM25, hard for dense. Cited one source although slides and OSTEP teach most topics twice, so a correct retrieval of the textbook page scored as a miss | A8b, A8c |
| **current**: course terminology, **every** parent that answers is cited, ids are parent ids (`Introduction to OS__slide2`) | none known; but see H5 below | `eval_set.json` `notes` |

What changed when v2 became the current set (A11): BM25 recall@5 **0.500 to 0.885** with no change to the retriever;
dense 0.923 to 1.000; `full@5` fell because 17 questions now needed several parents. **Lesson: writing questions to
avoid the source's wording penalises lexical retrieval far more than semantic retrieval, so the benchmark was biased
against one of the techniques it existed to compare.** Retrieval metrics before and after an eval-set change are not
comparable.

Remaining weakness (**H5**, open): reference answers are less complete than the corpus. An answer scoring 0.61 listed
process states the corpus teaches but the reference omitted; one scoring 0.56 was content-identical but split a
bullet in two. Both lose points as false positives.

---

## 5. How each metric gets its number

### 5.1 Retrieval metrics: no LLM at all (`eval/retrieval_eval.py`)
Uses `source_parent_ids` as a retrieval ground truth. For each question:

1. `retrieved = parents_of(retriever.retrieve(question, top_k=20))`: parent ids in rank order, **de-duplicated**.
2. `expected = set(source_parent_ids)`.
3. For each k in {1, 3, 5, 10, 20}:
   - `recall@k` = 1 if `top-k ∩ expected` is non-empty (**at least one** cited parent found), else 0.
   - `full_recall@k` = 1 if `expected ⊆ top-k` (**every** cited parent found; what multi-part questions need).
4. `MRR` term = `1 / rank` of the first expected parent, 0 if absent.
5. Each is the mean over the 26 questions.

Note `full@5` here is "take the top 5 children, then dedupe parents", so it can see fewer than 5 parents. The H1
table instead dedupes first and then takes 5. They are not comparable with each other (HYPOTHESES says so).

Why this exists: RAGAS costs ~30 minutes per configuration; this costs seconds, and answer quality correlates with
retrieval metrics (context_recall r = +0.409) far more than with generator-side ones (faithfulness r = +0.092; A2).

### 5.2 RAGAS metrics (`src/evaluation.py::score_pipeline`, ragas 0.1.14)
The row handed to every metric is:

```python
row = {"question": q, "answer": llm_answer, "contexts": [parent_text, ...], "ground_truth": reference_answer}
```

Metrics are called one at a time with `metric.score(row)` (RunConfig max_workers=1), bypassing RAGAS's executor,
which deadlocked a single Ollama server on an 8 GB GPU. The judge is `qwen2.5:7b` (a different family from the
`llama3` generator, to avoid self-preference bias). Embeddings for two metrics are `BAAI/bge-small-en-v1.5` on CPU.
`reproducibility` is 1, so each judge prompt is sampled once (except `answer_relevancy`, n = 3).

Every judge prompt has the same skeleton: **instruction + JSON-schema output instruction + worked examples + "Your
actual task:" + the row's fields + an empty output slot.** The text below is from the installed ragas source; the
judge replies in the next section are from a real re-run.

| Metric | Calls | Judge prompt instruction (verbatim) | Arithmetic (verified in source) |
|---|---|---|---|
| `context_precision` | 1 per context | *"Given question, answer and context verify if the context was useful in arriving at the given answer. Give verdict as "1" if useful and "0" if not with json output."* The **answer slot is filled with the ground truth** (`_get_row_attributes` returns `row["ground_truth"]`). | verdicts `v_i` in context order. `AP = Σ_i (Σ_{j≤i} v_j / i) · v_i  /  Σ v_i`. Rewards relevant contexts being first. |
| `context_recall` | 1 | *"Given a context, and an answer, analyze each sentence in the answer and classify if the sentence can be attributed to the given context or not. Use only "Yes" (1) or "No" (0)…"* Context = all contexts joined by `\n`; answer slot = **ground truth**. | `attributed / total statements` |
| `context_entity_recall` | 2 | *"Given a text, extract unique entities without repetition…"* run once on the ground truth, once on the joined contexts. | `\|GT entities ∩ context entities\| / \|GT entities\|`, a **Python set intersection of exact strings** |
| `faithfulness` | 2 | (1) *"…break down each sentence into one or more fully understandable statements while also ensuring no pronouns are used…"* (2) *"…judge the faithfulness of a series of statements based on a given context… verdict 1 if the statement can be directly inferred… 0 if not."* | `supported / total statements` |
| `answer_relevancy` | 3 (n=3) | *"Generate a question for the given answer and Identify if answer is noncommittal…"* | mean cosine(question, each generated question) with bge-small, **× 0 if any of the 3 is noncommittal** |
| `answer_similarity` | 0 | none | cosine of bge-small embeddings of answer and ground truth |
| `answer_correctness` | 3 (+0 embed) | statements for answer, statements for GT (same decomposition prompt), then *"…classify them in one of: TP … FP … FN"* | `0.75 · F1 + 0.25 · answer_similarity`, `F1 = TP / (TP + ½(FP + FN))`, F1 = 0 if TP = 0 |

Code details that explain real behaviour:

- **Sentence filter.** In `faithfulness` and `answer_correctness`, only sentences whose stripped text **ends with
  "."** are given to the statement-splitting prompt. A bullet list or a sentence ending in `:` or `)` can silently
  vanish from scoring. No statements gives `NaN` for `faithfulness`.
- **`answer_relevancy` and refusals.** A refusal is flagged noncommittal, so the whole score becomes 0, but
  `faithfulness` for the same refusal is 1.0 (A1). Same answer, opposite extremes.
- **NaN-safe means.** Local models do not always emit the JSON RAGAS expects. `score_pipeline` averages each metric
  over only the rows where it parsed (`math.isnan` filter), rather than zeroing or poisoning the mean.
- **Judge call count per question** = k contexts + 1 + 2 + 2 + 3 + 3 = **11 + k**. With k about 5 that is 16, and
  `pipeline_runs.xlsx` shows 418 to 420 judge calls over 26 questions (16.1 each). The match is an inference check, not
  proof, but it supports the table above.

### 5.3 The composites (`src/evaluation.py::composite_scores`)
```
correctness              = mean(faithfulness, answer_correctness)
completeness             = mean(context_recall, context_entity_recall)
correctness_completeness = mean(correctness, completeness)     <- the ranking key in eval/ragas_eval.py
```
`answer_similarity` is left out because `answer_correctness` already folds it in. **Weakness:** half of
`completeness` is `context_entity_recall`, which A15 showed to be unreliable (H7). That is why the composite understates
the prompt gain (+0.012 composite vs +0.092 answer_correctness, A17).

---

## 6. A complete worked example: one real question, every input, every judge reply

This is eval question 8 (`process_abstraction`), taken from `eval/ragas_details.xlsx`, config `temp_0.0` =
`dense + multi_query(5) + cross_encoder`, `few_shot` prompt, temperature 0.0. **I re-ran all seven RAGAS metrics on
this stored row with the real judge and logged every call; the re-run reproduced the stored scores exactly.** The
script is in Appendix A. (Not stored in the repo, so not shown: the 5 query variants llama3 wrote for this question.
`pipeline_runs.xlsx` records only that the call took 63 input and 64 output tokens, and the answer call 1,070 input and
54 output tokens.)

### Step 1: the question and reference
```
question:     What are the states of a process, and what makes a process blocked?
ground_truth: A process can be running, meaning currently executing on the CPU; ready, meaning waiting to be
              scheduled; or blocked, meaning suspended and not ready to run. A process becomes blocked while
              waiting for some event, such as an I/O request it issued to disk.
source_parent_ids: ["Process abstractions__slide5", "process abstraction__page6"]   (the lecture slide and the OSTEP page)
```

### Step 2: retrieval (what happened, in order)
1. llama3 writes 5 reformulations. Queries = original + 5 = 6.
2. Each query retrieves 24 child chunks from FAISS by cosine.
3. RRF fuses the 6 ranked lists (`Σ 1/(60+rank)`), keeping 24.
4. The cross-encoder scores `(original question, child text)` and keeps 8.
5. Expansion swaps children for parents, drops duplicates, windows anything over 400 tokens. **Result: 5 contexts.**

The five contexts (verbatim starts; total 3,884 characters): the OSTEP "Figure 4.2 Process: State Transitions" page
(`"Running Ready / Blocked / Descheduled / Scheduled…"`), the OSTEP "Key process terms" aside, the lecture slide
**"States of a process / Running: currently executing on CPU / Ready: waiting to be scheduled / Blocked: suspended, not
ready to run / Why? Waiting for some event, e.g., process issues a read from disk / New: being created / Dead:
terminated"**, an OSTEP page on process creation (stack/heap), and the OSTEP "Tracing Process State" figure page.

### Step 3: the generation prompt (the `few_shot` template above, filled)
```
Answer the question using only the context below. If the context doesn't contain the answer, say so.
...two worked examples...
Context:
<context 1 text>\n\n<context 2 text>\n\n<context 3 text>\n\n<context 4 text>\n\n<context 5 text>

Question: What are the states of a process, and what makes a process blocked?

Answer:
```
(1,070 input tokens in the run's call log.)

### Step 4: the model's answer
```
The states of a process are running, ready, blocked, new, and dead. A process is blocked because it has performed
some kind of operation that makes it not ready to run until some other event takes place, such as waiting for an I/O
request to complete.
```

### Step 5: the row sent to the judge
```python
{"question": "...", "answer": "<the answer above>", "contexts": [<5 strings>], "ground_truth": "<reference>"}
```

### Step 6: each metric, with the judge's actual replies

**`context_precision` = 0.95.** Five judge calls, one per context, each with the reference as the "answer". Replies:
`verdict 1, 1, 1, 0, 1`. The 0 was the process-creation page (the judge said it *"primarily discussed memory
allocation and paging mechanisms"*). Computation:

```
v = [1, 1, 1, 0, 1]
AP = (1/1·1 + 2/2·1 + 3/3·1 + 0 + 4/5·1) / 4 = (1 + 1 + 1 + 0.8) / 4 = 0.95
```
Teaching point: the 0 sits fourth. Had it been first, `AP = (0 + 1/2 + 2/3 + 3/4 + 4/5) / 4 = 0.68`. Order matters.

**`context_recall` = 0.75.** One call, all contexts joined. The judge split the reference into 4 statements and returned
`attributed = 1, 0, 1, 1`:
```
"A process can be running, meaning currently executing on the CPU;"              -> 1
"A process can be ready, meaning waiting to be scheduled;"                         -> 0
   judge's reason: "...does not specifically mention that this means 'waiting to be scheduled'."
"A process can be blocked, meaning suspended and not ready to run."               -> 1
"A process becomes blocked while waiting for some event, such as an I/O request…" -> 1
score = 3/4 = 0.75
```
**This is a judge error you can point at.** The lecture slide in the contexts literally says *"Ready: waiting to be
scheduled"*. A 7B judge missed it. That single misjudgement is worth 0.25 on this question.

**`context_entity_recall` = 0.2857.** Two calls.
```
GT entities      (call 1): ["process","CPU","ready","blocked","event","I/O request","disk"]            7 items
context entities (call 2): ["Blocked","Running","Ready","I/O","OS","process","CPU","memory","stack","heap",
                            "main()","argc","argv","Process 0","Process 1"]                            15 items
set intersection  = {"process", "CPU"}  ->  2 / 7 = 0.2857
```
Every concept is in the context, yet the score is 0.29, because `"ready" != "Ready"`, `"blocked" != "Blocked"`,
`"I/O request" != "I/O"`. This is exactly FINDINGS A15: *the metric measures string-set agreement between two
non-exhaustive LLM extractions, not whether the information reached the model.*

**`faithfulness` = 1.0.** Two calls. (1) The answer's two sentences become 3 statements:
```
"The states of a process include running, ready, blocked, new, and dead."
"A process is blocked when it has performed an operation that makes it not ready to run until another event occurs."
"Examples of such events include waiting for an I/O request to complete."
```
(2) The judge marks all three `verdict: 1` (it accepts "new" and "dead" because the lecture slide lists them). 3/3 = 1.0.

**`answer_relevancy` = 0.9349.** Three identical-prompt calls (n = 3). The judge returned the same question each time:
*"What are the states that a process can be in and what does it mean for a process to be blocked?"*, `noncommittal: 0`.
Score = mean cosine(original question, generated question) using bge-small, × 1 (nothing noncommittal) = 0.9349.

**`answer_similarity` = 0.9121.** No judge. Cosine of bge-small embeddings of answer vs reference.

**`answer_correctness` = 0.5614.** Three calls. Statements for the answer (3, as above) and for the reference (5):
```
GT: running = executing on CPU / ready = waiting to be scheduled / blocked = suspended, not ready to run /
    becomes blocked when waiting for some event / example: an I/O request issued to disk
```
The judge's TP/FP/FN classification: **TP = 2, FP = 0, FN = 5**.
```
F1    = TP / (TP + ½(FP + FN)) = 2 / (2 + 2.5) = 0.4444
score = 0.75 · 0.4444 + 0.25 · 0.9121 = 0.3333 + 0.2280 = 0.5614      (matches the stored 0.5614)
```
**Why this answer scores 0.56 although it is a reasonable answer:** the judge accepted two of the answer's three
statements as supported by the reference (TP 2) but treated *none* of the five reference statements as present in the
answer, so all five count as FN. A human would say the answer covers "blocked" and the I/O example; the statement-level
judge was strict about "running means executing on the CPU" and "ready means waiting to be scheduled" never being
stated. This is the "answer_correctness is an F1 over statement sets" effect that explains the CoT result, the 0.56
bullet-splitting case, and why more complete answers can score lower (A19).

### Step 7: what the example teaches (say these three things in the talk)
1. **Retrieval was fine** (recall 0.75, precision 0.95, the right slide present) but the *score* is 0.56. The pipeline's
   weak point is not retrieval, it is how the metric reads the answer (A2, A17).
2. **Two of seven numbers here are judge or metric artifacts**: the ready/waiting misjudgement and the
   case-sensitive entity set.
3. The three small steps (pick context, fill prompt, decompose into statements) are each inspectable, which is why the
   defects (F1 to F16) were findable at all.

The re-run reproducing all seven scores exactly means the judge was deterministic for these inputs in this run. That
fits A19's observation that rows with identical contexts scored identical context metrics. **[inference]** that the
0.027 noise floor therefore comes from the *generation side* (stochastic multi-query variants, server numerics), not
from the judge. I did not test judge determinism across sessions or models.

---

## 7. Orchestration: how a sweep runs

`eval/ragas_eval.py` builds a list of `ConfigVariant`s and, for each: build `RAGPipeline`, ingest, `score_pipeline`.

- **Axes** (`default_config_variants`): retrieval technique {dense, bm25, hybrid_rrf, hyde} × multi_query × reranker
  {cross_encoder, none} × MMR {on, off}. Chunking is **not** an axis (F5: forcing one strategy across formats compares
  formats, not strategies; semantic chunking a deck collapsed 51 chunks into 6). 84 variants became 28 became 8
  ("focused") once `retrieval_eval` showed bm25 and hybrid_rrf dominated on every retrieval metric (A12).
- **Two passes** inside `score_pipeline`: (1) generate **every** answer, (2) release the GPU, (3) judge every answer.
  Reason: llama3 (~4.7 GB) and a 7B judge do not fit in 8 GB together, so Ollama evicts one to load the other.
  Interleaving costs 2 model swaps **per question**; this costs 2 **per run**. torch also had to stay off the card
  (F9: llama3 2.0 s/call free, 25.8 s under contention; F10: `CrossEncoder.predict` re-pinned itself to the GPU every
  call).
- **Resumable and crash-safe:** results are written after every variant; `--resume` skips names in the workbook; one
  failing variant is logged and skipped.
- **Outputs:** `eval/comparison_results.md` (ranked table), `eval/ragas_details.xlsx` (per-question rows),
  `eval/pipeline_runs.xlsx` (one sheet per run with phase summary, metrics, token log, per-question rows).
- **Token and cost accounting** (`src/token_tracking.py`): every call is tokenised with OpenAI's `o200k_base` encoder
  and priced as if generation ran on GPT-4.1 ($2.00 in / $8.00 out per 1M tokens) and the judge on GPT-4o-mini ($0.15 /
  $0.60). The prices are a snapshot to verify, and **the dollars are hypothetical: nothing was billed**. One few_shot
  run: 52 generation calls, 420 judge calls, 513,810 input and 38,550 output tokens, $0.168.
- **F7:** the tracker first reported `judge=0` because RAGAS reaches the model through the **async** path
  (`agenerate_text`), so wrapping only `_generate` recorded nothing. Fixed by wrapping `_agenerate` too.

---

## 8. Findings catalogue with mechanisms

### 8.1 Defects that looked like results
| ID | Looked like | Actually | Effect |
|---|---|---|---|
| F1 | BM25 is the worst retriever (0.509 vs 0.616 dense) | question-shaped slide titles indexed as standalone chunks, ranked first by BM25, no content | bare question chunks 12 to 0 |
| F2 | model keeps saying "no answer in context" | `parent_text` was recorded but never read | refusals 11.7% to ~0% |
| F3 | decks are the expensive format | pages are (534 vs 72 tokens/parent) | cap 400 tokens, 1137 to 484 tokens/question at cap 250 |
| F13 | MMR and reranking mildly harmful | retrieve 10, rerank 5, MMR 5: nothing to select from | earlier conclusions discarded |
| A11 | BM25 recall@5 = 0.500 | the **benchmark** was biased against lexical retrieval | 0.500 to 0.885 with no pipeline change |
| F15/A18 | tables fixed, nothing improved | no question asked about operators | benchmark cannot see the improvement |

### 8.2 Analyses
- **A1 faithfulness rewards refusal.** Refusal makes zero claims, so faithfulness 1.0 with correctness collapsing.
  hyde: refusal 5.0%, faith 0.883, corr 0.707; dense: 3.8%, 0.813, 0.616; hybrid_rrf: 12.5%, 0.872, 0.649; bm25: 11.7%,
  0.828, 0.509. *Never rank on faithfulness alone; report refusal rate.* (Caution: refusal rate was measured by a
  keyword regex that over-counts, A4.)
- **A2 retrieval gates correctness.** r with answer_correctness: context_recall +0.409, context_precision +0.386,
  entity_recall +0.242, relevancy +0.163, faithfulness +0.092 (78 question-runs).
- **A12 no retrieval technique dominates** (26 Q): dense R@5 1.000, MRR 0.875; HyDE best full@5 0.692 but worst R@1
  0.654 (breadth vs precision); dense+multi_query best R@1 0.808. Dense is the only one needing no LLM call.
- **A13 refuted:** HyDE's retrieval breadth did not reach the answer (+0.002 answer_correctness; entity recall
  0.488 vs 0.491).
- **A16 first focused sweep (strict prompt):** best composite dense+multi_query 0.772; the two most expensive configs
  ranked fifth and seventh. Cost and quality anti-correlated: each LLM call in retrieval is another chance to drift.
  Reranking: dense +0.004, hyde +0.012, dense+multi_query −0.052 (it re-scores against the *original* question and
  discards the diversity multi-query created).
- **A17 prompt beats retrieval:** strict 0.664, **few_shot 0.756**, part_coverage 0.631 (faithfulness 0.942, 0.986,
  0.819). Mechanism: answers were losing points for statement granularity, not content.
- **A19 CoT refuted:** 0.7478 to 0.6887; answers 35.6 to 26.0 words (−27%); lost 14 of 26 questions. Mechanism: once the
  reasoning enumerates the facts, the answer becomes a summary of reasoning, and fewer statements means lost recall.
- **A20 temperature and noise floor:** temperature 0.2 to 0.0 moved answer_correctness −0.013 (not a result) and was
  adopted for reproducibility. The same config scored 0.7752 and 0.7478: **noise floor 0.027**.
- **A6, A9, A10 (three refuted retrieval refinements):** slide-level chunking (R@5 0.923 to 0.577), per-parent
  capping (distinct contexts 3.5 to 5.0, hit unchanged), MMR (hit@8 1.000 to 0.962). **Every post-retrieval
  refinement measured worse than leaving it out**, so the winning pipeline is the simplest one.
- **A15:** `context_entity_recall` unreliable (worked example above).

### 8.3 The effect-size table, the one slide that matters (A20)
| Change | Δ answer_correctness | vs noise 0.027 |
|---|---|---|
| defect fixes | +0.111 | 4x, established |
| strict to few_shot | +0.092 | 3x, established |
| few_shot to CoT | −0.059 | 2x, established, mechanism confirmed |
| cross-encoder (A16) | +0.029 | ~1x, **not established** |
| multi-query (A16) | +0.014 | below, **not established** |
| temperature 0.2 to 0.0 | −0.013 | below, not established |

The later sweep (`eval/comparison_results.md`, few_shot prompt) ranks `dense+multi_query+cross_encoder` first at
0.7752 and `hyde+none` last at 0.7082. Its spread (0.067) is larger than the noise but its adjacent gaps are mostly
inside it. Say "the top three are not separable" if asked.

---

## 9. Statistics and honesty

- **Single run per configuration, no significance tests.** The only variance estimate is 0.027 from one repeated
  config. The fix is repeated runs per config and paired tests over per-question scores (LEARNING_GUIDE Part 11).
- **Multiple comparisons.** 8 variants × 7 metrics = 56 numbers; picking the winner post hoc overstates its margin.
- **Where the noise comes from** (A19/A20): stochastic multi-query variant generation, and nondeterministic server
  numerics that survive temperature 0 (greedy decoding is deterministic in theory; floating-point non-associativity
  under batching is not). No setting removes it; only repetition averages it.
- **Judge risk:** a 7B local judge, never validated against hand labels (explicitly parked, so say it is a limitation,
  do not hide it).
- **Hypothetical dollars** (section 7).
- **Ground truth is the ceiling** (H5).

---

## 10. Limitations to state, in your own words

1. 26 questions, one course, one 22-document corpus (now 37 files, unmeasured).
2. 7B judge, unvalidated; one example above shows it missing a literal quote.
3. One run per configuration; reranking and multi-query gains are not established.
4. `context_entity_recall` and the `completeness` composite are unreliable here.
5. The tutoring layer is not measured by these metrics.
6. The measured prompt (`few_shot`) is **not** the prompt the chat uses in production. The chat uses the Socratic
   `teaching_prompt` (`src/generation/teaching_prompt.py`). The RAGAS numbers describe the answer pipeline under the
   evaluation prompt. **[verify before presenting]** that `src/config.py` defaults match the config whose table you are
   quoting; today's defaults are dense, no multi-query, no reranker, which is not the A20 "best" config.
7. Questions are recall of course material, so conclusions about prompts (CoT) do not generalise to derivation tasks.

---

## 11. The chat turn and the tutoring layer: what is sent, what comes back

The tutor lives in `src/tutor/` and `api/routes/chat.py`. Principle: **policy lives in code, a model only phrases.**
Which concept a message is about, whether an answer is right, how understanding changes, which question or chip comes
next: all deterministic and unit-tested. A model is used in two advisory places (`src/tutor/llm.py`) and for the
explanation itself.

### 11.1 One turn, with the real inputs

The browser POSTs `/chat`:

```json
{"session_id": "<uuid per chat>", "question": "what is a page table?", "model_name": "llama3.1:8b",
 "detail_level": "undergrad", "socratic": true}
```

| Step | Where | What happens |
|---|---|---|
| 1. Plan | `engine.plan_turn(state, message)` | Triage (distress, off-scope, prompt injection, smalltalk) then `conversation.classify` gives one intent (answer, question, hint, tell-me, skip, ack, format, capability, dissatisfied, struggle, quiz, path, lost...). If a Socratic question is pending, the message is graded or handled first. Result is either an authored `Reply` (no retrieval, no model) or a `RagPlan(query, concept_id, lead, resume_line, flags)` |
| 2a. Authored turn | `chat.py` | Text is streamed in 24-character `token` events, then a `ui` event, then an empty `sources` event. About half of real chat turns end here |
| 2b. Retrieve | `pipeline._retrieve_candidates(plan.query)` in a thread | Dense bge-large retrieval, parent expansion (Section 2). A "continue / bullet points" turn reuses the previous turn's context instead |
| 3. Relevance gate | `chat.py` | If the best score is below `chat_min_relevance` (0.60) **and** the query names no course concept, answer with the authored off-topic bridge and make no model call. Measured on this corpus: "what is fear / love / football" score 0.53 to 0.59, real course questions 0.65 to 0.94; borderline "hard link vs soft link" is 0.61, so 0.60 only catches the unambiguous cases |
| 4. Prompt | `teaching_prompt.build_teaching_prompt` | detail-level template + the strict length rules (at most 3 short sentences, about 55 words, no headings, one example) + last 6 turns of history (answers cut to 900 chars) + an optional misconception note + the retrieved context + the student's message |
| 5. Generate | `chat._ollama_stream` | Ollama `/api/generate`, `stream: true`, `keep_alive: "30m"`, options `temperature 0.0`, `num_predict 150` (`chat_max_tokens`), `num_ctx 4096` |
| 6. Shape | `tutor/shaping.SentenceGate` | Text is released only at sentence or line boundaries. At most 5 sentences or lines (`chat_max_units`): once reached, the model is stopped early. If the budget cut the model off, the unfinished tail is dropped, so an answer never ends mid-word. One quiet retry with half the context if Ollama fails before the first sentence |
| 7. Finish | `engine.finish_rag` | Appends at most **one** authored Socratic question (`choose_question(after_explanation=True)`: predict or consequence first, since the student was just told the idea), or three follow-up chips. Never quizzes after a refusal, never stacks a second question on a pending one |
| 8. Events | SSE | `token` (many), `ui` (kind, chips, concept card, pending question, events), `sources` (end of turn), or `error` |

The chat's token budget (150) is **not** `GenerationConfig.max_tokens` (900). That one belongs to the evaluated
pipeline, and the RAGAS numbers in this guide were measured with it and with the `few_shot` prompt, not with the chat
teaching prompt. Say this out loud if asked whether the chat is what was measured.

Grading a reply to a Socratic question (also no retrieval): `pedagogy.classify_answer` matches the student's text
against the question's authored regex groups and returns CORRECT, PARTIAL, MISCONCEPTION or UNCLEAR. State moves
UNKNOWN, INTRODUCED, ATTEMPTED, PARTIALLY_UNDERSTOOD, UNDERSTOOD, MASTERED (MASTERED only through a correct TRANSFER
question). Only when the keys cannot read an earnest free-text answer does `llm.realise_turn` make one JSON-mode Ollama
call (`format: json`, `num_predict 260`); its suggested label is clamped by `apply_advisory` to at most one level up and
never to UNDERSTOOD, and its prose never changes state.

### 11.2 The pieces

| Piece | What it does | Why it exists |
|---|---|---|
| Knowledge model (`os_course.py`) | 30 concepts, 96 authored questions with regex answer keys, 16 misconceptions with a probe and a correction, 8 starters, a 30-step learning path | The tutor needs to know what to ask without a model deciding what is correct |
| Question policy | Type from state (recall first, then why/predict, then analysis, transfer last); 4-turn cooldown; a question once asked, even if skipped, is never repeated; a correct answer earns one harder question; after 2 misses it explains instead of asking again | Socratic without being a nag |
| Intents (`conversation.py`) | hint, just tell me, skip, example, quiz, pause, path, lost, struggle (confused, overwhelmed, frustrated, repeat, uncertain), plus the short real-world messages below | Respond to how the student feels, not only what they ask |
| Short messages | "done / yes / ok" with a question open nudges toward a real attempt and keeps the question; with nothing open it moves to the next idea in the path. "next" always advances. "hi bro", "thanks", "how are you", "who are you" get a warm one-liner plus course chips. "in simple words" gets a simpler explanation; "as bullet points / step by step" re-shapes the last answer (no new quiz question); "give me a video / ppt" gets an honest text-only reply; "I'm not satisfied" offers three fixes | Real tutoring chats are dominated by messages of three words or fewer; a tutor that treats them as questions looks broken |
| Never-repeat guard | The same authored reply is never sent twice in a row | A canned line repeated back to back reads as a stuck bot |
| Triage (`triage.py`) | Distress, off-scope, prompt injection get fixed replies, no retrieval or model | Must not depend on a model being reachable |
| Follow-ups (`followups.py`) | Exactly three chips per answer, each a complete message: authored concept chips (example, test my understanding, what to know first or how it connects), chips from the slide titles the answer was grounded in (one-word or numbered headings are rejected), padded with fixed actions ("Show an example", "Next topic", "Where should I start?"). Model-written follow-ups exist but are off by default (`OS_RAG_MODEL_FOLLOWUPS=1`) because they cost a second model call | A student who knows nothing is never facing an empty box |

### 11.3 How to demo it (5 minutes)
1. Open the app. The empty chat shows starter questions and the course map. Say "I know nothing about this."
2. Tap *"I'm new to operating systems. Where should I start?"*: authored learning path, no model call, instant.
3. Tap the first chip, or ask *"What is a process?"*. A short grounded answer with sources, then **one** Socratic question and three chips.
4. Reply **"done"**: it asks for a real attempt instead of grading "done". Reply **"no idea"**: a simpler explanation and an easier way in.
5. Say *"hint"*, then *"just tell me"*: the ladder, hint then reveal. Say *"next"*: it moves to the next idea.
6. Say *"in bullet points"*: the last answer re-shaped, no new quiz.
7. Say *"test my understanding"*: a 3-question quiz and a summary. Say *"skip"*: the next question is a different one.
8. Ask *"what is fear"*: a short bridge back to the course, no model call. Say *"give me a video"*: honest text-only reply.
9. Resize the window to a phone width: chats move into a drawer, settings fold away, chips become full-width taps.

If asked "is it evaluated?": there is no RAGAS-style score for the tutor. See Q&A 21 for the honest answer. What does exist is 877 unit and dialogue tests, and live runs with Ollama. A reply-length check from one live session: median 270 characters, 90th percentile about 510 (including the Socratic question).

---

## 12. Where the research paper fits

The second research track in this repo, **Reference-Choice Robustness (RCR)**, is a separate paper about benchmark
validity on tasks with many correct answers. It does not use this chatbot. Everything about it (numbers, controls,
reviewer attacks, talk track, discrepancies) is in **Part 1: `docs/GUIDE_PART1_RESEARCH_PAPER.md`**.

The one link between the parts: both are about *measurement validity*. Here, a judge's reading of statements; there, a
metric's reference choice. Same lesson: before comparing systems, test whether the benchmark can resolve the difference
you care about.

---

## 13. Talk tracks

### 13.1 Ten-minute track (7 slides, matching the department's format)
| Min | Slide | Say |
|---|---|---|
| 0:00 | 1 Title | OS Tutor: a RAG tutor, and what measuring it taught us |
| 0:30 | 2 Introduction and objective | Students learn OS from slides plus a textbook; objective: a grounded tutor that teaches Socratically, and an honest evaluation of which design choices matter |
| 2:00 | 3 Methodology (architecture) | The pipeline diagram (section 2); small chunks to match, parent to read; the tutor layer above it; the judge setup (generator llama3, judge qwen2.5, different families) |
| 4:00 | 4 R&D 1: prompt and evaluation | The few_shot prompt verbatim; the row sent to RAGAS; the seven metrics in one line each; the worked example's three numbers (0.95, 0.29 from a case mismatch, 0.56) |
| 6:00 | 5 R&D 2: results | The effect-size chart (section 8.3) against the 0.027 band; refusal vs faithfulness; defects that looked like results |
| 8:00 | 6 Conclusion | Fix defects first; prompt shape beat every retrieval technique; most comparisons are inside the noise; limitations |
| 9:30 | 7 References | RAGAS (Es et al.), HyDE (Gao et al.), Lewis et al. RAG, Zheng et al. LLM-as-judge, OSTEP |

### 13.2 Twenty-minute track
Add, in order: the golden-set history (section 4, 2 min); the full worked example as a build-up slide per metric
(section 6, 4 min); the three refuted retrieval refinements (A6, A9, A10, 1.5 min); the tutor demo (section 11.3, 4 min);
then 3 minutes of questions. (If the examiner asks about the paper, use Part 1's talk track.) Cut the retrieval table (A12) first if you run short.

### Delivery tips
- Lead with a result that surprised **you**. "BM25 looked terrible; the cause was our chunker" earns trust fast.
- When you cite a number, say what it is *against* (the 0.027 band).
- Say "not established" about the reranking gain. Saying it first removes the examiner's best attack.

---

## 14. Run it yourself

```bash
# 0. one-time: the embedding models are not cached on this machine right now (HF cache holds only lock dirs),
#    and src/evaluation.py sets HF_HUB_OFFLINE=1. Download once with the network up:
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 .venv/bin/python -c "from sentence_transformers import SentenceTransformer as S; [S(m) for m in ('BAAI/bge-large-en-v1.5','BAAI/bge-small-en-v1.5')]"

# 1. retrieval metrics only (no LLM, seconds)
PYTHONPATH=. .venv/bin/python -m eval.retrieval_eval

# 2. RAGAS smoke test: 3 questions, 2 variants (needs Ollama with llama3 and qwen2.5:7b pulled)
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --quick

# 3. the fixed-config prompt and temperature comparisons
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --prompts few_shot cot
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --temperatures 0.0 0.2

# 4. the tutor and chat-turn tests (no model needed)
PYTHONPATH=. .venv/bin/pytest tests/tutor -q

# 5. run the chatbot (port 8000 is free on most machines; pass another --port if not)
PYTHONPATH=. .venv/bin/uvicorn api.main:app --port 8000
cd frontend && npm install && npm run dev
```
`ollama list` on this machine shows `llama3.1:8b`, `qwen2.5:7b`, `qwen3:8b`, `gemma2:9b`, `mistral:7b-instruct`,
`phi4-mini`. **There is no `llama3:latest`**, which is `GenerationConfig.model_name`'s default. Pull it or change the
default before running generation. **[unverified]** whether that default is overridden elsewhere.

---

## 15. Cheat sheet

**Files.** `src/config.py` (every default and the reason for it), `src/pipeline.py` (retrieve, select, expand),
`src/generation/local_llm.py` (the four prompts), `src/evaluation.py` (judge wiring, composites, workbook),
`eval/retrieval_eval.py`, `eval/ragas_eval.py`, `eval/eval_set.json`, `FINDINGS.md`, `HYPOTHESES.md`.

**Definitions in one line.**
- *Recall@k*: some cited parent is in the top k. *full@k*: all of them are. *MRR*: mean of 1 / rank of the first hit.
- *context_precision*: average precision of per-context usefulness verdicts. *context_recall*: share of reference
  statements the context supports.
- *faithfulness*: share of answer statements the context supports. *answer_correctness*: 0.75 × statement F1 + 0.25 ×
  embedding similarity to the reference.
- *RRF*: `Σ 1/(60 + rank)`. *HyDE*: embed a hypothetical answer. *Multi-query*: embed several rewrites and fuse.

**Memorise.** 0.027 · +0.111 · +0.092 · −0.059 · 26 questions · 22 documents measured, 37 now · recall@5 = 1.000 for dense.

---

## 16. Hostile Q&A (practise answering out loud)

**1. Why a 7B judge? That is not trustworthy.**
It is a local-only constraint (an 8 GB GPU) and I chose a different model family from the generator to avoid
self-preference bias. You are right it is weak: I showed one case where it missed a quote that was literally in the
context. I did not validate it against hand labels and I list that as a limitation. H6 proposes re-judging stored answers
with a stronger model, and the expected cost with GPT-4o-mini is about $0.26 by our own token accounting.

**2. Why only 26 questions?**
It is a case study and every question was hand-checked against a named slide. 26 cannot resolve differences of a few
hundredths, which is exactly why I measured the noise floor (0.027) and refused to call anything inside it a result.

**3. What does faithfulness = 1.0 actually mean?**
Every statement the answer made was supported by the context. A refusal makes no statements, so it also scores 1.0.
That is why it must never be used alone: dense had the lowest faithfulness yet the second-highest correctness.

**4. Your reranking and multi-query gains are within noise. So what did you learn?**
That is the finding. Technique choice (+0.029, +0.014) is inside a 0.027 floor; fixing defects (+0.111) and one prompt
(+0.092) are not. I would need repeated runs per config to say more.

**5. How do you know the noise is 0.027? One pair of runs.**
Correct: it is one estimate, from two scorings of one config. It is a lower-confidence bound on the real noise, which
makes my claims conservative. Repeated runs are the next step.

**6. Is the benchmark biased?**
It was, and I found and fixed that (A11): questions avoiding the source's vocabulary penalised BM25 far more than dense.
BM25 recall@5 jumped 0.500 to 0.885 with no retriever change. It can still be biased: reference answers are less complete
than the corpus (H5).

**7. Why not a bigger embedding model?**
Dense recall@5 is already 1.000. There is nothing to win, and a larger model cannot recover meaning absent from the text.

**8. Why does a tiny chunk beat a whole slide?**
A slide embedding averages five or six unrelated bullets and is less discriminative than one focused bullet (A6: R@5
0.923 to 0.577). So match small, read big.

**9. Isn't `context_entity_recall` broken?**
For this content, yes: it intersects exact strings from two LLM extractions. On the worked example "Ready" and "ready"
differ, giving 0.29 with every concept present. I flagged it (A15), and it should leave the composite (H7).

**10. Why did chain-of-thought hurt? Everyone says CoT helps.**
It helps derivation. These are recall questions. The reasoning section moved content out of the answer, so answers got 27%
shorter, and `answer_correctness` is an F1 over statements, so fewer statements means lost recall. It lost 14 of 26.

**11. Is making answers longer just gaming the metric?**
It would be, and I explicitly decided **not** to pursue terser or longer answers to move the number (HYPOTHESES "not
pursuing"). The few_shot win aligned answer *shape* with the reference without changing what the model knows.

**12. What is `answer_correctness` really?**
0.75 × F1 over decomposed statements (TP, FP, FN judged by the LLM) + 0.25 × embedding similarity. In the worked example
TP 2, FP 0, FN 5 gives F1 0.444, and the score is 0.5614.

**13. Why temperature 0?**
For reproducibility, not score (−0.013 is inside noise). It also makes query rewriting repeatable. It cannot remove
server numerical nondeterminism.

**14. Why dense retrieval and not hybrid?**
Fusing a strong retriever with a weaker one hurt (A5, A12): RRF weights BM25's rankings equally. Dense also needs no
LLM call.

**15. Why does HyDE rank the top chunk worst yet find more sources?**
It embeds a hypothetical answer that mentions several facets, so it matches more sources but matches the single closest
passage less sharply. I predicted that breadth would raise answer quality and it did not (A13: +0.002).

**16. What if your parent expansion injects noise?**
Cost was measured (F3) and capped at 400 tokens with windowing around the match. Slides are cheap, pages expensive.
Refusals fell from 11.7% to about 0%.

**17. How do you know retrieval, not generation, is the bottleneck?**
Correlations (A2) and a controlled comparison: entity recall <0.35 gave 0.578 correctness, ≥0.60 gave 0.717 with the same
model and prompt. Caveat: entity recall is itself noisy (A15), so I lean on context_recall, which is unaffected.

**18. Does it generalise beyond OS?**
Not claimed. One course; the prompt result in particular may depend on answers being recall-style.

**19. Would a human agree with the judge?**
Unknown: no human validation was done. That is stated as a limitation.

**20. Why local models? Why not GPT-4?**
Cost, privacy and reproducibility. The dollar figures are hypothetical, priced at API rates for comparison only.

**21. Is the tutoring layer evaluated?**
Honestly: not with RAGAS or a learning study. RAGAS evaluates the **answer pipeline** with the `few_shot` prompt, not the
Socratic chat prompt or the question flow. The tutor's behaviour is deterministic by design and covered by unit tests
(concept-state transitions, grading, triage precision, chip rules, short-message handling, reply-length bounds), but there is no measure of whether students learn
more. A study would need real students or at least simulated ones. I treat that as future work.

**22. Why is Socratic policy in code and not a prompt?**
Because "is this answer right?" and "what should happen next?" must not depend on a model's mood. Code decides, the model
only phrases, and its one classification is clamped to move a concept at most one level and never to UNDERSTOOD.

**23. How does the tutor help a student who knows nothing?**
It never shows an empty box: starter questions, a learning path, "what should I know first?", "what comes next?", chips
from the retrieved sources' own slide titles, and validated model-written questions. A "where do I start" message is
answered with authored orientation.

**24. What stops the tutor quizzing on something it just refused to answer?**
`finish_rag` skips the Socratic question when the answer is a refusal, and never stacks a second question on a pending one.

**25. What did you get wrong along the way?**
Plenty, and it is in FINDINGS: an MMR conclusion drawn from a configuration that could not diversify (F13, A10); a
"retrieval is the gap" claim that rested on a broken metric (A15); a blanket "reranking hurts" from a biased benchmark
(A7 superseded by A14/A16). The method note: measure before prescribing.

**26. What would you do with another month?**
Repeat each config 3 to 5 times with paired tests; rewrite references from the sources and re-baseline once (H5);
re-judge with a stronger model (H6); re-measure on the 37-file corpus; add a small student study for the tutor.

---

## Appendix A: reproduce the judge trace for any stored row

Re-scores one row of `eval/ragas_details.xlsx` with the real metrics and logs every judge call. Run it with the network
available once (bge-small must be downloaded) and Ollama serving `qwen2.5:7b`.

```python
# save as trace_row.py in the repo root; run: PYTHONPATH=. .venv/bin/python trace_row.py 8
import asyncio, json, sys, openpyxl
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (answer_correctness, answer_relevancy, answer_similarity, context_entity_recall,
                           context_precision, context_recall, faithfulness)
from ragas.run_config import RunConfig

LOG, CUR = [], ["?"]
class Tracing(ChatOllama):                       # same trick as src/evaluation.py: wrap the ASYNC path too
    async def _agenerate(self, messages, stop=None, run_manager=None, **kw):
        res = await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kw)
        LOG.append({"metric": CUR[0], "prompt": "\n".join(str(m.content) for m in messages),
                    "response": res.generations[0].message.content})
        return res

rows = list(openpyxl.load_workbook("eval/ragas_details.xlsx", read_only=True)["All Results (by question)"].iter_rows(values_only=True))
d = dict(zip(rows[0], rows[int(sys.argv[1])]))
row = {"question": d["question"], "answer": d["answer"],
       "contexts": d["contexts"].split("\n---\n"), "ground_truth": d["ground_truth_answer"]}

llm = LangchainLLMWrapper(Tracing(model="qwen2.5:7b", base_url="http://localhost:11434"))
emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5", model_kwargs={"device": "cpu"}))
metrics = [context_precision, context_recall, context_entity_recall, faithfulness, answer_relevancy,
           answer_correctness, answer_similarity]
for m in metrics:
    m.llm = llm
    if hasattr(m, "embeddings"): m.embeddings = emb
    m.init(RunConfig(max_workers=1))
try: asyncio.get_event_loop()
except RuntimeError: asyncio.set_event_loop(asyncio.new_event_loop())
for m in metrics:
    CUR[0] = m.name
    print(m.name, m.score(row))
json.dump(LOG, open("judge_trace.json", "w"), indent=1)   # every prompt and raw reply
```
Row index 8 is the example in section 6; indices run 1 to 26. On this row the call counts were: precision 5, recall 1,
entity 2, faithfulness 2, relevancy 3, correctness 3, similarity 0 = 16.

## Appendix B: files read to write this guide

`src/evaluation.py`, `eval/ragas_eval.py`, `eval/retrieval_eval.py`, `eval/eval_set.json`, `src/generation/local_llm.py`,
`src/retrieval/{dense,multi_query,hyde,hybrid_rrf}.py`, `src/context_expansion.py`, `src/chunking/{structure_aware,page_aware}.py`,
`src/reranking/cross_encoder.py`, `src/token_tracking.py`, `src/config.py`, `FINDINGS.md`, `HYPOTHESES.md`,
`LEARNING_GUIDE.md` (Part 10 and 11), `eval/{comparison,prompt_comparison,temperature_comparison}_results.md`,
`eval/ragas_details.xlsx`, `eval/pipeline_runs.xlsx`, ragas 0.1.14 `metrics/_*.py` in `.venv`,
`research/ssr_pilot/results/rcrc/*.json|csv`, `paper/PAPER_FINAL.md`, and `src/tutor/*`, `api/routes/chat.py`.
