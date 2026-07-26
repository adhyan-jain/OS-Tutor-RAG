"""Tune the post-retrieval stages by what actually reaches the generator.

eval/retrieval_eval.py measures the retriever alone. This measures the whole
selection chain -- retrieve, rerank, diversify, expand -- and asks the question
that matters for answer quality: did the slide the question is answerable from
survive into the final contexts, or did a later stage discard it?

That distinction is the point. Dense retrieval reaches recall@10 of 1.000 on
this corpus while only five contexts are forwarded, so correct material is
demonstrably being found and then dropped. Which stage drops it, and what
configuration stops it happening, is answerable without generating a single
token.

Reports hit rate (any cited parent survived), full hit rate (all of them did,
which multi-part questions need), and the context token cost of getting there.

    PYTHONPATH=. .venv/bin/python -m eval.stage_tuning_eval
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from src.config import GenerationConfig, PathConfig, PipelineConfig
from src.pipeline import RAGPipeline
from src.token_tracking import count_tokens
from eval.ragas_eval import load_raw_documents


def _score(pipeline: RAGPipeline, examples: list[dict]) -> dict[str, float]:
    """Hit rate and token cost of a pipeline's final context selection."""
    hits, full_hits, tokens, counts = [], [], [], []

    for example in examples:
        candidates = pipeline._retrieve_candidates(example["question"])
        parents = {
            sc.chunk.metadata.get("parent_id") or sc.chunk.chunk_id for sc in candidates
        }
        expected = set(example["source_parent_ids"])

        hits.append(1.0 if parents & expected else 0.0)
        full_hits.append(1.0 if expected <= parents else 0.0)
        tokens.append(sum(count_tokens(sc.chunk.text) for sc in candidates))
        counts.append(len(candidates))

    return {
        "hit_rate": statistics.mean(hits),
        "full_hit_rate": statistics.mean(full_hits),
        "tokens": statistics.mean(tokens),
        "contexts": statistics.mean(counts),
    }


def _configs(include_hyde: bool = True) -> list[tuple[str, PipelineConfig]]:
    """The configurations under test.

    Four questions, each isolated so the answer is attributable:

    - how many contexts to forward (final_k), since recall@10 is perfect but
      only five are forwarded;
    - whether the cross-encoder earns its place, given reranking measured ~0.05
      *worse* on answer_correctness than omitting it;
    - whether widening the candidate pool improves what survives, or merely
      costs cross-encoder time;
    - whether HyDE retrieves better than plain dense. HyDE costs one LLM call
      per question to draft a hypothetical answer and embed that instead of the
      question, so it is the only technique here that is not free to measure;
      it earns its place in the grid because it led both faithfulness and
      answer_correctness in the earlier sweep.
    """
    configs: list[tuple[str, PipelineConfig]] = []

    def build(
        rerank: str, mmr: bool, final_k: int, multiplier: int, technique: str = "dense"
    ) -> PipelineConfig:
        config = PipelineConfig(generation=GenerationConfig())
        config.retrieval.technique = technique
        config.retrieval.candidate_pool_multiplier = multiplier
        config.reranking.method = rerank
        config.reranking.top_n = max(config.reranking.top_n, final_k * 2)
        config.diversification.enabled = mmr
        config.diversification.top_k = final_k
        return config

    for final_k in (5, 8, 10):
        configs.append((f"mmr_only            k={final_k} pool=3", build("none", True, final_k, 3)))
    for final_k in (5, 8, 10):
        configs.append((f"rerank+mmr          k={final_k} pool=3", build("cross_encoder", True, final_k, 3)))
    for multiplier in (2, 4, 6):
        configs.append((f"rerank+mmr          k=8 pool={multiplier}", build("cross_encoder", True, 8, multiplier)))
    for multiplier in (2, 4, 6):
        configs.append((f"mmr_only            k=8 pool={multiplier}", build("none", True, 8, multiplier)))
    configs.append(("no_rerank_no_mmr    k=10", build("none", False, 10, 3)))

    if include_hyde:
        for final_k in (5, 8):
            configs.append(
                (f"hyde+mmr_only       k={final_k} pool=3", build("none", True, final_k, 3, "hyde"))
            )
        configs.append(
            ("hyde+rerank+mmr     k=8 pool=3", build("cross_encoder", True, 8, 3, "hyde"))
        )
        configs.append(
            ("hyde+mmr_only       k=8 pool=6", build("none", True, 8, 6, "hyde"))
        )

    return configs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", default="eval/eval_set.json")
    parser.add_argument(
        "--no-hyde",
        action="store_true",
        help="Skip HyDE configs, which need a running Ollama and one LLM call per question.",
    )
    args = parser.parse_args()

    examples = json.load(open(args.eval_set))["examples"]
    documents = load_raw_documents(PathConfig().data_raw_dir)
    print(f"{len(documents)} documents, {len(examples)} questions")
    print("baseline: dense retriever alone reaches recall@5 0.923, recall@10 1.000\n")

    header = f"{'config':38s} {'hit':>6s} {'full':>6s} {'ctxs':>5s} {'tokens':>7s}"
    print(header)
    print("-" * len(header))

    for label, config in _configs(include_hyde=not args.no_hyde):
        started = time.time()
        pipeline = RAGPipeline(config)
        pipeline.ingest(documents)
        s = _score(pipeline, examples)
        print(
            f"{label:38s} {s['hit_rate']:6.3f} {s['full_hit_rate']:6.3f} "
            f"{s['contexts']:5.1f} {s['tokens']:7.0f}   ({time.time() - started:.0f}s)"
        )


if __name__ == "__main__":
    main()
