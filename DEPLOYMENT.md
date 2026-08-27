# Deployment

This document makes the repo deployable in a container. It does not pick a
host, and it does not stand up an autoscaled service -- see "Scale" below.

## What's here

- `api/Dockerfile` -- backend image (FastAPI app in `api/main.py`). Build
  context is the **repo root**, not `api/`, because `api/*.py` imports from
  `src/` (`from src.config import PipelineConfig`, etc). Build with:
  ```
  docker build -f api/Dockerfile -t os-tutor-rag-api .
  ```
- `requirements-docker.txt` -- CPU-only pins for the backend image (see
  "The CUDA-torch problem" below). `requirements.txt` (the dev-machine file)
  is untouched.
- `frontend/Dockerfile` -- frontend image (Next.js app in `frontend/`).
  Build context is `frontend/` itself.
- `docker-compose.yml` -- both services wired together for local full-stack
  testing, plus the host's Ollama.
- `GET /health` on the backend (`api/main.py`) -- liveness + index-loaded
  status.

## Persistent volume: `data/index/`

`data/index/` (`dense.faiss`, `dense_chunks.pkl`, `bm25.pkl`, `manifest.json`)
holds the built retrieval index. `api/pipeline_instance.py`'s `load_index()`
runs on every process startup and, in order: uses whatever's already in
`data/index/` on disk, else rebuilds from `data/raw/`, else starts up with no
index loaded (retrieval and `/chat` then fail until one exists -- see
`/health`).

Mount `data/index/` as a volume so a container restart reuses the index
instead of rebuilding it (rebuilding re-embeds the whole corpus, which is
slow).

`data/raw/` and `data/processed/` are also mountable (see
`docker-compose.yml`) if you want the from-scratch rebuild path available
inside the container; skip them if you always seed `data/index/` directly
(e.g. by copying a built index onto the volume).

The path itself is configurable via `INDEX_DIR` (new: `src/config.py`'s
`PathConfig.index_dir` / `RetrievalConfig.index_dir` now read
`os.environ.get("INDEX_DIR", "data/index")` at construction time via a
`default_factory`, rather than being frozen at import time) if you'd rather
mount the volume somewhere else.

## Environment variables

