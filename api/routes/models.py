"""GET /models — lists model names available on the configured Ollama server,
for a frontend dropdown."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from api.auth import AUTH_ENABLED, require_user_email
from src.config import PipelineConfig

router = APIRouter()

_GEN = PipelineConfig().generation
_OLLAMA_BASE_URL = _GEN.ollama_base_url


def _list_models() -> list[str]:
    try:
        response = httpx.get(f"{_OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Could not reach Ollama at {_OLLAMA_BASE_URL}: {exc}"
        ) from exc

    data = response.json()
    names = [model["name"] for model in data.get("models", [])]
    # Preferred chat models first, so the UI preselects one that is installed
    # (the config default may not be pulled); the rest keep Ollama's order.
    rank = {name: i for i, name in enumerate(_GEN.chat_model_preference)}
    return sorted(names, key=lambda n: rank.get(n, len(rank)))


def _warm(model: str) -> None:
    """Load the model into memory so the first answer is not slow. Best effort."""
    try:
        httpx.post(
            f"{_OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": "", "stream": False, "keep_alive": _GEN.chat_keep_alive},
            timeout=120,
        )
    except httpx.HTTPError:
        pass


class WarmRequest(BaseModel):
    model_name: str


# Same on/off dependency pattern as chat.py: the auth dependency is only
# referenced in the route signature -- and therefore only ever invoked -- when
# AUTH_ENABLED is true.
if AUTH_ENABLED:

    @router.get("/models")
    def list_models(user_email: str = Depends(require_user_email)) -> list[str]:
        return _list_models()

    @router.post("/models/warm", status_code=202)
    def warm_model(request: WarmRequest, background: BackgroundTasks, user_email: str = Depends(require_user_email)) -> dict:
        background.add_task(_warm, request.model_name)
        return {"status": "warming"}

else:

    @router.get("/models")
    def list_models() -> list[str]:
        return _list_models()

    @router.post("/models/warm", status_code=202)
    def warm_model(request: WarmRequest, background: BackgroundTasks) -> dict:
        background.add_task(_warm, request.model_name)
        return {"status": "warming"}
