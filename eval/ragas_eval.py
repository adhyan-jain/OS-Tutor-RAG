"""Evaluate pipeline configurations against eval_set.json using RAGAS metrics."""

from __future__ import annotations

from pathlib import Path

from src.pipeline import RAGPipeline


def run_ragas_eval(pipeline: RAGPipeline, eval_set_path: Path) -> dict[str, float]:
    """Run RAGAS evaluation of a pipeline against a labeled eval set.

    Args:
        pipeline: The configured RAGPipeline instance to evaluate.
        eval_set_path: Path to a JSON eval set (see eval_set.json).

    Returns:
        A mapping of RAGAS metric name to score.
    """
    raise NotImplementedError
