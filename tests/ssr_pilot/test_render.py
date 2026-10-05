"""Rendering tests: surface variants must round-trip through parse and never leak the reference."""

import pytest

from research.ssr_pilot import families as F
from research.ssr_pilot import oracle, render
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.worlds import load_worlds

WORLDS = load_worlds()


@pytest.mark.parametrize("world", WORLDS, ids=lambda w: w["id"])
@pytest.mark.parametrize("variant", list(render.VARIANTS))
def test_roundtrip_all_variants(world, variant):
    r = render.render_variant(world, variant)
    bank = load_bank(world)
    traces = [bank["reference"], *bank["valid"][:5], *[x["steps"] for x in bank["invalid_rule"][:5]],
              *bank["invalid_constraint"][:3]]
    for t in traces:
        shown = "Sure.\nTRACE: " + F.format_steps(world, t, r["style"], r["c2s"])
        steps, info = F.parse(world, shown, r["s2c"])
        assert not info["unknown"], (world["id"], variant, info)
        assert steps == t, (world["id"], variant, t, steps)
        base = oracle.evaluate_candidate(world, "TRACE: " + F.format_steps(world, t))
        via = oracle.evaluate_candidate(world, shown, shown2canon=r["s2c"])
        assert base.semantic_valid == via.semantic_valid


@pytest.mark.parametrize("world", WORLDS, ids=lambda w: w["id"])
def test_prompt_does_not_contain_reference(world):
    bank = load_bank(world)
    for variant in render.VARIANTS:
        r = render.render_variant(world, variant)
        ref = render.reference_text(world, bank["reference"], r)
        assert ref not in r["prompt"]
        assert "canonical" not in r["prompt"].lower() and "reference" not in r["prompt"].lower()


@pytest.mark.parametrize("world", WORLDS, ids=lambda w: w["id"])
def test_name_maps_are_injective_and_safe(world):
    for variant in render.VARIANTS:
        m = render.name_maps(world, variant)
        assert len(set(m.values())) == len(m)
        assert not {v.lower() for v in m.values()} & F._STOP
        assert "idle" not in {v.lower() for v in m.values()}


def test_variants_differ_but_describe_same_world():
    for w in WORLDS:
        prompts = [render.render_variant(w, v)["prompt"] for v in render.VARIANTS]
        assert len(set(prompts)) == 3
        for p in prompts:
            assert "any valid answer is accepted" in p
            for c in w.get("constraints", []):
                assert "Constraint:" in p
