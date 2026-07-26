"""Shared RAGAS scoring logic, used by both RAGPipeline.evaluate() (single-run,
auto-triggered after ingest) and eval/ragas_eval.py (mass comparison across
every technique combination). Single source of truth so both stay consistent.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import TYPE_CHECKING

# Force local-only HF Hub access: all models used here (bge-*) are already
# cached locally, and this environment's network to huggingface.co has been
# unreliable (has caused multi-minute hangs on cache-check requests).
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from src.config import PipelineConfig
from src.embedding_cache import release_gpu_memory
from src.token_tracking import LLMCallTracker, estimate_cost_usd

if TYPE_CHECKING:
    from src.pipeline import RAGPipeline

METRIC_NAMES = [
    "context_precision",
    "context_recall",
    "context_entity_recall",
    "faithfulness",
    "answer_relevancy",
    "answer_correctness",
    "answer_similarity",
]


def load_eval_set(eval_set_path: Path, num_questions: int | None = None) -> list[dict]:
    """Load eval examples from an eval_set.json file.

    Args:
        eval_set_path: Path to a JSON eval set (see eval/eval_set.json).
        num_questions: If given, only the first N examples are returned --
            lets you analyze on a smaller/larger slice without editing the
            eval set file itself.

    Returns:
        The list of example dicts (question, ground_truth_answer,
        source_chunk_ids, topic).
    """
    with open(eval_set_path) as f:
        data = json.load(f)
    examples = data["examples"]
    return examples[:num_questions] if num_questions is not None else examples


def _make_tracking_chat_ollama(model_name: str, base_url: str, tracker: LLMCallTracker):
    """Build a ChatOllama that logs every call's token usage to `tracker`.

    Ragas's metrics call the judge LLM internally (we don't control those call
    sites directly), so tracking happens by wrapping the LangChain chat model
    itself. Both the sync and async entry points are wrapped: ragas reaches the
    model through LangchainLLMWrapper.agenerate_text(), so overriding only
    _generate() records nothing.
    """
    from langchain_community.chat_models import ChatOllama

    def _record(messages, result) -> None:
        prompt_text = "\n".join(str(m.content) for m in messages)
        response_text = result.generations[0].message.content if result.generations else ""
        tracker.record("ragas_judge", prompt_text, response_text)

    class _TrackingChatOllama(ChatOllama):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            result = super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            _record(messages, result)
            return result

        async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
            result = await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
            _record(messages, result)
            return result

    return _TrackingChatOllama(model=model_name, base_url=base_url)


def score_pipeline(
    pipeline: "RAGPipeline", eval_set: list[dict]
) -> tuple[dict[str, float], list[dict], LLMCallTracker]:
    """Score a pipeline's answers against a labeled eval set using RAGAS.

    Scores each row against each metric using the metric's synchronous
    ``.score(row)`` method, one call at a time. This deliberately bypasses
    ragas's own ``evaluate()``/executor machinery: that executor fires many
    concurrent async sub-calls per row (per ragas's internal metric
    implementations, not something RunConfig(max_workers=1) actually limits),
    which repeatedly deadlocked a single local Ollama server on an 8GB-VRAM
    GPU (confirmed via nvidia-smi/ollama ps/thread CPU-time sampling showing
    zero progress). Fully sequential scoring is slower but reliable here.

    Args:
        pipeline: The configured (and already-ingested) RAGPipeline instance
            to evaluate.
        eval_set: Eval examples as returned by load_eval_set().

    Returns:
        A tuple of (mean scores dict, per-question detail rows list, eval_tracker).
        Mean scores are NaN-safe: a metric that fails to parse for some rows
        (local LLMs don't always follow ragas's expected structured output)
        is averaged over only the rows where it succeeded, not zeroed out
        or left to poison the whole mean. eval_tracker logs every judge LLM
        call made while scoring (separate from pipeline.tracker, which logs
        the pipeline's own generation/retrieval-side calls) -- see
        append_run_to_workbook for how the two are reported together.
    """
    import asyncio

    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        answer_correctness,
        answer_relevancy,
        answer_similarity,
        context_entity_recall,
        context_precision,
        context_recall,
        faithfulness,
    )
    from ragas.run_config import RunConfig

    # metric.score() calls asyncio.get_event_loop() internally, which Python
    # 3.14 no longer auto-creates in the main thread (older Python did).
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    eval_tracker = LLMCallTracker()
    judge_llm = LangchainLLMWrapper(
        _make_tracking_chat_ollama(
            pipeline.config.eval.judge_model_name, pipeline.config.generation.ollama_base_url, eval_tracker
        )
    )
    # Pinned to CPU deliberately: the judge LLM (gemma2:9b) already fills this
    # machine's 8GB VRAM on its own, so putting even a small embedding model on
    # the GPU alongside it risks an OOM mid-sweep. bge-small is cheap enough on
    # CPU that the tradeoff is one-sided -- it embeds only a handful of short
    # strings per question (answer_relevancy, answer_similarity).
    judge_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5", model_kwargs={"device": "cpu"}
        )
    )
    run_config = RunConfig(max_workers=1)

    metrics = [
        context_precision,
        context_recall,
        context_entity_recall,
        faithfulness,
        answer_relevancy,
        answer_correctness,
        answer_similarity,
    ]
    for metric in metrics:
        metric.llm = judge_llm
        if hasattr(metric, "embeddings"):
            metric.embeddings = judge_embeddings
        metric.init(run_config)

    # Two passes, deliberately not interleaved: the generation model and the
    # judge model don't fit in this machine's 8GB VRAM together (llama3 4.7GB
    # + gemma2:9b 5.4GB), so Ollama evicts one to load the other. Generating
    # every answer first, then scoring every answer, costs 2 model loads per
    # run instead of 2 per question.
    # Release before generation too, not just before judging: under
    # OS_RAG_EMBEDDING_DEVICE=cuda the embedding models are still resident from
    # ingest at this point, and Ollama needs the card from here on.
    release_gpu_memory()

    generated: list[tuple[dict, str, list[str]]] = []
    for i, example in enumerate(eval_set):
        print(f"  generating {i + 1}/{len(eval_set)}: {example['question']!r}")
        answer, contexts = pipeline.answer_with_contexts(example["question"])
        generated.append((example, answer, contexts))

    # Hand the GPU back before the judge model loads (see release_gpu_memory).
    release_gpu_memory()

    detail_rows = []
    for i, (example, answer, contexts) in enumerate(generated):
        print(f"  scoring {i + 1}/{len(generated)}: {example['question']!r}")
        row = {
            "question": example["question"],
            "answer": answer,
            "contexts": contexts,
            "ground_truth": example["ground_truth_answer"],
        }
        detail_row = {
            "question": example["question"],
            "topic": example.get("topic"),
            "answer": answer,
            "ground_truth_answer": example["ground_truth_answer"],
            "contexts": "\n---\n".join(contexts),
        }
        for metric in metrics:
            score = metric.score(row)
            detail_row[metric.name] = score
            print(f"    {metric.name}: {score:.4f}")
        detail_rows.append(detail_row)

    mean_scores = {}
    for name in METRIC_NAMES:
        values = [row[name] for row in detail_rows if not math.isnan(row[name])]
        mean_scores[name] = sum(values) / len(values) if values else float("nan")

    return mean_scores, detail_rows, eval_tracker


def safe_mean(values: list[float]) -> float:
    """Mean of the non-NaN values, or NaN if none are valid."""
    clean = [v for v in values if not math.isnan(v)]
    return sum(clean) / len(clean) if clean else float("nan")


def phase_summary(config: PipelineConfig) -> dict[str, object]:
    """Summarize which technique/setting each pipeline phase is using.

    Used for the header table written above each run's detail sheet and for
    the "Final Analysis" sheet's per-run columns, so it's easy to see at a
    glance what produced a given set of scores.

    Args:
        config: The PipelineConfig a run was executed with.

    Returns:
        An ordered mapping of phase name to the technique/setting used.
    """
    by_type = config.chunking.strategy_by_source_type
    chunking_label = ", ".join(f"{source}={strategy}" for source, strategy in sorted(by_type.items()))
    return {
        "chunking": chunking_label,
        "retrieval": config.retrieval.technique,
        "multi_query": config.retrieval.use_multi_query,
        "reranking": config.reranking.method,
        "mmr": config.diversification.enabled,
        "context_expansion": config.context_expansion.enabled,
        "generation_backend": config.generation.backend,
        "generation_model": config.generation.model_name,
        "judge_model": config.eval.judge_model_name,
    }


def composite_scores(mean_scores: dict[str, float]) -> dict[str, float]:
    # answer_similarity is left out here even though it's a generation-quality
    # signal: ragas's answer_correctness already folds it in internally
    # (weighted with a factual-overlap score), so including it again here
    # would double-count the same signal. It's still reported standalone in
    # METRIC_NAMES as a diagnostic (e.g. to spot "right facts, oddly worded"
    # vs "wrong facts" cases when correctness is low).
    correctness = safe_mean([mean_scores["faithfulness"], mean_scores["answer_correctness"]])
    completeness = safe_mean([mean_scores["context_recall"], mean_scores["context_entity_recall"]])
    return {
        "correctness": correctness,
        "completeness": completeness,
        "correctness_completeness": safe_mean([correctness, completeness]),
    }


def _unique_sheet_name(workbook, base_name: str) -> str:
    name = base_name[:31]
    if name not in workbook.sheetnames:
        return name
    for suffix in range(2, 1000):
        candidate = f"{base_name[:28]}_{suffix}"
        if candidate not in workbook.sheetnames:
            return candidate
    raise RuntimeError("Could not find a unique sheet name")


def _token_cost_summary(generation_tracker: LLMCallTracker, eval_tracker: LLMCallTracker) -> dict[str, float]:
    """Summarize call/token counts and estimated OpenAI-equivalent cost.

    Generation-side calls (answer generation, hyde, multi_query, llm_rerank --
    whatever the pipeline itself called the LLM for) are priced as if run on
    GPT-4.1; evaluation-side calls (the RAGAS judge) are priced as if run on
    GPT-4o-mini, matching how each role would realistically be assigned a
    model if this pipeline used hosted APIs instead of a local Ollama model.

    Args:
        generation_tracker: Tracker covering the pipeline's own LLM calls.
        eval_tracker: Tracker covering the RAGAS judge's LLM calls.

    Returns:
        A flat dict of call counts, token totals, and cost estimates (USD),
        both per-role and combined.
    """
    generation_cost = estimate_cost_usd(
        generation_tracker.total_input_tokens, generation_tracker.total_output_tokens, "gpt-4.1"
    )
    eval_cost = estimate_cost_usd(eval_tracker.total_input_tokens, eval_tracker.total_output_tokens, "gpt-4o-mini")
    return {
        "generation_llm_calls": generation_tracker.num_calls,
        "generation_input_tokens": generation_tracker.total_input_tokens,
        "generation_output_tokens": generation_tracker.total_output_tokens,
        "generation_cost_usd_gpt4.1": generation_cost,
        "eval_llm_calls": eval_tracker.num_calls,
        "eval_input_tokens": eval_tracker.total_input_tokens,
        "eval_output_tokens": eval_tracker.total_output_tokens,
        "eval_cost_usd_gpt4o-mini": eval_cost,
        "total_llm_calls": generation_tracker.num_calls + eval_tracker.num_calls,
        "total_input_tokens": generation_tracker.total_input_tokens + eval_tracker.total_input_tokens,
        "total_output_tokens": generation_tracker.total_output_tokens + eval_tracker.total_output_tokens,
        "total_cost_usd": generation_cost + eval_cost,
    }


def append_run_to_workbook(
    workbook_path: Path,
    run_name: str,
    config: PipelineConfig,
    mean_scores: dict[str, float],
    detail_rows: list[dict],
    generation_tracker: LLMCallTracker,
    eval_tracker: LLMCallTracker,
) -> None:
    """Append one pipeline run's results to a shared Excel workbook.

    Each call adds a new sheet (named after ``run_name``) containing a phase
    summary table (which technique each phase used), an LLM usage summary
    (call counts, token totals, and estimated cost as if run on OpenAI's
    API -- GPT-4.1 for generation-side calls, GPT-4o-mini for the RAGAS
    judge), a per-call token log, and the per-question detail rows. Also
    adds/updates a row for this run in the workbook's "Final Analysis" sheet
    (one row per run ever recorded, so you can compare runs over time
    without losing history).

    Args:
        workbook_path: Path to the .xlsx workbook (created if it doesn't exist).
        run_name: Short identifier for this run (used as the new sheet name,
            truncated/suffixed to stay unique and within Excel's 31-char limit).
        config: The PipelineConfig this run was executed with.
        mean_scores: Mean RAGAS metric scores, as returned by score_pipeline().
        detail_rows: Per-question detail rows, as returned by score_pipeline().
        generation_tracker: LLMCallTracker covering the pipeline's own calls
            (typically ``pipeline.tracker``).
        eval_tracker: LLMCallTracker covering the RAGAS judge's calls, as
            returned by score_pipeline().
    """
    import openpyxl
    import pandas as pd
    from openpyxl.utils.dataframe import dataframe_to_rows

    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = (
        openpyxl.load_workbook(workbook_path) if workbook_path.exists() else openpyxl.Workbook()
    )
    # A fresh Workbook() starts with one blank "Sheet"; drop it once we have
    # real content to write, so it doesn't linger as clutter.
    if workbook.sheetnames == ["Sheet"] and workbook["Sheet"].max_row == 1 and workbook["Sheet"].max_column == 1:
        del workbook["Sheet"]

    phases = phase_summary(config)
    composite = composite_scores(mean_scores)
    token_summary = _token_cost_summary(generation_tracker, eval_tracker)

    # --- Per-run sheet: phase summary header table, then detail rows. ---
    sheet_name = _unique_sheet_name(workbook, run_name)
    sheet = workbook.create_sheet(sheet_name)

    sheet.append(["Phase", "Setting"])
    for phase, setting in phases.items():
        sheet.append([phase, setting])
    sheet.append([])
    sheet.append(["Metric", "Mean Score"])
    for metric_name in METRIC_NAMES:
        sheet.append([metric_name, mean_scores[metric_name]])
    for name, value in composite.items():
        sheet.append([name, value])
    sheet.append([])

    sheet.append(["LLM Usage Summary", "Value"])
    for key, value in token_summary.items():
        sheet.append([key, value])
    sheet.append([])

    sheet.append(["LLM Call Log", "Purpose", "Input Tokens", "Output Tokens"])
    for call in generation_tracker.calls:
        sheet.append(["generation", call["purpose"], call["input_tokens"], call["output_tokens"]])
    for call in eval_tracker.calls:
        sheet.append(["evaluation", call["purpose"], call["input_tokens"], call["output_tokens"]])
    sheet.append([])

    detail_df = pd.DataFrame(detail_rows)
    for row in dataframe_to_rows(detail_df, index=False, header=True):
        sheet.append(row)

    # --- Final Analysis sheet: one row per run, across all runs ever recorded. ---
    if "Final Analysis" not in workbook.sheetnames:
        analysis_sheet = workbook.create_sheet("Final Analysis")
        analysis_sheet.append(
            ["run_name", *phases.keys(), *METRIC_NAMES, *composite.keys(), *token_summary.keys()]
        )
    else:
        analysis_sheet = workbook["Final Analysis"]
    analysis_sheet.append(
        [
            sheet_name,
            *phases.values(),
            *(mean_scores[m] for m in METRIC_NAMES),
            *composite.values(),
            *token_summary.values(),
        ]
    )

    workbook.save(workbook_path)
