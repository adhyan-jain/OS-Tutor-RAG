"""POST /chat -- one tutoring turn, streamed as server-sent events.

Every turn goes through the tutoring layer (``src.tutor``) twice:

1. ``engine.plan_turn`` runs BEFORE retrieval. Many turns never need the RAG
   pipeline at all and are answered by authored text chosen by code: triage,
   orientation for a student who does not know what to ask, a graded reply to
   the pending Socratic question, a hint, a quiz question. Those cost zero
   retrieval and (almost always) zero model calls.
2. Otherwise the turn is a real question: retrieve through the shared pipeline's
   ``_retrieve_candidates`` and stream a grounded answer token-by-token from
   Ollama. Afterwards ``engine.finish_rag`` picks the single Socratic question
   to append and the follow-up chips.

SSE events: ``token`` (answer text), ``ui`` (kind, chips, concept card, the
pending question -- a full replacement each time), ``sources`` (final event; the
frontend treats it as end-of-turn), ``error``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
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
from src.tutor import conversation as conv
from src.tutor import engine, llm
from src.tutor import followups as fu
from src.tutor import pedagogy as ped
from src.tutor.shaping import SentenceGate

logger = logging.getLogger("api.chat")

router = APIRouter()

# The old per-message misconception model call is replaced by deterministic
# pattern detection (engine.plan_turn); it can be switched back on as a fallback.
_LLM_MISCONCEPTION = os.environ.get("OS_RAG_LLM_MISCONCEPTION", "").strip().lower() in ("1", "true")

# A second, blocking model call per answer for model-written follow-ups doubles the
# wait. The authored chips already cover follow-ups, so it is off unless asked for.
_MODEL_FOLLOWUPS = os.environ.get("OS_RAG_MODEL_FOLLOWUPS", "").strip().lower() in ("1", "true")

_REFUSAL_RE = re.compile(
    r"(?:context|material|notes|slides?|text)\s+(?:provided\s+)?(?:does\s*n[o']t|doesn't|do not|does not)\s+"
    r"(?:contain|cover|mention|include|provide|say|discuss|have)", re.I)


def _units(level: str) -> int:
    gen = pipeline.config.generation
    return gen.chat_level_budget.get(level, (gen.chat_max_tokens, gen.chat_max_units))[1]


class ChatRequest(BaseModel):
    session_id: str
    question: str
    model_name: str
    detail_level: Literal["eli5", "undergrad", "exam_prep"] = "undergrad"
    # Guided mode: after an answer the tutor asks one short question and grades
    # the reply. Off = plain answers, no questions.
    socratic: bool = True


def _event(name: str, payload) -> dict:
    return {"event": name, "data": json.dumps(payload)}


def _chunks(text: str, size: int = 24):
    """Authored text is sent as a few small token events so the UI renders it
    the same way as a generated answer."""
    for i in range(0, len(text), size):
        yield text[i : i + size]


def _sources_payload(candidates) -> list[dict]:
    return [
        {"chunk_id": sc.chunk.chunk_id, "doc_id": sc.chunk.doc_id, "metadata": sc.chunk.metadata, "score": sc.score}
        for sc in candidates
    ]


def _history_questions(session_key: str) -> list[str]:
    return [t.question for t in session.get_history(session_key)[-8:]]


async def _ollama_stream(request: ChatRequest, prompt: str):
    """Yield ('token', str) pairs, then ('done', done_reason); or ('error', msg).
    The chat uses its own small token budget (not the pipeline's 900)."""
    gen = pipeline.config.generation
    base_url = gen.ollama_base_url
    payload = {
        "model": request.model_name,
        "prompt": prompt,
        "stream": True,
        "keep_alive": gen.chat_keep_alive,
        "options": {
            "temperature": gen.temperature,
            "num_predict": gen.chat_level_budget.get(request.detail_level, (gen.chat_max_tokens, gen.chat_max_units))[0],
            "num_ctx": gen.chat_num_ctx,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{base_url}/api/generate", json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield "error", (
                        f"Ollama returned {response.status_code} for model "
                        f"{request.model_name!r}: {body.decode(errors='replace')}"
                    )
                    return
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if "error" in chunk:
                        yield "error", chunk["error"]
                        return
                    token = chunk.get("response", "")
                    if token:
                        yield "token", token
                    if chunk.get("done"):
                        yield "done", chunk.get("done_reason") or "stop"
                        break
    except httpx.ConnectError as exc:
        yield "error", f"Could not reach Ollama at {base_url}: {exc}"
    except httpx.HTTPError as exc:
        yield "error", f"Ollama request failed: {exc}"


async def _stream_chat(request: ChatRequest, session_key: str):
    state = session.get_tutor_state(session_key)
    base_url = pipeline.config.generation.ollama_base_url
    plan = engine.plan_turn(state, request.question, socratic=request.socratic)

    # ------------------------------------------------ turns handled by code
    if isinstance(plan, engine.Reply):
        text = plan.text
        events = dict(plan.events)
        if plan.realise is not None:
            realised = await llm.realise_turn(plan.realise, base_url=base_url, model=request.model_name)
            if realised is not None:
                text = realised.response
                cid = plan.realise.get("concept_id")
                if cid and not plan.realise.get("free"):
                    cs = ped.ConceptStates.from_dict(state.concepts)
                    after = ped.apply_advisory(cs, cid, realised.suggested)
                    state.concepts = cs.to_dict()
                    events.update(realised=True, advisory=realised.suggested, state_after=after.state)
                    if plan.ui.get("concept"):
                        plan.ui["concept"]["state"] = after.state
                        plan.ui["concept"]["state_label"] = engine.STATE_LABEL[after.state]
        for piece in _chunks(text):
            yield _event("token", {"token": piece})
        yield _event("ui", {**plan.ui, "events": events})
        prior = session.get_history(session_key)
        session.append_turn(
            session_key, request.question, text,
            prior[-1].context_text if prior else "", prior[-1].sources_payload if prior else [],
        )
        yield _event("sources", prior[-1].sources_payload if prior else [])
        return

    # ------------------------------------------------ turns that need RAG
    continuation = plan.continuation or is_continuation_message(request.question)
    history = session.get_history(session_key)
    previous_sources: list[dict] | None = None
    context_text: str | None = None
    if continuation and history and history[-1].context_text:
        context_text = history[-1].context_text
        previous_sources = history[-1].sources_payload

    if context_text is None:
        try:
            candidates = await asyncio.to_thread(pipeline._retrieve_candidates, plan.query)
        except Exception as exc:  # retrieval failure shouldn't crash the app
            logger.exception("Retrieval failed")
            yield _event("error", {"error": f"Retrieval failed: {exc}"})
            return
        top = max((sc.score for sc in candidates), default=0.0)
        if top < pipeline.config.generation.chat_min_relevance and not fu.concept_for_text(plan.query):
            # Nothing in the course matches: a short authored bridge, no model call.
            reply = engine.off_topic(state)
            text = reply.text + engine.resume_line(state)
            for piece in _chunks(text):
                yield _event("token", {"token": piece})
            yield _event("ui", {**reply.ui, "events": {**reply.events, "top_score": round(top, 3)}})
            prior = session.get_history(session_key)
            session.append_turn(
                session_key, request.question, text,
                prior[-1].context_text if prior else "", prior[-1].sources_payload if prior else [],
            )
            yield _event("sources", [])
            return
        context_text = "\n\n".join(sc.chunk.text for sc in candidates)
        sources_payload = _sources_payload(candidates)
    else:
        sources_payload = previous_sources or []

    note = plan.misconception_note
    if not note and _LLM_MISCONCEPTION and not continuation:
        note = await asyncio.to_thread(
            check_misconception, plan.query, ollama_base_url=base_url, model_name=request.model_name,
            temperature=pipeline.config.generation.temperature,
        )

    prompt = build_teaching_prompt(
        plan.detail_override or request.detail_level,
        plan.query,
        context_text,
        session.format_history(session_key),
        note,
        socratic=request.socratic,
    )

    parts: list[str] = []
    if plan.lead:
        lead = plan.lead + "\n\n"
        parts.append(lead)
        for piece in _chunks(lead):
            yield _event("token", {"token": piece})

    # Text is released only up to the last sentence/line boundary; if the model hit
    # the small chat budget, its unfinished tail is dropped (see tutor.shaping).
    # One quiet retry with half the context if the model fails before saying anything.
    gate = SentenceGate(max_units=_units(request.detail_level))
    truncated = False
    for attempt in (1, 2):
        failure: str | None = None
        sent_any = False
        stream = _ollama_stream(request, prompt)
        async for kind, value in stream:
            if kind == "token":
                out = gate.feed(value)
                if out:
                    sent_any = True
                    parts.append(out)
                    yield _event("token", {"token": out})
                if gate.full:  # enough said: stop the model instead of waiting for it
                    break
            elif kind == "done":
                truncated = value == "length"
            else:
                failure = value
                break
        await stream.aclose()
        if failure is None:
            break
        if attempt == 2 or sent_any or gate.emitted:
            yield _event("error", {"error": failure})
            return
        logger.warning("Ollama failed before the first sentence (%s); retrying with less context", failure)
        gate = SentenceGate(max_units=_units(request.detail_level))
        prompt = build_teaching_prompt(
            plan.detail_override or request.detail_level, plan.query, context_text[: max(len(context_text) // 2, 400)],
            session.format_history(session_key), note, socratic=request.socratic,
        )
    tail = gate.finish(truncated)
    if tail:
        parts.append(tail)
        yield _event("token", {"token": tail})
    answer = gate.emitted

    refused = bool(_REFUSAL_RE.search(answer)) and len(answer) < 400
    finish = engine.finish_rag(
        state, plan, message=request.question, sources=sources_payload, refused=refused, socratic=request.socratic
    )
    suffix = finish.text
    if suffix:
        parts.append(suffix)
        for piece in _chunks(suffix):
            yield _event("token", {"token": piece})
    ui = {**finish.ui, "events": {**plan.events, **finish.events}}
    yield _event("ui", ui)

    # Optional, validated, model-written follow-ups. Never blocks the answer:
    # the student already has the answer and the authored chips by now.
    if _MODEL_FOLLOWUPS and not refused and not continuation and not state.pending:
        avoid = _history_questions(session_key) + list(state.asked_chips)
        socratic_q, extra = await llm.generate_followups(
            request.question, answer, context_text, base_url=base_url, model=request.model_name, avoid=avoid
        )
        no_question_yet = not state.pending and not finish.ui.get("question")
        changed = False
        if socratic_q and request.socratic and no_question_yet:
            q_text = f"\n\n**Think about this:** {socratic_q}"
            parts.append(q_text)
            for piece in _chunks(q_text):
                yield _event("token", {"token": piece})
            state.pending = {
                "kind": "free", "question": socratic_q, "concept_id": state.topic,
                "context": context_text[:1200], "source": "followup",
            }
            ui = {**ui, "kind": "answer", "chips": [conv.ACTIONS["tell_me"], conv.ACTIONS["skip"]],
                  "question": {"id": "free", "type": "CHECK", "level": "understanding", "concept": "",
                               "source": "followup"}}
            changed = True
        elif extra and no_question_yet:
            merged = list(ui.get("chips", []))
            for q in extra:
                if q.lower() not in {c.lower() for c in merged} and len(merged) < 5:
                    merged.append(q)
            if merged != ui.get("chips"):
                ui = {**ui, "chips": merged}
                changed = True
        if changed:
            engine._remember(state, ui.get("chips", []))
            yield _event("ui", ui)

    full_text = "".join(parts)
    session.append_turn(session_key, request.question, full_text, context_text, sources_payload)
    yield _event("sources", sources_payload)


def _key(session_id: str, email: str | None) -> str:
    """The session store is keyed by "{email}:{session_id}" when auth is on --
    scoped to the authenticated account but still one distinct history per
    conversation thread -- and by the client-supplied session_id alone when
    auth is off."""
    return f"{email}:{session_id}" if email else session_id


if AUTH_ENABLED:

    @router.post("/chat")
    async def chat(request: ChatRequest, user_email: str = Depends(require_user_email)):
        return EventSourceResponse(_stream_chat(request, session_key=_key(request.session_id, user_email)))

else:

    @router.post("/chat")
    async def chat(request: ChatRequest):
        return EventSourceResponse(_stream_chat(request, session_key=_key(request.session_id, None)))
