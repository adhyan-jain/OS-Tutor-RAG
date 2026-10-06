"""
Exhaustive reference-invariance and domain validation tests for E3 Semantic Oracle.

Verifies:
  1. E3 never receives or accesses reference R (architectural signature check).
  2. For all 24 worlds and candidate model outputs, E3 semantic validity verdict is
     100% invariant to which valid reference is present or compared against.
  3. Domain-specific verification for Scheduling, Synchronization, and Banker's Algorithm.
"""

import glob
import inspect
import json
import pytest

from research.ssr_pilot import families as F
from research.ssr_pilot.core.oracle import (
    assert_oracle_has_no_reference_parameter,
    evaluate_oracle,
)
from research.ssr_pilot.core.valid_space import build_all_valid_spaces
from research.ssr_pilot.oracle import compare_to_reference, evaluate_candidate
from research.ssr_pilot.worlds import load_worlds


def test_oracle_signature_has_no_reference_parameter():
    """Verify evaluate_candidate has no reference-related parameters."""
    assert assert_oracle_has_no_reference_parameter(), "evaluate_candidate signature contains forbidden reference argument"
    sig = inspect.signature(evaluate_candidate)
    assert "reference" not in sig.parameters
    assert "ref" not in sig.parameters
    assert "r" not in sig.parameters


def test_oracle_reference_invariance_exhaustive_across_all_24_worlds():
    """
    Exhaustively test all 24 worlds: for candidate generations across all 4 baseline models,
    verify that exercising the reference comparison path across every valid reference in V(x)
    produces identical semantic validity verdicts with zero leakage or side effects.
    """
    worlds_list = load_worlds()
    worlds = {w["id"]: w for w in worlds_list}
    valid_spaces = build_all_valid_spaces(worlds_list)

    # Load all 1,152 generations
    raw_records = []
    for path in sorted(glob.glob("research/ssr_pilot/runs/*.jsonl")):
        with open(path) as f:
            for line in f:
                if line.strip():
                    raw_records.append(json.loads(line))

    assert len(raw_records) == 1152

    for rec in raw_records:
        w_id = rec["world"]
        world = worlds[w_id]
        v_sols = valid_spaces[w_id].valid_solutions
        raw_text = rec["response"]

        base_verdict = evaluate_oracle(world, raw_text)
        steps = base_verdict.steps

        # Test against all valid references in V(x)
        for ref_steps in v_sols:
            # Exercise reference comparison
            comp = compare_to_reference(world, steps, raw_text, ref_steps)
            assert isinstance(comp, dict)

            # Re-evaluate oracle and confirm 100% invariance
            subsequent_verdict = evaluate_oracle(world, raw_text)
            assert subsequent_verdict.semantic_valid == base_verdict.semantic_valid
            assert subsequent_verdict.reason == base_verdict.reason


def test_domain_scheduling_semantics_and_invalid_mutants():
    """Verify scheduling validator accepts valid noncanonical ties and rejects invalid mutants."""
    # World sched_01: P1 burst 24, P2 burst 3, P3 burst 3, all arrival 0, FCFS
    # Multiple tie permutations are valid
    w = {
        "id": "test_sched",
        "family": "scheduling",
        "policy": "FCFS",
        "processes": [
            {"pid": "P1", "arrival": 0, "burst": 2},
            {"pid": "P2", "arrival": 0, "burst": 2},
        ],
        "constraints": []
    }

    # Valid tie order 1: P1 then P2
    v1 = evaluate_candidate(w, "TRACE: P1 0-2, P2 2-4")
    assert v1.semantic_valid == "TRUE"
    assert v1.reason == "ok"

    # Valid tie order 2: P2 then P1
    v2 = evaluate_candidate(w, "TRACE: P2 0-2, P1 2-4")
    assert v2.semantic_valid == "TRUE"
    assert v2.reason == "ok"

    # Invalid mutant 1: Overlapping execution
    bad_overlap = evaluate_candidate(w, "TRACE: P1 0-2, P2 1-3")
    assert bad_overlap.semantic_valid == "FALSE"
    assert bad_overlap.reason == "rule:overlapping_segments"

    # Invalid mutant 2: Incomplete execution
    bad_incomplete = evaluate_candidate(w, "TRACE: P1 0-2")
    assert bad_incomplete.semantic_valid == "FALSE"
    assert bad_incomplete.reason == "rule:incomplete"

    # Invalid mutant 3: Wrong burst duration
    bad_burst = evaluate_candidate(w, "TRACE: P1 0-3, P2 3-5")
    assert bad_burst.semantic_valid == "FALSE"
    assert bad_burst.reason == "rule:wrong_burst_length"


