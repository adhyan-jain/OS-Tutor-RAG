"""GET /models — lists model names available on the configured Ollama server,
for a frontend dropdown."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

from src.config import PipelineConfig

router = APIRouter()

_OLLAMA_BASE_URL = PipelineConfig().generation.ollama_base_url


@router.get("/models")
def list_models() -> list[str]:
    try:
        response = httpx.get(f"{_OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Could not reach Ollama at {_OLLAMA_BASE_URL}: {exc}"
        ) from exc

    data = response.json()
    return [model["name"] for model in data.get("models", [])]
