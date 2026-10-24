"""
Pilot implementation of second enumerable domain: Blocks World Planning.

Features:
1. Deterministic STRIPS state-transition model for Blocks World.
2. Complete valid space enumeration via all-shortest-paths BFS.
3. Trustworthy semantic execution oracle (E3).
4. Reference-matching evaluators: E1 (string match), E2 (normalized action match).
5. Verification of the Attenuation Law and RCR metrics on finite planning worlds.
"""

from collections import deque
import json
import os
import sys
from typing import Dict, List, Set, Tuple, Optional
import numpy as np

from research.ssr_pilot.rcrc.exact_margin_distribution import compute_exact_pairwise_margin


class BlocksWorld:
    """
    Finite state transition system for Blocks World.
    State representation: (on_tuples, on_table_set, clear_set)
    """
    def __init__(self, blocks: List[str]):
        self.blocks = sorted(blocks)

    def is_valid_state(self, on: Dict[str, str], on_table: Set[str], clear: Set[str]) -> bool:
        # Every block is either on table or on exactly one other block
        for b in self.blocks:
            in_on = b in on
            in_table = b in on_table
            if in_on == in_table:
                return False
        # No cyclic stacks
        visited = set()
        for b in self.blocks:
            curr = b
            path = set()
            while curr in on:
                if curr in path:
                    return False
                path.add(curr)
                curr = on[curr]
        # Clear blocks cannot have anything on them
        for top, bottom in on.items():
            if bottom in clear:
                return False
        return True

    def get_applicable_actions(self, on: Dict[str, str], on_table: Set[str], clear: Set[str]) -> List[Tuple[str, ...]]:
        actions = []
        for x in self.blocks:
            if x not in clear:
                continue
            # Action 1: Move x to table (if currently on something)
            if x in on:
                actions.append(("move_to_table", x))
            # Action 2: Move x onto another clear block y
            for y in self.blocks:
                if y != x and y in clear:
                    actions.append(("move", x, y))
        return sorted(actions)

    def apply_action(
        self,
        on: Dict[str, str],
        on_table: Set[str],
        clear: Set[str],
        action: Tuple[str, ...],
    ) -> Tuple[Dict[str, str], Set[str], Set[str]]:
        new_on = dict(on)
        new_on_table = set(on_table)
        new_clear = set(clear)

        act_type = action[0]
        x = action[1]

        if act_type == "move_to_table":
            z = new_on.pop(x)
            new_on_table.add(x)
            new_clear.add(z)
        elif act_type == "move":
            y = action[2]
            if x in new_on:
                z = new_on.pop(x)
                new_clear.add(z)
            else:
                new_on_table.remove(x)
            new_on[x] = y
            new_clear.remove(y)

        return new_on, new_on_table, new_clear

    def state_to_key(self, on: Dict[str, str], on_table: Set[str]) -> Tuple:
        return (tuple(sorted(on.items())), tuple(sorted(on_table)))

    def is_goal(self, on: Dict[str, str], on_table: Set[str], goal_on: Dict[str, str], goal_table: Set[str]) -> bool:
        for k, v in goal_on.items():
            if on.get(k) != v:
                return False
        for b in goal_table:
            if b not in on_table:
                return False
        return True

    def enumerate_all_minimal_plans(
        self,
        init_on: Dict[str, str],
        init_table: Set[str],
        init_clear: Set[str],
        goal_on: Dict[str, str],
        goal_table: Set[str],
    ) -> List[List[Tuple[str, ...]]]:
        """
        All-shortest-paths BFS to enumerate the complete valid space V(x).
        """
        start_key = self.state_to_key(init_on, init_table)
        queue = deque([(init_on, init_table, init_clear, [])])
        shortest_dist: Dict[Tuple, int] = {start_key: 0}
        valid_plans: List[List[Tuple[str, ...]]] = []
        min_goal_dist: Optional[int] = None

        while queue:
            on, table, clear, plan = queue.popleft()
            dist = len(plan)

            if min_goal_dist is not None and dist > min_goal_dist:
                break

            if self.is_goal(on, table, goal_on, goal_table):
                if min_goal_dist is None:
                    min_goal_dist = dist
                if dist == min_goal_dist:
                    valid_plans.append(plan)
                continue

            for act in self.get_applicable_actions(on, table, clear):
                next_on, next_table, next_clear = self.apply_action(on, table, clear, act)
                next_key = self.state_to_key(next_on, next_table)
                next_dist = dist + 1

                if next_key not in shortest_dist or shortest_dist[next_key] == next_dist:
                    shortest_dist[next_key] = next_dist
                    queue.append((next_on, next_table, next_clear, plan + [act]))

        return valid_plans


