#!/usr/bin/env bash
# One-time setup after cloning: bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=$(command -v python3.12 || command -v python3.11 || true)
[ -n "$PY" ] || { echo "Need Python 3.11 or 3.12 (pinned deps do not install on newer versions)."; exit 1; }
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install -r requirements-docker.txt          # CPU deps, no GPU/vllm needed
.venv/bin/pip install httpx requests uvicorn fastapi sse-starlette 2>/dev/null || true
[ -f .env ] || { [ -f .env.example ] && cp .env.example .env; } || true
# embedding model (one-time download, ~1.3 GB)
.venv/bin/python -c "from sentence_transformers import SentenceTransformer as S; S('BAAI/bge-large-en-v1.5')"
# Ollama chat model
if command -v ollama >/dev/null; then
  (curl -s -m 3 localhost:11434/api/tags >/dev/null || { nohup ollama serve >/dev/null 2>&1 & sleep 3; })
  ollama list | grep -q . && [ "$(ollama list | wc -l)" -gt 1 ] || ollama pull llama3.1:8b
else echo "Install Ollama from https://ollama.com, then re-run this script."; fi
# frontend
(cd frontend && npm install --silent)
# index (needs the course files in data/raw/)
if [ ! -f data/index/dense.faiss ]; then
  if ls data/raw/* >/dev/null 2>&1; then PYTHONPATH=. .venv/bin/python -m src.build_index
  else echo "NOTE: data/raw/ is empty. Copy the course .pptx/.pdf/.docx files there and run: PYTHONPATH=. .venv/bin/python -m src.build_index"; fi
fi
.venv/bin/python scripts/check_env.py || true
