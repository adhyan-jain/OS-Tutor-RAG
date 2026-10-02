"""
Baseline Evaluation Runner.
Executes baseline models (Zero-Shot, CoT, Reference-Provided vs Reference-Absent, Symbolic Validator)
across the benchmark splits.
"""

import json
import os
from typing import Dict, Any, List
from research.simulator.cpu_scheduler import CPUSchedulerSimulator, Process
from research.evaluation.metrics import compute_rsg, evaluate_reference_sensitivity, analyze_ranking_inversions

class BaselineModel:
    def __init__(self, name: str, heuristic: str = "first_fit"):
        self.name = name
        self.heuristic = heuristic

    def predict_trace(self, problem: List[Dict[str, Any]], reference: List[Any] = None) -> List[Any]:
        # Simulate model predictions with deterministic/heuristics or reference-dependence
        procs = [Process(p["pid"], p["arrival_time"], p["burst_time"]) for p in problem]
        sim = CPUSchedulerSimulator(algorithm="FCFS")
        valid_traces = sim.generate_all_valid_traces(procs)

        if not valid_traces:
            return []

        if self.heuristic == "first_fit":
            return valid_traces[0]
        elif self.heuristic == "last_fit":
            return valid_traces[-1]
        elif self.heuristic == "reference_biased":
            if reference and reference in valid_traces:
                return reference
            return valid_traces[0]
        else:
            return valid_traces[0]

    def judge_candidate(self, problem: List[Dict[str, Any]], candidate: List[Any], reference: List[Any]) -> bool:
        """Judges candidate trace given a reference trace R."""
        if self.heuristic == "strict_reference_matcher":
            return candidate == reference
        elif self.heuristic == "symbolic_verifier":
            procs = [Process(p["pid"], p["arrival_time"], p["burst_time"]) for p in problem]
            sim = CPUSchedulerSimulator(algorithm="FCFS")
            return sim.validate_trace(procs, candidate)
        elif self.heuristic == "reference_sensitive_llm":
            # Model accepts candidate if exact match to reference OR if first step matches reference
            if candidate == reference:
                return True
            if candidate and reference and candidate[0] == reference[0]:
                return True
            return False
        return False

def run_all_baselines(dataset_path: str = "research/benchmark/dataset.json") -> Dict[str, Any]:
    with open(dataset_path, "r") as f:
        data = json.load(f)

    models = [
        BaselineModel("Canonical_Exact_Matcher", heuristic="strict_reference_matcher"),
        BaselineModel("Reference_Sensitive_Judge", heuristic="reference_sensitive_llm"),
        BaselineModel("Symbolic_Validator_Oracle", heuristic="symbolic_verifier")
    ]

    results = {}

    for model in models:
        ref_scores = []
        sem_scores = []
        preds_r1 = []
        preds_r2 = []

        for item in data.get("id_split", []):
            prob = item["problem"]
            r1 = item["R1"]
            r2 = item["R2"]
            inv = item["I"]

            # Evaluate on candidate R2 (which is semantically valid but R2 != R1)
            # Reference-relative scoring evaluates R2 against reference R1
            j_r1 = model.judge_candidate(prob, candidate=r2, reference=r1)
            j_r2 = model.judge_candidate(prob, candidate=r2, reference=r2)

            # Ground truth semantics
            procs = [Process(p["pid"], p["arrival_time"], p["burst_time"]) for p in prob]
            sim = CPUSchedulerSimulator(algorithm="FCFS")
            v_sem = sim.validate_trace(procs, r2)

            ref_scores.append(float(j_r1))
            sem_scores.append(float(v_sem))

            preds_r1.append(j_r1)
            preds_r2.append(j_r2)

        rsg_stats = compute_rsg(ref_scores, sem_scores)
        sens_stats = evaluate_reference_sensitivity(preds_r1, preds_r2)

        results[model.name] = {
            "rsg_metrics": rsg_stats,
            "sensitivity_metrics": sens_stats
        }

    return results

if __name__ == "__main__":
    res = run_all_baselines()
    print(json.dumps(res, indent=2))
