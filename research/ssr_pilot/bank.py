"""
Trace bank per world, derived from the world's semantics.

  reference        first task-valid trace in canonical enumeration order
  valid            other task-valid traces (all if <= 60, else 20 sampled)
  invalid_rule     samples from the transition system with ONE rule relaxed,
                   kept only if the oracle rejects them for a rule violation
  invalid_constraint  rule-valid traces that violate the task constraint
                   (enumerated: V_rules minus V_task)

Nothing is made by editing the reference. Invalid traces are sampled from a
relaxed copy of the rules and then filtered by the oracle.
"""

import json
import os
import random
from typing import Dict, List

from research.ssr_pilot import families as F

BANK_DIR = "research/ssr_pilot/data/banks"
SEED = 20261004


def _steps(world: Dict, raw) -> tuple:
    f = world["family"]
    if f == "scheduling":
        return tuple((str(p), int(s), int(e)) for p, s, e in raw)
    if f == "sync":
        return tuple((str(t), str(o), str(a)) for t, o, a in raw)
    return tuple(str(p) for p in raw)


def build_bank(world: Dict, seed: int = SEED) -> Dict:
    rng = random.Random(f"{seed}-{world['id']}")
    V = F.enumerate_rules(world)
    task = [t for t in V if not F.violated_constraints(world, t)]
    cviol = [t for t in V if F.violated_constraints(world, t)]
    ref = task[0]
    alts = [t for t in task if t != ref]
    if len(alts) > 60:
        alts = rng.sample(alts, 20)
    vset = set(V)
    pool_rule, seen = [], set()
    for relax in F.relaxations(world):
        got = 0
        for _ in range(1500):
            t = F.relaxed_sample(world, relax, rng)
            if t is None or t in seen or t in vset:
                continue
            ok, reason = F.rules_check(world, t)
            if ok or reason == "incomplete":
                continue
            seen.add(t)
            pool_rule.append({"steps": t, "relaxation": relax, "reason": reason})
            got += 1
            if got >= 60:
                break
    pool_con = rng.sample(cviol, min(60, len(cviol)))

    # Profile matching (PREREGISTRATION deviation D1): K0 showed that distance-to-R alone separated valid
    # alternatives from invalid traces, because invalid traces sat farther from R. Each valid alternative is
    # therefore paired with the unused invalid trace whose similarity profile to R is closest.
    pool = [("rule", r["steps"], r) for r in pool_rule] + [("constraint", t, None) for t in pool_con]
    pairs, used = [], set()
    order = list(range(len(alts)))
    rng.shuffle(order)
    for i in order:
        pv = F.profile(world, alts[i], ref)
        best, best_cost = None, None
        for j, (cls, t, _) in enumerate(pool):
            if j in used:
                continue
            cost = sum(abs(x - y) for x, y in zip(F.profile(world, t, ref), pv)) + 1e-6 * rng.random()
            if best_cost is None or cost < best_cost:
                best, best_cost = j, cost
        if best is None:
            break
        used.add(best)
        pairs.append({"valid": alts[i], "invalid": pool[best][1], "class": pool[best][0],
                      "cost": best_cost})
    invalid_rule = [dict(pool[j][2]) for j in sorted(used) if pool[j][0] == "rule"]
    inv_c = [pool[j][1] for j in sorted(used) if pool[j][0] == "constraint"]
    return {"world": world["id"], "n_rules": len(V), "n_task": len(task), "reference": ref, "valid": alts,
            "invalid_rule": invalid_rule, "invalid_constraint": inv_c, "pairs": pairs,
            "n_invalid_rule_pool": len(pool_rule), "n_invalid_constraint_pool": len(cviol)}


def save_bank(bank: Dict, directory: str = BANK_DIR) -> None:
    os.makedirs(directory, exist_ok=True)
    with open(f"{directory}/{bank['world']}.json", "w") as f:
        json.dump(bank, f, indent=1)


def load_bank(world: Dict, directory: str = BANK_DIR) -> Dict:
    b = json.load(open(f"{directory}/{world['id']}.json"))
    b["reference"] = _steps(world, b["reference"])
    b["valid"] = [_steps(world, t) for t in b["valid"]]
    b["invalid_constraint"] = [_steps(world, t) for t in b["invalid_constraint"]]
    for r in b["invalid_rule"]:
        r["steps"] = _steps(world, r["steps"])
    for p in b["pairs"]:
        p["valid"], p["invalid"] = _steps(world, p["valid"]), _steps(world, p["invalid"])
    return b


def build_all(worlds: List[Dict]) -> List[Dict]:
    banks = [build_bank(w) for w in worlds]
    for b in banks:
        save_bank(b)
    return banks


if __name__ == "__main__":
    from research.ssr_pilot.worlds import load_worlds
    for b in build_all(load_worlds()):
        print(b["world"], "rules", b["n_rules"], "task", b["n_task"], "valid", len(b["valid"]),
              "inv_rule", len(b["invalid_rule"]), "inv_constraint", len(b["invalid_constraint"]))
