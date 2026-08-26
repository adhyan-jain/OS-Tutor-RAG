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
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.auth import AUTH_ENABLED, require_user_email
from api.pipeline_instance import pipeline
from api.routes import session
from src.generation.misconception_check import check_misconception
from src.generation.teaching_prompt import build_teaching_prompt, is_continuation_message

logger = logging.getLogger("api.chat")

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    question: str
    model_name: str
    detail_level: Literal["eli5", "undergrad", "exam_prep"] = "undergrad"


def _build_prompt(request: ChatRequest, context_text: str, session_key: str) -> str:
    ollama_base_url = pipeline.config.generation.ollama_base_url

    # A continuation nudge ("continue", "go on", ...) has no mental model of
    # its own to classify -- skip the extra blocking LLM call entirely.
    misconception_note = (
        ""
        if is_continuation_message(request.question)
        else check_misconception(
            request.question,
            ollama_base_url=ollama_base_url,
            model_name=request.model_name,
            temperature=pipeline.config.generation.temperature,
        )
    )

    history_text = session.format_history(session_key)

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


async def _stream_chat(request: ChatRequest, session_key: str):
    ollama_base_url = pipeline.config.generation.ollama_base_url

    # A short continuation nudge ("continue", "go on", ...) isn't a new
    # search query -- retrieving fresh content for it (even using the prior
    # question's text) and telling the model to ground its answer in that
    # NEW content silently derails the continuation onto whatever topic the
    # retrieval happened to surface, rather than actually continuing what was
    # already being explained. So a continuation reuses the exact context
    # (and sources) the previous turn was grounded in instead of retrieving
    # at all; only falls back to a fresh retrieval if there's no prior turn.
    previous_sources_payload: list[dict] | None = None
    if is_continuation_message(request.question):
        history = session.get_history(session_key)
        if history:
            context_text = history[-1].context_text
            previous_sources_payload = history[-1].sources_payload
        else:
            context_text = None
    else:
        context_text = None

    if context_text is None:
        try:
            candidates = pipeline._retrieve_candidates(request.question)
        except Exception as exc:  # retrieval failure shouldn't crash the app
            logger.exception("Retrieval failed")
            yield {"event": "error", "data": json.dumps({"error": f"Retrieval failed: {exc}"})}
            return
        context_text = "\n\n".join(sc.chunk.text for sc in candidates)
        sources_payload = _sources_payload(candidates)
    else:
        sources_payload = previous_sources_payload or []

    prompt = _build_prompt(request, context_text, session_key)

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
    session.append_turn(session_key, request.question, full_answer, context_text, sources_payload)

    yield {"event": "sources", "data": json.dumps(sources_payload)}


# The session store is keyed by the authenticated user's email when auth is
# on (so one account's history follows them across browser sessions/devices),
# and by the client-supplied session_id when it's off -- exactly today's
# behavior. `request.session_id` is still accepted either way; when auth is
# on it's just ignored for keying purposes.
if AUTH_ENABLED:

    @router.post("/chat")
    async def chat(request: ChatRequest, user_email: str = Depends(require_user_email)):
        return EventSourceResponse(_stream_chat(request, session_key=user_email))

else:

    @router.post("/chat")
    async def chat(request: ChatRequest):
        return EventSourceResponse(_stream_chat(request, session_key=request.session_id))
