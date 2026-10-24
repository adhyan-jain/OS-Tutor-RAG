"""
Blocks World Benchmark Task Suite (N = 24 planning tasks)
Structured into three cardinality tiers:
- Tier 1: Unique-Solution Tasks (8 tasks, |V_i| = 1)
- Tier 2: Commutative Sub-Goal Tasks (8 tasks, |V_i| in [2, 6])
- Tier 3: High-Permutation Tasks (8 tasks, |V_i| in [8, 24])

Provides:
- BlocksWorld deterministic state transition engine and all-shortest-paths BFS enumerator.
- 24 benchmark task definitions.
- Three prompt surface variants: v0 (PDDL-like), v1 (natural language), v2 (structured JSON).
- Robust action parser extracting ("move", X, Y) and ("move_to_table", X).
- Evaluators: E1 (strict string match), E2 (normalized action match), E3 (semantic state oracle).
"""

from collections import deque
import json
import re
from typing import Dict, List, Optional, Set, Tuple


class BlocksWorld:
    """
    Finite state transition system for Blocks World.
    State representation: (on, on_table, clear)
    where on is Dict[top, bottom], on_table is Set[block], clear is Set[block].
    """
    def __init__(self, blocks: List[str]):
        self.blocks = sorted(blocks)

    def is_valid_state(self, on: Dict[str, str], on_table: Set[str], clear: Set[str]) -> bool:
        for b in self.blocks:
            in_on = b in on
            in_table = b in on_table
            if in_on == in_table:
                return False
        # No cyclic stacks
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
            # Move x to table if currently on another block
            if x in on:
                actions.append(("move_to_table", x))
            # Move x onto another clear block y
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
            if x not in new_on:
                raise ValueError(f"Cannot move {x} to table: not on another block")
            z = new_on.pop(x)
            new_on_table.add(x)
            new_clear.add(z)
        elif act_type == "move":
            y = action[2]
            if x not in new_clear or y not in new_clear or x == y:
                raise ValueError(f"Illegal move {x} onto {y}")
            if x in new_on:
                z = new_on.pop(x)
                new_clear.add(z)
            else:
                new_on_table.remove(x)
            new_on[x] = y
            new_clear.remove(y)
        else:
            raise ValueError(f"Unknown action type {act_type}")

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
        All-shortest-paths level-synchronous BFS to enumerate the complete valid space V(x).
        Guarantees that all and only shortest paths from s_0 to G are found.
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