def test_domain_synchronization_semantics_and_invalid_mutants():
    """Verify synchronization validator accepts valid interleavings and rejects illegal operations."""
    w = {
        "id": "test_sync",
        "family": "sync",
        "threads": {
            "T1": [["lock", "m1"], ["write", "x"], ["unlock", "m1"]],
            "T2": [["lock", "m1"], ["write", "y"], ["unlock", "m1"]],
        },
        "semaphores": {},
        "constraints": []
    }

    # Valid interleaving 1: T1 then T2
    v1 = evaluate_candidate(w, "TRACE: T1 lock(m1), T1 write(x), T1 unlock(m1), T2 lock(m1), T2 write(y), T2 unlock(m1)")
    assert v1.semantic_valid == "TRUE"

    # Valid interleaving 2: T2 then T1
    v2 = evaluate_candidate(w, "TRACE: T2 lock(m1), T2 write(y), T2 unlock(m1), T1 lock(m1), T1 write(x), T1 unlock(m1)")
    assert v2.semantic_valid == "TRUE"

    # Invalid: Mutual exclusion violation (T2 acquires m1 while held by T1)
    bad_mutex = evaluate_candidate(w, "TRACE: T1 lock(m1), T2 lock(m1), T1 write(x), T1 unlock(m1), T2 write(y), T2 unlock(m1)")
    assert bad_mutex.semantic_valid == "FALSE"
    assert bad_mutex.reason == "rule:mutual_exclusion_violation"

    # Invalid: Program order violation (T1 writes before lock)
    bad_po = evaluate_candidate(w, "TRACE: T1 write(x), T1 lock(m1), T1 unlock(m1), T2 lock(m1), T2 write(y), T2 unlock(m1)")
    assert bad_po.semantic_valid == "FALSE"
    assert bad_po.reason == "rule:program_order_violation"


def test_domain_banker_semantics_and_invalid_mutants():
    """Verify Banker validator accepts all valid safe sequences and rejects unsafe transitions."""
    w = {
        "id": "test_bank",
        "family": "banker",
        "available": [3, 3, 2],
        "processes": [
            {"pid": "P0", "alloc": [0, 1, 0], "max": [7, 5, 3]},
            {"pid": "P1", "alloc": [2, 0, 0], "max": [3, 2, 2]},
            {"pid": "P2", "alloc": [3, 0, 2], "max": [9, 0, 2]},
            {"pid": "P3", "alloc": [2, 1, 1], "max": [2, 2, 2]},
            {"pid": "P4", "alloc": [0, 0, 2], "max": [4, 3, 3]},
        ],
        "constraints": []
    }

    # Valid safe sequence 1: P1, P3, P4, P0, P2
    v1 = evaluate_candidate(w, "TRACE: P1, P3, P4, P0, P2")
    assert v1.semantic_valid == "TRUE"
    assert v1.reason == "ok"

    # Valid safe sequence 2: P1, P3, P4, P2, P0
    v2 = evaluate_candidate(w, "TRACE: P1, P3, P4, P2, P0")
    assert v2.semantic_valid == "TRUE"
    assert v2.reason == "ok"

    # Invalid: Need exceeds work (P0 cannot execute first)
    bad_need = evaluate_candidate(w, "TRACE: P0, P1, P3, P4, P2")
    assert bad_need.semantic_valid == "FALSE"
    assert bad_need.reason == "rule:need_exceeds_work"

    # Invalid: Repeated process
    bad_rep = evaluate_candidate(w, "TRACE: P1, P1, P3, P4, P0")
    assert bad_rep.semantic_valid == "FALSE"
    assert bad_rep.reason == "rule:repeated_process"

    # Invalid: Incomplete sequence
    bad_inc = evaluate_candidate(w, "TRACE: P1, P3, P4")
    assert bad_inc.semantic_valid == "FALSE"
    assert bad_inc.reason == "rule:incomplete"
