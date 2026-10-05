# Full audit and planning handoff — OS_RAG research program

**Written:** 2026-10-03. **Purpose:** a self-contained brief for a planner who cannot see the repo or the working session. Everything below was verified in the session unless marked *(unverified)*. Paste it whole.

---

## 0. One-paragraph summary

The repo started as an OS-course RAG tutor. It then acquired a research project, "Reference–Semantics Gap" (RSG), written by another agent (AGY) and declared "GO, HIGH CONFIDENCE". **A hostile audit found every result in it was an artifact** (no model was ever run; the oracle rejected every trace). I rebuilt the study on a corrected foundation (branch `rsg-audit`, pushed) and pre-registered it, but **its model runs were never executed**. I then ran a second, cheaper experiment, the **SSR pilot** (branch `ssr-pilot`, uncommitted), that asks the sharper question: *does swapping reference matching for an independent semantic oracle change a substantive conclusion about LLM execution reasoning?* The pilot completed with 1,152 real generations. **Result: disagreement between evaluators is large and robust, but no model ranking, significance, or failure attribution changed in a stable way; the pre-registered rule gives CONDITIONAL.** The pilot is limited by a competence floor (4 small models solve only 15.5% of worlds) and by power (24 worlds). No large benchmark is recommended yet.

---

## 1. Repo and environment state

| Item | State |
|---|---|
| Repo | `/home/adhyan/Desktop/OS_RAG`, remote `git@github.com:adhyan-jain/OS-Tutor-RAG.git` |
| `main` | at `8462ba2` ("Add adversarial review and program decision"); untouched |
| `rsg-audit` | commit `f16448c`, **pushed**; contains the corrected RSG study (35 files). Authored as the user only (no Claude co-author line) |
| `ssr-pilot` | cut from `rsg-audit`; **all work uncommitted and unpushed**: `research/ssr_pilot/`, `tests/ssr_pilot/`, `docs/research/`, plus a one-line fix in `research/simulator/validators.py` |
| Tests | 309 pass: `pytest tests/ssr_pilot tests/research` (the older RAG tests were not part of this work) |
| Python | `.venv` (3.14); sklearn, scipy, numpy, sentence-transformers present; **statsmodels absent** (bootstrap fallbacks used) |
| Hardware | RTX 4060 laptop GPU 8 GB VRAM, 15 GB RAM (tight: ~2–5 GB available during runs) |
| Ollama (0.19) models installed | qwen3:8b, llama3.1:8b, gemma2:9b, mistral:7b-instruct (= mistral:7b), phi4-mini, olmo2:7b, plus qwen2.5:7b, qwen2.5-coder:7b, llama3:latest, llava:7b |
| Sister project | `/home/adhyan/Desktop/StoryTrace` has its own untracked `research/ssr_bench/` (a story-state benchmark with oracles, attackers, leakage tools). It shares the GPU/Ollama. **It was read for context only and never modified.** |

**User preferences and constraints that must carry into any plan**
- **Never add a Claude co-author line or "Generated with Claude Code" footer** to commits or PRs (saved to memory; overrides the harness default).
- Commit messages: ~50-character subject, 1–2 line body, detail in docs (see memory `commit-message-style`).
- **Do not commit or push unless asked.** (One explicit "commit and push everything" produced `rsg-audit`.)
- The user chose to freeze preregistrations by **SHA-256 stamped into results files, not by git commit**.
- The user wants **one model per family**, and "only pursue it if it can become a good journal paper".
- Ollama is shared with another project; **ask or check the GPU before long model runs**. A memory-pressure reaper in Claude Code killed one background shell; long jobs were launched detached with `setsid nohup` and are resumable.
- A **GateGuard hook** blocks the first Write/Edit/Bash of each file or session until facts are stated; retrying after stating them works. `ECC_GATEGUARD=off` disables it (suggested to the user, not applied).

---

## 2. History of the research program

