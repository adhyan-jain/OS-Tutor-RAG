"""GET /models — lists model names available on the configured Ollama server,
for a frontend dropdown."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException

from api.auth import AUTH_ENABLED, require_user_email
from src.config import PipelineConfig

router = APIRouter()

_OLLAMA_BASE_URL = PipelineConfig().generation.ollama_base_url


def _list_models() -> list[str]:
    try:
        response = httpx.get(f"{_OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Could not reach Ollama at {_OLLAMA_BASE_URL}: {exc}"
        ) from exc

    data = response.json()
    return [model["name"] for model in data.get("models", [])]


# Same on/off dependency pattern as chat.py: the auth dependency is only
# referenced in the route signature -- and therefore only ever invoked -- when
# AUTH_ENABLED is true.
if AUTH_ENABLED:

    @router.get("/models")
    def list_models(user_email: str = Depends(require_user_email)) -> list[str]:
        return _list_models()

else:

    @router.get("/models")
    def list_models() -> list[str]:
        return _list_models()
