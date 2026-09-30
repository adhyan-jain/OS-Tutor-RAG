# Idea Kill Log

Each idea was attacked with the prior art that the 2026-09-30 searches surfaced (six areas plus targeted follow-ups). **Depth is limited:** a "survives" verdict means "no close prior art found in a partial search", never "novel" (Rules 3 and 14). Every survivor lists the extra searches needed before commitment. Full candidate details are in `research/candidate_ideas.json`; the earlier three ideas are in `docs/KILL_LIST.md`.

## A. Ideas inherited from the project

| Idea | Initial novelty | Closest prior art | Overlap | Verdict | Revised idea |
|---|---|---|---|---|---|
| Adaptive RAG tutor (learner state + RAG) | Assumed high | TutorLLM, LPITutor, Frontiers 2026, DeepTutor, KITE (all read) | Methodological | **KILLED** as architecture | Evaluation-validity questions (C06) |
| GraphRAG for OS tutoring | Assumed medium | 2509.07846, 2509.16780, 2506.05690, 2502.11371 (read) | Methodological for RAG-vs-GraphRAG | **PARTIALLY CROWDED** | Only cross-concept + matched cost (C10, still crowded) |
| RAG + misconception detection | Assumed medium | MisEdu-RAG, MiRAGE, misconception_aware_rag (null result) | Methodological | **PARTIALLY CROWDED** | Needs validated OS misconceptions (C01) |
| **Mechanism-grounded evidence verification (MGEV)** as a *method* | Assumed high | **MechSim 2606.04505** (claims verified against simulator mechanisms with a verification agent), **FAX 2605.27879** (claim decomposition + execution-based tests), Explanation-Refiner (EMNLP 2024, theorem-prover verification of NL explanations), CRITIC (tool-verified correction), ProgramFC | MechSim/FAX cover the "decompose then check by executing" pattern in other domains | **PARTIALLY CROWDED / method claim killed.** Surviving piece is a controlled *evaluation* of what executable checks catch vs judges in a discrete-state OS domain, plus coverage reporting (C03, C04). None of the project's MGEV numbers is evidence (audit) | C03 / C04 |

## B. Literature-derived candidates

