"""The /chat turn loop with retrieval and Ollama stubbed out: event contract,
authored turns costing no retrieval, state carried per thread, advisory clamp."""

import asyncio
import json
import sys
import types

import pytest

from src.config import PipelineConfig
from src.schemas import Chunk, ScoredChunk


class FakePipeline:
    def __init__(self):
        self.config = PipelineConfig()
        self.retrievals: list[str] = []
        self.score = 0.9

    def _retrieve_candidates(self, query):
        self.retrievals.append(query)
        chunk = Chunk("d__chunk0", "d", "A TLB caches translations.", 0, 10,
                      {"slide_title": "Interrupts\nHardware / Interrupt handling", "parent_id": "d__slide1"})
        return [ScoredChunk(chunk, self.score, "dense")]


@pytest.fixture()
def chat(monkeypatch):
    fake = types.ModuleType("api.pipeline_instance")
    fake.pipeline = FakePipeline()
    fake.index_loaded = True
    fake.load_index = lambda: None
    monkeypatch.setitem(sys.modules, "api.pipeline_instance", fake)
    sys.modules.pop("api.routes.chat", None)
    import api.routes.chat as chat_mod
    from api.routes import session

    session._SESSIONS.clear()
    session._TUTOR.clear()

    async def fake_stream(request, prompt):
        for t in ["A TLB is a ", "cache of translations."]:
            yield "token", t

    async def no_followups(*a, **k):
        return None, []

    async def no_realise(*a, **k):
        return None

    monkeypatch.setattr(chat_mod, "_ollama_stream", fake_stream)
    monkeypatch.setattr(chat_mod.llm, "generate_followups", no_followups)
    monkeypatch.setattr(chat_mod.llm, "realise_turn", no_realise)
    chat_mod.pipeline = fake.pipeline
    yield chat_mod
    sys.modules.pop("api.routes.chat", None)


def run_turn(chat, text, sid="s1", socratic=True):
    req = chat.ChatRequest(session_id=sid, question=text, model_name="m", socratic=socratic)

    async def collect():
        return [e async for e in chat._stream_chat(req, session_key=sid)]

    events = asyncio.run(collect())
    out = {"text": "", "ui": None, "sources": None, "error": None, "order": [e["event"] for e in events]}
    for e in events:
        d = json.loads(e["data"])
        if e["event"] == "token":
            out["text"] += d["token"]
        elif e["event"] == "ui":
            out["ui"] = d
        elif e["event"] == "sources":
            out["sources"] = d
        elif e["event"] == "error":
            out["error"] = d
    return out


def test_rag_turn_event_contract(chat):
    r = run_turn(chat, "what is a TLB?")
    assert r["error"] is None
    assert r["order"][-1] == "sources"  # the frontend treats it as end-of-turn
    assert "ui" in r["order"] and r["order"].index("ui") < len(r["order"]) - 1
    assert r["text"].startswith("A TLB is a cache") and "Think about this" in r["text"]
    assert r["ui"]["question"]["id"] and r["ui"]["chips"]
    assert r["sources"][0]["doc_id"] == "d"


def test_authored_turns_cost_no_retrieval(chat):
    r = run_turn(chat, "I'm new to operating systems")
    assert r["ui"]["kind"] == "path" and chat.pipeline.retrievals == []
    assert r["sources"] == []


def test_answering_the_question_is_graded_without_retrieval(chat):
    run_turn(chat, "what is a TLB?")
    n = len(chat.pipeline.retrievals)
    r = run_turn(chat, "skip")
    assert len(chat.pipeline.retrievals) == n and "carry on" in r["text"]


def test_state_is_per_thread(chat):
    run_turn(chat, "what is a TLB?", sid="a")
    from api.routes import session
    assert session.get_tutor_state("a").pending and not session.get_tutor_state("b").pending


def test_socratic_off_asks_nothing(chat):
    r = run_turn(chat, "what is a TLB?", socratic=False)
    assert "Think about this" not in r["text"] and "question" not in r["ui"]


def test_continuation_reuses_previous_context(chat):
    run_turn(chat, "what is a TLB?", socratic=False)
    n = len(chat.pipeline.retrievals)
    run_turn(chat, "continue", socratic=False)
    assert len(chat.pipeline.retrievals) == n


def test_retrieval_failure_is_an_error_event(chat):
    def boom(q):
        raise RuntimeError("index missing")

    chat.pipeline._retrieve_candidates = boom
    r = run_turn(chat, "what is a TLB?")
    assert "index missing" in r["error"]["error"]


def test_model_written_question_becomes_pending(chat, monkeypatch):
    async def followups(*a, **k):
        return "Why does a TLB speed up translation?", ["What is a page table walk?"]

    monkeypatch.setattr(chat.llm, "generate_followups", followups)
    monkeypatch.setattr(chat, "_MODEL_FOLLOWUPS", True)
    # a topic with no authored question left: use a concept-free question
    r = run_turn(chat, "tell me about interrupt handling")
    assert "Think about this" in r["text"] and "Why does a TLB speed up translation?" in r["text"]
    from api.routes import session
    assert session.get_tutor_state("s1").pending["kind"] == "free"


