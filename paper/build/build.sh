#!/usr/bin/env bash
# Rebuild manuscript tables, LaTeX and PDF from the Markdown source of truth.
# Usage (from the repository root): bash paper/build/build.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

PY="${PYTHON:-python}"

# 1. Regenerate Tables 3-6 from the extended-analysis artifact.
"$PY" paper/build_tables.py > /dev/null

# 2. Markdown -> LaTeX.
"$PY" paper/build/md2tex.py paper/PAPER_FINAL.md paper/build/PAPER_FINAL.tex

# 3. LaTeX -> PDF.
cd paper/build
latexmk -pdf -interaction=nonstopmode -halt-on-error PAPER_FINAL.tex > latex.log 2>&1 \
  || { echo "LaTeX failed; see paper/build/latex.log" >&2; exit 1; }

echo "Built paper/build/PAPER_FINAL.pdf ($(pdfinfo PAPER_FINAL.pdf | awk '/Pages/ {print $2}') pages)"