def define_benchmark_worlds() -> List[Dict]:
    """
    Defines 6 benchmark planning worlds with varying valid-space cardinality |V_i|.
    """
    worlds = [
        {
            "id": "bw_01_single_stack",
            "blocks": ["A", "B"],
            "init_on": {},
            "init_table": {"A", "B"},
            "init_clear": {"A", "B"},
            "goal_on": {"A": "B"},
            "goal_table": {"B"},
        },
        {
            "id": "bw_02_independent_pairs",
            "blocks": ["A", "B", "C", "D"],
            "init_on": {},
            "init_table": {"A", "B", "C", "D"},
            "init_clear": {"A", "B", "C", "D"},
            "goal_on": {"A": "B", "C": "D"},
            "goal_table": {"B", "D"},
        },
        {
            "id": "bw_03_three_subgoals",
            "blocks": ["A", "B", "C", "D", "E", "F"],
            "init_on": {},
            "init_table": {"A", "B", "C", "D", "E", "F"},
            "init_clear": {"A", "B", "C", "D", "E", "F"},
            "goal_on": {"A": "B", "C": "D", "E": "F"},
            "goal_table": {"B", "D", "F"},
        },
        {
            "id": "bw_04_unstack_and_stack",
            "blocks": ["A", "B", "C"],
            "init_on": {"A": "B"},
            "init_table": {"B", "C"},
            "init_clear": {"A", "C"},
            "goal_on": {"C": "A"},
            "goal_table": {"A", "B"},
        },
        {
            "id": "bw_05_sussman_anomaly",
            "blocks": ["A", "B", "C"],
            "init_on": {"C": "A"},
            "init_table": {"A", "B"},
            "init_clear": {"B", "C"},
            "goal_on": {"A": "B", "B": "C"},
            "goal_table": {"C"},
        },
        {
            "id": "bw_06_parallel_clear",
            "blocks": ["A", "B", "C", "D"],
            "init_on": {"A": "B", "C": "D"},
            "init_table": {"B", "D"},
            "init_clear": {"A", "C"},
            "goal_on": {},
            "goal_table": {"A", "B", "C", "D"},
        },
    ]
    return worlds


