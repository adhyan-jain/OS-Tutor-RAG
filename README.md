# OS-Tutor-RAG

A RAG (Retrieval-Augmented Generation) pipeline for OS course tutoring, built as a retrieval technique comparison study. Source documents (PPT/DOCX course material) are ingested, chunked, retrieved, reranked, and answered by a local LLM, with each stage swappable via config so different technique combinations can be compared.

```
ingestion -> chunking -> retrieval -> reranking -> diversification -> generation
```

## Techniques implemented

- **Ingestion**: DOCX (heading-based sectioning), PPT/PPTX (per-slide title/bullets/notes)
- **Chunking**: structure-aware (parent-child, per slide/section), semantic (sentence-similarity boundaries)
- **Retrieval**: dense (FAISS + bge-large), sparse (BM25), hybrid (Reciprocal Rank Fusion), HyDE, Multi Query (LLM query reformulation + RRF)
- **Reranking**: cross-encoder (bge-reranker-large), LLM-as-judge
- **Diversification**: MMR
- **Generation**: local LLM via vLLM or Ollama (Llama-3.1-8B-Instruct default; llama3:latest/gemma2:9b in local dev)

Every stage above is swappable purely via `PipelineConfig` (see `src/config.py`) — no code edits needed to change technique. Setting `reranking.method = "none"` or `diversification.enabled = False` cleanly skips that stage.

## Evaluation

- `RAGPipeline.evaluate()` — scores the current pipeline config against `eval/eval_set.json` with RAGAS (context_precision, context_recall, faithfulness, answer_relevancy, answer_correctness), appending results to `eval/pipeline_runs.xlsx` (one sheet per run, showing which technique each phase used, plus a "Final Analysis" sheet aggregating every run). Controlled by `PipelineConfig.eval` (`num_questions` limits how many eval questions to run).
- `eval/ragas_eval.py` — mass evaluator: runs every retrieval-technique × reranking-method combination and writes a ranked comparison table (`eval/comparison_results.md`) plus per-question detail (`eval/ragas_details.xlsx`).
- Both share scoring logic from `src/evaluation.py`.

## Setup

_TODO: fill in setup instructions (environment, dependencies, data preparation, running the pipeline)._
