"""FastAPI app wrapping the existing RAG pipeline (src/) as an HTTP API.

Builds one shared RAGPipeline instance at import time (api.pipeline_instance)
and loads the on-disk index into its retriever on startup, so every request
reuses the same embedding model / retriever / reranker rather than rebuilding
them per call.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
