"""FastAPI app wrapping the existing RAG pipeline (src/) as an HTTP API.

Builds one shared RAGPipeline instance at import time (api.pipeline_instance)
and loads its retriever's index on startup -- using an existing local index
or falling back to a full local rebuild (see api.pipeline_instance.load_index
for the exact order) -- so every request reuses the same embedding model /
retriever / reranker rather than rebuilding them per call.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import pipeline_instance
from api.pipeline_instance import load_index
from api.routes import chat, models, tutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.main")


def _use_installed_model() -> None:
    """If the configured Ollama model (default llama3:latest) is not pulled on
    this machine, use the first installed one from chat_model_preference so
    query rewriting and other background LLM calls do not 404. Best effort."""
    gen = pipeline_instance.pipeline.config.generation
    try:
        import httpx

        names = [m["name"] for m in httpx.get(f"{gen.ollama_base_url}/api/tags", timeout=5).json().get("models", [])]
    except Exception:
        return
    if not names or gen.model_name in names:
        return
    pick = next((m for m in gen.chat_model_preference if m in names), names[0])
    logger.warning("Configured model %s is not installed; using %s instead.", gen.model_name, pick)
    gen.model_name = pick


@asynccontextmanager
async def lifespan(app: FastAPI):
    _use_installed_model()
    load_index()
    yield


app = FastAPI(title="os-tutor-rag API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    # any local dev port (the frontend may run on 3000, 3200, ...)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(models.router)
app.include_router(tutor.router)


@app.get("/health")
def health() -> dict:
    """Liveness/readiness check for a deploy host.

    Always 200 (the process being reachable at all is the liveness signal);
    ``index_loaded`` reports whether the retriever actually has a usable
    index, so a health check -- or a human -- can tell "process is up" apart
    from "index failed to load and /chat will error on retrieval".
    """
    return {
        "status": "ok",
        "index_loaded": pipeline_instance.index_loaded,
    }
