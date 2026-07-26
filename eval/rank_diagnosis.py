"""Inspect why the wrong chunks outrank the right ones.

Dense retrieval reaches recall@5 of 0.923 but recall@1 of only 0.731, so for a
quarter of questions something the question is *not* answerable from scores
above something it is. Aggregate metrics cannot say what, so this dumps the
actual competing chunks: for each question, where the first correct chunk
ranked, and what outscored it.

Prints a per-question table plus, for the worst cases, the text of the chunks
that won so the failure mode can be read directly rather than inferred.

    PYTHONPATH=. .venv/bin/python -m eval.rank_diagnosis
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from src.config import GenerationConfig, PathConfig, PipelineConfig
from src.pipeline import RAGPipeline
from src.token_tracking import count_tokens
from eval.ragas_eval import load_raw_documents


def _parent_of(scored_chunk) -> str:
    return scored_chunk.chunk.metadata.get("parent_id") or scored_chunk.chunk.chunk_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="eval/eval_set.json")
    parser.add_argument("--depth", type=int, default=20, help="How deep to search for the answer.")
    parser.add_argument("--show", type=int, default=5, help="How many bad cases to dump in full.")
    args = parser.parse_args()

    examples = json.load(open(args.eval_set))["examples"]
    documents = load_raw_documents(PathConfig().data_raw_dir)

    config = PipelineConfig(generation=GenerationConfig())
    config.retrieval.technique = "dense"
    config.reranking.method = "none"
    config.diversification.enabled = False
    config.context_expansion.enabled = False
    pipeline = RAGPipeline(config)
    pipeline.ingest(documents)

    rows = []
    for example in examples:
        retrieved = pipeline.retriever.retrieve(example["question"], top_k=args.depth)
        expected = set(example["source_parent_ids"])
        first_correct = next(
            (i for i, sc in enumerate(retrieved, start=1) if _parent_of(sc) in expected), None
        )
        rows.append({"example": example, "retrieved": retrieved, "rank": first_correct})

    ranked = [r for r in rows if r["rank"]]
    print(f"{len(examples)} questions, searching top {args.depth}\n")
    print(f"  first correct chunk at rank 1 : {sum(1 for r in rows if r['rank'] == 1)}")
    print(f"  rank 2-5                      : {sum(1 for r in rows if r['rank'] and 2 <= r['rank'] <= 5)}")
    print(f"  rank 6-{args.depth:<2d}                     : {sum(1 for r in rows if r['rank'] and r['rank'] > 5)}")
    print(f"  never found in top {args.depth}         : {sum(1 for r in rows if not r['rank'])}")
    if ranked:
        print(f"  median rank of first correct  : {statistics.median(r['rank'] for r in ranked):.0f}")

    # What kind of chunk wins when the right one loses?
    distractors = []
    for row in rows:
        if row["rank"] == 1:
            continue
        expected = set(row["example"]["source_parent_ids"])
        for sc in row["retrieved"][: (row["rank"] - 1) if row["rank"] else 5]:
            if _parent_of(sc) not in expected:
                distractors.append(sc)

    if distractors:
        by_type = Counter(sc.chunk.metadata.get("source_type") for sc in distractors)
        lengths = [count_tokens(sc.chunk.text) for sc in distractors]
        corpus_lengths = [count_tokens(c.text) for c in pipeline.retriever.chunks]
        print(f"\n  {len(distractors)} chunks outranked a correct one")
        print(f"    by source type   : {dict(by_type)}")
        print(f"    median tokens    : {statistics.median(lengths):.0f}  (corpus median {statistics.median(corpus_lengths):.0f})")

    worst = sorted(rows, key=lambda r: -(r["rank"] or 999))[: args.show]
    print("\n" + "=" * 100)
    print("WORST CASES -- what outranked the correct chunk")
    print("=" * 100)
    for row in worst:
        example = row["example"]
        print(f"\nQ: {example['question']}")
        print(f"   wants: {example['source_parent_ids']}   first correct at rank: {row['rank']}")
        for i, sc in enumerate(row["retrieved"][:4], start=1):
            mark = "OK " if _parent_of(sc) in set(example["source_parent_ids"]) else "   "
            text = " ".join(sc.chunk.text.split())[:105]
            print(f"   {mark}#{i} score={sc.score:.3f} [{_parent_of(sc)}] {text}")


if __name__ == "__main__":
    main()
