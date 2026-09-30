# MGEV: Archived Prototype (frozen 2026-09-30)

The "Mechanism-Grounded Evidence Verification" prototype from commit `f1d4943` (2026-09-26) is frozen. It stays in the repository for provenance. It is **not deleted, not evidence and not reused**.

## Frozen files (left in place; do not extend)
- `eval/benchmark_builder.py`, `eval/OS_MechanismBench.json`: a template-generated 300-question set with no answerable ground truth.
- `eval/mgev_eval.py`, `eval/mgev_results.json`: baseline correctness is assigned by question type, not by running a system.
- `eval/corruption_eval.py`, `eval/corruption_results.json`: n = 3; the textual-RAG arm is a literal `True`; predictions are hand-encoded.
- `eval/error_attribution.py`, `scripts/generate_paper_tables.py`
- `src/mechanism/*`, `src/query/*`, `src/verification/*`: the simulators are real code but have only been tested on hard-coded inputs.
- `docs/PAPER_DRAFT.md`, `docs/PAPER_TABLES.md`, `docs/PRIOR_ART_MATRIX.md`, `docs/RESEARCH_GAP.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/THREATS_TO_VALIDITY.md`

## Rules
1. Do not cite any MGEV number (70%, 90%, 90.5%, 100%, "300 questions") as evidence. The reasons are in `docs/CURRENT_PROJECT_AUDIT.md`, Part A.
2. Do not use OS-MechanismBench in any new study.
3. The simulators in `src/verification/` may be *rewritten* as candidate verifiers. Before use they must be validated against textbook worked examples.
4. The prior-art matrix is superseded by `docs/KILL_LIST.md`, `docs/IDEA_KILL_LOG.md` and `docs/ADVERSARIAL_LITERATURE_REVIEW.md`. It does not mention the closest known work (MechSim, FAX).
