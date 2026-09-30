# From-Scratch Research Options

**Premise:** OS-Tutor-RAG never existed. We have the same course material (now the 37-file OS corpus), the same skills, one 8 GB GPU with local models, and access to some students and instructors (extent UNKNOWN). We choose only from the literature gaps in `docs/NOVELTY_GAP_REPORT.md`. Only after this list is the repo compared (bottom).

Options are ordered by how well they fit "genuine gap + evaluable + feasible", not by excitement. Codes point to `research/candidate_ideas.json`.

| # | What we would build / study | Gap it targets | Would we start here? | Needs |
|---|---|---|---|---|
| 1 | **Expert-labelled claim-level correctness set for LLM explanations of OS mechanisms** (C02), the shared asset for options 2, 3 and 5 | No OS-explanation correctness audit found | **Yes, first** | 2 annotators, ~150 human-authored questions, several LLMs |
| 2 | **Validity of automated scorers (judges, RAGAS-style metrics) against those labels**, incl. same- vs cross-family judging and the abstention confound (C06, C07) | Judge validity unmeasured in tutoring/OS | **Yes** | Option 1 labels; API or local judges |
| 3 | **Claim-coverage audit, then executable-check vs judge comparison** on injected + natural errors (C04, C03) | Coverage and claim-level accuracy of "verified" explanations unreported | **Yes**, after 1 | Option 1 labels; rewritten simulators |
| 4 | **Validated OS misconception inventory** (C01) | Only a 10-item unvalidated OS inventory found | Yes if student data exist | Student responses from >= 2 cohorts |
| 5 | **OS-state reasoning benchmark with trace + cause scoring, human-authored problems** (C22, C05) | Code-execution benchmarks are Python-only; OS state untested | Yes | Human-authored problems; simulators as ground truth |
| 6 | **Factorial study of retrieval-pipeline interactions with a controlled noise floor** (C09) | Single-factor studies only | Maybe (methodological) | Larger reviewed question set |
| 7 | **Guardrail-component RCT with delayed retention in an OS course** (C14) | Which guardrail prevents dependency is unresolved | Later, if a cohort is available | Cohort, ethics, a tutor |
| 8 | **Do tutor-benchmark scores predict learning?** (C13) | No predictive-validity evidence | No (too hard for one group) | Many students and tutors |
| 9 | **Simulated-student fidelity for OS misconceptions** (C12, C21) | Contested validity; 2026 competitors | No (crowded, blocked on option 4) | Option 4 data |
| 10 | **Meta-research audit of noise/power in RAG-tutor papers** (C08) | Adoption of error-bar practice | Only as a side note | Literature only |
| 11 | **A tutor (RAG or otherwise) for OS** | Killed as a contribution: learner-state RAG tutors, GraphRAG tutors and misconception-aware RAG all exist | **No** as research; yes as a testbed | Engineering |

## What we would actually build today
A **measurement study**, not a tutor: (1) a human-authored OS question set and expert claim-level labels, (2) a small harness that runs several LLMs (with and without retrieval) on it, (3) scorers under test (judges, RAGAS-style metrics, simulator-based checkers), (4) paired statistics with an explicit noise floor. The tutor exists only as one of the systems under test. This yields several papers from one asset (options 1 to 3, 5) and avoids competing on architecture, where the literature is crowded.

## Comparison with OS-Tutor-RAG (done last, on purpose)
- **What the repo gives:** the corpus and ingestion, a working retrieval and generation pipeline (a legitimate system-under-test), an evaluation harness with per-question rows, hard-won measurement practice (A16-A20: decoy chunks, biased golden set, refusal-rewarding faithfulness, noise floor), and four deterministic OS simulators.
- **What it does not give:** any valid MGEV evidence (audit), a real benchmark with ground truth, human labels, or student data.
- **Verdict on sunk cost:** the repo is a useful instrument for options 1-3, 5 and 6; it is not the research contribution.
