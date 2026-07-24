"""Evaluate pipeline configurations against eval_set.json using RAGAS metrics.

Runs RAGPipeline across a set of technique combinations (config variants),
scores each with RAGAS (context_precision, context_recall, faithfulness,
answer_relevancy, answer_correctness) using a local judge (Ollama LLM + a
local sentence-transformer for embeddings, not OpenAI), and writes a
comparison table ranking configs by correctness + completeness.

This is the *mass* evaluator (every technique combination, one full run).
For evaluating a single pipeline config as you iterate, use
RAGPipeline.evaluate() instead (src/pipeline.py), which appends to a shared
per-run workbook via src/evaluation.py -- both share the same scoring logic.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from src.config import GenerationConfig, PathConfig, PipelineConfig
from src.evaluation import METRIC_NAMES, load_eval_set, safe_mean, score_pipeline
from src.ingestion.extract_docx import extract_docx
from src.ingestion.extract_pdf import extract_pdf
from src.ingestion.extract_ppt import extract_ppt
from src.pipeline import RAGPipeline

_EXTRACTORS = {
    ".pptx": lambda path: [extract_ppt(path)],
    ".docx": lambda path: extract_docx(path),
    ".pdf": lambda path: [extract_pdf(path)],
}


def load_raw_documents(raw_dir: Path):
    """Extract Documents from every supported file in data/raw/.

    Args:
        raw_dir: Directory to scan (e.g. PathConfig().data_raw_dir).

    Returns:
        A flat list of Documents across all supported raw files.
    """
    documents = []
    for path in sorted(raw_dir.iterdir()):
        extractor = _EXTRACTORS.get(path.suffix.lower())
        if extractor is not None:
            documents.extend(extractor(path))
    return documents


@dataclass
class ConfigVariant:
    """A named PipelineConfig variant to evaluate."""

    name: str
    config: PipelineConfig


def default_config_variants(generation_config: GenerationConfig | None = None) -> list[ConfigVariant]:
    """Build the default set of config variants to compare.

    Varies retrieval technique and reranking method; chunking, diversification,
    and generation are held fixed across variants for a controlled comparison.

    Args:
        generation_config: Generation settings shared by all variants.
            Defaults to GenerationConfig() (currently backend="ollama",
            model_name="llama3:latest" — see config.py).

    Returns:
        A list of named ConfigVariants.
    """
    base = PipelineConfig(generation=generation_config or GenerationConfig())

    variants = []
    for technique in ("dense", "bm25", "hybrid_rrf", "hyde", "multi_query"):
        for method in ("cross_encoder", "none"):
            config = copy.deepcopy(base)
            config.retrieval.technique = technique
            config.reranking.method = method
            variants.append(ConfigVariant(name=f"{technique}+{method}", config=config))
    return variants


def run_comparison(
    variants: list[ConfigVariant],
    documents,
    eval_set_path: Path,
    output_path: Path,
    details_output_path: Path | None = None,
) -> None:
    """Run RAGAS eval across config variants and write a ranked comparison table.

    Also writes a per-question detail workbook (one sheet per config variant,
    plus an "All Results (by question)" sheet grouping every variant's answer
    for the same question in adjacent rows) so answers aren't just summarized
    away into the aggregate table.

    Args:
        variants: Named PipelineConfig variants to evaluate.
        documents: Documents to ingest into each variant's pipeline before eval.
        eval_set_path: Path to the eval_set.json file.
        output_path: Where to write the comparison table (.md or .csv, by extension).
        details_output_path: Where to write the per-question Excel workbook.
            Defaults to output_path's directory / "ragas_details.xlsx".
    """
    eval_set = load_eval_set(eval_set_path)
    rows = []
    all_detail_rows: list[dict] = []
    details_output_path = details_output_path or output_path.parent / "ragas_details.xlsx"

    for variant in variants:
        print(f"Evaluating variant: {variant.name}")
        pipeline = RAGPipeline(variant.config)
        pipeline.ingest(documents)
        scores, detail_rows = score_pipeline(pipeline, eval_set)
        rows.append({"config": variant.name, **scores})
        for question_index, detail_row in enumerate(detail_rows):
            all_detail_rows.append({"config": variant.name, "question_index": question_index, **detail_row})
        print(f"  {scores}")

        # Write after every variant (not just at the end) so a crash midway
        # through this multi-hour run doesn't lose already-computed results.
        _write_details_workbook(all_detail_rows, details_output_path)
        _write_table(_ranked(rows), output_path)

    print(f"Comparison table written to {output_path}")
    print(f"Per-question details written to {details_output_path}")


def _ranked(rows: list[dict]) -> list[dict]:
    """Rank configs by correctness + completeness, not a flat 5-metric average.

    - correctness = mean(faithfulness, answer_correctness) -- is the answer
      factually grounded in the retrieved context, and does it match the
      ground truth.
    - completeness = context_recall -- did retrieval surface everything
      needed to fully answer the question.
    NaN-safe: a metric that failed to parse for a config doesn't drop out of
    the whole row, it's just excluded from whichever composite uses it.
    """
    ranked_rows = []
    for row in rows:
        ranked_row = dict(row)
        ranked_row["correctness"] = safe_mean([row["faithfulness"], row["answer_correctness"]])
        ranked_row["completeness"] = row["context_recall"]
        ranked_row["correctness_completeness"] = safe_mean(
            [ranked_row["correctness"], ranked_row["completeness"]]
        )
        ranked_rows.append(ranked_row)
    ranked_rows.sort(key=lambda r: r["correctness_completeness"], reverse=True)
    return ranked_rows


def _write_details_workbook(all_detail_rows: list[dict], output_path: Path) -> None:
    """Write per-question results in a side-by-side-comparable layout.

    The "All Results (by question)" sheet is sorted by question first, then
    config, so every variant's answer/scores for the same question sit in
    adjacent rows -- easy to scan across configs for one question at a time,
    rather than having to flip between per-variant sheets.
    """
    import pandas as pd

    df = pd.DataFrame(all_detail_rows)
    by_question = df.sort_values(["question_index", "config"]).drop(columns=["question_index"])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        by_question.to_excel(writer, sheet_name="All Results (by question)", index=False)
        for variant_name in df["config"].unique():
            sheet_name = variant_name.replace("+", "_")[:31]
            variant_df = df[df["config"] == variant_name].drop(columns=["question_index", "config"])
            variant_df.to_excel(writer, sheet_name=sheet_name, index=False)


def _write_table(rows: list[dict], output_path: Path) -> None:
    columns = ["config", *METRIC_NAMES, "correctness", "completeness", "correctness_completeness"]

    if output_path.suffix == ".csv":
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        return

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(f"{row[c]:.4f}" if c != "config" else row[c] for c in columns) + " |"
        )
    output_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Smoke-test mode: first 3 eval questions, 2 config variants only.",
    )
    parser.add_argument(
        "--output",
        default="eval/comparison_results.md",
        help="Output path for the comparison table (.md or .csv).",
    )
    args = parser.parse_args()

    documents = load_raw_documents(PathConfig().data_raw_dir)
    print(f"Loaded {len(documents)} documents from data/raw/")

    variants = default_config_variants()
    eval_set_path = Path("eval/eval_set.json")

    if args.quick:
        variants = variants[:2]
        eval_set = load_eval_set(eval_set_path)[:3]
        quick_eval_set_path = Path("eval/_quick_eval_set.json")
        quick_eval_set_path.write_text(json.dumps({"examples": eval_set}))
        eval_set_path = quick_eval_set_path

    run_comparison(variants, documents, eval_set_path, Path(args.output))


if __name__ == "__main__":
    main()
