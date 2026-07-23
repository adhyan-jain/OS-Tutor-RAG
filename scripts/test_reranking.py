"""Manual smoke test for reranking: takes HybridRRFRetriever top-20 results
(reusing the corpus/queries from scripts/test_retrieval.py), reranks with
both CrossEncoderReranker (bge-reranker-large) and LLMReranker (llama3:latest
via Ollama), and prints before/after ordering side by side.
"""

from __future__ import annotations

from src.config import GenerationConfig, RerankingConfig, RetrievalConfig
from src.reranking.cross_encoder import CrossEncoderReranker
from src.reranking.llm_rerank import LLMReranker
from src.retrieval.hybrid_rrf import HybridRRFRetriever
from scripts.test_retrieval import _QUERIES, build_corpus


def _print_ranking(label: str, results) -> None:
    print(f"  [{label}]")
    for r in results:
        print(f"    {r.rank}. ({r.score:.4f}) {r.chunk.text[:80]!r}")


def main() -> None:
    retrieval_config = RetrievalConfig(top_k=20)
    reranking_config = RerankingConfig(top_n=5)
    generation_config = GenerationConfig(model_name="llama3:latest", backend="ollama")

    chunks = build_corpus()

    print("Building hybrid RRF index...")
    hybrid = HybridRRFRetriever(retrieval_config)
    hybrid.build_index(chunks)

    print("Loading cross-encoder (bge-reranker-large)...")
    cross_encoder = CrossEncoderReranker(reranking_config)

    print("Setting up LLM reranker (llama3:latest via Ollama)...\n")
    llm_reranker = LLMReranker(reranking_config, generation_config)

    for query in _QUERIES[:4]:
        print(f"=== Query: {query!r} ===")
        top20 = hybrid.retrieve(query, top_k=20)
        _print_ranking("HYBRID_RRF (before, top-5 of 20 shown)", top20[:5])

        ce_reranked = cross_encoder.rerank(query, top20)
        _print_ranking("CROSS_ENCODER (after)", ce_reranked)

        llm_reranked = llm_reranker.rerank(query, top20)
        _print_ranking("LLM_RERANK (after)", llm_reranked)
        print()


if __name__ == "__main__":
    main()
