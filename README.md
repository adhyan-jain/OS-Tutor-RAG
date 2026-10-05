# OS-Tutor-RAG & Reference-Choice Robustness (RCR) Research

This repository contains two main subsystems:
1. **OS-Tutor-RAG**: A retrieval-augmented generation pipeline and Socratic tutoring application for operating systems concepts (lecture decks, OSTEP chapters, lab handouts).
2. **Reference-Choice Robustness (RCR) Research Project**: The final research implementation and publication package analyzing reference-choice sensitivity, benchmark identifiability, and executable semantic oracles in LLM reasoning benchmarks.

---

## 🔬 Research Focus: Reference-Choice Robustness (RCR)

### Central Research Question
> *Is an executable reasoning benchmark scientifically identifiable when its gold/reference trajectory is an arbitrary valid member of the task's complete valid-solution set \(V(x)\)?*

### Primary Findings
- **Benchmark Instability**: Evaluating 1,152 model outputs across 24 formal OS tasks (Scheduling, Synchronization Interleaving, Banker's Deadlock Avoidance) reveals that changing only the selected gold reference \(R \in V(x)\) while holding tasks, outputs, and evaluators fixed causes substantial ranking instability (\(\text{Kendall } \tau = 0.463 \pm 0.343\)) and flips pairwise model winners in **18.45%** of reference pairs.
- **Statistical Significance Flips**: For key model comparisons (e.g. `gemma2:9b` vs `qwen3:8b`), **50.0% of valid reference selections yield a statistically significant difference (\(p < 0.05\))** while **50.0% yield a non-significant result (\(p \ge 0.05\))**.
- **Underestimation of Model Competence**: Canonical exact matching recovers the reference-invariant semantic oracle ranking only **4.0%** of the time, and normalized matching recovers it only **28.0%** of the time, falsely rejecting valid trajectories that diverge from an arbitrary canonical reference.
- **Oracle Decision Stability**: Replaying candidate trajectories through an independent executable semantic oracle (\(E_3\)) eliminates reference-choice dependence entirely, achieving **100% rank stability** (\(\text{Kendall } \tau = 1.000 \pm 0.000\), 0% reversals, 100% oracle recovery).

### Research Code & Paper Artifacts
- **Primary Manuscript Draft**: [`paper/PAPER_DRAFT_V1.md`](paper/PAPER_DRAFT_V1.md)
- **Paper Claims Audit**: [`paper/CLAIMS_AUDIT_V1.md`](paper/CLAIMS_AUDIT_V1.md)
- **Publication Tables**: [`paper/TABLES/table1_rcr_primary.md`](paper/TABLES/table1_rcr_primary.md), [`paper/TABLES/table2_significance_flips.md`](paper/TABLES/table2_significance_flips.md), [`paper/TABLES/table3_adversarial_meta.md`](paper/TABLES/table3_adversarial_meta.md)
- **Primary Experimental Report**: [`research/ssr_pilot/reports/RCRC_REPORT.md`](research/ssr_pilot/reports/RCRC_REPORT.md)
- **RCR Method Formalization**: [`docs/RCRC_METHOD.md`](docs/RCRC_METHOD.md)
- **RCR Protocol & Reproducibility**: [`docs/RCRC_EXPERIMENT_PROTOCOL.md`](docs/RCRC_EXPERIMENT_PROTOCOL.md)
- **Novelty Positioning Matrix**: [`docs/RCRC_NOVELTY_POSITIONING.md`](docs/RCRC_NOVELTY_POSITIONING.md)
- **RCR Core Package**: [`research/ssr_pilot/core/`](research/ssr_pilot/core/)
- **RCR Analysis Engine**: [`research/ssr_pilot/rcrc/`](research/ssr_pilot/rcrc/)
- **Adversarial Meta-Evaluation**: [`research/ssr_pilot/adversarial/`](research/ssr_pilot/adversarial/)
- **Unit Test Suite**: [`tests/ssr_pilot/`](tests/ssr_pilot/)

---

## 🛠️ OS-Tutor-RAG Pipeline Overview

The RAG pipeline is built as a **technique comparison study**, where every stage is selected by configuration:

```
ingestion -> chunking -> retrieval -> reranking -> diversification -> expansion -> generation
```

Measurements of which techniques help or hurt are recorded in [`FINDINGS.md`](FINDINGS.md).

### Implemented Techniques
- **Ingestion**: PPTX (per-slide title/bullets/notes), PDF (per-page text), DOCX (per-heading section).
- **Chunking**: Structure-aware (`pptx`, `docx`), Page-aware (`pdf`), Semantic (plain text).
- **Retrieval**: Dense (FAISS + `bge-large`), Sparse (BM25), Hybrid RRF, HyDE, Multi-query wrapping.
- **Reranking**: Cross-encoder (`bge-reranker-large`), Pointwise LLM-as-judge.
- **Diversification**: Maximal Marginal Relevance (MMR).
- **Context Expansion**: Parent slide/page substitution with token windowing.
- **Generation**: Local LLM via Ollama (`llama3`, `qwen3`, `gemma3`, `olmo2`).

---

## 🚀 Quick Start & Reproducibility

### Setup Virtual Environment
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Run Research Tests
```bash
PYTHONPATH=. .venv/bin/pytest tests/ssr_pilot/ tests/research/ tests/test_verifiers.py
```

### Run RCR Core Analysis
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION
```

### Run Adversarial Meta-Evaluation
```bash
PYTHONPATH=. .venv/bin/python -c "from research.ssr_pilot.adversarial.construction import build_adversarial_dataset, evaluate_evaluators_on_adversarial; evaluate_evaluators_on_adversarial(build_adversarial_dataset())"
```

### Run Chat Backend & Frontend
```bash
# Backend (FastAPI)
PYTHONPATH=. .venv/bin/uvicorn api.main:app --port 8000

# Frontend (Next.js)
cd frontend && npm install && npm run dev
```

---

## 📁 Repository Layout

```
paper/
  PAPER_DRAFT_V1.md            full formal research manuscript draft
  CLAIMS_AUDIT_V1.md           traceability matrix mapping claims to empirical artifacts
  TABLES/                      camera-ready publication markdown tables
docs/
  RCRC_METHOD.md               formal mathematical formulation of RCR
  RCRC_EXPERIMENT_PROTOCOL.md   reproducible experimental protocol
  RCRC_NOVELTY_POSITIONING.md   positioning matrix relative to TRACE, OTAP, LogicGraph
research/
  ssr_pilot/
    core/                      data schemas, valid space formalization, semantic oracle, reference regimes
    rcrc/                      RCR metrics, ranking stability, significance stability, oracle recovery
    adversarial/               adversarial dataset builder and evaluator meta-evaluation
    reports/                   RCRC_REPORT.md primary experimental report
    results/                   machine-readable JSON & JSONL evaluation records
    runs/                      raw 1,152 baseline model outputs
    runs_competence_pilot/      stronger-model outputs (gemma3:12b, olmo2:7b)
tests/
  ssr_pilot/                   unit tests for valid space, oracle invariance, RCR metrics, statistics
src/                           RAG pipeline source code (config, retrieval, chunking, reranking)
api/                           FastAPI endpoints and Socratic tutoring routes
frontend/                      Next.js web client and chat UI
FINDINGS.md                    RAG pipeline empirical findings and defects
DEPLOYMENT.md                  Docker and deployment instructions
```
