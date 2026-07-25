"""Pre-sweep smoke test: exercise the riskiest config paths end-to-end once.

Runs one question through the config variants whose code paths differ most
(LLM-in-retrieval for hyde/multi_query, the sparse retriever, and MMR on/off),
so a crash surfaces in minutes rather than hours into the real sweep. Also
reports wall-clock timing per variant to ground the full sweep's estimate.

    PYTHONPATH=. .venv/bin/python -m eval._smoke_test
"""

from __future__ import annotations

import time
import traceback
from pathlib import Path

from src.config import GenerationConfig, PathConfig, PipelineConfig
from src.evaluation import load_eval_set, score_pipeline
from src.pipeline import RAGPipeline
from eval.ragas_eval import load_raw_documents

# (name, technique, use_multi_query, reranking method, mmr) -- chosen to cover
# every branch that the full sweep can take, not every combination of them.
_SMOKE_VARIANTS = [
    ("dense+cross_encoder+mmr", "dense", False, "cross_encoder", True),
    ("bm25+none+no_mmr", "bm25", False, "none", False),
    ("hybrid_rrf+multi_query", "hybrid_rrf", True, "cross_encoder", True),
    ("hyde+none", "hyde", False, "none", True),
]


def main() -> None:
    import torch

    print(f"torch {torch.__version__} | cuda available: {torch.cuda.is_available()}", flush=True)
    if torch.cuda.is_available():
        print(f"  device: {torch.cuda.get_device_name(0)}", flush=True)

    started_load = time.time()
    documents = load_raw_documents(PathConfig().data_raw_dir)
    eval_set = load_eval_set(Path("eval/eval_set.json"), num_questions=1)
    print(
        f"Loaded {len(documents)} documents, {len(eval_set)} eval question(s) "
        f"in {time.time() - started_load:.1f}s\n",
        flush=True,
    )

    failures = []
    for name, technique, use_multi_query, method, mmr in _SMOKE_VARIANTS:
        config = PipelineConfig(generation=GenerationConfig())
        config.retrieval.technique = technique
        config.retrieval.use_multi_query = use_multi_query
        config.reranking.method = method
        config.diversification.enabled = mmr

        print(f"=== {name}", flush=True)
        started = time.time()
        try:
            pipeline = RAGPipeline(config)
            ingest_started = time.time()
            pipeline.ingest(documents)
            ingest_elapsed = time.time() - ingest_started
            print(f"  ingest: {ingest_elapsed:.1f}s", flush=True)

            scores, _detail_rows, eval_tracker = score_pipeline(pipeline, eval_set)
            elapsed = time.time() - started
            total_calls = pipeline.tracker.num_calls + eval_tracker.num_calls
            print(f"  OK in {elapsed:.1f}s (ingest {ingest_elapsed:.1f}s) | llm_calls={total_calls} "
                  f"(gen={pipeline.tracker.num_calls}, judge={eval_tracker.num_calls})", flush=True)
            print(f"  scores: { {k: round(v, 3) for k, v in scores.items()} }\n", flush=True)
        except Exception as error:  # noqa: BLE001 - smoke test reports, doesn't raise
            print(f"  FAILED after {time.time() - started:.1f}s: {type(error).__name__}: {error}", flush=True)
            traceback.print_exc()
            failures.append(name)
            print(flush=True)

    if failures:
        print(f"SMOKE TEST FAILED for: {failures}")
        raise SystemExit(1)
    print("All smoke variants passed.")


if __name__ == "__main__":
    main()