| ID | Idea | Initial novelty | Closest prior art | Why it fails / survives | Revised idea / extra search needed |
|---|---|---|---|---|---|
| C01 | Validated OS misconception inventory | Medium-high | Webb and Taylor 2014 (10 items, unvalidated); small qualitative studies; validated inventories in other CS topics (snippet) | **Survives**: no validated OS inventory found; method is established elsewhere. Thin search (ACM DL not readable) | Search SIGCSE/ITiCSE 2015-2026 for OS/concurrency inventory follow-ups and check for a published validation of Webb and Taylor |
| C02 | Claim-level correctness audit of LLM OS explanations | Medium | Grade Like a Human (6 OS questions), SortingHat (no evaluation), Demystify/CES (Python code) | **Survives**: no OS-explanation audit found | Search "LLM explanation correctness" in systems/architecture education |
| C03 | Executable checks vs judges vs NLI on injected errors | Low-medium as method, medium as evaluation | MechSim, FAX, Explanation-Refiner, CRITIC | **Survives narrowly**: prior work reports judge scores, not claim-level recall/false-accept vs independent labels; FAX admits only local verification. Extending MechSim/FAX with an OS domain would not remove the evaluation contribution, but would remove any "new method" claim | Read MechSim and FAX in full (only limitations and abstracts read); search "verifier recall false accept explanation" 2026 |
| C04 | Claim-coverage audit | Medium | FAX caveat only | **Survives**; small on its own; feasibility precondition for C03 | None |
| C05 | Trace vs causal attribution on OS traces | Medium | TempoBench, PetriBench (snippet), CES | **Partially crowded**: framing exists; OS domain adds a modest step | Read PetriBench; check for OS versions |
| C06 | Judge/metric validity on OS answers vs teacher labels | Medium | MT-Bench, MRBench, RAGAS validation on WikiEval and an educational set (snippet) | **Survives** as a domain study; general judge-validity work is abundant, so novelty rests on domain + claim-level labels + abstention analysis. RAGAS reports high agreement with humans on WikiEval (contradiction to the project's A1, unresolved) | Read RAGAS validation details; search educational judge validity 2025-2026 |
| C07 | Faithfulness-abstention confound | Medium | Sufficient Context; TRUST-SCORE / grounded-refusal metrics (snippet) | **Weak alone**; refusal-aware metrics exist; fold into C06 | None |
| C08 | Noise/power audit of RAG-tutor papers | Medium | Bean et al. 2025 (445 benchmarks), Miller 2024, Card 2020 | **Weak**: adoption audit; scope overlaps Bean et al. | Check for a RAG-specific audit |
| C09 | RAG factorial interaction study | Low-medium | Chunk-cliff, expansion-failure, long-context RAG | **Survives** as a careful empirical study; incremental; risk of a null result | Search "RAG ablation interaction reranker query expansion 2025-2026" (arXiv API failed) |
| C10 | GraphRAG vs vector at matched cost on OS | Low | Four studies (two read fully) | **Partially crowded**; low priority | None |
| C11 | Misconception-conditioned retrieval, validated | Medium | misconception_aware_rag null result | **Blocked on C01** | -- |
| C12 | Simulated students vs real OS distractors | Medium | Benedetto 2024; 2605.12748 and 2603.15547 (2026, snippet) | **Partially crowded**: direct competitors appeared in 2026 | Read 2605.12748 and 2603.15547 |
| C13 | Benchmark score vs learning gain | High | None found | **Too hard to evaluate**: needs large multi-tutor RCT | -- |
| C14 | Guardrail components and delayed retention, OS course | Medium | Bastani; dissociation RCT; Guardrails RCT; 2606.01375 and 2608.12292 (snippet) | **High-risk**: active area, expensive | Read 2606.01375 |
| C15 | Perception vs learning for an OS tutor | Low | dissociation RCT; ai2503 | **TAKEN** in adjacent domains | -- |
| C16 | Simulator-grounded generation vs post-hoc check | Low | Mind's Eye, MechSim, CRITIC | **Weak** | -- |
| C17 | Robustness to plausible wrong passages | Low | PoisonedRAG, RGB, GSM-IC | **Weak**, well covered generally | -- |
| C18 | Duplicate lecture versions in retrieval | Low | Byte-exact deduplication in RAG (2605.09611, snippet) | **TAKEN**; treat as a data-quality control | Deduplicate before experiments |
| C19 | Abstention thresholds for tutors | Low | Sufficient Context | **Partially crowded** | -- |
| C20 | IRT calibration of LLM-authored OS items | Low | Madaan 2024, Liu 2025 (abstract) | **Weak** | -- |
| C21 | LLM distractors vs real OS distributions | Medium | 2603.15547 (snippet) | **Partially crowded**; blocked on C01 | -- |
| C22 | OS-state reasoning benchmark, human-authored | Medium | CRUXEval, CES, Demystify, PetriBench (snippet), CacheMind (RAG on cache traces, snippet) | **Survives with risk**: OS mechanisms not found, but adjacent benchmarks exist; template-benchmark critique means problems must be human-authored | Read PetriBench and CacheMind |
| C23 | Length/position bias for tutor judges | Low | AlpacaEval LC; MT-Bench | **TAKEN**; fold into C06 | -- |

## C. Ideas that initially looked novel and were killed or crowded (for the record)
1. "Mechanism-grounded RAG / executable verification" as a new method: close prior art in MechSim, FAX and Explanation-Refiner.
2. "Adaptive RAG tutor": five implemented systems exist, with no significant real-learner effect where measured.
3. "Simulated-student fidelity for OS misconceptions": 2026 papers on misconception faithfulness of LLM simulators appeared.
