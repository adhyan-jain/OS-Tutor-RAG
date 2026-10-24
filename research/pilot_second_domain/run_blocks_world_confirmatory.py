"""
Confirmatory execution runner for the second-domain (Blocks World) preregistered experiment.

Preregistered specifications:
- 24 tasks across 3 cardinality tiers.
- 4 local open-weight models: qwen3:8b, gemma2:9b, llama3.1:8b, mistral:7b-instruct.
- 3 surface variants: v0 (PDDL-like), v1 (natural language), v2 (structured JSON).
- 4 generation seeds: 0, 1, 2, 3.
- Total generations: 24 * 3 * 4 = 288 per model; 1,152 in total.
- Decoding: temperature=0.7, top_p=0.9, max_tokens=512.
- Resumable JSONL logging preserving all raw model outputs, timestamps, latencies, and tokens.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import time
from typing import Dict, List
import requests

from research.pilot_second_domain.blocks_world_tasks import (
    get_all_tasks,
    render_task_prompt,
    extract_plan,
    evaluate_plan_semantic,
    format_plan_as_string,
    plan_to_tuple,
    BlocksWorld,
)

RUNS_DIR = "research/pilot_second_domain/runs"
MODELS = ["qwen3:8b", "gemma2:9b", "llama3.1:8b", "mistral:7b-instruct"]
VARIANTS = ["v0", "v1", "v2"]
SEEDS = [0, 1, 2, 3]
SETTINGS = {"temperature": 0.7, "top_p": 0.9, "num_predict": 512}
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def call_key(model: str, task_id: str, variant: str, seed: int) -> str:
    payload = [model, task_id, variant, seed, SETTINGS]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class RunLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.keys = set()
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            self.keys.add(rec["key"])
                        except Exception:
                            pass

    def add(self, rec: Dict):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "a") as f:
            f.write(json.dumps(rec) + "\n")
        self.keys.add(rec["key"])


def generate_single_completion(model: str, prompt: str, seed: int) -> Dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {**SETTINGS, "seed": seed},
    }
    if model.startswith("qwen3"):
        body["think"] = False

    t0 = time.time()
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=300)
            r.raise_for_status()
            res = r.json()
            latency = round(time.time() - t0, 3)
            return {
                "response": res.get("message", {}).get("content", ""),
                "done_reason": res.get("done_reason", "stop"),
                "eval_count": res.get("eval_count", 0),
                "prompt_eval_count": res.get("prompt_eval_count", 0),
                "latency_s": latency,
                "error": None,
            }
        except Exception as e:
            last_err = str(e)
            time.sleep(2 * (attempt + 1))

    return {
        "response": "",
        "done_reason": "error",
        "eval_count": 0,
        "prompt_eval_count": 0,
        "latency_s": round(time.time() - t0, 3),
        "error": last_err,
    }


def run_confirmatory_for_model(model: str, tasks: List[Dict]) -> None:
    safe_name = model.replace(":", "_").replace("/", "_")
    log_path = f"{RUNS_DIR}/{safe_name}.jsonl"
    logger = RunLogger(log_path)

    # Build queue of 288 calls
    queue = []
    for task in tasks:
        t_id = task["id"]
        for var in VARIANTS:
            prompt = render_task_prompt(task, var)
            p_sha = hashlib.sha256(prompt.encode()).hexdigest()
            for seed in SEEDS:
                k = call_key(model, t_id, var, seed)
                if k not in logger.keys:
                    queue.append({
                        "key": k,
                        "model": model,
                        "task_id": t_id,
                        "variant": var,
                        "seed": seed,
                        "prompt": prompt,
                        "prompt_sha256": p_sha,
                        "task": task,
                    })

    total = len(tasks) * len(VARIANTS) * len(SEEDS)
    print(f"[{model}] {len(queue)} to run ({len(logger.keys)} already logged out of {total})", flush=True)

    t_start = time.time()
    for i, item in enumerate(queue, 1):
        gen_res = generate_single_completion(model, item["prompt"], item["seed"])
        rec = {
            "key": item["key"],
            "model": model,
            "task_id": item["task_id"],
            "variant": item["variant"],
            "seed": item["seed"],
            "prompt": item["prompt"],
            "prompt_sha256": item["prompt_sha256"],
            "settings": SETTINGS,
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            **gen_res,
        }
        logger.add(rec)

        if i % 20 == 0 or i == len(queue):
            elapsed = time.time() - t_start
            per_call = elapsed / i
            rem = per_call * (len(queue) - i)
            print(f"[{model}] {i}/{len(queue)} completed ({per_call:.2f}s/call, ETA: {rem/60:.1f}m)", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Run Blocks World Confirmatory LLM Experiment")
    parser.add_argument("--model", type=str, default="", help="Specific model to run (comma-separated if multiple)")
    args = parser.parse_args()

    tasks = get_all_tasks()
    selected_models = args.model.split(",") if args.model else MODELS

    print(f"=== Starting Confirmatory Run for {len(selected_models)} models across {len(tasks)} tasks ===")
    for m in selected_models:
        if m in MODELS:
            run_confirmatory_for_model(m, tasks)
        else:
            print(f"Warning: Model {m} not in registered model list {MODELS}")

    print("=== All requested model runs finished ===")


if __name__ == "__main__":
    main()
