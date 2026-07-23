"""Manual smoke test for HyDE retrieval: compares HyDE against dense/BM25/hybrid
from scripts/test_retrieval.py on the same sample OS queries, reusing the same
saved index (see scripts/test_retrieval.py::build_corpus / _QUERIES).

Uses llama3:latest via a local Ollama server as a stand-in for the eventual
gemma2:9b / vLLM Llama-3.1-8B-Instruct backend (see DELAYED_TASKS.md).
"""

from __future__ import annotations

from src.config import GenerationConfig, RetrievalConfig
from src.retrieval.hybrid_rrf import HybridRRFRetriever
from src.retrieval.hyde import HyDERetriever
from scripts.test_retrieval import _QUERIES, build_corpus


def main() -> None:
    config = RetrievalConfig(top_k=5)
    generation_config = GenerationConfig(model_name="llama3:latest", backend="ollama")

    chunks = build_corpus()

    print("Building indexes (dense + BM25, for comparison)...")
    baseline = HybridRRFRetriever(config)
    baseline.build_index(chunks)

    print("Loading dense index for HyDE (reusing DenseRetriever's saved index)...")
    hyde = HyDERetriever(config, generation_config)
    hyde.dense = baseline.dense  # reuse the already-built dense index directly

    for query in _QUERIES:
        print(f"=== Query: {query!r} ===")

        hypothetical = hyde.llm.generate_hypothetical_document(query)
        print(f"  [HyDE hypothetical answer] {hypothetical[:200]!r}")

        dense_results = baseline.dense.retrieve(query)
        hyde_results = hyde.retrieve(query)

        for label, results in (("DENSE (raw query)", dense_results), ("HYDE", hyde_results)):
            print(f"  [{label}]")
            for r in results:
                print(f"    {r.rank}. ({r.score:.4f}) {r.chunk.text[:80]!r}")
        print()


if __name__ == "__main__":
    main()