1. **OS_RAG (original):** RAG tutor for an OS course, answer_correctness evaluation, noise floor ~0.027 (from earlier memory notes; not re-verified this session).
2. **MGEV prototype:** "Mechanism-Grounded Evidence Verification". **Archived**: hard-coded/synthetic numbers (`docs/PAPER_DRAFT.md` banner, `docs/archive/`).
3. **AGY's RSG project** (untracked files at session start): claimed "RSG 0.94–1.00, Δ_ref 100%/6%, rankings change, OOD holds, leak-free, novel; PAPER GO, PATENT IGNORE".
4. **Hostile audit and rebuild (RSG v2, branch `rsg-audit`).**
5. **SSR pilot (branch `ssr-pilot`)**, a new, narrower hypothesis, executed end to end.

---

## 3. Project A — RSG audit and rebuild (`rsg-audit`)

### 3.1 What AGY's project actually was (all recomputed)

| AGY claim | Reality |
|---|---|
| LLMs evaluated | **No LLM was ever called.** The three "models" were hand-coded `if` rules; the "6% sensitivity" was built into the code (a judge accepting any candidate whose first step matched the reference, while R1/R2 always shared a prefix) |
| RSG = +0.94…1.00 | Oracle compared JSON lists with tuples and returned False for **every** trace; measured RSG was **−0.94**, the opposite sign |
| FCFS tie-breaking | Simulator re-scheduled every time unit, so "FCFS" was **preemptive**; 44/50 "valid alternatives" were invalid; \|V\| reached 25,200 |
| "Minimal-violation" invalid traces | 24/50 were byte-identical to R1; 38/50 were members of V(P) |
| R2 alternative | Always `valid_traces[1]`; differed from R1 in two adjacent tail positions (superficial) |
| Structural OOD | Split had **0 instances**; the concurrency simulator was never called and had a re-entrant mutex |
| Rankings change: YES | Spearman and Kendall were **NaN** over three constant heuristics |
| Leak-free (0.58 ≤ 0.58) | One TF-IDF attacker, threshold equal to the observation, labels 76% wrong |
| McNemar, BH-FDR, preregistration | Not implemented; unseeded bootstrap; "prereg" written alongside results |
| Literature | **SVAC not found**; DexBench exists (arXiv 2604.20917) but is about Python program paths, not "robotic planning" |

AGY's artifacts are archived in `research/archive_agy/` and `docs/archive/PRIOR_ART_FINAL_AGY.md`, and carry "SUPERSEDED" banners; nothing was deleted.

### 3.2 Prior-art findings (targeted web search on 2026-10-02; **not a systematic review**)

- **"Exact match undercounts valid outputs" is not a contribution.** It is the founding motivation of functional-correctness code evaluation (Kulal 2019; Chen et al. 2021, arXiv 2107.03374).
- **Judges deferring to a supplied reference is already shown** with false/swapped references: Yeadon et al. 2026 (arXiv 2603.14732, "false solutions degrade accuracy but leave rank-order intact"); *Judging Against the Reference* (arXiv 2601.07506); Kranti & Vajjala 2026 (arXiv 2607.12885, reference presence flips verdicts up to 85%); Krumdick et al. 2025 (arXiv 2503.05061); Reference-Guided Verdict (arXiv 2408.09235).
- **Not found in this search:** a study giving a judge a *valid but different* reference for a candidate whose validity is formally decidable. That is the only narrow gap, and it is a gap in *this* search.
- Verified to exist: CoRE (arXiv 2507.05269), EquiBench (arXiv 2502.12466), CONCUR (arXiv 2603.03683, concurrency code generation verified over all interleavings).
- **Construct threat:** many OS courses fix the tie-break by convention ("smaller PID first"), so real graders often *should* reject non-canonical answers.
- Full detail: `docs/PRIOR_ART_FINAL.md`; sources added to `research/literature_database.csv`.

### 3.3 The rebuilt study

