"""Compare reranker models, and reranking against not reranking at all.

Reranking measured *worse* than omitting it on this corpus (FINDINGS.md A7),
which is the opposite of the usual expectation. Two explanations are worth
separating before concluding that reranking does not help here:

- the reranker model is a poor fit -- `bge-reranker-large` is general-purpose
  and has no advantage on operating-systems lecture material;
- or the *approach* is wrong for this pipeline, because the reranker discards
  the retriever's scores entirely and substitutes its own judgement. Dense
  retrieval already reaches recall@5 of 0.923, so overruling it can only help
  if the reranker is the better judge; blending the two signals instead lets
  it adjust a good ranking rather than replace it.

Scored by whether the slide a question is answerable from survives into the
top-k after reranking -- no generation, no LLM judging.

    PYTHONPATH=. .venv/bin/python -m eval.reranker_eval
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from src.config import GenerationConfig, PathConfig, PipelineConfig
from src.embedding_cache import get_cross_encoder
from src.pipeline import RAGPipeline
from eval.ragas_eval import load_raw_documents

# (label, model id). None means no reranking: the retriever's own order.
_RERANKERS: list[tuple[str, str | None]] = [
    ("no reranking (dense order)", None),
    ("bge-reranker-large (current)", "BAAI/bge-reranker-large"),
    ("bge-reranker-v2-m3", "BAAI/bge-reranker-v2-m3"),
    ("ms-marco-MiniLM-L-6-v2", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
]

# How much weight to give the reranker when blending with the retriever's own
# ranking. 1.0 reproduces today's behaviour of ignoring the retriever entirely.
_BLEND_WEIGHTS = (1.0, 0.7, 0.5, 0.3)


def _rank_scores(n: int) -> list[float]:
    """Reciprocal-rank scores for a ranking of length n, normalised to [0, 1]."""
    return [1.0 / (1 + i) for i in range(n)]


def _normalise(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _score_config(
    pipeline: RAGPipeline,
    examples: list[dict],
    model_id: str | None,
    blend: float,
    pool_k: int,
    top_k: int,
) -> dict[str, float]:
    """Hit rate of the top-k after reranking `pool_k` retrieved candidates."""
    cross_encoder = get_cross_encoder(model_id) if model_id else None
    hits, full_hits = [], []

    for example in examples:
        candidates = pipeline.retriever.retrieve(example["question"], top_k=pool_k)
        if not candidates:
            hits.append(0.0)
            full_hits.append(0.0)
            continue

        if cross_encoder is None:
            ordered = candidates
        else:
            rerank_scores = _normalise(
                [float(s) for s in cross_encoder.predict([(example["question"], c.chunk.text) for c in candidates])]
            )
            retriever_scores = _normalise(_rank_scores(len(candidates)))
            combined = [
                blend * r + (1 - blend) * q for r, q in zip(rerank_scores, retriever_scores)
            ]
            ordered = [c for _, c in sorted(zip(combined, candidates), key=lambda p: -p[0])]

        parents = {
            c.chunk.metadata.get("parent_id") or c.chunk.chunk_id for c in ordered[:top_k]
        }
        expected = set(example["source_parent_ids"])
        hits.append(1.0 if parents & expected else 0.0)
        full_hits.append(1.0 if expected <= parents else 0.0)

    return {"hit": statistics.mean(hits), "full": statistics.mean(full_hits)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="eval/eval_set.json")
    parser.add_argument("--pool", type=int, default=30, help="Candidates to rerank.")
    parser.add_argument("--top-k", type=int, default=8, help="Kept after reranking.")
    args = parser.parse_args()

    examples = json.load(open(args.eval_set))["examples"]
    documents = load_raw_documents(PathConfig().data_raw_dir)

    config = PipelineConfig(generation=GenerationConfig())
    config.retrieval.technique = "dense"
    config.reranking.method = "none"
    config.diversification.enabled = False
    pipeline = RAGPipeline(config)
    pipeline.ingest(documents)

    print(f"{len(documents)} documents, {len(examples)} questions")
    print(f"reranking top {args.pool} candidates down to {args.top_k}\n")
    header = f"{'reranker':32s} {'blend':>6s} {'hit':>6s} {'full':>6s}"
    print(header)
    print("-" * len(header))

    for label, model_id in _RERANKERS:
        weights = (1.0,) if model_id is None else _BLEND_WEIGHTS
        for blend in weights:
            started = time.time()
            try:
                s = _score_config(pipeline, examples, model_id, blend, args.pool, args.top_k)
            except Exception as error:  # noqa: BLE001 - a missing model shouldn't end the comparison
                print(f"{label:32s} {blend:6.1f}  FAILED: {type(error).__name__}: {str(error)[:50]}")
                break
            shown = "-" if model_id is None else f"{blend:.1f}"
            print(f"{label:32s} {shown:>6s} {s['hit']:6.3f} {s['full']:6.3f}   ({time.time() - started:.0f}s)")


if __name__ == "__main__":
    main()
