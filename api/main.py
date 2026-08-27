"""FastAPI app wrapping the existing RAG pipeline (src/) as an HTTP API.

Builds one shared RAGPipeline instance at import time (api.pipeline_instance)
and loads its retriever's index on startup -- using an existing local index
or falling back to a full local rebuild (see api.pipeline_instance.load_index
for the exact order) -- so every request reuses the same embedding model /
retriever / reranker rather than rebuilding them per call.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import pipeline_instance
from api.pipeline_instance import load_index
from api.routes import chat, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_index()
    yield


app = FastAPI(title="os-tutor-rag API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(models.router)


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
