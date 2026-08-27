# OS-Tutor-RAG

A retrieval-augmented generation pipeline over an operating-systems course
corpus (lecture decks, OSTEP chapters, lab handouts), built as a **technique
comparison study**. Every stage is selected by config, so comparing techniques
is a configuration change rather than a code edit.

```
ingestion -> chunking -> retrieval -> reranking -> diversification -> expansion -> generation
```

The interesting output of this project is not the pipeline but the
**measurements**: which techniques help, which measurably hurt, and which
apparent results turned out to be artifacts of the benchmark rather than
properties of the system. Those are recorded in
[FINDINGS.md](FINDINGS.md) with the evidence for each.

## Techniques implemented

- **Ingestion** — PPTX (per-slide title/bullets/notes), PDF (per-page text),
  DOCX (one Document per heading section)
- **Chunking**, matched to how each format is written rather than swept as a
  tunable axis:
  - `structure_aware` (pptx, docx) — title-qualified bullet children, slide or
    section as parent
  - `page_aware` (pdf) — semantic passages bounded by the page, page as parent
  - `semantic` (plain text) — sentence-similarity boundaries
- **Retrieval** — dense (FAISS + bge-large), BM25, hybrid RRF, HyDE, and
  multi-query as an orthogonal flag that wraps any of them
- **Reranking** — cross-encoder (bge-reranker-large), pointwise LLM-as-judge
- **Diversification** — MMR
- **Context expansion** — retrieved children are replaced by their parent slide
  or page before generation, with a token cap so an oversized parent is
  windowed around the matched passage rather than sent whole
- **Generation** — local LLM via Ollama (llama3) or vLLM

## Configuration

`src/config.py` holds one dataclass tree (`PipelineConfig`), so a full pipeline
configuration is a single object that can be logged and diffed per experiment.

**Defaults are what measured best on this corpus, not what is conventional.**
Reranking, diversification and sparse fusion are all off by default because
each measured *worse* than omitting it, and every such default carries the
measurement that justifies it as a comment. See FINDINGS.md A5, A7, A10.

```python
config = PipelineConfig()
config.retrieval.technique = "hyde"      # dense | bm25 | hybrid_rrf | hyde
config.retrieval.use_multi_query = True  # composes with any of the above
config.reranking.method = "cross_encoder"
```

## Evaluation

Three harnesses, deliberately layered by cost — retrieval is characterised
without an LLM before anything expensive runs, because correctness correlates
far more strongly with the retrieval metrics than with the generator
(FINDINGS.md A2).

| harness | measures | LLM calls | runtime |
|---|---|---|---|
| `eval/retrieval_eval.py` | recall@k, full_recall@k, MRR against the golden set's cited sources | none (except HyDE/multi-query) | seconds |
| `eval/rank_diagnosis.py` | *why* wrong chunks outrank right ones -- dumps the competing chunks | none | seconds |
| `eval/ragas_eval.py` | full RAGAS: faithfulness, correctness, precision, recall, entity recall, relevancy, similarity | ~19 per question | ~30 min per config |

```bash
# characterise retrieval first (cheap)
PYTHONPATH=. .venv/bin/python -m eval.retrieval_eval
PYTHONPATH=. .venv/bin/python -m eval.rank_diagnosis

# then score answer quality for configs worth the time
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --focused
```

`ragas_eval.py` writes a ranked table (`eval/comparison_results.md`),
per-question detail (`eval/ragas_details.xlsx`), and a per-run workbook
(`eval/pipeline_runs.xlsx`) carrying each run's phase summary, metric scores,
LLM call/token counts and an OpenAI-equivalent cost estimate. Results are
written after every variant and `--resume` skips completed ones, so a
multi-hour sweep survives interruption.

The judge model is deliberately a **different family from the generator**
(`qwen2.5:7b` judging `llama3`): scoring a model's answers with that same model
is a known self-preference bias.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# CUDA build of torch, if the GPU should be used for embedding
pip install --index-url https://download.pytorch.org/whl/cu126 "torch==2.13.0+cu126"

# generation and judge models used by the pipeline defaults and the eval suite
ollama pull llama3:latest    # GenerationConfig.model_name default
ollama pull qwen2.5:7b       # EvalConfig.judge_model_name default
ollama pull gemma2:9b        # alternate generation model referenced in src/config.py / teaching-mode code
```

Ollama must be running locally (`ollama serve`, or the desktop app) at
`http://localhost:11434` before starting the backend or running any eval that
calls a model.