- **Simulators:** `research/simulator/{traces,cpu_scheduler,concurrency_interleaver,validators}.py`. Non-preemptive FCFS/SJF/Priority plus RR(q) with the arrival/requeue ambiguity; mutex (non-re-entrant) and semaphores. Enumerators and independent rule validators agree on ~195k cross-checks.
- **Benchmark:** `research/benchmark/benchmark_v2.json`, 630 instances, seed 20261002, 7 splits (id, lexical_ood, long_trace, high_branching, rr_primitive, struct_mutex, struct_semaphore). Each instance has R1 (canonical), R2 (substantive alternative; for sync it is in a different Mazurkiewicz class), R3, I and I2 (invalid, matched to R2 on length, per-entity totals, and distance profile). Two-oracle label checks; 8 hand-checked instances.
- **Preregistration V2:** `docs/PREREGISTRATION_V2.md` (H1–H5; sha256 `d7b59abd…`). Deviations D1–D3 recorded.
- **Harness (built and dry-run, never run on real models):** `research/evaluation/{prompts,llm_client,experiments,metrics,analysis,provenance}.py`; experiments E1 (generation), E2 (judging with ablations: none / R1 / R3 / self / R1-reworded / invalid / irrelevant / mitigation note), E3 (ranking), E4 (scaling), E5 (OOD), noise floor.
- **Leakage audit result (the honest part):** the first audit **failed** (divergence position 0.591, reference similarity 0.608, local plausibility 0.602). Redesign (adjacent-pair filtering, profile matching, adversarial filtering with a disjoint auxiliary set) fixed scheduling (passes all attackers) but **concurrency still fails** the adjacent-pair (0.628) and bge-embedding (0.710) attackers, and the pooled embedding result fails (0.576). Thresholds (CI lower bound > chance + 0.05) were never moved. Recorded as D2/D3: **valid-vs-invalid claims are restricted to scheduling; the anchoring tests (H2/H3) remain valid on all splits** because they never use the invalid trace.

### 3.4 RSG status and open item

- **Decision (provisional): PAPER = MODIFY, PATENT = NO.** AGY's paper is killed. A narrow measurement paper ("do LLM judges anchor on a valid alternative reference beyond generic context effects?") may survive depending on Phase B.
- **Phase B (model runs) is PENDING**: 6 models (one per family: qwen3, llama3.1, gemma2, mistral, phi4-mini, olmo2; all downloaded), about 5.5k calls per model, ~6–9 GPU-hours. **The planner/user must decide whether to run it at all** now that the SSR pilot suggests the evaluator effect is modest.
- Docs: `docs/CLAUDE_FINAL_RESEARCH_AUDIT.md` (sections A–N; E–I are marked PENDING PHASE B), `docs/PREREGISTRATION_V2.md`, `research/docs/FORMAL_FRAMEWORK.md` (corrected), `scripts/reproduce_all.py`.
- **Open decision recorded in the audit:** keep concurrency in the reference tests only (current plan) or drop it entirely.

---

## 4. Project B — SSR pilot (`ssr-pilot`, uncommitted)

### 4.1 Question and design

*Does replacing canonical-reference matching with an independent semantic oracle materially change conclusions about LLM execution reasoning?* The statement "multiple valid traces exist, so reference matching is flawed" is explicitly **not** the claim.

- **24 worlds** (the statistical unit): 8 scheduling (FCFS/SJF/Priority/RR), 8 synchronisation (mutex/semaphore), 8 Banker's safe sequences. Four textbook cases; every second world carries a task constraint found by search so that it bites. \|V_task\| is 2–192, mostly < 20.
- **Traces derived from world semantics:** reference R = first task-valid trace in canonical enumeration order; valid alternatives = the rest of the task-valid set; invalid = samples from the transition system with **one rule relaxed**, kept only if the oracle rejects them, plus rule-valid-but-constraint-violating traces. After the K0 failure, each valid alternative is paired with the invalid trace of closest similarity profile to R (D1).
- **Oracle** (`research/ssr_pilot/oracle.py`): `evaluate_candidate(world, raw_text, truncated)` **has no reference parameter**; returns TRUE / FALSE (named witness) / UNVERIFIABLE; reference match and outcome equivalence come from a separate function. Scheduling/sync replay delegates to the earlier `validators.py`; Banker's replay is new.
- **Evaluators:** A_strict (string match), A_norm (parsed normalised trajectory), B (oracle TRUE; UNVERIFIABLE counts as invalid), C (B ∧ outcome-equivalent to R).
- **Variants** (matched renderings, never independent): v0 plain; v1 renamed + paraphrased; v2 reversed rows + reordered narration + table output.
- **Prompt does not state the reference convention**; it says any valid answer is accepted.
- **Models and settings:** qwen3:8b (think off), llama3.1:8b, gemma2:9b, mistral:7b-instruct; temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600, seeds 0–3. **24 × 3 × 4 × 4 = 1,152 generations, all complete.**
- **Attackers:** always-reference, random-valid (mechanical floor 1 − E[1/\|V\|] = 0.83), random-invalid, symbolic solver with a different tie-break; cheap evaluator proxies (distance-to-R, final-state-only); surface classifiers (length, char n-grams, listing-order, distance-to-R) under grouped CV and leave-one-structure-out.
- **Preregistered kill criteria** (`docs/research/SSR_PILOT_PREREG.md`, frozen by hash before outputs): K0 integrity, K1 non-trivial disagreement (pooled FRR ≥ 0.10, CI lower bound > 0.05), K2 survives normalisation (each variant), K3 survives attacker baselines (proxy balanced agreement < 0.95), K4 changes a model-level conclusion (stable reversal, significance change, or a model whose majority of "reference-wrong" outputs are valid), K5 more than one family. GREENLIGHT iff all pass; CONDITIONAL if K0–K3 pass and K4/K5 are inconclusive for power; KILL if K0–K3 fail or K4 fails with adequate precision (evaluator effect within ±0.05 for every pair).

