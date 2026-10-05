# OS-Tutor-RAG & Reference-Choice Robustness (RCR) Research

This repository contains two main subsystems:
1. **OS-Tutor-RAG**: A retrieval-augmented generation pipeline and Socratic tutoring application for operating systems concepts (lecture decks, OSTEP chapters, lab handouts).
2. **Reference-Choice Robustness (RCR) Research Project**: The formal research implementation and publication package analyzing reference-choice sensitivity, benchmark identifiability, and executable semantic validators in LLM reasoning benchmarks.

---

## 🔬 Research Focus: Reference-Choice Robustness (RCR)

### Central Research Question
> *Is an executable reasoning benchmark scientifically identifiable when its gold reference trajectory is an arbitrary valid member of the task's complete valid-solution space \(V(x)\)?*

### Primary Recomputed Findings (50,000 Monte Carlo Reference Vector Draws)
- **Benchmark Instability**: Evaluating 1,152 model outputs across 24 formal OS tasks (Scheduling, Synchronization Interleaving, Banker's Deadlock Avoidance) reveals that changing only the selected gold reference \(R \in V(x)\) while holding tasks, outputs, and evaluators fixed causes substantial ranking instability (\(\text{Kendall } \tau_b = 0.489 \pm 0.356\), \(\text{SE} = 0.0016\)) and flips pairwise model winners in **18.61%** of reference vector draws.
- **World-Level Inference**: Applying the preregistered world-level paired sign-flip permutation test (20,000 sign flips, Holm-Bonferroni corrected over 6 model pairs) demonstrates that world-level variance dominates pairwise model differences (\(p \ge 0.05\) across all model pairs).
- **Underestimation of Model Competence**: Canonical exact matching (\(E_1\)) recovers the reference-invariant oracle ranking only **2.86%** of the time, and normalized matching (\(E_2\)) recovers it only **23.92%** of the time, falsely rejecting valid noncanonical trajectories.
- **Stated-Convention Control**: Disclosing canonical tie-breaking rules fails to eliminate noncanonical outputs (\(\text{FRR}_{\text{norm}} = 0.625\)), proving that noncanonical trajectory generation persists when conventions are disclosed.
- **Model Competence**: Gemma 3 12B (\(n_{\text{valid}} = 42\)) exhibits 61.9% False Rejection Rate (\(\text{FRR}_{\text{norm}} = 0.619\)), confirming that noncanonical trajectory diversity persists under increased model capability.
- **Oracle Decision Stability**: Replaying candidate trajectories through reference-independent executable semantic validators (\(E_3\)) eliminates reference-choice dependence entirely, achieving **100% rank stability** (\(\text{Kendall } \tau_b = 1.000 \pm 0.000\), 0% reversals, 100% oracle recovery).

### Canonical Research & Paper Artifacts
- **Canonical Manuscript**: [`paper/PAPER_FINAL.md`](paper/PAPER_FINAL.md)
- **Reproducibility Guide & Hashes**: [`paper/REPRODUCIBILITY.md`](paper/REPRODUCIBILITY.md)
- **Paper Claims Audit**: [`paper/CLAIMS_AUDIT_FINAL.md`](paper/CLAIMS_AUDIT_FINAL.md)
- **Reviewer Attack Report**: [`paper/REVIEWER_ATTACK.md`](paper/REVIEWER_ATTACK.md)
- **Novelty & Prior Art Audit**: [`paper/NOVELTY_POSITIONING_FINAL.md`](paper/NOVELTY_POSITIONING_FINAL.md)
- **Final Research Status Report**: [`paper/FINAL_RESEARCH_STATUS.md`](paper/FINAL_RESEARCH_STATUS.md)
- **Dead Code & Docs Audit Log**: [`DEAD_CODE_AND_DOCS_AUDIT.md`](DEAD_CODE_AND_DOCS_AUDIT.md)
- **Recomputed RCR Summary Data**: [`research/ssr_pilot/results/rcrc/rcr_summary.json`](research/ssr_pilot/results/rcrc/rcr_summary.json)
- **RCR Core Engine**: [`research/ssr_pilot/core/`](research/ssr_pilot/core/)
- **RCR Protocol & Analysis**: [`research/ssr_pilot/rcrc/`](research/ssr_pilot/rcrc/)
- **Adversarial Meta-Evaluation**: [`research/ssr_pilot/adversarial/`](research/ssr_pilot/adversarial/)
- **Automated Consistency Gate & Test Suite**: [`tests/`](tests/)

---

## 🛠️ OS-Tutor-RAG Application Pipeline Overview

The RAG pipeline is built as a technique comparison study:
```
ingestion -> chunking -> retrieval -> reranking -> diversification -> expansion -> generation
```
Measurements of technique performance are recorded in [`FINDINGS.md`](FINDINGS.md).

### Implemented Techniques
- **Ingestion**: PPTX (per-slide title/bullets/notes), PDF (per-page text), DOCX (per-heading section).
- **Chunking**: Structure-aware (`pptx`, `docx`), Page-aware (`pdf`), Semantic (plain text).
- **Retrieval**: Dense (FAISS + `bge-large`), Sparse (BM25), Hybrid RRF, HyDE, Multi-query wrapping.
- **Reranking**: Cross-encoder (`bge-reranker-large`), Pointwise LLM-as-judge.
- **Diversification**: Maximal Marginal Relevance (MMR).
- **Context Expansion**: Parent slide/page substitution with token windowing.
- **Generation**: Local LLM via Ollama (`llama3`, `qwen3`, `gemma3`, `olmo2`).

---

## 📁 Repository Layout

```
paper/
  PAPER_FINAL.md                canonical journal manuscript
  CLAIMS_AUDIT_FINAL.md         complete claims traceability matrix
  REPRODUCIBILITY.md            reproducibility guide & 64-char SHA-256 hashes
  REVIEWER_ATTACK.md            5-reviewer hostile attack simulation
  NOVELTY_POSITIONING_FINAL.md   prior art & novelty audit
  FINAL_RESEARCH_STATUS.md      research status report & decision gate
research/
  ssr_pilot/core/              reference-independent semantic oracle & valid-space enumeration
  ssr_pilot/rcrc/              50,000-draw RCR Monte Carlo protocol & statistics engine
  ssr_pilot/adversarial/       adversarial contrast dataset & evaluator meta-evaluation
  ssr_pilot/runs/              raw baseline generation outputs (1,152 records)
  ssr_pilot/runs_stated_conv/  raw stated-convention control outputs (1,152 records)
  ssr_pilot/results/           recomputed JSON summary artifacts
tests/
  test_consistency_gate.py     automated manuscript-to-JSON consistency gate
  ssr_pilot/                   unit tests for semantics, valid space, oracle, & statistics
src/                           OS-Tutor-RAG ingestion, retrieval, & generation pipeline
api/                           FastAPI backend routes
frontend/                      Next.js web user interface
```

---

## 🚀 Quick Start & Reproducibility

### Setup Environment
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Run Unit Tests & Automated Consistency Gate
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

### Run 50,000 Draw RCR Protocol
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION
```

### Run Stated-Convention Control Analysis
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_stated_convention
```

### Run Competence Pilot Analysis
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_competence_pilot
```

### Run Adversarial Meta-Evaluation
```bash
PYTHONPATH=. .venv/bin/python -c "from research.ssr_pilot.adversarial.construction import build_adversarial_dataset, evaluate_evaluators_on_adversarial; evaluate_evaluators_on_adversarial(build_adversarial_dataset())"
```

### Run Application (FastAPI + Next.js)
```bash
# Backend (FastAPI)
PYTHONPATH=. .venv/bin/uvicorn api.main:app --port 8000

# Frontend (Next.js)
cd frontend && npm install && npm run dev
```