def run_blocks_world_rcr_pilot():
    worlds = define_benchmark_worlds()
    valid_spaces = {}
    
    print("--- 1. Exhaustive Valid-Space Enumeration ---")
    for w in worlds:
        bw = BlocksWorld(w["blocks"])
        plans = bw.enumerate_all_minimal_plans(
            w["init_on"], w["init_table"], w["init_clear"],
            w["goal_on"], w["goal_table"]
        )
        valid_spaces[w["id"]] = plans
        print(f"World {w['id']}: |V(x)| = {len(plans)} plans (length = {len(plans[0]) if plans else 0})")

    # Generate synthetic candidate models to test the attenuation and reversal mechanics
    # Model 1: 'planner_alpha' (high-competence, explores uniform over V)
    # Model 2: 'planner_beta' (favors alphabetical order)
    # Model 3: 'planner_gamma' (lower pass rate)
    models = ["planner_alpha", "planner_beta", "planner_gamma"]
    K_GENS = 12

    # Synthesize candidate generation distributions
    rng = np.random.default_rng(20261025)
    candidates = {m: {} for m in models}

    for w in worlds:
        w_id = w["id"]
        v_plans = valid_spaces[w_id]
        n_v = len(v_plans)

        # Alpha: 90% valid, distributed uniformly over V
        gens_a = []
        for _ in range(K_GENS):
            if rng.random() < 0.90:
                idx = rng.integers(0, n_v)
                gens_a.append(v_plans[idx])
            else:
                gens_a.append([("invalid_move", "X")])
        candidates["planner_alpha"][w_id] = gens_a

        # Beta: 80% valid, concentrated on plan 0 (canonical)
        gens_b = []
        for _ in range(K_GENS):
            if rng.random() < 0.80:
                gens_b.append(v_plans[0])
            else:
                gens_b.append([("invalid_move", "Y")])
        candidates["planner_beta"][w_id] = gens_b

        # Gamma: 50% valid, distributed randomly over V
        gens_c = []
        for _ in range(K_GENS):
            if rng.random() < 0.50:
                idx = rng.integers(0, n_v)
                gens_c.append(v_plans[idx])
            else:
                gens_c.append([("invalid_move", "Z")])
        candidates["planner_gamma"][w_id] = gens_c

    print("\n--- 2. Attenuation Law Verification ---")
    # Verify E[E2] = E3 / |V_i|
    ratios = []
    for w in worlds:
        w_id = w["id"]
        v_plans = valid_spaces[w_id]
        n_v = len(v_plans)
        bw = BlocksWorld(w["blocks"])

        for m in models:
            gens = candidates[m][w_id]
            # Semantic validity (E3)
            sem_pass = 0
            for g in gens:
                on = dict(w["init_on"])
                table = set(w["init_table"])
                clear = set(w["init_clear"])
                valid = True
                for act in g:
                    if act[0] not in ("move", "move_to_table"):
                        valid = False
                        break
                    # Check action legality
                    app = bw.get_applicable_actions(on, table, clear)
                    if act not in app:
                        valid = False
                        break
                    on, table, clear = bw.apply_action(on, table, clear, act)
                if valid and bw.is_goal(on, table, w["goal_on"], w["goal_table"]):
                    sem_pass += 1

            e3_score = sem_pass / K_GENS

            # Expected E2 score under uniform reference sampling
            e2_matches_per_ref = [0] * n_v
            for g in gens:
                for r_idx, ref in enumerate(v_plans):
                    if g == ref:
                        e2_matches_per_ref[r_idx] += 1
            expected_e2 = np.mean(e2_matches_per_ref) / K_GENS

            predicted_e2 = e3_score / n_v
            diff = abs(expected_e2 - predicted_e2)
            if e3_score > 0:
                ratio = expected_e2 / predicted_e2
                ratios.append(ratio)
            print(f"[{w_id}] {m:15s}: E3={e3_score:.3f}, |V|={n_v:2d}, Exp E2={expected_e2:.4f}, Pred E2={predicted_e2:.4f}, diff={diff:.1e}")

    print(f"\nAttenuation Law Check: Mean Ratio (Exp / Pred) = {np.mean(ratios):.6f}, Max Abs Diff = {np.max(np.abs(np.array(ratios) - 1.0)):.1e}")

    # 3. Dynamic Programming Exact Margin Distribution
    print("\n--- 3. Exact DP Pairwise Reversal Analysis ---")
    pairs = [("planner_alpha", "planner_beta"), ("planner_alpha", "planner_gamma"), ("planner_beta", "planner_gamma")]
    pair_results = {}

    for mA, mB in pairs:
        task_data = []
        for w in worlds:
            w_id = w["id"]
            v_plans = valid_spaces[w_id]
            k = len(v_plans)

            cA = [sum(1 for g in candidates[mA][w_id] if g == ref) for ref in v_plans]
            cB = [sum(1 for g in candidates[mB][w_id] if g == ref) for ref in v_plans]
            task_data.append({"c_A": cA, "c_B": cB, "n_refs": k})

        dp_res = compute_exact_pairwise_margin(task_data, K=K_GENS, q_type="uniform")
        pair_results[f"{mA}_vs_{mB}"] = dp_res
        print(f"Pair {mA} vs {mB}:")
        print(f"  Expected Margin: {dp_res['expected_margin']:.4f}")
        print(f"  P(A > B): {dp_res['p_positive']:.4f}, P(B > A): {dp_res['p_negative']:.4f}, P(Tie): {dp_res['p_zero']:.4f}")
        print(f"  Exact Winner Reversal Probability: {dp_res['winner_reversal_probability']:.4%}")

    # Output artifact
    out_dir = "research/pilot_second_domain/results"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "blocks_world_pilot.json")
    with open(out_file, "w") as f:
        json.dump({
            "domain": "BlocksWorld_Planning",
            "n_worlds": len(worlds),
            "valid_space_sizes": {w["id"]: len(valid_spaces[w["id"]]) for w in worlds},
            "models": models,
            "pairwise_results": {k: {
                "expected_margin": v["expected_margin"],
                "winner_reversal_probability": v["winner_reversal_probability"],
                "p_positive": v["p_positive"],
                "p_negative": v["p_negative"],
                "p_zero": v["p_zero"]
            } for k, v in pair_results.items()},
            "attenuation_check": {
                "mean_ratio_observed_over_predicted": float(np.mean(ratios)),
                "max_absolute_error": float(np.max(np.abs(np.array(ratios) - 1.0)))
            }
        }, f, indent=2)

    print(f"\nSaved pilot results to {out_file}")


if __name__ == "__main__":
    run_blocks_world_rcr_pilot()
