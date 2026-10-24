"""
Unit tests for the second-domain Blocks World pilot simulation and verifier.
"""

import json
import os
import pytest
from research.pilot_second_domain.blocks_world_rcr_pilot import (
    BlocksWorld,
    define_benchmark_worlds,
    run_blocks_world_rcr_pilot,
)


def test_blocks_world_bfs_enumeration():
    worlds = define_benchmark_worlds()
    assert len(worlds) == 6

    # Test single stack world has 1 plan
    w1 = worlds[0]
    bw1 = BlocksWorld(w1["blocks"])
    plans1 = bw1.enumerate_all_minimal_plans(
        w1["init_on"], w1["init_table"], w1["init_clear"],
        w1["goal_on"], w1["goal_table"]
    )
    assert len(plans1) == 1
    assert plans1[0] == [("move", "A", "B")]

    # Test independent pairs has 2 plans (independent commutation)
    w2 = worlds[1]
    bw2 = BlocksWorld(w2["blocks"])
    plans2 = bw2.enumerate_all_minimal_plans(
        w2["init_on"], w2["init_table"], w2["init_clear"],
        w2["goal_on"], w2["goal_table"]
    )
    assert len(plans2) == 2


def test_blocks_world_pilot_execution():
    run_blocks_world_rcr_pilot()
    out_file = "research/pilot_second_domain/results/blocks_world_pilot.json"
    assert os.path.exists(out_file)
    with open(out_file) as f:
        data = json.load(f)
    assert data["domain"] == "BlocksWorld_Planning"
    assert data["n_worlds"] == 6
    assert abs(data["attenuation_check"]["mean_ratio_observed_over_predicted"] - 1.0) < 1e-6