| Var | Required? | Default | Purpose |
|---|---|---|---|
| `OLLAMA_HOST` | no | `http://localhost:11434` | Base URL of the Ollama server the backend talks to for generation (`api/routes/chat.py`), the model list (`api/routes/models.py`), and every other LLM call in `src/` (HyDE, multi-query, misconception check, LLM rerank). **New**: `src/config.py`'s `GenerationConfig.ollama_base_url` now reads this via a `default_factory` -- previously it was a hardcoded dataclass default with no env override. In `docker-compose.yml` this is set to `http://host.docker.internal:11434` so the container reaches the *host* machine's Ollama (Ollama is never containerized -- see below). |
| `INDEX_DIR` | no | `data/index` | Where the retrieval index lives on disk. Point this at your mounted volume. |
| `NEXT_PUBLIC_API_BASE` | no | `http://localhost:8000` | **Frontend, build-time.** The backend URL the *browser* calls. `frontend/lib/api.ts` already read this via `process.env.NEXT_PUBLIC_API_BASE` before this task -- no code change was needed there, only wiring it through `frontend/Dockerfile` as a build `ARG`. Because `Chat.tsx` is a client component, this must be a URL reachable from the end user's browser (e.g. the backend's host-published port), **not** the compose network name (`http://backend:8000` resolves only container-to-container and would silently break the browser's requests). Next.js also inlines `NEXT_PUBLIC_*` vars into the client bundle at build time, so this must be set as a Docker build arg, not just a runtime `environment:` entry. |

`OLLAMA_HOST` and `INDEX_DIR` are exactly what's already in `.env.example`,
alongside the `src/config.py` change that makes them actually take effect.

## The CUDA-torch problem

`requirements.txt` pins `torch==2.4.0+cu121` (the dev machine's GPU build, an
RTX 4060) via `--extra-index-url https://download.pytorch.org/whl/cu121`.
That wheel requires an NVIDIA GPU and matching CUDA runtime and will not
install (or would install but be unusable) in a typical CPU-only deploy
container.

Resolved with a separate `requirements-docker.txt` at the repo root, used
only by `api/Dockerfile`:
- Same pins as `requirements.txt` for everything the API process actually
  imports, except `torch`, which points at the CPU wheel index
  (`https://download.pytorch.org/whl/cpu`, `torch==2.4.0` with no `+cuNNN`
  suffix) instead.
- Drops `vllm` (backend defaults to `"ollama"`; the `vllm` import in
  `src/generation/local_llm.py` is inside the `backend == "vllm"` branch, so
  it's never imported when running against Ollama) and the eval-only
  packages (`ragas`, `langchain-community`, `datasets`, `openpyxl`) that are
  only ever imported lazily inside `src/evaluation.py` functions the API
  never calls. `tiktoken` is kept, unlike those -- it
  turned out to be a hard top-level import (`src/token_tracking.py`, pulled
  in by `src/pipeline.py` at module load for token accounting), caught only
  by actually starting the container (see "Testing" below) rather than by
  static analysis of the eval-only cluster it looked like it belonged to.

`requirements.txt` itself is untouched, since it's what the user's own GPU
dev machine installs from (and per `DELAYED_TASKS.md` #1, it already has its
own pin/Python-version reproducibility issues on that machine, unrelated to
this task).

The backend Dockerfile also deliberately pins Python 3.11 (`python:3.11-slim`)
rather than whatever the dev machine runs, because DELAYED_TASKS.md #1 notes
the dev machine's Python 3.14 has no prebuilt wheels for several of these
pins (`faiss-cpu==1.8.0`, `torch==2.4.0`); 3.11 is a version every pin here
has a wheel for.

## Ollama stays external

Ollama is **not** containerized here and is not expected to be. It must be
reachable from wherever the backend container runs:
- **Local docker-compose testing**: the backend container reaches the *host*
  machine's already-running Ollama via `http://host.docker.internal:11434`,
  which requires `extra_hosts: ["host.docker.internal:host-gateway"]` in
  `docker-compose.yml` (Linux Docker; Docker Desktop on Mac/Windows resolves
  `host.docker.internal` without it, but the entry is harmless there too).
- **A real deploy**: point `OLLAMA_HOST` at wherever Ollama actually runs --
  a GPU host you operate, or a remote Ollama-compatible endpoint. This repo
  does not run or manage that host.

### Required host-side prerequisite: Ollama must not be loopback-only

`extra_hosts`/`OLLAMA_HOST` alone are **not enough** on this machine (and any
similarly-configured Linux host). Ollama's default bind is
`127.0.0.1:11434` -- loopback only, confirmed here via `ss -tlnp | grep
11434` showing `127.0.0.1:11434` rather than `0.0.0.0:11434`. Traffic from a
container via `host.docker.internal`/`host-gateway` arrives on the **docker
bridge interface**, not loopback, so a loopback-only bind is structurally
unreachable from any container -- no compose/Dockerfile change on the
container side can fix this; the fix has to happen where Ollama itself
binds.

Symptom: `curl http://localhost:8000/models` (or a `/chat` request) returns
```json
{"detail":"Could not reach Ollama at http://host.docker.internal:11434: timed out"}
```

Fix: restart Ollama listening on an interface the container can reach, e.g.:
```
OLLAMA_HOST=0.0.0.0 ollama serve
```
(or however Ollama is managed on your machine -- a systemd unit's
`Environment=OLLAMA_HOST=0.0.0.0`, etc). This is a one-line change but it's a
host-level one, so it isn't made automatically by anything in this repo --
restarting a long-running local service on someone's behalf isn't something
`docker-compose.yml` should do silently. It's called out here because it's
the single most likely first-run trap: the compose stack builds and starts
cleanly, `/health` reports `index_loaded: true`, and only `/models`/`/chat`
fail, in a way that looks like a container-networking bug rather than an
Ollama bind setting.

## Scale

This is designed for **single/low-concurrency use**. Generation runs against
a local/self-hosted LLM server (Ollama) that this repo assumes is one
process on one machine -- there is no batching, queueing, or horizontal
scaling story for the generation backend. Don't put the backend behind an
autoscaler expecting to scale request concurrency the way a hosted-model API
(OpenAI/Anthropic/etc) would; extra backend replicas would still all be
serializing generation calls against the same single Ollama instance.

## `/health`

`GET /health` on the backend returns:
```json
{"status": "ok", "index_loaded": true}
```
`status` is always `"ok"` if the process can answer at all (that's the
liveness signal). `index_loaded` reports whether `load_index()` actually
ended up with a usable index (`api/pipeline_instance.py` sets a module-level
flag at the end of a successful load) -- so a deploy host's health check, or
a human, can tell "process is up" apart from "index failed to load and
`/chat` will error on retrieval."

## Picking a host (not done here)

This makes the repo deployable, it doesn't commit to a specific host. What
you'll generically need, whenever you pick one:
- Somewhere to run the backend container that the frontend (and end users'
  browsers) can reach -- a VPS, Render/Railway/Fly/etc, or your own machine.
- A GPU host (or your own machine) for Ollama, reachable from the backend
  via `OLLAMA_HOST`.
