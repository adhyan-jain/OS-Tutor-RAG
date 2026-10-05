"""Tests for the competence-filter mini-pilot: gate logic, resume, strata, decision rubric, isolation."""

import pytest

from research.ssr_pilot import analyze_competence_pilot as ACP
from research.ssr_pilot import families as F
from research.ssr_pilot import run_competence_pilot as RCP
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.run_pilot import Log, call_key
from research.ssr_pilot.worlds import load_worlds

WORLDS = load_worlds()
IDLE_GPU = {"vram_used_mib": 300.0, "vram_total_mib": 8188.0, "util_pct": 2.0}


# ---------------------------------------------------------------- gate

def test_gate_free_when_nothing_else_is_running():
    assert RCP.decide_busy("qwen3:14b", 10.8, [], [], IDLE_GPU, 12.0) == []


def test_gate_busy_on_foreign_job_foreign_model_gpu_and_ram():
    busy = lambda **kw: RCP.decide_busy("qwen3:14b", 10.8, kw.get("jobs", []), kw.get("loaded", []),
                                         kw.get("gpu", IDLE_GPU), kw.get("ram", 12.0))
    assert any("foreign job" in r for r in busy(jobs=["123 python -m research.ssr_bench.run"]))
    assert any("foreign model" in r for r in busy(loaded=["qwen2.5:7b"]))
    assert any("GPU memory" in r for r in busy(gpu={**IDLE_GPU, "vram_used_mib": 4900.0}))
    assert any("utilisation" in r for r in busy(gpu={**IDLE_GPU, "util_pct": 45.0}))
    assert any("RAM" in r for r in busy(ram=2.9))


def test_gate_ignores_own_model_load_and_does_not_double_count_ram():
    # our model is resident: its own VRAM/utilisation/RAM use must not make the gate report "busy"
    gpu_busy_by_us = {"vram_used_mib": 6000.0, "vram_total_mib": 8188.0, "util_pct": 90.0}
    assert RCP.decide_busy("qwen3:14b", 10.8, [], ["qwen3:14b"], gpu_busy_by_us, 1.0) == []
    # but a second, foreign model next to ours is reported
    assert RCP.decide_busy("qwen3:14b", 10.8, [], ["qwen3:14b", "qwen2.5:7b"], gpu_busy_by_us, 1.0)


def test_poll_interval_is_five_minutes():
    assert RCP.POLL_S in (5, 300) and RCP.CHECK_EVERY == 25


def test_missing_model_is_skipped_only_when_no_download_is_running(monkeypatch):
    monkeypatch.setattr(RCP, "installed", lambda: [])
    monkeypatch.setattr(RCP, "log_event", lambda msg: None)
    monkeypatch.setattr(RCP, "download_pending", lambda: False)
    assert RCP.run_model("gemma3:12b", WORLDS, smoke=True) == "not_installed"
    waits = {"n": 0}

    def pending():
        waits["n"] += 1
        return waits["n"] < 3  # a pull is running for the first two checks, then it is over

    monkeypatch.setattr(RCP, "download_pending", pending)
    monkeypatch.setattr(RCP.time, "sleep", lambda s: None)
    assert RCP.run_model("gemma3:12b", WORLDS, smoke=True) == "not_installed"
    assert waits["n"] == 3  # it waited instead of skipping at once


# ---------------------------------------------------------------- resume / smoke selection

def test_select_todo_skips_finished_calls_and_never_duplicates(tmp_path):
    log = Log(str(tmp_path / "m.jsonl"))
    model = "gemma3:12b"
    full = RCP.select_todo(model, WORLDS, log, smoke=False)
    assert len(full) == 24 * 3 * 4
    for t in full[:10]:
        log.add({"key": call_key(model, t["rendered"]["prompt_sha256"], t["seed"]), "model": model})
    again = RCP.select_todo(model, WORLDS, Log(str(tmp_path / "m.jsonl")), smoke=False)
    assert len(again) == len(full) - 10
    done = {call_key(model, t["rendered"]["prompt_sha256"], t["seed"]) for t in full[:10]}
    assert not done & {call_key(model, t["rendered"]["prompt_sha256"], t["seed"]) for t in again}


def test_smoke_covers_each_family_once_with_all_variants():
    smoke = RCP.select_todo("gemma3:12b", WORLDS, Log("/nonexistent/none.jsonl"), smoke=True)
    assert len(smoke) == 9
    assert {t["world"]["family"] for t in smoke} == {"scheduling", "sync", "banker"}
    assert {t["variant"] for t in smoke} == {"v0", "v1", "v2"} and {t["seed"] for t in smoke} == {0}


def test_preflight_convention_present_and_reference_absent_for_all_worlds():
    RCP.preflight(WORLDS)  # raises on any violation