Drop course files into `data/raw/` (`.pptx`, `.pdf`, `.docx`), then build the
index:

```bash
PYTHONPATH=. .venv/bin/python -m src.build_index
```

Only new or changed files are re-chunked; the manifest fingerprints the
chunking settings as well as file contents, so changing `ChunkingConfig`
correctly invalidates the cache.

**Legacy `.doc` is not supported** (only `.pptx`/`.pdf`/`.docx`) and is skipped
silently by the eval loader. Convert first:

```bash
soffice --headless --convert-to docx "file.doc"
```

### GPU note

Embedding models default to **CPU** because this project's target machine
shares one 8GB GPU with Ollama, and torch holding VRAM pushed generation from
2.0s to 25.8s per call before OOMing outright. Set
`OS_RAG_EMBEDDING_DEVICE=cuda` for a much faster ingest; the GPU is released
before generation so Ollama still gets the whole card.

```bash
OS_RAG_EMBEDDING_DEVICE=cuda PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --focused
```

## Chat app (API + frontend)

A FastAPI backend and Next.js frontend wrap the pipeline in a chat UI, in
teaching mode: answers arrive as an incremental explanation plus a
comprehension-check question rather than a complete answer, and every reply
cites the slide/section chunks it drew from.

### Backend

Requires an index at `data/index/` (see Setup above) and Ollama running
locally with at least the model(s) you intend to select in the UI pulled.

```bash
PYTHONPATH=. .venv/bin/uvicorn api.main:app --port 8000
```

No `.env` is required for local dev. `api/pipeline_instance.py` tries, in
order: an existing local index at `data/index/`, then a full local rebuild
from `data/raw/`. If you do want to set `OLLAMA_HOST`/`INDEX_DIR`/auth vars
(see `.env.example` for the full list, all optional), copy `.env.example` to
`.env`, fill in the values, and export them (e.g. `set -a; source .env; set
+a`) before starting uvicorn.

`GET /models` proxies Ollama's `/api/tags` for the model dropdown; `POST
/chat` is a server-sent-events endpoint (`session_id`, `question`,
`model_name`, `detail_level`) streaming `token` events, then one `sources`
event, or an `error` event if retrieval or generation fails (e.g. Ollama
unreachable, or the requested model isn't pulled).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:3000` and talks to the backend at
`http://localhost:8000` (override with `NEXT_PUBLIC_API_BASE`). The backend's
CORS is configured for `http://localhost:3000` specifically.

## Layout

```
src/
  config.py            all stage parameters, with measurements justifying defaults
  pipeline.py          orchestration and stage sizing
  chunking/            structure_aware, page_aware, semantic
  retrieval/           dense, sparse_bm25, hybrid_rrf, hyde, multi_query
  reranking/           cross_encoder, llm_rerank
  diversification/     mmr
  context_expansion.py child -> parent substitution, capped and windowed
  embedding_cache.py   model / embedding memoization, GPU release
  token_tracking.py    call and token accounting, cost estimation
  evaluation.py        shared RAGAS scoring
  build_index.py       incremental index build
eval/
  eval_set.json        golden QA set, questions cited to source slides/pages
  retrieval_eval.py    LLM-free retrieval scoring
  rank_diagnosis.py    why wrong chunks outrank right ones
  stage_tuning_eval.py what survives the selection chain
  reranker_eval.py     reranker models and score blending
  ragas_eval.py        full sweep
api/
  main.py               FastAPI app, CORS, startup index loading
  pipeline_instance.py  shared RAGPipeline instance, local/rebuild index loading
  routes/chat.py        POST /chat (SSE streaming), teaching-mode prompting
  routes/models.py      GET /models (proxies Ollama's /api/tags)
  routes/session.py     in-memory per-session chat history
frontend/
  app/                  Next.js App Router pages
  components/           Chat, ModelSelect, DetailToggle, Composer, MessageBubble, SourcesPanel
  lib/                  api client, hand-rolled SSE-over-fetch parser, types
FINDINGS.md            defects, diagnoses, measured effects, refuted hypotheses
```
