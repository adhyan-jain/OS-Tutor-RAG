"""
Independent verification of the Blocks World reference spaces V(x_i).

Deliberately shares NO code with blocks_world_tasks.BlocksWorld:
  * states are tuples of stacks (bottom -> top), not (on, on_table, clear) dicts;
  * search is iterative-deepening DFS over ALL action sequences with NO visited-state
    pruning, so it cannot inherit a pruning bug from the level-synchronous BFS;
  * legality is re-derived from stack geometry.

For each task it checks that
  1. no plan of length < L* reaches the goal (so L* is the true shortest length),
  2. the number of goal-reaching sequences of length L* equals |V| from the BFS,
  3. the set of sequences is identical to the BFS set (not just equal in size),
  4. every enumerated plan is executable and ends in a goal state.
"""

import json
import sys
from typing import Dict, List, Set, Tuple

from research.pilot_second_domain.blocks_world_tasks import (
    BlocksWorld,
    get_all_tasks,
    plan_to_tuple,
)

Stacks = Tuple[Tuple[str, ...], ...]
Action = Tuple[str, ...]


def initial_stacks(task: Dict) -> Stacks:
    below = dict(task["init_on"])  # top -> bottom
    tops_of = {b: t for t, b in below.items()}
    stacks = []
    for b in task["init_table"]:
        s = [b]
        while s[-1] in tops_of:
            s.append(tops_of[s[-1]])
        stacks.append(tuple(s))
    return tuple(sorted(stacks))


def is_goal(stacks: Stacks, task: Dict) -> bool:
    pos = {}
    for s in stacks:
        for i, b in enumerate(s):
            pos[b] = (s, i)
    for top, bottom in task["goal_on"].items():
        st, i = pos[top]
        if i == 0 or st[i - 1] != bottom:
            return False
    for b in task["goal_table"]:
        if pos[b][1] != 0:
            return False
    return True


def successors(stacks: Stacks):
    n = len(stacks)
    for i in range(n):
        x = stacks[i][-1]
        src = stacks[i]
        others = [s for k, s in enumerate(stacks) if k != i]
        # move x to the table (only meaningful if it is not already alone on the table)
        if len(src) > 1:
            yield ("move_to_table", x), tuple(sorted(others + [src[:-1], (x,)]))
        # move x onto the top of another stack
        for j in range(n):
            if j == i:
                continue
            y = stacks[j][-1]
            new_stacks = [s for k, s in enumerate(stacks) if k not in (i, j)]
            new_stacks.append(stacks[j] + (x,))
            if len(src) > 1:
                new_stacks.append(src[:-1])
            yield ("move", x, y), tuple(sorted(new_stacks))


def enumerate_by_iddfs(task: Dict, max_depth: int = 10):
    start = initial_stacks(task)
    for limit in range(0, max_depth + 1):
        found: List[Tuple[Action, ...]] = []

        def dfs(state: Stacks, path: List[Action]):
            if len(path) == limit:
                if is_goal(state, task):
                    found.append(tuple(path))
                return
            for act, nxt in successors(state):
                path.append(act)
                dfs(nxt, path)
                path.pop()

        dfs(start, [])
        if found:
            return limit, found
    raise RuntimeError(f"No plan within depth {max_depth} for {task['id']}")


def replay(task: Dict, plan: Tuple[Action, ...]) -> bool:
    state = initial_stacks(task)
    for act in plan:
        nxt = [s for a, s in successors(state) if a == act]
        if not nxt:
            return False
        state = nxt[0]
    return is_goal(state, task)


def verify_all() -> Dict:
    report = {}
    all_ok = True
    for t in get_all_tasks():
        bw = BlocksWorld(t["blocks"])
        clear = set(t["blocks"]) - set(t["init_on"].values())
        bfs = {
            plan_to_tuple(p)
            for p in bw.enumerate_all_minimal_plans(
                t["init_on"], set(t["init_table"]), clear, t["goal_on"], set(t["goal_table"])
            )
        }
        length, dfs_plans = enumerate_by_iddfs(t)
        dfs_set: Set = set(dfs_plans)
        checks = {
            "iddfs_shortest_length": length,
            "declared_min_length": t["min_length"],
            "length_matches_declared": length == t["min_length"],
            "bfs_cardinality": len(bfs),
            "iddfs_cardinality": len(dfs_set),
            "declared_cardinality": t["expected_cardinality"],
            "cardinality_matches_declared": len(dfs_set) == t["expected_cardinality"],
            "sets_identical": bfs == dfs_set,
            "no_duplicates": len(dfs_plans) == len(dfs_set),
            "all_replay_valid": all(replay(t, p) for p in dfs_set),
            "all_bfs_len_equal": all(len(p) == length for p in bfs),
        }
        checks["ok"] = all(v for v in checks.values() if isinstance(v, bool))
        all_ok &= checks["ok"]
        report[t["id"]] = checks
    return {"all_ok": all_ok, "tasks": report}


if __name__ == "__main__":
    rep = verify_all()
    for tid, c in rep["tasks"].items():
        print(f"{tid:34s} L*={c['iddfs_shortest_length']} |V|bfs={c['bfs_cardinality']:2d} "
              f"|V|iddfs={c['iddfs_cardinality']:2d} identical={c['sets_identical']} ok={c['ok']}")
    print("ALL OK" if rep["all_ok"] else "MISMATCH")
    with open("research/pilot_second_domain/results/reference_space_verification.json", "w") as f:
        json.dump(rep, f, indent=2)
    sys.exit(0 if rep["all_ok"] else 1)