def get_all_tasks() -> List[Dict]:
    """
    Returns 24 preregistered Blocks World tasks with three tiers.
    """
    return [
        # --- TIER 1: Unique-Solution Tasks (|V_i| = 1, 8 tasks) ---
        {
            "id": "bw_01_single_stack",
            "tier": 1,
            "blocks": ["A", "B"],
            "init_on": {},
            "init_table": ["A", "B"],
            "goal_on": {"A": "B"},
            "goal_table": ["B"],
            "expected_cardinality": 1,
            "min_length": 1,
        },
        {
            "id": "bw_02_unstack_and_stack",
            "tier": 1,
            "blocks": ["A", "B", "C"],
            "init_on": {"A": "B"},
            "init_table": ["B", "C"],
            "goal_on": {"C": "A"},
            "goal_table": ["A", "B"],
            "expected_cardinality": 1,
            "min_length": 2,
        },
        {
            "id": "bw_03_sussman_anomaly",
            "tier": 1,
            "blocks": ["A", "B", "C"],
            "init_on": {"C": "A"},
            "init_table": ["A", "B"],
            "goal_on": {"A": "B", "B": "C"},
            "goal_table": ["C"],
            "expected_cardinality": 1,
            "min_length": 3,
        },
        {
            "id": "bw_04_stack_three_linear",
            "tier": 1,
            "blocks": ["A", "B", "C"],
            "init_on": {},
            "init_table": ["A", "B", "C"],
            "goal_on": {"A": "B", "B": "C"},
            "goal_table": ["C"],
            "expected_cardinality": 1,
            "min_length": 2,
        },
        {
            "id": "bw_05_invert_two",
            "tier": 1,
            "blocks": ["A", "B"],
            "init_on": {"A": "B"},
            "init_table": ["B"],
            "goal_on": {"B": "A"},
            "goal_table": ["A"],
            "expected_cardinality": 1,
            "min_length": 2,
        },
        {
            "id": "bw_06_clear_and_place",
            "tier": 1,
            "blocks": ["A", "B", "C"],
            "init_on": {"A": "B"},
            "init_table": ["B", "C"],
            "goal_on": {"C": "B"},
            "goal_table": ["B"],
            "expected_cardinality": 1,
            "min_length": 2,
        },
        {
            "id": "bw_07_four_stack_linear",
            "tier": 1,
            "blocks": ["A", "B", "C", "D"],
            "init_on": {},
            "init_table": ["A", "B", "C", "D"],
            "goal_on": {"A": "B", "B": "C", "C": "D"},
            "goal_table": ["D"],
            "expected_cardinality": 1,
            "min_length": 3,
        },
        {
            "id": "bw_08_unstack_deep",
            "tier": 1,
            "blocks": ["A", "B", "C", "D"],
            "init_on": {"A": "B", "B": "C", "C": "D"},
            "init_table": ["D"],
            "goal_on": {"A": "D"},
            "goal_table": ["B", "C", "D"],
            "expected_cardinality": 1,
            "min_length": 4,
        },

        # --- TIER 2: Commutative Sub-Goal Tasks (|V_i| in [2, 6], 8 tasks) ---
        {
            "id": "bw_09_independent_pairs",
            "tier": 2,
            "blocks": ["A", "B", "C", "D"],
            "init_on": {},
            "init_table": ["A", "B", "C", "D"],
            "goal_on": {"A": "B", "C": "D"},
            "goal_table": ["B", "D"],
            "expected_cardinality": 2,
            "min_length": 2,
        },
        {
            "id": "bw_10_parallel_clear",
            "tier": 2,
            "blocks": ["A", "B", "C", "D"],
            "init_on": {"A": "B", "C": "D"},
            "init_table": ["B", "D"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D"],
            "expected_cardinality": 2,
            "min_length": 2,
        },
        {
            "id": "bw_11_clear_and_stack",
            "tier": 2,
            "blocks": ["A", "B", "C", "D"],
            "init_on": {"A": "B"},
            "init_table": ["B", "C", "D"],
            "goal_on": {"C": "D"},
            "goal_table": ["A", "B", "D"],
            "expected_cardinality": 2,
            "min_length": 2,
        },
        {
            "id": "bw_12_two_towers_unstack_3",
            "tier": 2,
            "blocks": ["A", "B", "C", "D", "E"],
            "init_on": {"A": "B", "B": "C", "D": "E"},
            "init_table": ["C", "E"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E"],
            "expected_cardinality": 3,
            "min_length": 3,
        },
        {
            "id": "bw_13_tower_and_single_4",
            "tier": 2,
            "blocks": ["A", "B", "C", "D", "E", "F"],
            "init_on": {"A": "B", "B": "C", "C": "D", "E": "F"},
            "init_table": ["D", "F"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F"],
            "expected_cardinality": 4,
            "min_length": 4,
        },
        {
            "id": "bw_14_three_subgoals",
            "tier": 2,
            "blocks": ["A", "B", "C", "D", "E", "F"],
            "init_on": {},
            "init_table": ["A", "B", "C", "D", "E", "F"],
            "goal_on": {"A": "B", "C": "D", "E": "F"},
            "goal_table": ["B", "D", "F"],
            "expected_cardinality": 6,
            "min_length": 3,
        },
        {
            "id": "bw_15_three_clears",
            "tier": 2,
            "blocks": ["A", "B", "C", "D", "E", "F"],
            "init_on": {"A": "B", "C": "D", "E": "F"},
            "init_table": ["B", "D", "F"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F"],
            "expected_cardinality": 6,
            "min_length": 3,
        },
        {
            "id": "bw_16_two_towers_of_two_6",
            "tier": 2,
            "blocks": ["A", "B", "C", "D", "E", "F"],
            "init_on": {"A": "B", "B": "C", "D": "E", "E": "F"},
            "init_table": ["C", "F"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F"],
            "expected_cardinality": 6,
            "min_length": 4,
        },

        # --- TIER 3: High-Permutation Tasks (|V_i| in [8, 24], 8 tasks) ---
        {
            "id": "bw_17_unstack_interleave_10",
            "tier": 3,
            "blocks": ["A", "B", "C", "D", "E", "F", "G"],
            "init_on": {"A": "B", "B": "C", "C": "D", "E": "F", "F": "G"},
            "init_table": ["D", "G"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F", "G"],
            "expected_cardinality": 10,
            "min_length": 5,
        },
        {
            "id": "bw_18_unstack_interleave_12",
            "tier": 3,
            "blocks": ["A", "B", "C", "D", "E", "F", "G"],
            "init_on": {"A": "B", "B": "C", "D": "E", "F": "G"},
            "init_table": ["C", "E", "G"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F", "G"],
            "expected_cardinality": 12,
            "min_length": 4,
        },
        {
            "id": "bw_19_unstack_interleave_12_alt",
            "tier": 3,
            "blocks": ["P", "Q", "R", "S", "T", "U", "V"],
            "init_on": {"P": "Q", "Q": "R", "S": "T", "U": "V"},
            "init_table": ["R", "T", "V"],
            "goal_on": {},
            "goal_table": ["P", "Q", "R", "S", "T", "U", "V"],
            "expected_cardinality": 12,
            "min_length": 4,
        },
        {
            "id": "bw_20_unstack_interleave_20",
            "tier": 3,
            "blocks": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "init_on": {"A": "B", "B": "C", "C": "D", "E": "F", "G": "H"},
            "init_table": ["D", "F", "H"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "expected_cardinality": 20,
            "min_length": 5,
        },
        {
            "id": "bw_21_unstack_interleave_20_alt",
            "tier": 3,
            "blocks": ["P", "Q", "R", "S", "T", "U", "V", "W"],
            "init_on": {"P": "Q", "Q": "R", "R": "S", "T": "U", "V": "W"},
            "init_table": ["S", "U", "W"],
            "goal_on": {},
            "goal_table": ["P", "Q", "R", "S", "T", "U", "V", "W"],
            "expected_cardinality": 20,
            "min_length": 5,
        },
        {
            "id": "bw_22_four_clears_24",
            "tier": 3,
            "blocks": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "init_on": {"A": "B", "C": "D", "E": "F", "G": "H"},
            "init_table": ["B", "D", "F", "H"],
            "goal_on": {},
            "goal_table": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "expected_cardinality": 24,
            "min_length": 4,
        },
        {
            "id": "bw_23_four_clears_24_alt",
            "tier": 3,
            "blocks": ["P", "Q", "R", "S", "T", "U", "V", "W"],
            "init_on": {"P": "Q", "R": "S", "T": "U", "V": "W"},
            "init_table": ["Q", "S", "U", "W"],
            "goal_on": {},
            "goal_table": ["P", "Q", "R", "S", "T", "U", "V", "W"],
            "expected_cardinality": 24,
            "min_length": 4,
        },
        {
            "id": "bw_24_unstack_interleave_10_alt",
            "tier": 3,
            "blocks": ["P", "Q", "R", "S", "T", "U", "V"],
            "init_on": {"P": "Q", "Q": "R", "R": "S", "T": "U", "U": "V"},
            "init_table": ["S", "V"],
            "goal_on": {},
            "goal_table": ["P", "Q", "R", "S", "T", "U", "V"],
            "expected_cardinality": 10,
            "min_length": 5,
        },
    ]


def format_plan_as_string(plan: List[Tuple[str, ...]]) -> str:
    """
    Formats action list into canonical string representation:
    e.g. 'move_to_table(A), move(A, B)'
    """
    return ", ".join(
        f"{act[0]}({', '.join(act[1:])})" for act in plan
    )


def plan_to_tuple(plan: List[Tuple[str, ...]]) -> Tuple[Tuple[str, ...], ...]:
    return tuple(tuple(act) for act in plan)


def render_task_prompt(task: Dict, variant: str) -> str:
    """
    Renders prompt for a task under one of 3 surface variants:
    - v0: Declarative PDDL-like notation
    - v1: Natural language description
    - v2: Structured JSON problem statement
    """
    blocks = sorted(task["blocks"])
    init_on = task["init_on"]
    init_table = sorted(task["init_table"])
    goal_on = task["goal_on"]
    goal_table = sorted(task["goal_table"])

    # Clear blocks initially
    clear = sorted(set(blocks) - set(init_on.values()))

    if variant == "v0":
        # Declarative PDDL-like
        on_preds = [f"on({k}, {v})" for k, v in sorted(init_on.items())]
        table_preds = [f"ontable({b})" for b in init_table]
        clear_preds = [f"clear({b})" for b in clear]
        init_preds = ", ".join(on_preds + table_preds + clear_preds)

        g_on_preds = [f"on({k}, {v})" for k, v in sorted(goal_on.items())]
        g_table_preds = [f"ontable({b})" for b in goal_table]
        goal_preds = ", ".join(g_on_preds + g_table_preds) if (g_on_preds or g_table_preds) else "all clear on table"

        prompt = (
            f"In Blocks World, blocks are: {', '.join(blocks)}.\n"
            f"Initial state: {init_preds}.\n"
            f"Goal: {goal_preds}.\n"
            f"Available operators: move(X, Y) [moves clear block X onto clear block Y], move_to_table(X) [moves clear block X to table].\n"
            f"Provide the plan as comma-separated actions starting with 'PLAN:'. For example: PLAN: move_to_table(A), move(A, B).\n"
            f"If several choices are allowed at any step, any of them may be chosen; more than one valid plan may exist, and any valid shortest plan is accepted.\n"
            f"Reply with the plan only, with no explanation."
        )

    elif variant == "v1":
        # Natural language room description
        init_desc = []
        for k, v in sorted(init_on.items()):
            init_desc.append(f"block {k} is stacked on block {v}")
        for b in init_table:
            init_desc.append(f"block {b} is on the table")
        init_text = ", ".join(init_desc)

        goal_desc = []
        for k, v in sorted(goal_on.items()):
            goal_desc.append(f"block {k} should be on block {v}")
        for b in goal_table:
            goal_desc.append(f"block {b} should be on the table")
        goal_text = ", ".join(goal_desc) if goal_desc else "all blocks should be on the table"

        prompt = (
            f"You are a robotic arm arranging wooden blocks: {', '.join(blocks)}.\n"
            f"Current layout: {init_text}.\n"
            f"Your target arrangement is: {goal_text}.\n"
            f"You can execute: move(X, Y) to put clear block X on clear block Y, or move_to_table(X) to place clear block X directly on the table.\n"
            f"Provide the complete plan as comma-separated actions starting with 'PLAN:'. For example: PLAN: move_to_table(A), move(A, B).\n"
            f"If multiple valid action orderings exist, any valid shortest plan is accepted.\n"
            f"Reply with the plan only, with no explanation."
        )

    elif variant == "v2":
        # Structured JSON problem statement
        spec = {
            "domain": "Blocks World Planning",
            "blocks": blocks,
            "initial_state": {
                "on": dict(sorted(init_on.items())),
                "on_table": init_table,
                "clear": clear,
            },
            "goal_state": {
                "on": dict(sorted(goal_on.items())),
                "on_table": goal_table,
            },
            "operators": ["move(X, Y)", "move_to_table(X)"],
        }
        json_str = json.dumps(spec, indent=2)

        prompt = (
            f"Consider the following structured Blocks World planning problem:\n"
            f"```json\n{json_str}\n```\n"
            f"Provide the complete solution plan as comma-separated actions starting with 'PLAN:'. For example: PLAN: move_to_table(A), move(A, B).\n"
            f"If multiple valid shortest paths exist, any of them is accepted.\n"
            f"Reply with the plan only, with no explanation."
        )

    else:
        raise ValueError(f"Unknown variant {variant}")

    return prompt


def extract_plan(response_text: str) -> List[Tuple[str, ...]]:
    """
    Extracts action sequence from LLM response.
    Recognizes actions like move(A, B) and move_to_table(A).
    """
    # Look for 'PLAN:' prefix if present
    text = response_text
    m = re.search(r"PLAN:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    if m:
        text = m.group(1)

    # Clean code blocks or extra markdown
    text = re.sub(r"```[a-z]*", "", text)
    text = text.replace("`", "")

    # Regex to match actions: move_to_table(X) or move(X, Y)
    pattern = re.compile(r"\b(move_to_table|move)\s*\(\s*([A-Za-z0-9_]+)\s*(?:,\s*([A-Za-z0-9_]+))?\s*\)", re.IGNORECASE)

    actions: List[Tuple[str, ...]] = []
    for match in pattern.finditer(text):
        op = match.group(1).lower()
        arg1 = match.group(2).strip().upper()
        arg2 = match.group(3).strip().upper() if match.group(3) else None

        if op == "move_to_table":
            actions.append(("move_to_table", arg1))
        elif op == "move":
            if arg2 is not None:
                if arg2 == "TABLE":
                    actions.append(("move_to_table", arg1))
                else:
                    actions.append(("move", arg1, arg2))
            else:
                actions.append(("move_to_table", arg1))

    return actions


def evaluate_plan_semantic(task: Dict, plan: List[Tuple[str, ...]]) -> bool:
    """
    E3 Semantic State Oracle:
    Executes plan step-by-step from initial state on BlocksWorld transition model.
    Checks whether:
    1. Plan is non-empty.
    2. Every action is legal in the current state.
    3. Final state satisfies the goal condition.
    Does NOT depend on any reference plan.
    """
    if not plan:
        return False

    blocks = task["blocks"]
    init_on = dict(task["init_on"])
    init_table = set(task["init_table"])
    init_clear = set(blocks) - set(init_on.values())
    goal_on = task["goal_on"]
    goal_table = set(task["goal_table"])

    bw = BlocksWorld(blocks)
    on = init_on
    table = init_table
    clear = init_clear

    for act in plan:
        app = bw.get_applicable_actions(on, table, clear)
        if act not in app:
            return False
        try:
            on, table, clear = bw.apply_action(on, table, clear, act)
        except Exception:
            return False

    return bw.is_goal(on, table, goal_on, goal_table)
