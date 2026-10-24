#!/usr/bin/env bash
# Rebuild the figures, report (docx+pdf) and presentation (pptx+pdf).
# Needs: python-docx python-pptx matplotlib pillow in $VENV, LibreOffice (soffice), poppler (pdftotext/pdfinfo).
#   python3 -m venv /tmp/subvenv && /tmp/subvenv/bin/pip install python-docx python-pptx matplotlib pillow
# Run from anywhere:  bash submission/build/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SUB="$HERE/.."; REPO="$SUB/.."
VENV="${VENV:-/tmp/subvenv}"; PY="$VENV/bin/python"
# 1. real tutor transcript (no models needed)
(cd "$REPO" && PYTHONPATH=. .venv/bin/python submission/build/transcript.py > /dev/null)
# 2. figures
"$PY" "$HERE/figs.py"
# 3. report, two passes so the table of contents has page numbers
cd "$SUB"
"$PY" "$HERE/report.py"; soffice --headless --convert-to pdf OS_Tutor_RAG_Report.docx >/dev/null 2>&1
python3 "$HERE/toc.py" >/dev/null
"$PY" "$HERE/report.py" x; soffice --headless --convert-to pdf OS_Tutor_RAG_Report.docx >/dev/null 2>&1
python3 "$HERE/toc.py"
# 4. presentation
"$PY" "$HERE/ppt.py"; soffice --headless --convert-to pdf OS_Tutor_RAG_Presentation.pptx >/dev/null 2>&1
pdfinfo OS_Tutor_RAG_Report.pdf | grep Pages; pdfinfo OS_Tutor_RAG_Presentation.pdf | grep Pages
