# Literature Search Log

Search date: 2026-09-30 (all queries). Compiled from the reports of six area-specific research subagents plus the direct full-paper audit behind `docs/KILL_LIST.md`.

## Coverage, honestly stated

**Databases actually queried:** arXiv (API and direct PDF download; API returned empty for many multi-clause queries and rate-limited under bursts), OpenAlex, Crossref (one query), web search, PubMed Central and PeerJ (LPITutor), publisher pages fetched directly where open access.

**Requested but not effectively searched:** Semantic Scholar (HTTP 429 in every area), ACL Anthology, Google Scholar, IEEE Xplore, Springer, Wiley, ScienceDirect (HTTP 403), Nature/Scientific Reports beyond one paper, and the conference proceedings sites (NeurIPS, ICML, ICLR, EMNLP, AAAI, IJCAI, EDM, LAK, AIED, ITS). ACM Digital Library items were seen as titles or abstracts only.

**Consequence:** the search is a broad first pass, not an exhaustive review. About 150 distinct items were retrieved across areas, but roughly a third were read past the abstract and none in full except the 6 papers audited end to end for `KILL_LIST.md`. Absence of a paper in this log is never evidence that it does not exist (Rule 3).

## Per-area summary

| Area | Focus | Papers retrieved | Read beyond abstract | Main limits |
|---|---|---|---|---|
| A | RAG / IR robustness, evaluation validity | 30 arXiv (+leads) | 16 (partial) | About 20 arXiv queries empty; nothing found on RAG benchmark contamination, run-to-run noise or citation-manipulation defenses (a search failure) |
| B | Factuality, verification, judges | about 28 | 8 | No refusal-metric, executable-verification or NLI-on-causal-error papers retrieved |
| C | Executable, simulation, causal, formal verification | about 50 | about 22 (limitations sections) | Shallow synonym search; none read in full |
| D | LLM tutoring, ITS, learning outcomes | 23 | 13 (4 with real-learner outcomes) | Bastani (PNAS), Nie, Khanmigo, Fan, Lyu, Xue, Thomas, Darvishi abstract-only |
| E | CS / OS education, programming education | 26 | 12 (9 on topic) | Every ACM DL item abstract-only; concurrency-misconception papers title-only |
| F | Benchmark science, judges, reliability | about 35 | about 12 | No paper found on hard-coded template scoring or unexecuted baselines (answers inferred) |

## Representative queries (database | query | hits | selected)

**A (RAG/IR).** arXiv: "corrective retrieval augmented generation" (2: 2401.15884, 2603.16169); "semantic chunking" AND retrieval (4: 2410.13070, 2601.14123); LLM-as-a-judge AND faithfulness (2: 2505.04847, 2502.17163). OpenAlex: "query expansion fails LLM generative" (2309.08541); "GraphRAG versus vanilla RAG unfair evaluation" (2502.11371, 2506.05690); "HyDE limitations" (2212.10496). Semantic Scholar: "RAG reranking hurts": HTTP 429.

**B (factuality/judges).** arXiv: LLM-as-a-judge AND bias (2410.21819, 2506.22316, 2602.02219); self-preference AND LLM (2506.02592, 2601.22548, 2604.22891, 2606.20093). WebSearch: "LLMs cannot self-correct reasoning yet" (2310.01798); citation accuracy attribution evaluation (2305.14627, 2410.11217); FActScore limitations (2305.14251, 2505.23295); NLI faithfulness metrics fail causal errors (2411.16638, 2511.07689, 2212.09955); LLM judge reward hacking RLVR (2507.08794, 2604.15149, 2609.01354, 2607.11022, 2510.00915); benchmark contamination survey (2410.18966, 2410.03249).

**C (executable/simulation/causal).** OpenAlex: "execution-based fact checking of LLM claims program" (ProgramFC, 2305.12744); "autoformalization proof assistant verification of LLM output" (2405.01379, 2305.12295). WebSearch: "LLM explanations verified by executing simulator" (2606.04505 MechSim, 2604.03253, 2405.01379, 2507.05118); "LLM explanation faithfulness verified by re-executing code / counterfactual simulatability" (2605.27879 FAX, 2510.27544 TempoBench, 2402.04614, 2601.03775, 2602.02639); "counterfactual code execution reasoning benchmark" (2510.01539, 2604.20917, 2502.11008); "hallucinated code execution reasoning, CodeMind CRUXEval limitations" (2512.00215, 2510.15079, 2504.14119, 2402.09664). Direct PDF fetch of 17 known IDs (PAL, PoT, Logic-LM, SatLM, CRITIC, NExT, and others), titles verified.

**D (tutoring/learning outcomes).** OpenAlex (2022+): RCT of LLM tutor learning outcomes (Kestin 2025); generative AI harms learning field experiment (Bastani 2025); Tutor CoPilot; Rori Ghana; simulated-student validity (Benedetto 2024); MRBench, MathTutorBench, PedagogicalRL; LearnLM; sycophancy in LLM tutors.

**E (CS/OS education).** WebSearch: "operating systems concept inventory validated misconceptions students" (Webb and Taylor 2014, Koli 2013, Pamplona et al.); "operating systems course LLM teaching assistant evaluation SIGCSE 2025" (SortingHat, CodeAid); "concurrency misconceptions students" (ICER/ITiCSE/Koli 2019 titles); "OS visualization simulator" (cpusim, JITE virtual simulations). arXiv: CodeHelp 2308.06921; Grade Like a Human 2405.19694. Crossref: "Less stress better scores same learning" (dissociation RCT, N = 275).

**F (benchmark science).** arXiv id-list verification of 23 known IDs (MT-Bench 2306.05685, error bars 2411.00640, variance 2406.10229, GSM1k 2405.00332, GSM-Symbolic 2410.05229, tinyBenchmarks 2402.14992, RGB 2309.01431, PoisonedRAG 2402.07867). arXiv: "construct validity AND benchmarks" (2511.04703, 2603.15121); "item response theory AND language model AND benchmark" (2505.15055, 2509.11106); "student simulation AND language models AND fidelity" (2601.05473).

## Queries that returned nothing (not evidence of absence)
About 40 arXiv boolean queries across areas returned empty (rate limiting or over-strict syntax), including RAG benchmark contamination, run-to-run variance, citation-manipulation defenses, refusal metrics, simulated-student realism, statistical power for RAG, and notional-machine LLM work. These topics are **unsearched**, not negative.

## Leads noted but not read
EduGuard (arXiv 2607.15738), a prompt-engineering personalization paper (2609.03402), Wiley doi 10.1002/cae.70153, a ScienceDirect systematic survey of educational RAG (pii S2666920X25000578), "Steering AI Tutors Through System Prompts" (ICER 2026), Bastani et al. PNAS full text, Khanmigo NBER working paper full text.