### 4.2 Integrity checks that passed

- 309 tests: oracle verdict unchanged by any reference field; agreement with exhaustive enumeration; Banker's checked against an independently formulated brute force; textbook cases pinned; UNVERIFIABLE never reported as FALSE; format → parse → oracle round-trips in all variants; no prompt leaks its reference.
- **9 worlds hand-audited** against textbook rules (sched_04/06/08, sync_02/04/06, bank_04/06/08): all correct.
- **Dry-run identities hold:** always-reference scores 1.0 under every evaluator; the symbolic solver with a different tie-break scores B=1, A=0 (a perfect solver is "wrong" under reference matching); random-invalid scores B=0; random-valid FRR 0.851 vs floor 0.831.
- **K0 failed first** (distance-to-R classifier 0.663 [0.616, 0.711] > 0.65), was repaired by bank redesign without moving the threshold, and now passes (worst: distance-to-R 0.563 grouped CV). A modest residual remains.

### 4.3 Results (1,152 outputs; world-clustered 95% CIs)

| model | B semantic | A_norm | A_strict | C | FRR_norm | UNVERIFIABLE |
|---|---|---|---|---|---|---|
| qwen3:8b | 0.309 | 0.132 | 0.090 | 0.219 | 0.573 [0.348, 0.807] | 0.049 |
| gemma2:9b | 0.170 | 0.024 | 0.010 | 0.125 | 0.857 [0.611, 1.000] | 0.045 |
| mistral:7b-instruct | 0.076 | 0.017 | 0.007 | 0.066 | 0.773 [0.429, 0.971] | 0.194 |
| llama3.1:8b | 0.066 | 0.003 | 0.003 | 0.052 | 0.947 [0.800, 1.000] | 0.104 |
| **pooled** | **0.155** | **0.044** | 0.028 | 0.115 | **0.715 [0.511, 0.891]** | 0.098 |

(FRR = share of semantically valid outputs rejected by reference matching; with UNVERIFIABLE counted as valid, pooled FRR = 0.808.)

- **Disagreement** = 0.111 of outputs, all of it false rejection; reference matching has no false acceptances (R is valid).
- **By family:** Banker's FRR 0.954 (65 valid outputs); sync 0.622 (90); scheduling 0.417 (**24 valid outputs, all from qwen3**; gemma2, llama3.1 and mistral produced zero valid scheduling traces, e.g. two processes on the CPU at once, idling while ready).
- **By variant:** FRR 0.686 / 0.667 / 0.756; v2 (reversed listing + table output) has the highest model validity (0.224) and disagreement (0.169); the two differences are confounded.
- **Cheap proxies:** distance proxy 0.703 and final-state-only 0.643 balanced agreement; final-state-only accepts 46% of oracle-rejected outputs.
- **K4 (do conclusions change?):**
  - **Ranking identical** under both evaluators: qwen3 > gemma2 > mistral > llama3.1 (Kendall τ = 1.0).
  - Two pairs (qwen3 vs llama3.1 and vs mistral) are significant under the oracle only (Holm p 0.014/0.017 vs 0.078) but **unstable** under bootstrap (0.10, 0.13).
  - Only 11.6% of outputs that reference matching calls wrong are actually valid; no model has a majority.
  - **Magnitude does change:** the oracle roughly doubles qwen3's lead (0.128→0.243 vs llama; 0.115→0.233 vs mistral); for 4 of 6 pairs the evaluator-effect CI excludes 0, but direction never flips. For 5 of 6 pairs the CI exceeds ±0.05, so K4 fails *without adequate precision*.
