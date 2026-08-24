"""POST /chat — retrieves context via the real pipeline, then streams a
generated answer token-by-token straight from Ollama (bypassing
LocalLLM._complete, which hardcodes stream=False and cannot stream).

Retrieval/reranking/diversification/context-expansion still go through the
shared pipeline's real `_retrieve_candidates()` — only the generation call is
reimplemented here, against the same prompt templates LocalLLM uses.
"""

from __future__ import annotations

import json
import logging
from typing import Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.pipeline_instance import pipeline
from api.routes import session
from src.generation.misconception_check import check_misconception
from src.generation.teaching_prompt import build_teaching_prompt

logger = logging.getLogger("api.chat")

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    question: str
    model_name: str
    detail_level: Literal["eli5", "undergrad", "exam_prep"] = "undergrad"


def _build_prompt(request: ChatRequest, context_text: str) -> str:
    ollama_base_url = pipeline.config.generation.ollama_base_url

    misconception_note = check_misconception(
        request.question,
        ollama_base_url=ollama_base_url,
        model_name=request.model_name,
        temperature=pipeline.config.generation.temperature,
    )

    history_text = session.format_history(request.session_id)

    return build_teaching_prompt(
        request.detail_level,
        request.question,
        context_text,
        history_text,
        misconception_note,
    )


def _sources_payload(candidates) -> list[dict]:
    sources = []
    for sc in candidates:
        sources.append(
            {
                "chunk_id": sc.chunk.chunk_id,
                "doc_id": sc.chunk.doc_id,
                "metadata": sc.chunk.metadata,
                "score": sc.score,
            }
        )
    return sources


async def _stream_chat(request: ChatRequest):
    ollama_base_url = pipeline.config.generation.ollama_base_url

    try:
        candidates = pipeline._retrieve_candidates(request.question)
    except Exception as exc:  # retrieval failure shouldn't crash the app
        logger.exception("Retrieval failed")
        yield {"event": "error", "data": json.dumps({"error": f"Retrieval failed: {exc}"})}
        return

    context_text = "\n\n".join(sc.chunk.text for sc in candidates)
    prompt = _build_prompt(request, context_text)

    payload = {
        "model": request.model_name,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": pipeline.config.generation.temperature,
            "num_predict": pipeline.config.generation.max_tokens,
        },
    }

    answer_parts: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{ollama_base_url}/api/generate", json=payload
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield {
                        "event": "error",
                        "data": json.dumps(
                            {
                                "error": (
                                    f"Ollama returned {response.status_code} for model "
                                    f"{request.model_name!r}: {body.decode(errors='replace')}"
                                )
                            }
                        ),
                    }
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if "error" in chunk:
                        yield {"event": "error", "data": json.dumps({"error": chunk["error"]})}
                        return
                    token = chunk.get("response", "")
                    if token:
                        answer_parts.append(token)
                        yield {"event": "token", "data": json.dumps({"token": token})}
                    if chunk.get("done"):
                        break
    except httpx.ConnectError as exc:
        yield {
            "event": "error",
            "data": json.dumps({"error": f"Could not reach Ollama at {ollama_base_url}: {exc}"}),
        }
        return
    except httpx.HTTPError as exc:
        yield {"event": "error", "data": json.dumps({"error": f"Ollama request failed: {exc}"})}
        return

    full_answer = "".join(answer_parts)
    session.append_turn(request.session_id, request.question, full_answer)

    yield {"event": "sources", "data": json.dumps(_sources_payload(candidates))}


@router.post("/chat")
async def chat(request: ChatRequest):
    return EventSourceResponse(_stream_chat(request))
