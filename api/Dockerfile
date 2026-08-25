# Backend image for os-tutor-rag's FastAPI app (api/main.py).
#
# Build context must be the REPO ROOT, not api/ -- api/*.py imports from
# src/ (e.g. `from src.config import PipelineConfig`), so both api/ and src/
# need to be in the build context. From the repo root:
#
#   docker build -f api/Dockerfile -t os-tutor-rag-api .
#
# (docker-compose.yml at the repo root sets `context: .` / `dockerfile:
# api/Dockerfile` for you.)
#
# Python 3.11 is used deliberately, not whatever the dev machine happens to
# run (DELAYED_TASKS.md #1 notes the dev machine is on Python 3.14, which has
# no prebuilt wheels for several pinned versions here, e.g. faiss-cpu==1.8.0
# or torch==2.4.0). 3.11 is the newest interpreter every pin in
# requirements-docker.txt has a prebuilt wheel for, so the image installs
# fast and reproducibly instead of falling back to slow/fragile source builds.

# ---- build stage: install Python deps into a venv ----
FROM python:3.11-slim AS builder

WORKDIR /build

# torch/faiss/sentence-transformers all ship manylinux wheels for this
# Python/platform combo, so no compiler toolchain is required for the common
# case -- but keep build-essential in the builder stage only (not the
# runtime stage) in case pip falls back to a source build for anything.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-docker.txt .
# torch CPU install is large and slow (the extra index serves CPU-only
# wheels ~200MB+) -- this is expected, let it finish.
RUN pip install --no-cache-dir -r requirements-docker.txt

# ---- runtime stage: slim image with only the venv + app code ----
FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Only what api/ and src/ need at runtime -- not data/ (mounted as a volume,
# see docker-compose.yml and DEPLOYMENT.md), not eval/, frontend/, tests/, or
# the dev-machine requirements.txt.
COPY api/ ./api/
COPY src/ ./src/
COPY scripts/ ./scripts/

EXPOSE 8000

# OLLAMA_HOST (read by src/config.py's GenerationConfig.ollama_base_url
# default_factory) points this at wherever Ollama actually runs -- it is
# never bundled into this image. Defaulted here to the conventional Linux
# Docker bridge alias; override at `docker run`/compose time for any other
# host.
ENV OLLAMA_HOST=http://host.docker.internal:11434

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