def test_tasks_use_the_stated_convention_prompt():
    from research.ssr_pilot import render
    for t in RCP.select_todo("phi4:14b", WORLDS, Log("/nonexistent/x.jsonl"), smoke=False)[:30]:
        assert "Convention for tie-breaking:" in t["rendered"]["prompt"]
        assert t["rendered"]["prompt_sha256"] != render.render_variant(t["world"], t["variant"])["prompt_sha256"]


# ---------------------------------------------------------------- strata

def _literal_follower(w):
    if w["family"] == "banker":
        procs = {p["pid"]: p for p in w["processes"]}
        work, left, out = list(w["available"]), list(procs), []
        while left:
            ok = [p for p in left if all(m - a <= x for m, a, x in zip(procs[p]["max"], procs[p]["alloc"], work))]
            out.append(ok[0])
            left.remove(ok[0])
            work = [x + a for x, a in zip(work, procs[ok[0]]["alloc"])]
        return tuple(out)
    return F.system(w).canonical()


def test_stratum_U_is_exactly_the_worlds_where_the_literal_reading_misses_R():
    underdetermined = sorted(w["id"] for w in WORLDS if _literal_follower(w) != load_bank(w)["reference"])
    assert underdetermined == sorted(ACP.STRATUM_U)
    assert len(ACP.STRATUM_U) == 8 and len(WORLDS) - len(ACP.STRATUM_U) == 16


# ---------------------------------------------------------------- decision rubric (frozen)

@pytest.mark.parametrize("gain,n,mean,lo,hi,expected", [
    (0.10, 400, 0.70, 0.55, 0.85, "C"),      # gate fails on gain
    (0.30, 60, 0.70, 0.55, 0.85, "C"),       # gate fails on n_valid
    (0.30, 200, 0.70, 0.55, 0.85, "A"),      # survives
    (0.30, 200, 0.50, 0.30, 0.70, "A"),      # boundary: >= 0.50, drop 0.125, lo > 0.10
    (0.30, 200, 0.45, 0.30, 0.60, "C"),      # below 0.50 but CI straddles 0.50
    (0.30, 200, 0.30, 0.15, 0.45, "B"),      # whole CI under 0.50, drop 0.325
    (0.30, 200, 0.40, 0.20, 0.49, "B"),      # drop 0.225 >= 0.15, hi < 0.50
    (0.30, 200, 0.55, 0.05, 0.80, "C"),      # >= 0.50 but lower bound not above 0.10
])
def test_decision_rubric_cases(gain, n, mean, lo, hi, expected):
    assert ACP.decide_competence(gain, n, mean, lo, hi)["decision"] == expected


def test_decision_with_no_valid_outputs_is_inconclusive():
    assert ACP.decide_competence(0.5, 0, None, None, None)["decision"] == "C"


def test_rubric_file_states_the_same_thresholds():
    text = open(ACP.RUBRIC).read()
    for token in ("competence gain ≥ 0.15", "n_valid ≥ 100", "FRR_norm ≥ 0.50", "0.625", "Stratum D", "Stratum U"):
        assert token in text


# ---------------------------------------------------------------- statistics helpers

def _rec(world, b, a):
    return {"world": world, "B": b, "A_norm": a}


def test_frr_diff_ci_is_zero_for_identical_inputs():
    recs = [_rec(f"w{i}", True, i % 2 == 0) for i in range(12)] * 2
    d = ACP.frr_diff_ci(recs, recs, n_boot=200)
    assert d["diff"] == pytest.approx(0.0) and d["ci95"][0] <= 0 <= d["ci95"][1]


def test_frr_diff_ci_sign():
    new = [_rec(f"w{i}", True, True) for i in range(12)]            # FRR 0
    base = [_rec(f"w{i}", True, False) for i in range(12)]          # FRR 1
    assert ACP.frr_diff_ci(new, base, n_boot=200)["diff"] == pytest.approx(-1.0)


# ---------------------------------------------------------------- isolation

def test_new_outputs_never_collide_with_existing_results():
    existing = ["research/ssr_pilot/runs", "research/ssr_pilot/runs_stated_convention", "research/ssr_pilot/runs_dry",
                "research/ssr_pilot/results/llm", "research/ssr_pilot/results/stated_convention"]
    assert RCP.RUNS not in existing and RCP.OUT not in existing
    assert RCP.RUNS.endswith("runs_competence_pilot") and RCP.OUT.endswith("results/competence_pilot")


def test_models_are_one_per_family_and_not_previously_used():
    fam = [m.split(":")[0].rstrip("0123456789") for m in RCP.MODELS]
    assert len(set(fam)) == len(fam) and len(fam) in (2, 3)
    assert not set(RCP.MODELS) & {"qwen3:8b", "llama3.1:8b", "gemma2:9b", "mistral:7b-instruct"}
