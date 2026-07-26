"""Measure retrieval quality alone, without generation or LLM judging.

The RAGAS sweep costs ~30 minutes per configuration because every question
runs the full generate-then-judge stack. But correctness correlates far more
strongly with the retrieval metrics than with anything the generator does
(context_recall r=+0.41 against faithfulness r=+0.09 -- see FINDINGS.md A2),
so retrieval is where the tuning effort belongs, and tuning it through the
full stack is enormously wasteful.

The golden QA set names the slide or section each question is answerable from
(``source_parent_ids``). That is a retrieval ground truth, so recall@k can be
computed directly from the retrieved chunks' parents with no LLM in the loop --
seconds per configuration instead of half an hour.

    PYTHONPATH=. .venv/bin/python -m eval.retrieval_eval

Techniques that call an LLM to reformulate the query (hyde, multi_query) are
skipped by default, since including them would reintroduce the cost this exists
to avoid; pass --include-llm-techniques to measure them too.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from src.chunking import chunk_document
from src.config import ChunkingConfig, GenerationConfig, PathConfig, PipelineConfig
from src.pipeline import RAGPipeline
from eval.ragas_eval import load_raw_documents

_DEFAULT_KS = (1, 3, 5, 10, 20)


def _parents_of(scored_chunks) -> list[str]:
    """Parent ids of retrieved chunks, in rank order, de-duplicated."""
    seen: list[str] = []
    for scored_chunk in scored_chunks:
        parent_id = scored_chunk.chunk.metadata.get("parent_id") or scored_chunk.chunk.chunk_id
        if parent_id not in seen:
            seen.append(parent_id)
    return seen


def evaluate_retrieval(
    pipeline: RAGPipeline,
    examples: list[dict],
    ks: tuple[int, ...] = _DEFAULT_KS,
) -> dict[str, float]:
    """Score a pipeline's retriever against the eval set's cited parents.

    Args:
        pipeline: An already-ingested RAGPipeline. Only its retriever is used;
            reranking, diversification and generation are bypassed so the
            measurement reflects retrieval alone.
        examples: Eval examples carrying ``source_parent_ids``.
        ks: Cut-offs to report recall at.

    Returns:
        recall@k for each k (fraction of questions with at least one cited
        parent retrieved), plus full_recall@k (fraction where *every* cited
        parent was retrieved, which is what multi-part questions need) and MRR.
    """
    max_k = max(ks)
    hits: dict[int, list[float]] = {k: [] for k in ks}
    full: dict[int, list[float]] = {k: [] for k in ks}
    reciprocal_ranks: list[float] = []

    for example in examples:
        expected = set(example["source_parent_ids"])
        retrieved = _parents_of(pipeline.retriever.retrieve(example["question"], top_k=max_k))

        for k in ks:
            top = set(retrieved[:k])
            hits[k].append(1.0 if top & expected else 0.0)
            full[k].append(1.0 if expected <= top else 0.0)

        rank = next((i for i, p in enumerate(retrieved, start=1) if p in expected), None)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

    scores = {f"recall@{k}": statistics.mean(hits[k]) for k in ks}
    scores.update({f"full_recall@{k}": statistics.mean(full[k]) for k in ks})
    scores["mrr"] = statistics.mean(reciprocal_ranks)
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="eval/eval_set.json")
    parser.add_argument(
        "--include-llm-techniques",
        action="store_true",
        help="Also measure hyde and multi_query (needs a running Ollama, much slower).",
    )
    args = parser.parse_args()

    examples = json.load(open(args.eval_set))["examples"]
    missing = [e["question"] for e in examples if not e.get("source_parent_ids")]
    if missing:
        raise SystemExit(f"{len(missing)} example(s) lack source_parent_ids; cannot score retrieval")

    documents = load_raw_documents(PathConfig().data_raw_dir)
    print(f"{len(documents)} documents, {len(examples)} questions\n")

    techniques = ["dense", "bm25", "hybrid_rrf"]
    if args.include_llm_techniques:
        techniques += ["hyde"]

    header = f"{'config':34s} {'R@1':>6s} {'R@3':>6s} {'R@5':>6s} {'R@10':>6s} {'full@5':>7s} {'MRR':>6s}"
    print(header)
    print("-" * len(header))

    for technique in techniques:
        config = PipelineConfig(generation=GenerationConfig())
        config.chunking = ChunkingConfig()
        config.retrieval.technique = technique

        started = time.time()
        pipeline = RAGPipeline(config)
        pipeline.ingest(documents)
        scores = evaluate_retrieval(pipeline, examples)

        label = technique
        print(
            f"{label:34s} {scores['recall@1']:6.3f} {scores['recall@3']:6.3f} "
            f"{scores['recall@5']:6.3f} {scores['recall@10']:6.3f} "
            f"{scores['full_recall@5']:7.3f} {scores['mrr']:6.3f}"
            f"   ({time.time() - started:.0f}s)"
        )


if __name__ == "__main__":
    main()