- **Failure taxonomy:** Banker's errors are almost all `need_exceeds_work` (unsafe order) for every model; other profiles differ (mistral: overlapping segments 0.267; llama3.1: idle-while-ready 0.156; qwen3: policy violation 0.139). Descriptive only.
- **Descriptive quality note (not a tested claim; 24 outputs, one model, textbook P1=24 world dominates):** valid non-canonical scheduling outputs have lower mean waiting time (3.1) than canonical ones (11.2).

| K0 | K1 | K2 | K3 | K4 | K5 |
|---|---|---|---|---|---|
| pass | pass | pass | pass | **fail (inconclusive)** | pass (thinly) |

**Mechanical verdict: CONDITIONAL.** `docs/research/SSR_PILOT_DECISION.md` ends with exactly that word.

### 4.4 Defects and deviations (all disclosed in the docs)

- **D1** (before any LLM output): K0 failed → bank redesigned, threshold unchanged.
- **D2** (before any LLM output): defined K3 proxy fitting (strongest proxy, fitted to the oracle on other families) and "adequate precision" (±0.05).
- **D3a** (after first outputs): `validators.py` raised `ValueError` on a trailing `IDLE` after all processes finished; now FALSE (`idle_after_completion`) with a test.
- **D3b** (after first scoring): A_norm counted "reference + out-of-world token" as an exact match. It affected 5 of 1,152 outputs (mistral) and **had created the only apparent ranking reversal in the data** (τ 0.667); after the fix τ = 1.0. All K outcomes unchanged. **Lesson: at this sample size, "the evaluator reverses a ranking" can be manufactured by a handful of outputs.**
- The 12-output smoke test became part of the final run (identical call keys). K4(ii)'s stability rule, as preregistered, is strict for borderline Holm results; not changed.

---

## 5. What is and is not established (cross-project synthesis)

