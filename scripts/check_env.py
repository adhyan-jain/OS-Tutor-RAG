"""Preflight for a fresh clone: tells you exactly what is missing and how to fix it.

    python scripts/check_env.py          # exit 0 when ready, 1 otherwise
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
problems: list[str] = []


def ok(msg): print(f"  ok   {msg}")
def bad(msg, fix): print(f"  FAIL {msg}\n       fix: {fix}"); problems.append(msg)


print("OS Tutor preflight")
if sys.version_info[:2] in ((3, 11), (3, 12)):
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    print(f"  note Python {sys.version.split()[0]}: the pinned requirements target 3.11/3.12; use python3.12 -m venv .venv if install fails")

try:
    names = [m["name"] for m in json.load(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5)).get("models", [])]
    ok(f"Ollama reachable at {OLLAMA}")
    if names: ok("chat models: " + ", ".join(names[:5]))
    else: bad("Ollama has no models", "ollama pull llama3.1:8b")
except Exception:
    bad(f"Ollama not reachable at {OLLAMA}", "install from https://ollama.com and run: ollama serve")

hf = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
if (hf / "models--BAAI--bge-large-en-v1.5").exists(): ok("embedding model cached (bge-large-en-v1.5)")
else: bad("embedding model not downloaded", "bash scripts/setup.sh (needs internet once)")

if (ROOT / "data/index/dense.faiss").exists(): ok("search index present")
elif any((ROOT / "data/raw").glob("*")) if (ROOT / "data/raw").exists() else False:
    bad("no index yet but data/raw has files", "PYTHONPATH=. python -m src.build_index")
else:
    bad("no index and no course files in data/raw/", "put the course .pptx/.pdf/.docx files in data/raw/ then run scripts/setup.sh")

if (ROOT / "frontend/node_modules").exists(): ok("frontend dependencies installed")
else: bad("frontend dependencies missing", "cd frontend && npm install")

print("\nREADY: run bash scripts/start.sh" if not problems else f"\n{len(problems)} problem(s) above.")
sys.exit(1 if problems else 0)
