"""
Unit tests for the second-domain (Blocks World) 24-task confirmatory benchmark suite.
"""

import os
import pytest
from research.pilot_second_domain.blocks_world_tasks import (
    get_all_tasks,
    render_task_prompt,
    extract_plan,
    evaluate_plan_semantic,
    format_plan_as_string,
    plan_to_tuple,
    BlocksWorld,
)


def test_24_tasks_specification():
    tasks = get_all_tasks()
    assert len(tasks) == 24

    tier1 = [t for t in tasks if t["tier"] == 1]
    tier2 = [t for t in tasks if t["tier"] == 2]
    tier3 = [t for t in tasks if t["tier"] == 3]

    assert len(tier1) == 8, f"Expected 8 Tier 1 tasks, got {len(tier1)}"
    assert len(tier2) == 8, f"Expected 8 Tier 2 tasks, got {len(tier2)}"
    assert len(tier3) == 8, f"Expected 8 Tier 3 tasks, got {len(tier3)}"

    for t in tier1:
        assert t["expected_cardinality"] == 1
    for t in tier2:
        assert 2 <= t["expected_cardinality"] <= 6
    for t in tier3:
        assert 8 <= t["expected_cardinality"] <= 24


def test_bfs_shortest_paths_validity():
    tasks = get_all_tasks()
    for t in tasks:
        bw = BlocksWorld(t["blocks"])
        clear = set(t["blocks"]) - set(t["init_on"].values())
        plans = bw.enumerate_all_minimal_plans(
            t["init_on"], set(t["init_table"]), clear,
            t["goal_on"], set(t["goal_table"])
        )
        assert len(plans) == t["expected_cardinality"], (
            f"Task {t['id']}: enumerated {len(plans)} plans, expected {t['expected_cardinality']}"
        )
        assert len(plans[0]) == t["min_length"], (
            f"Task {t['id']}: plan length {len(plans[0])}, expected {t['min_length']}"
        )

        # Check deduplication
        plan_tuples = [plan_to_tuple(p) for p in plans]
        assert len(plan_tuples) == len(set(plan_tuples)), f"Duplicate plans found in task {t['id']}"

        # Check semantic execution
        for p in plans:
            assert evaluate_plan_semantic(t, p), f"Plan {p} failed semantic validation on task {t['id']}"


def test_plan_extraction_and_semantics():
    task = get_all_tasks()[0]  # bw_01_single_stack: A on B

    # Test extracting from standard prompt response
    text1 = "PLAN: move(A, B)"
    plan1 = extract_plan(text1)
    assert plan1 == [("move", "A", "B")]
    assert evaluate_plan_semantic(task, plan1) is True

    # Test extracting with move_to_table
    text2 = "Here is the plan:\nPLAN: move_to_table(A), move(A, B)"
    plan2 = extract_plan(text2)
    assert plan2 == [("move_to_table", "A"), ("move", "A", "B")]

    # Test illegal action rejection (A is already on table, cannot move to table)
    assert evaluate_plan_semantic(task, [("move_to_table", "A")]) is False

    # Test empty plan rejection
    assert evaluate_plan_semantic(task, []) is False


def test_prompt_rendering_variants():
    tasks = get_all_tasks()
    t = tasks[0]
    for var in ["v0", "v1", "v2"]:
        p = render_task_prompt(t, var)
        assert len(p) > 50
        assert "PLAN:" in p
        assert "A" in p and "B" in p


# ---------------------------------------------------------------------------
# Confirmatory-run integrity (actual local-model generations, 1,152 records)
# ---------------------------------------------------------------------------
import json

RUNS_DIR = "research/pilot_second_domain/runs"
REG_MODELS = ["qwen3:8b", "gemma2:9b", "llama3.1:8b", "mistral:7b-instruct"]
REG_SETTINGS = {"temperature": 0.7, "top_p": 0.9, "num_predict": 512}


def _load_runs(model):
    path = f"{RUNS_DIR}/{model.replace(':', '_')}.jsonl"
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_confirmatory_runs_account_for_every_planned_generation():
    tasks = {t["id"] for t in get_all_tasks()}
    total = 0
    for m in REG_MODELS:
        recs = _load_runs(m)
        total += len(recs)
        assert len(recs) == 288, f"{m}: {len(recs)} records, expected 288"
        assert len({r["key"] for r in recs}) == 288, f"{m}: duplicate generation keys"
        combos = {(r["task_id"], r["variant"], r["seed"]) for r in recs}
        expected = {(t, v, s) for t in tasks for v in ("v0", "v1", "v2") for s in range(4)}
        assert combos == expected, f"{m}: planned (task, variant, seed) grid not covered exactly"
        for r in recs:
            assert r["model"] == m
            assert r["settings"] == REG_SETTINGS
            assert r["error"] is None and r["done_reason"] in ("stop", "length")
            assert r["ts"] and r["prompt_sha256"] and r["prompt"] and "response" in r
    assert total == 1152


def test_prompts_contain_no_reference_plan():
    # The only plan-like string allowed in a prompt is the fixed demonstration example,
    # and it must not itself be a reference plan of any task.
    example = "move_to_table(A), move(A, B)"
    all_refs = set()
    for t in get_all_tasks():
        bw = BlocksWorld(t["blocks"])
        clear = set(t["blocks"]) - set(t["init_on"].values())
        refs = bw.enumerate_all_minimal_plans(
            t["init_on"], set(t["init_table"]), clear, t["goal_on"], set(t["goal_table"]))
        for p in refs:
            s = format_plan_as_string(p)
            all_refs.add(s)
            for v in ("v0", "v1", "v2"):
                prompt = render_task_prompt(t, v).replace(example, "")
                assert s not in prompt, f"{t['id']}/{v}: reference plan leaked into prompt"
    assert example not in all_refs


def test_reference_spaces_independently_verified():
    from research.pilot_second_domain.verify_reference_spaces import verify_all
    rep = verify_all()
    assert rep["all_ok"], {k: v for k, v in rep["tasks"].items() if not v["ok"]}


def test_confirmatory_result_statuses_not_vacuous():
    with open("research/pilot_second_domain/results/blocks_world_confirmatory.json") as f:
        res = json.load(f)["hypotheses_results"]
    h3, h4 = res["H3_near_tie_concentration"], res["H4_detection_loss"]
    if not h3["separated_pairs"]:
        # no E3-separated pair => H3/H4 must not be reported as confirmed
        assert h3["passed"] is None and h3["status"].startswith("NOT_INFORMATIVE")
        assert h4["passed"] is None and h4["status"].startswith("NOT_TESTABLE")
    h1 = res["H1_attenuation_law"]
    assert h1["n_nonzero_cells"] == 16
    assert abs(h1["pearson_r"] - h1["pearson_r_nonzero_cells"]) < 1e-12
