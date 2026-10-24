#!/usr/bin/env bash
# Start backend (8000) and frontend (3000): bash scripts/start.sh   (Ctrl-C stops both)
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python scripts/check_env.py || { echo "Fix the problems above first."; exit 1; }
curl -s -m 3 localhost:11434/api/tags >/dev/null || { nohup ollama serve >/dev/null 2>&1 & sleep 3; }
trap 'kill 0' EXIT
HF_HUB_OFFLINE=1 PYTHONPATH=. .venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000 &
(cd frontend && npm run dev -- -p 3000) &
echo "Open http://localhost:3000"
wait
