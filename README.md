# OS-Tutor-RAG & Reference-Choice Robustness (RCR) Research

This repository contains two main subsystems:
1. **OS-Tutor-RAG**: A retrieval-augmented generation pipeline and Socratic tutoring application for operating systems concepts (lecture decks, OSTEP chapters, lab handouts).
2. **Reference-Choice Robustness (RCR) Research Project**: The formal research implementation and publication package analyzing reference-choice sensitivity, benchmark identifiability, and executable semantic validators in LLM reasoning benchmarks.

---

## Quickstart (fresh clone)

```bash
git clone <repo> && cd OS-Tutor-RAG
# put the course .pptx/.pdf/.docx files in data/raw/  (not stored in git)
bash scripts/setup.sh     # venv, deps, embedding model, Ollama model, frontend, index
bash scripts/start.sh     # backend :8000 + frontend :3000  ->  http://localhost:3000
python scripts/check_env.py   # tells you what is missing and how to fix it
```
Needs Python 3.11/3.12, Node 18+, and [Ollama](https://ollama.com). Setup needs internet once.

---


## 🔬 Research Focus: Reference-Choice Robustness (RCR)

### Central Research Question
> *Is an executable reasoning benchmark scientifically identifiable when its gold reference trajectory is an arbitrary valid member of the task's complete valid-solution space \(V(x)\)?*

### Primary Recomputed Findings (50,000 Monte Carlo Reference Vector Draws)
- **Benchmark Instability**: Evaluating 1,152 model outputs across 24 formal OS tasks (Scheduling, Synchronization Interleaving, Banker's Deadlock Avoidance) reveals that changing only the selected gold reference \(R \in V(x)\) while holding tasks, outputs, and evaluators fixed causes substantial ranking instability (\(\text{Kendall } \tau_b = 0.618 \pm 0.351\), \(\text{SE} = 0.0016\)) and flips pairwise model winners in **17.56%** of reference vector draws. Under the single canonical reference \(E_2\) reproduces the oracle ordering, so the instability appears only when other valid references are used.
- **Reference-Distribution Sensitivity**: Evaluating 11 reference-selection distributions (550,000 draws) shows that increasing canonical selection bias attenuates instability monotonically (Uniform: 17.23%, \(p=0.50\): 12.14%, \(p=0.80\): 7.35%, \(p=0.95\): 2.30%, Similarity-weighted: 17.04%); instability persists unless alternative valid references are almost never selected.
- **Detection Loss (all 50,000 draws, per evaluator)**: The reference-independent validator \(E_3\) finds `qwen3:8b` significantly better than `llama3.1:8b` and `mistral:7b-instruct` (Holm-adjusted \(p = 0.013, 0.018\)); reference-matching evaluators miss both differences in 100% (\(E_1\)) and 99.99% (\(E_2\)) of draws and retain only 12–18% of the true pairwise gaps. This is an exact attenuation law, \(\mathbb{E}[E_2] = E_3/|V(x)|\); matching against \(k \approx 25\) references restores about 85% detection, whereas an inverse-\(|V|\) correction removes the bias but not the variance.
- **Where the Reversals Live**: 85.6% of \(E_2\)'s winner-reversal mass lies in model pairs that \(E_3\) itself cannot separate (near-ties); reversal is concentrated in Banker's (21.0%) and synchronization (10.0%) and absent in scheduling (three of four models solve none of its worlds).
- **Underestimation of Model Competence**: Canonical exact matching (\(E_1\)) recovers the reference-invariant oracle ranking only **2.86%** of the time, and normalized matching (\(E_2\)) recovers it only **13.63%** of the time, falsely rejecting valid noncanonical trajectories.
- **Stated-Convention Control**: Disclosing canonical tie-breaking rules fails to eliminate noncanonical outputs (\(\text{FRR}_{\text{norm}} = 0.625\)), proving that noncanonical trajectory generation persists when conventions are disclosed.
- **Model Competence**: Gemma 3 12B (\(n_{\text{valid}} = 42\)) exhibits 61.9% False Rejection Rate (\(\text{FRR}_{\text{norm}} = 0.619\)), confirming that noncanonical trajectory diversity persists under increased model capability.
- **Oracle Decision Stability**: Reference-independent executable semantic validators (\(E_3\)) remove reference-choice dependence **by construction** (\(\text{Kendall } \tau_b = 1.000\), 0% reversals); the empirical content is the measured cost of not using one.
- **Scope and Status**: One 24-world benchmark and four sub-10B models at low accuracy. The RCR metrics are a post-hoc reanalysis of a pilot whose preregistered verdict was CONDITIONAL (see `paper/PAPER_FINAL.md` §9–10). Project name: **Aether**. Authors: Adhyan Jain (24BCI0111) and Atharva Sheersh Pandey (24BCI0069).

### Canonical Research & Paper Artifacts
- **Canonical Manuscript**: [`paper/PAPER_FINAL.md`](paper/PAPER_FINAL.md)
- **Reproducibility Guide & Hashes**: [`paper/REPRODUCIBILITY.md`](paper/REPRODUCIBILITY.md)
- **Paper Claims Audit**: [`paper/CLAIMS_AUDIT_FINAL.md`](paper/CLAIMS_AUDIT_FINAL.md)
- **Reviewer Attack Report**: [`paper/REVIEWER_ATTACK.md`](paper/REVIEWER_ATTACK.md)
- **Novelty & Prior Art Audit**: [`paper/NOVELTY_POSITIONING_FINAL.md`](paper/NOVELTY_POSITIONING_FINAL.md)
- **Final Research Status Report**: [`paper/FINAL_RESEARCH_STATUS.md`](paper/FINAL_RESEARCH_STATUS.md)
- **Repo Map (what every file is for)**: [`docs/REPO_MAP.md`](docs/REPO_MAP.md)
- **Recomputed RCR Summary Data**: [`research/ssr_pilot/results/rcrc/rcr_summary.json`](research/ssr_pilot/results/rcrc/rcr_summary.json)
- **Reference Sensitivity Analysis Data**: [`research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.json`](research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.json)
- **Extended Analysis Data (full-draw significance, detection, near-tie, per-family)**: [`research/ssr_pilot/results/rcrc/extended_analysis.json`](research/ssr_pilot/results/rcrc/extended_analysis.json)
- **k-Reference / Attenuation / Correction Data**: [`research/ssr_pilot/results/rcrc/kref_attenuation.json`](research/ssr_pilot/results/rcrc/kref_attenuation.json)
- **Verified Bibliography**: [`paper/references_verified.csv`](paper/references_verified.csv)
- **LaTeX/PDF build**: [`paper/build/`](paper/build/)
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

### The tutoring layer (`src/tutor/`)

The chatbot is a tutor, not only a retriever. Policy lives in code (testable); the model only phrases.

- **Socratic loop**: after a grounded answer the tutor appends *one* short question chosen from the student's concept state (30 authored concepts, 96 graded questions). The reply is graded deterministically; a wrong answer climbs a ladder (**hint, then scaffold, then the explanation after two misses**), a misconception gets a probing question before a correction, and "just tell me" / "skip" are always honoured.
- **Quiz mode** ("test my understanding of paging"): three questions moving recall, understanding, application, analysis, then a summary. A **Guided questions** switch turns all questioning off.
- **For a student who knows nothing**: "I'm new" / "where do I start" gives a learning path; an empty chat shows starter questions and the course map; every answer ends with follow-up chips (explain with an example, test me, what to know first, how it connects to the next idea, topics from the retrieved slides, and validated model-written questions). Every chip is a complete message.
- **Friendliness and safety**: difficulty detection ("I don't understand", "too hard") gives a simpler explanation then a full one; distress, off-topic and prompt-injection messages get fixed, kind replies with no model call.
- **Small, smooth replies**: answers are meant to be about three short sentences (a hard cap of 5 sentences/lines and `GenerationConfig.chat_max_tokens`; the stream ends on a sentence boundary, never mid-word), and the student can say "continue", "give that as bullet points" or "explain that more simply". Short messages are handled as people actually send them: "done", "yes", "ok" nudge toward an answer or move to the next idea, "next" advances the path, "hi bro", "thanks", "how are you" get a warm one-liner, requests for video/audio get an honest text-only reply, "I'm not satisfied" offers three ways to fix it, and the same canned reply is never sent twice in a row. A question retrieval finds nothing for ("what is fear") gets a short bridge back to the course instead of a model call. Model-written follow-ups are off by default (they cost a second model call); set `OS_RAG_MODEL_FOLLOWUPS=1` to enable them.
- **State and cost**: concept state is per chat thread (`api/routes/session.py`); `GET /tutor/overview`, `/tutor/progress/{id}`, `DELETE /tutor/session/{id}`. Most tutoring turns need no retrieval and no model call. The only model uses are phrasing and one clamped advisory classification.
- **Tests**: `PYTHONPATH=. .venv/bin/pytest tests/tutor -q` (scripted dialogues, answer-key checks, API event contract with stubbed retrieval/Ollama).
- **Research explainer**: the app's `/research` page; the two presentation guides are `docs/GUIDE_PART1_RESEARCH_PAPER.md` (the RCR research paper) and `docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md` (the chatbot's pipeline, metrics and tutoring layer).

---

## 📁 Repository Layout

```
paper/
  PAPER_FINAL.md                canonical journal manuscript
  CLAIMS_AUDIT_FINAL.md         complete claims traceability matrix
  REPRODUCIBILITY.md            reproducibility guide & 64-char SHA-256 hashes
  REVIEWER_ATTACK.md            8-reviewer hostile attack simulation
  references_verified.csv       bibliography checked against primary sources
  build_tables.py               regenerates manuscript Tables 3-6 from extended_analysis.json
  build/                        Markdown -> LaTeX -> PDF build
  NOVELTY_POSITIONING_FINAL.md   prior art & novelty audit
  FINAL_RESEARCH_STATUS.md      research status report & decision gate
research/
  ssr_pilot/core/              reference-independent semantic oracle & valid-space enumeration
  ssr_pilot/rcrc/              50,000-draw RCR Monte Carlo protocol & statistics engine
  ssr_pilot/adversarial/       adversarial contrast dataset & evaluator meta-evaluation
  ssr_pilot/runs/              raw baseline generation outputs (1,152 records)
  ssr_pilot/runs_stated_convention/  raw stated-convention control outputs (1,152 records)
  ssr_pilot/results/           recomputed JSON summary artifacts
tests/
  test_consistency_gate.py     automated manuscript-to-JSON consistency gate
  ssr_pilot/                   unit tests for semantics, valid space, oracle, & statistics
src/                           OS-Tutor-RAG ingestion, retrieval, & generation pipeline
src/tutor/                     tutoring layer (concept state, Socratic questions, follow-ups)
eval/                          RAGAS and retrieval evaluation harnesses
docs/REPO_MAP.md               what every directory and document is for
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

### Run Reference-Distribution Sensitivity Analysis (11 Distributions, 550,000 Draws)
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_reference_distribution_sensitivity
```

### Run Extended Analysis (all 50,000 draws; detection, near-tie, per-family) and Regenerate Tables
```bash
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_extended_analysis
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_kref_analysis
PYTHONPATH=. .venv/bin/python paper/build_tables.py
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
Needs a running Ollama (`ollama list` shows the chat models the UI offers) and the embedding model cached once
(`HF_HUB_OFFLINE=0 python -c "from huggingface_hub import snapshot_download as d; d('BAAI/bge-large-en-v1.5')"`).
If port 8000 is taken, pass another `--port`, set `NEXT_PUBLIC_API_BASE` for the frontend and
`CORS_ORIGINS` (comma-separated, default `http://localhost:3000`) for the API.
The chat prefers `llama3.1:8b`, then `qwen2.5:7b`, `mistral:7b-instruct` (`GenerationConfig.chat_model_preference`); `/models` lists the installed ones in that order and the UI warms the selected model so the first answer is not a cold start. On a small GPU, another process using a different Ollama model makes every turn reload models and take tens of seconds.