**Established (this session's evidence)**
1. AGY's claims are void; the corrected foundation is verified.
2. With an unspecified tie-break, reference matching rejects most valid model outputs (71.5% of valid outputs, robust to normalisation, rendering, family, and cheap proxies).
3. The independent oracle adds information that two cheap proxies lack.
4. A leakage-gated, hand-audited, test-covered pipeline exists (worlds, banks, oracle, attackers, analysis, manifests).

**Not established**
1. That evaluator choice changes any model ranking, significance conclusion, or failure attribution (K4 failed, inconclusive).
2. Anything about competent or frontier models: all four models are 7–9B and solve 15.5% of worlds.
3. Whether the disagreement survives when the convention is stated (no such arm was run).
4. Judge anchoring on a valid alternative reference (**RSG Phase B was never run**).
5. Anything novel: no novelty claim is made, and prior art makes "reference dependence of judges" a known effect.

---

## 6. Open decisions for the planner

1. **Pursue, pivot, or stop?** The pilot shows a real, robust disagreement that moves magnitudes but not conclusions. Is that worth a paper (a measurement/negative-result note) or only a follow-up?
2. **RSG Phase B:** run it (judging with reference ablations, 6 models, 6–9 GPU-hours), shrink it, or drop it? Its core hypothesis (anchoring) is the one most exposed to the prior art.
3. **Concurrency in RSG:** keep in reference tests only (current), or drop (it fails two leakage attackers).
4. **Branch hygiene:** commit/push `ssr-pilot`? Merge `rsg-audit` to `main`? (Both need user consent; no co-author line.)
5. **Which unit of evidence** to scale: more worlds, stronger models, or a stated-convention arm.

---

## 7. Candidate plans (with cost and kill rules)

| Plan | What | Cost | Success / kill |
|---|---|---|---|
| **A. Targeted SSR follow-up (recommended by the decision doc)** | Models that clear a competence floor (≥ 50% semantic-valid per family; stronger or reasoning-mode models, possibly via API, since local 7–9B cannot); ≥ 65 worlds; add a **convention-stated arm**; keep K4 definitions as preregistered | Needs new worlds (generator exists), banks (rerun K0), ~3× the pilot's calls; GPU/API cost depends on model choice | GREENLIGHT iff K0–K5 pass; **KILL if K4 fails with adequate precision** |
| **B. Run RSG Phase B as preregistered** | 6 models × ~5.5k judge calls | 6–9 GPU-hours, one model at a time | Tests anchoring; if H2 and H3 both fail → KILL; if H2 holds but the irrelevant/no-reference controls fail → "context-sensitivity" note |
| **C. Write up what exists as a short methods/negative-result paper** | Oracle-checkable OS trace worlds, the leakage-repair story, the "evaluator changes magnitude not direction" result, the bug-induced reversal as a cautionary example | Writing only; needs prior-art completion (systematic search) | Weak novelty; honest framing required |
| **D. Stop** | Archive both studies | none | Justified if neither follow-up is worth the cost |

**Cheapest informative next experiment:** the stated-convention arm alone, rerun on the existing 24 worlds with the same 4 models (≈ 288 calls per model, ~1 hour total). It isolates how much of the 71.5% is "nobody told the model the tie-break". Requires only a prompt change plus one new prereg entry.

---

## 8. File map

```
docs/
  CLAUDE_FINAL_RESEARCH_AUDIT.md        RSG audit (sections A–N; E–I pending Phase B)
  PREREGISTRATION_V2.md                 RSG prereg (hash d7b59abd…, deviations D1–D3)
  PRIOR_ART_FINAL.md                    verified prior-art review
  FINAL_RESEARCH_DECISION.md, PREREGISTRATION.md   AGY originals (SUPERSEDED banners)
  archive/PRIOR_ART_FINAL_AGY.md
  research/
    SSR_PILOT_PREREG.md  SSR_PILOT_REPORT.md  SSR_PILOT_DECISION.md  FULL_AUDIT_HANDOFF.md (this file)
research/
  simulator/{traces,cpu_scheduler,concurrency_interleaver,validators}.py
  benchmark/{generator,adversarial,audit_leakage}.py, benchmark_v2.json
  evaluation/{prompts,llm_client,experiments,metrics,analysis,provenance}.py
  docs/FORMAL_FRAMEWORK.md              corrected formal semantics
  archive_agy/                          AGY's invalid artifacts (README explains why)
  ssr_pilot/
    families.py oracle.py worlds.py bank.py render.py attackers.py scoring.py run_pilot.py analyze.py
    worlds/ (24 specs)  data/banks/  runs/ (1,152 raw outputs)  runs_dry/  manifests/  results/llm/  logs/
tests/research/test_semantics.py        RSG label tests
tests/ssr_pilot/{test_oracle,test_render,test_pipeline}.py
scripts/reproduce_all.py                RSG pipeline (benchmark → tests → leakage → mock/real runs → analysis)
```

**Commands**
- SSR pilot: `python -m research.ssr_pilot.worlds` → `...bank` → `...run_pilot --attackers` / `--models qwen3:8b,llama3.1:8b,gemma2:9b,mistral:7b-instruct` → `...analyze --tag llm`.
- RSG: `python scripts/reproduce_all.py` (mock dry run); add `--models …` for Phase B (needs the user's approval and a free GPU).
- Tests: `pytest tests/ssr_pilot tests/research -q`.

**Provenance hashes.** SSR prereg at launch `8db9eeaefc54303c…` (manifest `research/ssr_pilot/manifests/llm_20261002T230247.json`, git `f16448ca`, worktree dirty); current `0a2714b04126bbea…` (deviation D3 appended after launch); worlds index `331d41eb5117a5a1…`. RSG: prereg `d7b59abd…`, benchmark_v2 `890a7ea9…`, prompts `7a7e64bb…`.

---

## 9. Reliability notes for the planner

- **Prior art is from targeted searches and search-result summaries**, not a systematic literature review *(unverified beyond that)*. Claims of a "gap" mean "not found in this search".
- **Pilot power is low** (24 worlds, 4 models, CIs wide). The scheduling result rests on 24 outputs from one model.
- **K4's operationalisation was fixed before the data but is one of several reasonable choices;** its significance-stability rule compares a Holm-adjusted decision with a raw |t| > 2 in resamples and is strict for borderline cases.
- **The reference is defined by the world's own ordering** and the prompt does not state it. Part of the 71.5% is therefore an unspecified-convention effect, not a model flaw.
- **The invalid traces in the SSR bank are profile-matched** to valid ones, so specificity measured on the bank is harder than on natural errors; a small residual leak (0.563) remains.
- Two statements from the early session were corrected later: the pooled RSG leakage result fails on embeddings (not "passes"), and a "model run still in progress" message was a `pgrep` self-match. Neither affects results.
- Nothing in this document has been peer reviewed. The audit and the pilot were produced and checked by the same assistant, with tests, hand audits and disclosed deviations as the only independent checks.

---

## 10. Addendum — what happened after this document was written (2026-10-04)

1. **Stated-convention arm (run in a separate session).** Same 24 worlds and 4 local models, but the prompt states the tie-break convention. Pooled FRR_norm fell only from 0.715 to **0.625 [0.443, 0.816]**, so the discrepancy survives stating the convention (`results/stated_convention/REPORT.md`). Audit note: in 8 of the 12 constrained worlds a literal reading of the stated tie-break violates the task constraint, so there the prompt does not determine R; a world split (16 "determined" / 8 "underdetermined") was fixed in advance for the next phase.
2. **Competence mini-pilot (more capable models): not run; CLOSED as Decision C (inconclusive due to model/hardware constraints) on 2026-10-04** (`research/ssr_pilot/results/competence_pilot/REPORT.md`). Plan, frozen decision rubric, runner, analysis script and 24 tests were built (334 tests green). The GPU/RAM gate (poll every 5 min) polled 32 times between 18:45 and 21:20 on 2026-10-03 and never started a call: **RAM was short in all 32 polls** (2.8–6.2 GB available vs 9.6 GB required), the other project blocked 19 of them (job, resident model or GPU use), and from 19:35 the **GPU was idle but RAM alone** kept the gate closed for 13 polls. `gemma3:12b` downloaded; `qwen3:14b` failed digest verification; `phi4:14b` barely started. **Zero generations exist.** The frozen rubric applied to zero outputs returns C mechanically.
3. **AirLLM feasibility (user-requested): the planned 32B pilot was judged impractical on measured download and storage limits** (`airllm_feasibility.md`). The 65.5 GB Qwen2.5-32B-Instruct checkpoint downloads at 0.01–0.04 MB/s from the HuggingFace CDN (0.48 MB/s from the best mirror = 38 h) and the disk need (~83 GB) exceeds the 71 GB free. **AirLLM itself was never successfully run**: it was installed with `--no-deps` in a throwaway environment, `import airllm` fails there with `ModuleNotFoundError: No module named 'tqdm'`, no model was loaded, and no generation completed. **Still untested:** AirLLM runtime and speed (the ~6.5 h batched figure is a projection), compatibility with Qwen2.5-32B-Instruct, peak VRAM/RAM, batched generation and sampling.
4. **Status of the competence question: open.** Whether the discrepancy survives with materially more capable models is unknown. The 0.625 result stands for the four weak local models only. Remaining routes (not pursued): a hosted-API model (needs a key), or hardware with more free RAM and a working download path.
5. **Repo hygiene:** nine exploration-phase documents (`docs/{RESEARCH_OPPORTUNITY_MATRIX, FROM_SCRATCH_RESEARCH_OPTIONS, PAPER_CONCEPTS, TOP_5_RESEARCH_DIRECTIONS, RECOMMENDED_RESEARCH_PROGRAM, RESEARCH_PROGRAM_DECISION, NOVELTY_GAP_REPORT, CONTRADICTION_MAP, EVALUATION_BLIND_SPOTS}.md`) were deleted from the working tree. All are committed on `main`; restore with `git checkout -- docs/`. Nothing is committed on `ssr-pilot`.