def test_extra_model_chips_are_merged_when_no_question(chat, monkeypatch):
    async def followups(*a, **k):
        return None, ["What is a page table walk exactly?"]

    monkeypatch.setattr(chat.llm, "generate_followups", followups)
    monkeypatch.setattr(chat, "_MODEL_FOLLOWUPS", True)
    r = run_turn(chat, "tell me about interrupt handling", socratic=False)
    assert "What is a page table walk exactly?" in r["ui"]["chips"]


def test_advisory_is_applied_clamped(chat, monkeypatch):
    run_turn(chat, "what is a TLB?")
    from api.routes import session
    from src.tutor.llm import RealisedTurn

    async def realised(ctx, **k):
        return RealisedTurn("Good thinking. What would the cache hold?", "CORRECT")

    monkeypatch.setattr(chat.llm, "realise_turn", realised)
    r = run_turn(chat, "it keeps the hot stuff close to the cpu so lookups are quick and cheap overall")
    state = session.get_tutor_state("s1")
    rec = state.concepts["records"]["tlb"]
    assert rec["state"] != "UNDERSTOOD"  # the advisory can never reach UNDERSTOOD
    assert "Good thinking" in r["text"] or "Nice" in r["text"] or "attempt" in r["text"]


def test_realise_failure_falls_back_to_authored_reply(chat):
    run_turn(chat, "what is a TLB?")
    r = run_turn(chat, "banana banana banana banana banana banana")
    assert r["text"] and r["error"] is None


# ------------------------------------------------------------ small, smooth outputs


def test_no_blocking_followup_call_by_default(chat, monkeypatch):
    calls = []

    async def followups(*a, **k):
        calls.append(1)
        return None, []

    monkeypatch.setattr(chat.llm, "generate_followups", followups)
    run_turn(chat, "what is a TLB?")
    assert calls == []


def test_truncated_answer_ends_on_a_sentence(chat, monkeypatch):
    async def cut(request, prompt):
        for t in ["A TLB caches translations. ", "It makes paging fast. ", "Because the", " CPU does not wa"]:
            yield "token", t
        yield "done", "length"

    monkeypatch.setattr(chat, "_ollama_stream", cut)
    r = run_turn(chat, "what is a TLB?", socratic=False)
    assert r["text"].startswith("A TLB caches translations. It makes paging fast.")
    assert "Because" not in r["text"] and "wa" not in r["text"].split()[-1:]


def test_complete_answer_is_not_trimmed(chat, monkeypatch):
    async def whole(request, prompt):
        for t in ["A TLB caches translations. ", "It is fast"]:
            yield "token", t
        yield "done", "stop"

    monkeypatch.setattr(chat, "_ollama_stream", whole)
    r = run_turn(chat, "what is a TLB?", socratic=False)
    assert r["text"].endswith("It is fast")


def test_one_quiet_retry_when_the_model_fails_early(chat, monkeypatch):
    attempts = []

    async def flaky(request, prompt):
        attempts.append(len(prompt))
        if len(attempts) == 1:
            yield "error", "boom"
            return
        yield "token", "A TLB caches translations."
        yield "done", "stop"

    monkeypatch.setattr(chat, "_ollama_stream", flaky)
    r = run_turn(chat, "what is a TLB?", socratic=False)
    assert r["error"] is None and r["text"].startswith("A TLB caches")
    assert len(attempts) == 2 and attempts[1] <= attempts[0]


def test_two_failures_surface_one_error(chat, monkeypatch):
    async def dead(request, prompt):
        yield "error", "Could not reach Ollama"

    monkeypatch.setattr(chat, "_ollama_stream", dead)
    r = run_turn(chat, "what is a TLB?")
    assert r["error"] and "Ollama" in r["error"]["error"]


def test_unrelated_question_gets_a_short_bridge_and_no_model_call(chat, monkeypatch):
    called = []

    async def should_not_run(request, prompt):
        called.append(1)
        yield "token", "x"

    monkeypatch.setattr(chat, "_ollama_stream", should_not_run)
    chat.pipeline.score = 0.45
    r = run_turn(chat, "what is fear")
    assert called == [] and "outside this course" in r["text"]
    assert r["ui"]["events"]["verdict"] == "off_topic" and r["ui"]["chips"]
    assert r["sources"] == [] and r["order"][-1] == "sources"


def test_low_score_is_fine_when_a_course_concept_is_named(chat):
    chat.pipeline.score = 0.45
    r = run_turn(chat, "what is a page table?")
    assert "outside this course" not in r["text"]


def test_a_rambling_model_is_cut_at_the_unit_cap(chat, monkeypatch):
    async def rambling(request, prompt):
        for i in range(12):
            yield "token", f"Sentence number {i}. "
        yield "done", "stop"

    monkeypatch.setattr(chat, "_ollama_stream", rambling)
    r = run_turn(chat, "what is a TLB?", socratic=False)
    assert r["text"].count("Sentence number") == chat.pipeline.config.generation.chat_max_units
