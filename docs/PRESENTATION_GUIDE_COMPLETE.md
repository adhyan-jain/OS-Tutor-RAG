# Presentation Guide: RCR research paper (detailed) + OS Tutor RAG chatbot (concise)

Updated 2026-10-24 after the Claude-family follow-up.

- **Part A: the research paper (Reference-Choice Robustness, RCR)**, detailed. Start with the cheat sheet (§0), then §8.4 (newest result), §12 (talk track), §15 (hostile questions).
- **Part B: the RAG chatbot**, concise (one page plus a two-minute track). The full RAG guide is `docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md`.

| Time you have | Read |
|---|---|
| 10 minutes | A §0 cheat sheet, A §8.4, A §12 talk track, A §15.x, then Part B in full |
| An evening | All of Part A in order; rehearse A §12 aloud; skim Part B |

---

# Part A: The research paper (Reference-Choice Robustness, RCR), detailed

> This is **Part A**, the research paper, covered in depth. **Part B** (the RAG chatbot) is deliberately short; its full version is `docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md`.

**Audience:** Adhyan, who must explain the second research track in this repo end to end and survive a hostile examiner.
**Status of this guide:** updated 2026-10-24 (evening) after the Claude-family follow-up (§8.4); all other numbers are from the repo's own files. Every number below is tied to a file; where I recomputed something myself it says "recomputed". Where the repo contradicts itself, that is flagged in §16 rather than smoothed over.
**Not covered here:** the RAG chatbot, which is Part B (short) and `docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md` (full). §13 explains how the two connect.

> The one-sentence version: **in OS tasks where many different answers are all correct, grading a model by matching it to one "gold" answer hides real differences between models, and which answer you pick as gold changes the leaderboard. A checker that replays the answer through the rules does not have that problem.**

---

## 0. Cheat sheet (memorise this page)

| Thing | Value | Where it comes from |
|---|---|---|
| Tasks ("worlds") | 24 = 8 CPU scheduling + 8 synchronization + 8 Banker's | `research/ssr_pilot/worlds/*.json` |
| Models | qwen3:8b (think off), gemma2:9b, mistral:7b-instruct, llama3.1:8b | `run_pilot.py` `MODELS` |
| Generations | 24 worlds × 3 surface variants × 4 seeds × 4 models = **1,152** | `runs/*.jsonl` |
| Sampling | temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600, seeds 0–3 | `run_pilot.py` `SETTINGS` |
| Valid answers per task, \|V(x)\| | 2 … 192 (median small); e.g. sched_01 = 6, bank_01 = 16, sync_06 = 192 | `core/valid_space.py` (recomputed) |
| Oracle (E3) score per model | qwen3 **30.9%**, gemma2 17.0%, mistral 7.6%, llama3.1 6.6% | `rcr_summary.json` |
| E2 (match one reference) score, uniform reference | qwen3 4.1%, gemma2 1.7%, llama3.1 0.5%, mistral 0.5% | `extended_analysis.json` `score_context` |
| Reference vectors sampled | **50,000** from ∏ V(x_k) | `rcrc/analysis.py` |
| Kendall τ_b of E2 vs canonical | **0.618 ± 0.351** (n = 49,913 valid; 87 degenerate) | `rcr_summary.json` |
| Pairwise winner reversal, E2 | **17.56%** (Monte Carlo); 17.18% (vectorised); **17.15%** (exact DP) | `rcr_summary.json`, `extended_analysis.json`, `exact_dp_analysis.json` |
| Oracle ranking recovered, E2 / E1 | **13.63% / 2.86%** | `rcr_summary.json` |
| Oracle finds qwen3 > llama3.1 and qwen3 > mistral | Holm p = **0.0126**, **0.0175**, same in all 50,000 draws | `extended_analysis.json` |
| E2 detects those two differences | 5 of 50,000 draws each (**99.99% missed**); E1: 0 of 50,000 | `extended_analysis.json` |
| Gap that E2 keeps | 12–18% across pairs (15.1% and 15.8% for the two separated pairs) | `kref_attenuation.json` |
| Law | E[E2] = E3 / \|V(x)\| (r = 1.000, 42 cells) — near-identity | `kref_attenuation.json` |
| Reversal mass in pairs the oracle cannot separate | **85.6%** | `extended_analysis.json` |
| Remedy | match-any over k references: k=5 → 48–57% detection, k=25 → 84–88% | `kref_attenuation.json` |
| Stated-convention control | FRR_norm 0.625 [0.443, 0.816] (baseline 0.715 [0.511, 0.891]) | `stated_convention/analysis.json` |
| Gemma 3 12B | n_valid = 42, FRR_norm 0.619 | `competence_pilot/analysis.json` |
| Pilot preregistered verdict | **CONDITIONAL** (K4 failed without adequate precision) | `docs/research/SSR_PILOT_DECISION.md` |
| Second domain (Blocks World) | did **not** replicate behaviour: floor effect, H2 rejected (4.63% < 8%) | `paper/RCR_EMPIRICAL_DRAFT.md` §6 |
| **Claude-family arm (new)** | haiku/sonnet 4.5 and 5.5, 288 generations each (1,152), headless CLI, no tools, thinking off | `runs_claude/*.jsonl` |
| E3 validity, Claude arm | sonnet-5.5 **99.3%**, haiku-5.5 98.3%, sonnet-4.5 79.9%, haiku-4.5 73.3% | `rcrc_claude/hypotheses.json` |
| H1 floor | **supported** (4 of 4 above 30%) | same |
| H2 detection loss | **supported**: E2 detects the 4 oracle-separated pairs in **3.0%** of 50,000 draws (1.7–4.3% per pair) | `rcrc_claude/extended_analysis.json` |
| H3 canonical inflation | **supported**: CIF 2.26–3.30 (all > 1); "models differ" test is weak by construction | `hypotheses.json` |
| H4 ranking distortion > 1.5x | **NOT supported** (max 1.43x) | `hypotheses.json` |
| Claude arm reversal / tau_b | uniform-reference E2: **26.9%** / **0.472**; recovery 22.6% | `extended_analysis.json` |
| Claude arm k-reference | k=5: 36–44% detection; k=25: 51–69% | `kref_attenuation.json` |
| Tests | **1,304 passed** (my run, 2026-10-24, ~30 s) | `pytest tests -q` |

**The honest verdict to keep in your head:** an empirical measurement-and-methodology paper (not conceptual; the only analytic part is the attenuation identity). Workshop-ready, TMLR the realistic journal target; "publishable" cannot be promised. Main-track not ready (`paper/RCR_EMPIRICAL_READINESS.md`). The Claude-family follow-up removes the "models are at the floor" objection for the main findings, but it is still one 24-task benchmark. Its strength is that every number is recomputable and its limits are written down. Its weakness is that it is one 24-task benchmark with four weak models.

---

## 1. The problem in plain language

### 1.1 Why a benchmark has a "gold answer"

Most benchmarks grade a model by comparing its output with one stored correct output, the **reference** (gold answer). That is fine when there is one right answer ("what is 17 × 3?"). It is a problem when there are many.

### 1.2 OS tasks are full of "many right answers"

Take the very first world in this repo, `sched_01` (the exact prompt is in §4.2): three processes P1 (burst 24), P2 (burst 3), P3 (burst 3), all arriving at time 0, non-preemptive FCFS. The prompt says ties may be broken any way. All six orderings are legal:

```
0: P1 0-24, P2 24-27, P3 27-30      3: P2 0-3, P3 3-6, P1 6-30
1: P1 0-24, P3 24-27, P2 27-30      4: P3 0-3, P1 3-27, P2 27-30
2: P2 0-3, P1 3-27, P3 27-30        5: P3 0-3, P2 3-6, P1 6-30
```

(printed from `build_valid_space` — recomputed). The benchmark builder must pick one as gold. The code picks the first in enumeration order (`valid_space.py`: `canonical_ref = task_valid[0]`), i.e. index 0.

Now qwen3:8b answers `TRACE: P1 0-24, P2 24-27, P3 27-30`. That is index 0, so it matches and is "correct". gemma2:9b might have given any other correct ordering; it would be marked **wrong** even though it is just as right. Same task, same quality of reasoning, different mark. That is the whole idea of the paper, and it is a measurement problem, not a model problem.

### 1.3 A real example from the data (not a toy)

World `bank_01` is the textbook Banker's example (5 processes, 3 resource types). There are **16** valid safe sequences; the canonical (index 0) is `P1, P3, P0, P2, P4`. A real gemma2:9b output (from `runs/gemma2_9b.jsonl`) was:

```
TRACE: P1, P3, P0, P4, P2
```

It is a valid safe sequence (index 1). I scored it with the repo's evaluators against all 16 references (recomputed with `core/evaluators.py`):

| Evaluator | Passes under how many of the 16 possible references | Meaning |
|---|---|---|
| E1 exact string | 1 / 16 | passes only if the gold happens to be this exact string |
| E2 normalised | 1 / 16 | same, after parsing and normalising |
| E3 executable validator | **16 / 16** | replays the answer through the Banker's rules; the reference is never consulted |

So whether this answer is "right" depends on a coin with 16 sides if you grade by reference matching. By the validator it is right under every choice.

### 1.4 What the paper actually asks

> Hold the tasks, the model outputs and the evaluator fixed. Replace the gold reference by *another valid* trajectory. How much do the benchmark's **conclusions** change (model scores, rankings, who wins a pairwise comparison, whether a difference is statistically significant)?

Because the repo enumerates **every** valid trajectory (V(x)) and has a validator that gives the true verdict, the true ranking is known exactly, and reference choice can be varied as a controlled experimental factor over all possibilities. That is the methodological contribution. It is *not* the claim that reference choice matters in general: that is already published (Casola et al. 2025; Jeong et al. 2026; also Kulshreshtha et al. 2026, arXiv 2610.03825, per `paper/RCR_THEORY_CONTRIBUTION_DECISION.md`). Never say "first".

---

## 2. Formal definitions, mapped to code

### 2.1 Objects

| Symbol | Meaning | Code |
|---|---|---|
| x | a task ("world") | `worlds/*.json`, loaded by `worlds.load_worlds()` |
| V(x) | the **complete** set of trajectories that obey the system's transition rules **and** the task's constraints | `families.enumerate_rules` then filter `violated_constraints`; wrapped in `core/valid_space.build_valid_space` |
| R_k ∈ V(x_k) | the reference chosen for task k | `core/references.get_references` |
| **R** = (R_1…R_24) ∈ ∏ V(x_k) | a *benchmark reference vector* (one gold answer per task) | sampled in `rcrc/analysis.py` and `rcr_extended_analysis.sample_reference_vectors` |
| R_canonical | index 0 of every V(x_k) ("Draw 0") | `analysis.py` |
| y_{m,k} | model m's output on task k (12 generations per (model, world): 3 variants × 4 seeds) | `runs/*.jsonl` |

`V(x) = { y : RulesCheck(x, y) ∧ ConstraintsCheck(x, y) }` (PAPER_FINAL §2.1). Each member is independently re-verified in `build_valid_space` by `rules_check` and `violated_constraints`, and the oracle delegates scheduling/sync replay to `research/simulator/validators.py`, which was written separately from the enumerators (SSR_PILOT_PREREG §7.3). The Banker's family has an independent `BankerSolver` + `validate_banker`, cross-checked against brute-force permutation search (PAPER_FINAL §10.4).

### 2.2 The three evaluators (plus one unused)

All are scored in `rcrc/analysis.py` / `core/evaluators.py` (and vectorised in `rcr_extended_analysis.build_score_tensors`).

| ID | Name | Rule (one line) | Needs a reference? |
|---|---|---|---|
| **E1** | Canonical exact | whitespace-squashed answer text equals the formatted reference text | yes |
| **E2** | Normalised match | parsed trajectory, after normalisation (scheduling: fill gaps with IDLE, merge adjacent same-process segments), equals the reference; **and** the answer mentions no entity outside the world (deviation D3(b)) | yes |
| **E3** | Executable semantic validator ("oracle") | parse → replay through the rules → check constraints; TRUE / FALSE / UNVERIFIABLE; UNVERIFIABLE counts as not valid | **no** (the function has no reference parameter) |
| E4 | Observational equivalence | same observable outcome as the reference | yes (defined, not used in the headline) |

The no-reference property of E3 is enforced structurally: `core/oracle.assert_oracle_has_no_reference_parameter()` inspects the signature of `evaluate_candidate`, and `verify_oracle_reference_invariance` checks there is no side-channel. `compare_to_reference` is a separate function that never feeds back into the semantic verdict (`research/ssr_pilot/oracle.py` docstring). **Consequence you must be able to say aloud: E3's τ_b = 1.000 and 0% reversals are true by construction. They are not a finding.** The finding is the *cost of not using E3*.

Oracle verdict values (`oracle.evaluate_candidate`): `unparseable` → UNVERIFIABLE; entity not in the world → UNVERIFIABLE (`unknown_entity`); incomplete trace that is **not** truncated → FALSE (`rule:incomplete`); truncated with no visible violation → UNVERIFIABLE; any violated rule → FALSE with a named witness (e.g. `rule:need_exceeds_work`, `rule:mutual_exclusion_violation`); constraint violated → FALSE; else TRUE.

### 2.3 The metrics (exact formulas)

Let S_m(E | **R**) = (1/24) Σ_k E(y_{m,k} | R_k), where E(y_{m,k} | R_k) is the average pass over that model's 12 generations on world k (that is why every per-world score is a multiple of 1/12).

1. **Model score under a reference vector.** As above. Code: `rcr_extended_analysis.draw_world_scores` then `.mean(axis=1)`.
2. **Rank stability, Kendall τ_b.** τ_b between the 4-vector of scores under a random **R** and the 4-vector under **R_canonical** for the *same* evaluator. Tie-aware (`scipy.stats.kendalltau(variant='b')`). Code: `ranking_metrics.compute_kendall_tau_scores` (loop) and `rcr_reference_distribution_sensitivity.fast_kendall_tau_b_matrix` (vectorised).
   Degenerate policy D5: both vectors constant → 1.0; exactly one constant → NaN, excluded and counted (`kendall_tau_n_degenerate_draws`).
   **Trap:** for E2 the anchor is the *E2 canonical* vector. Under the canonical reference E2's ordering equals E3's ordering (qwen3 > gemma2 > mistral > llama), so "relative to canonical" and "relative to oracle" coincide. That is why the canonical reference is a favourable special case.
3. **Pairwise winner reversal.** For a model pair (A,B), over two independent reference vectors, probability that A wins strictly under one and B strictly under the other:
   P(rev) = 2·p₊·p₋ where p₊ = P(S_A > S_B), p₋ = P(S_B > S_A) over uniformly random **R** (formal method note §5; code counts `n_win_A * n_win_B / C(n,2)` in `ranking_metrics.compute_pairwise_win_matrix`). The headline "17.56%" is the mean over the 6 pairs. **Ties do not count as a win for anyone**, so a pair that ties 25% of the time has a smaller reversal rate than its instability suggests (see §6.4).
4. **Oracle-ranking recovery.** Fraction of draws where the evaluator's induced ordering equals the E3 ordering, *tie-aware*: for every model pair, sign(S_A − S_B) must equal the oracle's sign, ties included (`ranking_metrics.rankings_are_identical_tie_aware`). A descriptive, point-estimate measure, not "share of well-supported orderings overturned" (PAPER_FINAL §4.5).
5. **Detection.** For each draw, a world-level paired sign-flip test per model pair with Holm correction; compare the decision with E3's decision (§6).
6. **Evaluator effect on a gap.** Per pair, oracle gap minus expected E2 gap under a uniform reference, world-level paired bootstrap (5,000 resamples).
7. **Attenuation law, k-reference power, inverse-|V| correction** (§7).

### 2.4 Hand-checkable toy for the reversal formula

From `research/docs/RCR_FORMAL_METHOD_NOTE.md` §3 (verified by hand). Two tasks, two models, each task has two references.

| Draw (r₁, r₂) | D₁ | D₂ | Margin M = (D₁+D₂)/2 | Prob |
|---|---|---|---|---|
| (r₁₁, r₂₁) | +1.0 | −0.5 | +0.25 | 0.25 |
| (r₁₁, r₂₂) | +1.0 | +0.5 | +0.75 | 0.25 |
| (r₁₂, r₂₁) | −0.5 | −0.5 | −0.50 | 0.25 |
| (r₁₂, r₂₂) | −0.5 | +0.5 | 0.00 | 0.25 |

p₊ = 0.50, p₋ = 0.25, p₀ = 0.25, so P(reversal) = 2 × 0.50 × 0.25 = **0.25**. Model A "wins on average" (E[M] = +0.125) yet the winner flips one time in four depending on which references were drawn. Use this on a whiteboard.

---

## 3. The benchmark: 24 OS "worlds"

Source: `research/ssr_pilot/worlds.py`, `worlds/*.json`; sizes recomputed from `build_all_valid_spaces`.

| Family | Worlds | What is being asked | |V(x)| per world |
|---|---|---|---|
| scheduling | sched_01…08 | Build the Gantt trace for FCFS, SJF, Priority (non-preemptive) or Round-Robin (quantum q); ties may be broken any way | 6, 3, 6, 2, 4, 2, 6, 6 |
| sync | sync_01…08 | Produce an interleaving of thread operations (mutex lock/unlock or semaphore wait/signal) that respects mutual exclusion / semaphore counts / program order; a "before" constraint on half the worlds | 6, 114, 168, 4, 18, 192, 5, 192 |
| banker | bank_01…08 | Produce a safe completion order (each process's remaining need ≤ Work; on completion it releases its allocation) | 16, 12, 48, 3, 90, 2, 54, 12 |

Textbook cases are pinned: sched_01 (P1=24, P2=3, P3=3), sched_07 (same, RR q=4), sync_01, bank_01 (Silberschatz). Every second world carries one task constraint (precedence, deadline, "before") that excludes part of the rule-valid set, found by search so it bites. Nine worlds (3 per family) were verified by hand against textbook rules (SSR_PILOT_REPORT §4).

**Why the |V| spread matters** (this explains almost everything in §7): E2 under a uniform reference passes a valid answer with probability 1/|V(x)|. A task with |V| = 2 contributes 50% of its E3 signal; a task with |V| = 192 contributes 0.5%.

**Valid vs rule-valid.** `n_rules` = rule-valid traces; `n_valid_task` = those that also satisfy the task constraint. Only the latter is V(x). Example: sync_02 has 210 rule-valid but 114 task-valid traces.

**Surface variants** (same world, different rendering; never treated as independent observations): v0 plain; v1 renamed entities + paraphrased narration; v2 rows listed in reverse, rules after data, answer in table format (`render.VARIANTS`).

**Benchmark integrity gate K0 (the "leak" check).** The first trace bank leaked: distance-to-reference separated valid from invalid at 0.663 [0.616, 0.711] (> 0.65 limit). The bank was redesigned (valid alternatives paired with invalid traces of closest similarity profile) before any LLM spend and the threshold was **not** changed. After repair the worst classifier (distance_to_R, grouped CV) is 0.563 [0.524, 0.599] (SSR_PILOT_REPORT §4).

---

## 4. Exactly what was sent to the models, and how it was scored

### 4.1 Plumbing

`research/ssr_pilot/run_pilot.py`: for each (world, variant, seed) it renders a prompt (`render.render_variant`) and posts it to Ollama `/api/chat` as a single user message, `stream=False`, `options = {temperature 0.7, top_p 0.95, num_ctx 4096, num_predict 600, seed}`; for qwen3 `think=false`. Each call is appended to `runs/<model>.jsonl` with the prompt SHA-256, raw response, `done_reason` (`length` = hit 600 tokens) and token counts. A record key is a hash of (model, prompt hash, seed, settings), so runs are resumable and deduplicated. One record looks like (real, first record in the file):

```json
{"model":"gemma2:9b","world":"sched_01","variant":"v0","seed":0,
 "response":"TRACE: P2 0-3, P3 0-3, P1 3-27  \n","done_reason":"stop",
 "eval_count":26,"prompt_eval_count":258,"latency_s":8.05}
```

No system prompt, no few-shot examples, no tool access, no reference in the prompt (a test asserts no prompt contains its world's reference).

### 4.2 A real prompt (sched_01, variant v0), verbatim

```
Here is a CPU scheduling exercise.

Policy: non-preemptive First-Come-First-Served. Whenever the CPU is free it runs, to completion,
a ready process with the earliest arrival time. A process is ready once the current time is at or
after its arrival time. If several ready processes tie on the selection criterion, any one of them
may be chosen. If nothing is ready, the CPU idles until the next arrival.

Processes:
| Process | Arrival | Burst | Priority |
|---|---|---|---|
| P1 | 0 | 24 | 3 |
| P2 | 0 | 3 | 3 |
| P3 | 0 | 3 | 3 |

Write the whole trace on one line that starts with 'TRACE:', as comma-separated entries NAME START-END
in time order, using IDLE for idle CPU time (for example: TRACE: A 0-3, IDLE 3-4, B 4-6).

If several choices are allowed at some point, any of them may be chosen; more than one valid answer
can exist, and any valid answer is accepted. Reply with the trace only, with no explanation.
```

Note the last paragraph: the prompt tells the model that any valid answer is accepted. The reference-matching evaluators do not honour that sentence. That tension is the paper's point.

### 4.3 Real outputs for that prompt (seed 0, v0) and how each evaluator scores them

I scored these with `core/evaluators.evaluate_with_reference` against all 6 references (recomputed):

| Model | Raw output | E1 pass count /6 | E2 pass count /6 | E3 | Why |
|---|---|---|---|---|---|
| qwen3:8b | `TRACE: P1 0-24, P2 24-27, P3 27-30` | 1 | 1 (ref 0) | **TRUE** (all 6) | valid; equals canonical |
| gemma2:9b | `TRACE: P2 0-3, P3 0-3, P1 3-27` | 0 | 0 | FALSE | P2 and P3 overlap in time (`overlapping_segments`) |
| llama3.1:8b | `TRACE: P2 0-3, P1 3-27, IDLE 27-30, P3 30-33` | 0 | 0 | FALSE | idles while P3 is ready (`idle_while_ready`) |
| mistral:7b-instruct | ` TRACE: P1 0-24, IDLE 24-3, P2 3-6, …` | 0 | 0 | FALSE | `rule:overlapping_segments` (segment `24-3` runs backwards in time) |

This is the typical picture in the data: most failures are *genuine* invalidity that every evaluator catches. The disagreement lives in a thin slice: **179 of 1,152 outputs (15.5%) are semantically valid; only 51 of those match the canonical reference**, so 128 / 179 = **71.5% of valid outputs are rejected by canonical matching** (the pilot's FRR_norm; `SSR_PILOT_DECISION.md`, and I recomputed 179 and 51).

### 4.4 Real prompt and output, Banker's

`bank_01` prompt (verbatim, v0): "A process can run to completion only if its remaining need (Max − Allocation) is at most the currently available (Work) amount of every resource type. When it completes it releases its whole allocation, which is added to Work. Work starts equal to Available. A trace is the order in which all processes complete; every process must complete exactly once." followed by the Available vector and the 5-row Alloc/Max table and the same "any valid answer is accepted" sentence. Output and scores: §1.3.

### 4.5 The stated-convention prompt

`render_variant(..., stated_convention=True)` adds exactly one sentence (diff recomputed for sched_01):

```
+ Convention for tie-breaking: If several ready processes tie on the selection criterion, choose
  the process listed earliest in the Processes table (e.g. P1 before P2 before P3).
```

Used for the stated-convention arm (1,152 generations) and the competence arm (576 generations).

### 4.6 What the pipeline does with a record (scoring path)

1. `evaluate_oracle(world, raw, truncated=done_reason=="length", shown2canon=s2c)` → TRUE/FALSE/UNVERIFIABLE. `s2c` maps the shown (renamed) entity names back to canonical names for variant v1.
2. `F.parse(world, raw, s2c)` → parsed steps (or None). The parser takes the region after `TRACE:`, tolerates arrows/tables, and drops out-of-world tokens (hence rule D3(b), §9).
3. For each reference r in V(x): E2 pass = `normalize(steps) == normalize(r)` **and** `reason != "unknown_entity"`; E1 pass = squashed region == squashed formatted reference text; E3 pass = verdict TRUE (same for all r).
4. Aggregate per (world, reference, model) as mean over the 12 generations.
5. Draw reference vectors (§5), compute the metrics.

Efficiency note: `rcr_extended_analysis.build_score_tensors` builds a tensor `scores[e][world, ref, model]` once; each of the 50,000 draws is then just an index lookup, which is why 50,000 draws × 20,000 sign flips is feasible (~2.5 min per the Reproducibility doc).

---

## 5. How the headline numbers are produced, step by step

### 5.1 Drawing 50,000 reference vectors

- Main (legacy loop) analysis: `rcrc/analysis.py`, `np.random.RandomState(20261005)`; for each of 50,000 draws, for each of the 24 worlds, choose one reference index uniformly among that world's references; score the 4 models. "Draw 0" = canonical vector (index 0 everywhere) is evaluated separately and not counted among the 50,000.
- Independent vectorised re-implementation: `rcr_extended_analysis.py`, `np.random.default_rng(20261016)`, `rng.integers(0, |V_k|)` per world per draw. Different random stream; used to cross-check and for the inferential analyses.
- Exact value: `rcrc/exact_margin_distribution.py` + `rcr_exact_dp_analysis.py` compute the exact distribution of the benchmark margin M_AB by dynamic-programming convolution across the 24 independent tasks (no sampling), then reversal = 2p₊p₋. Result **0.1715180** (`exact_dp_analysis.json`).

Reconciling the reversal figures you may be asked about (all E2, all 50,000 draws; `research/docs/RCR_EVIDENCE_AUDIT_AND_CORRECTIONS.md` §3):

| Figure | Source | What it is |
|---|---|---|
| 18.61% | old PAPER_FINAL | **bugged** (7 mistral outputs wrongly counted as E2 matches; see §9 D9) |
| **17.56%** | `rcr_summary.json` | corrected, sequential Monte Carlo, seed 20261005 (headline) |
| 17.23% | `reference_distribution_sensitivity.json` | uniform grid point, seed 20261007 |
| 17.18% | `extended_analysis.json` | vectorised, seed 20261016 |
| **17.15%** | `exact_dp_analysis.json` | exact DP (the population value) |

The audit doc shows MC − exact = +0.00025 for the six-pair mean, z = +0.28 under the joint-covariance standard error (0.000906; variance inflation factor 1.62 because the six pairs share the same draws). So the Monte Carlo estimates are noise around the exact value. **The honest way to quote it:** "about 17%; exact value 17.15%".

### 5.2 τ_b = 0.618 ± 0.351

For each draw, take the 4-vector of E2 scores and compute τ_b with the canonical 4-vector. Mean over draws that have a defined τ_b: 0.6177 (SD 0.3505, n = 49,913); the "±" is the **standard deviation across draws, not a standard error**. The "SE = 0.0016" in Table 1 is the standard error of the *mean τ_b* (SD/√n = 0.3505/√49,913). It is tiny because there are 50,000 draws; it says nothing about generalising beyond this benchmark. A common slip is to quote it as if it were uncertainty of the finding.

Degenerate draws: 87 of 50,000 (0.17%) have one constant vector (e.g. all four models score 0 under that reference vector, while the canonical vector is non-constant), so τ_b is undefined and they are excluded (D5). Including them as 0 would change the mean 0.6177 → 0.6167.

### 5.3 Winner reversal 17.56%

For each of 6 pairs count draws with S_A > S_B (n_A), S_B > S_A (n_B); reversal = n_A·n_B / C(50,000, 2); average over pairs. Per-pair values (from `near_tie_decomposition`, vectorised stream): gemma2–llama 20.6%, gemma2–mistral 25.4%, gemma2–qwen3 14.6%, llama–mistral 27.7%, llama–qwen3 7.9%, mistral–qwen3 6.9%.

### 5.4 Oracle recovery 13.63% (E2) and 2.86% (E1)

Fraction of the 50,000 draws in which the sign of every one of the 6 pairwise score differences matches the oracle's (tie-aware): E2 6,814/50,000 = 13.63% [13.33%, 13.93%]; E1 1,430/50,000 = 2.86%. Recomputed on the vectorised draws: 13.50%. Why so low? Under E2 a random reference gives every model a score near 0, so **ties and flips are everywhere**: in 47.4% of draws at least one pair is tied (recomputed), and a tie never counts as matching the oracle's strict ordering.

### 5.5 Worked draw (to make it concrete)

From the vectorised sampler (seed 20261016), draw index 5 (recomputed): reference indices were e.g. bank_01 → 10, sched_01 → 3, sync_03 → 106 …. Under this reference vector the E2 scores are gemma2 0.35%, llama 0%, mistral 0%, **qwen3 0%**. The best model (oracle: 30.9%) scores zero and ranks tied-last; τ_b with the canonical ordering = 0.236. That is what "reference choice changes the leaderboard" looks like on one draw. Across draws, E2 ranks qwen3 strictly first in 86.2% (recomputed), so the typical error is not "qwen3 falls to last" but "the mid-ranked models shuffle and many ties appear".

### 5.6 What the canonical reference does

Under R_canonical the E2 ordering equals the E3 ordering (Table 1 note). The benchmark as normally built (one gold per task, first in enumeration order) therefore *looks fine*. The instability only appears when you notice that other valid golds were possible. This is both the strength (a clean thought experiment) and the standing objection (§15 Q6).

---

## 6. Detection: what reference matching fails to find

All in `rcr_extended_analysis.py`; artifact `extended_analysis.json`; seeds 20261016 (draws), 20261017 (sign flips, bootstrap).

### 6.1 The test

Statistical unit = the **world** (N = 24); the 12 generations per (model, world) are averaged first, then pairs are compared world by world.

1. For a model pair and a draw: d_w = score_A(w) − score_B(w), w = 1…24 (multiples of 1/12).
2. Statistic T = |mean(d)|.
3. Null: sign of each d_w is exchangeable. Draw 20,000 random ±1 sign vectors, compute T* for each; p = (#{T* ≥ T} + 1) / 20,001. Differences are scaled to integers so every comparison is exact in float32 (`sign_flip_pvalues`).
4. Holm step-down correction over the 6 pairs (`holm_rows`), α = 0.05.
5. Decision ∈ {A significantly better, B significantly better, not significant}.

Why not McNemar on all 288 cells? That treats the 12 nested generations per world as independent (pseudoreplication). It was used in an early analysis and withdrawn (D1).

### 6.2 Results (all 50,000 draws)

| Pair | E3 (oracle) Holm-adj p | E3 decision | E2 mean adj p | E2 misses oracle |
|---|---|---|---|---|
| gemma2 – llama | 0.1998 | n.s. | 0.991 | – |
| gemma2 – mistral | 0.1998 | n.s. | 0.991 | – |
| gemma2 – qwen3 | 0.1998 | n.s. | 0.946 | – |
| llama – mistral | 0.7948 | n.s. | 0.995 | – |
| **llama – qwen3** | **0.0126** | qwen3 better | 0.929 | **99.99%** |
| **mistral – qwen3** | **0.0175** | qwen3 better | 0.928 | **99.99%** |

(E1 misses both in 100%.) E3's decision is identical in all 50,000 draws (asserted in code: `assert np.all(decisions["E3_SEMANTIC_ORACLE"] == e3_dec[None,:])`). E2 detects each difference in 5 of 50,000 draws; there are no wrong-direction significant results and one spurious significant result (E2, gemma2 vs qwen3). **The failure is a loss of power, not a sign reversal.** The raw (pre-Holm) p-values implied are ≈ 0.0021 and ≈ 0.0035 (derived: adj = 6·p₁ and 5·p₂ — my arithmetic, not stored in the artifact).

Guardrail (audit doc §4.3): non-significance is **not** equivalence. Those 49,995 misses are a statement about statistical power under attenuation.

### 6.3 Is the evaluator effect real? (Table 4)

"Significant under E3, not under E2" is not itself evidence of a difference between evaluators (Gelman's classic point). So the effect on each gap is tested directly: per world, (oracle gap) − (E2 gap averaged over a uniform reference); 5,000 world-level bootstrap resamples.

| Pair | Oracle gap | E2 expected gap | Effect [95% CI] | Gap kept by E2 |
|---|---|---|---|---|
| gemma2–llama | +0.104 | +0.012 | +0.092 [+0.018, +0.176] | 12% |
| gemma2–mistral | +0.094 | +0.012 | +0.081 [+0.004, +0.170] | 13% |
| gemma2–qwen3 | −0.139 | −0.024 | −0.115 [−0.231, −0.006] | 18% |
| llama–mistral | −0.010 | +0.000 | −0.011 [−0.060, +0.032] | −2% (spans 0) |
| llama–qwen3 | −0.243 | −0.037 | −0.206 [−0.329, −0.090] | 15% |
| mistral–qwen3 | −0.233 | −0.037 | −0.196 [−0.321, −0.073] | 16% |

CI excludes 0 for 5 of 6 pairs. The sign of the expected gap never changes, except the −2% pair where the oracle gap is only −0.010.

### 6.4 Near-ties: where reversals really live (Table 5)

85.6% of E2's reversal mass is in the 4 pairs that E3 itself cannot separate (78.6% for E1). Mean reversal 22.1% there vs 7.4% in the 2 separated pairs. The suspicion "it's just noise between indistinguishable models" is **largely right**, and the paper says so. Two qualifications: "not separated" is absence of evidence at N = 24, not equality; and in the separated pairs E2's winner still opposes the oracle's in 3.7–4.2% of draws. Correct framing (PAPER_FINAL §4.5): *reference choice makes already-weak ranking evidence arbitrary and strongly attenuates the evidence that is real.* Do **not** say "17.56% of well-supported rankings get overturned".

### 6.5 By family (Table 6)

| Family | E1 rev | E2 rev | E2 τ_b (valid draws) | E3 scores gemma2/llama/mistral/qwen3 |
|---|---|---|---|---|
| scheduling | 0% | 0% | 1.000 (n=41,677) | 0 / 0 / 0 / 0.25 |
| sync | 2.1% | 10.0% | 0.495 (n=42,333) | 0.31 / 0.07 / 0.06 / 0.49 |
| banker | 1.1% | 21.0% | 0.158 (n=47,617) | 0.20 / 0.125 / 0.17 / 0.19 |

Scheduling's zero is **uninformative**: three of four models solve none of its 8 worlds under any evaluator. Banker's is the most unstable partly because the four models are bunched (0.125–0.198) and |V| is large. Eight worlds per family: descriptive, not replication.

---

## 7. Why it happens: the attenuation law, and the fixes

### 7.1 The law

For a uniformly random reference R ∈ V(x), E2 passes an output iff it equals R after normalisation. If every valid output equals exactly one element of V(x), and no invalid output equals any, then a valid output matches with probability 1/|V(x)|. Hence for each (task, model) cell: **E[E2] = E3 / |V(x)|** (Proposition 1, `RCR_FORMAL_METHOD_NOTE.md` §2).

Check in the data (`kref_attenuation.json`): 179 valid generations, 0 match no reference, 0 match more than one, 0 invalid generations match any reference; Pearson r = 1.000 over the 42 cells with positive E3, median observed/predicted ratio 1.00.

**What this is and is not.** It is algebra, not discovery. The paper itself says it is "close to an identity" and "would fail in domains where distinct references can be equivalent under normalization" (§4.7), and the draft says "elementary algebra" (RCR_EMPIRICAL_DRAFT §5.3). Its *value*: it identifies the mechanism and lets you predict attenuation from |V| alone, before running any model.

### 7.2 Consequence: reference matching re-weights tasks by 1/|V|

Benchmark-level: E[S_m^{E2}] = (1/N) Σ_i S_{mi}^{E3} / |V_i|. Tasks with |V| = 2 count 96× more than tasks with |V| = 192. The retained fraction of a pairwise gap is the E3-gap-weighted mean of 1/|V_i| (audit doc §5.3). That is also why llama–mistral flips to "+0.000185" in expectation: mistral's few valid answers sit on large-|V| tasks, which are heavily attenuated.

### 7.3 k-reference remedy (match-any), Table 7

An output passes if it matches any of k uniformly sampled references (k = |V| recovers E3). 2,000 draws per k, 20,000 flips (`rcr_kref_analysis.py`, seed 20261020).

| k | Detect qwen3 > llama | Detect qwen3 > mistral | Gap kept | False positive (any of 4 non-separated pairs) | Full-ordering recovery |
|---|---|---|---|---|---|
| 1 | 0.0% | 0.0% | 15% / 16% | 0.0% | 13.4% |
| 3 | 9.0% | 10.2% | 43% / 45% | 1.7% | 42.4% |
| 5 | 47.9% | 57.0% | 65% / 67% | 4.9% | 55.0% |
| 10 | 57.6% | 78.5% | 75% / 78% | 2.2% | 50.1% |
| 25 | 83.8% | 88.1% | 86% / 88% | 0.2% | 55.5% |
| 50 | 93.0% | 86.1% | 90% / 91% | 0.2% | 72.9% |
| all | 100% | 100% | 100% | 0.0% | 100% |

Curves are approximately, not strictly, monotone (MC SE about 1 point; note the k=10 → 25 dip in full-ordering recovery and the k=25 → 50 dip for mistral). Full-ordering recovery plateaus ≈ 50–55% because the llama–mistral gap (−0.010) is unresolvable. The thresholds (k ≈ 25 for ≈ 85%) rest on two oracle-significant pairs; **do not generalise them**.

### 7.4 The inverse-|V| (Horvitz–Thompson) correction

Multiply the mean match over k references by |V(x)|: unbiased for E3 under the one-match property (estimated/oracle gap 0.99–1.02) but with large variance: SD of the estimated qwen3–llama gap 0.37 (k=1), 0.21 (k=3), 0.10 (k=10) against a true gap of 0.243. Detection 0.1% (k=1), 6.5%/9.2% (k=3), 40.2%/31.0% (k=10), below match-any at the same k. Lesson: **correcting bias does not restore power**. Practical advice: enumerate V(x) and use a validator; failing that, match against many references.

### 7.5 Is the instability an artefact of uniform sampling? (Table 2)

No benchmark curator samples references uniformly. `rcr_reference_distribution_sensitivity.py` re-draws 50,000 vectors under 11 reference-selection distributions with the 1,152 generations frozen. Canonical bias p = probability the curator keeps the canonical R₀, uniform over the rest otherwise:

| p (canonical bias) | E2 reversal | E2 τ_b mean |
|---|---|---|
| 0.00 (non-canonical only) | 16.86% | 0.497 |
| 0.25 | 14.60% | 0.699 |
| 0.50 | 12.14% | 0.784 |
| 0.80 | 7.35% | 0.896 |
| 0.90 | 4.33% | 0.945 |
| 0.95 | 2.30% | 0.972 |
| 0.99 | 0.47% | 0.995 |
| similarity-weighted w = 1/(1+d) | 17.04% | 0.645 |
| uniform (reproduction) | 17.23% | 0.617 |
| adversarial worst case | single draw, τ_b = 0.6667 (n = 1; not a distribution) | |

Reading: instability falls monotonically with canonical bias and vanishes as p → 1 **by definition** (you evaluate against R₀ nearly always). So it is not a sampling artefact, but it needs alternative valid references to enter with non-negligible probability. A total-variation robustness certificate was also derived; it is a **sufficient** condition and is uninformative here (bound 0.66 vs largest expected margin 0.037; failure to certify ≠ instability) — see `RCR_FORMAL_METHOD_NOTE.md` §4 and `RCR_THEORY_CONTRIBUTION_DECISION.md` (verdict: **NO-GO** for a theory paper; the maths is textbook).

---

## 8. The controls

### 8.1 Stated convention ("maybe the models just did not know the tie-break rule")

The prompt gets the one-sentence tie-break convention (§4.5). 1,152 new generations. (`run_stated_convention.py`, `analyze_stated_convention.py`, `stated_convention/REPORT.md`.)

- Pooled FRR_norm (share of semantically valid outputs rejected by E2): **0.625** [0.443, 0.816] vs 0.715 [0.511, 0.891] original. The CIs overlap heavily; "reduced by 9 points" is not a significant reduction. Strict-match FRR 0.795.
- 110 / 1,152 (9.5%) outputs are valid-but-noncanonical.
- Canonical (E2) acceptance 4.4% → 5.7% (numbers are A_norm, not strict exact match; the paper text says "canonical exact matches": see §16).
- Conclusion: disclosing the convention does **not** eliminate noncanonical valid outputs.

### 8.2 Competence arm (stronger/other models)

`gemma3:12b` and `olmo2:7b`, stated-convention prompts, 288 generations each (`competence_pilot/analysis.json`):

| Model | n_valid | canonical | non-canonical | FRR_norm |
|---|---|---|---|---|
| gemma3:12b | 42 (B = 0.146) | 16 | 26 | 0.619 [0.440, 0.839] |
| olmo2:7b | 6 (B = 0.021) | 0 | 6 | 1.000 [1.000, 1.000] (degenerate: no canonical match among 6) |

Use gemma3 only. Pooled n_valid = 48 is feasibility evidence, not a capability claim. Models above ~12B were not run (≈ 83 GB needed vs 78 GB free, `airllm_feasibility.md`).

### 8.3 Adversarial meta-evaluation of the evaluators

79 outputs in a controlled contrast dataset (categories: canonical-valid, noncanonical-valid, lexical-similar-invalid, same-final-state-invalid; `adversarial/evaluator_meta_results.json`):

| Evaluator | Sensitivity | Specificity | FRR | Pass rate on noncanonical valid |
|---|---|---|---|---|
| E1 / E2 | 0.50 | 1.00 | 0.50 | **0.0** |
| E3 | 1.00 | 1.00 | 0.00 | 1.0 |

E3's perfect score is **tautological** (it defines validity). The valid point: E1/E2 reject 100% of noncanonical valid solutions, as they must. It is a stress diagnostic, not an estimate of natural error rates (PAPER_FINAL §7).

### 8.4 Claude-family follow-up: does it survive when models are competent? (new, §4.8 of the paper)

**Why it was run.** The main study's biggest weakness is the floor: E3 validity 6.6–30.9%, so most pairs are unseparable. The follow-up re-runs the *identical* 288 prompts per model (24 worlds x 3 variants x 4 repeats) on four stronger models through headless `claude -p` (`research/ssr_pilot/run_claude.py`): no tools, thinking off (`MAX_THINKING_TOKENS=0`), no settings/hooks/MCP, empty working directory. 1,152 calls, no permanent failures. Prompts, worlds, scorer, oracle and RCR modules are the frozen originals.

**What was fixed before any generation:** `docs/research/RCR_CLAUDE_FAMILY_PREREG.md` (internal SHA-256-stamped freeze, hash recorded in the run manifest; *not* an external registration; upload to OSF/AsPredicted to make it one). Four hypotheses with decision rules; "all results reported either way, no model dropped".

**Declared deviations from the local-model protocol:** temperature/top_p/max tokens are provider defaults (not controllable through the CLI); "seed" is a repeat index, not a sampling seed; the CLI adds a fixed Agent-SDK preamble and the account email to context. So this arm is a separate experiment, never pooled with Table 1.

| Model | E3 validity | E2 canonical | E1 canonical | Canonical share of valid | CIF (95% CI) |
|---|---|---|---|---|---|
| sonnet-5.5 | 99.3% | 55.6% | 23.3% | 55.9% | 3.30 (2.27–5.10) |
| haiku-5.5 | 98.3% | 45.1% | 19.8% | 45.9% | 2.67 (2.01–3.73) |
| sonnet-4.5 | 79.9% | 25.7% | 12.2% | 32.2% | 2.26 (1.36–3.58) |
| haiku-4.5 | 73.3% | 32.3% | 15.3% | 44.1% | 3.11 (1.94–5.18) |

**CIF (canonical inflation factor)** = valid outputs that match the canonical reference / the number you would expect if the model picked uniformly among valid solutions (sum of 1/|V(x)| over valid outputs). CIF = 1 means no preference for the canonical solution; CIF = 3 means three times more often. It is the new, empirical version of "models gravitate to the textbook answer".

**Outcomes against the plan**

| | Prediction | Result |
|---|---|---|
| H1 floor | at least 3 of 4 models >= 30% valid | **Supported**: 4 of 4 (73–99%) |
| H2 detection loss | uniform-reference E2 detects E3-separated pairs in < 50% of draws | **Supported**: 3.0% pooled over the 4 separated pairs (1.7%, 1.7%, 4.3%, 4.3%); the two non-separated pairs show 0.5–0.7% spurious significance |
| H3 canonical inflation | CIF > 1 for every model, and CIF differs between models | **Supported as written, with a flaw I must volunteer**: all CIF > 1 (2.26–3.30). The "differs" test bootstraps max-minus-min of noisy estimates, which is positive by construction (CI 0.42–2.69); the per-model CIs overlap heavily. Claim: inflation > 1 for all; do **not** claim models differ in canonical bias |
| H4 ranking distortion | best-vs-second E2 ratio differs from E3 ratio by > 1.5x for some adjacent pair | **Not supported**: max 1.43x |

**Other numbers (exploratory):** E3 separates 4 of 6 pairs (haiku-4.5 vs sonnet-4.5 and haiku-5.5 vs sonnet-5.5 are not separated; the 5.5 models are near ceiling, 99.3% vs 98.3%). Uniform-reference E2 reverses pairwise winners in **26.9%** of reference pairs (higher than the floor-limited 17.56%), tau_b 0.472, oracle recovery 22.6%. Attenuation law again exact: r = 1.000 over 92 model-world cells, no valid output matches zero or two references. k-reference scoring helps but less than before: k=5 detects the four separated pairs in 36–44% of draws, k=25 in 51–69% (k=1: 2–5%). Descriptively, canonical E2 puts haiku-4.5 above sonnet-4.5, the reverse of E3 (a non-separated pair). Scheduling is the hardest family for the 4.5 models (39.6%, 55.2% valid).

**How to say it (30 seconds):** "I then asked the obvious question: is this just a weak-model artifact? I preregistered four predictions, ran four Claude models that clear the floor, and three held and one did not. The detection loss persists: reference matching finds the real differences in 3% of draws. Models over-produce the canonical answer by a factor of two to three. But my prediction that this would distort the canonical ranking by 1.5x failed, at 1.43."

**What not to say:** that the preregistration is external; that H3 shows models differ in bias; that this proves generality (same 24 worlds, one domain); that the CLI arm is sampling-matched to the local arm.

**Open risk to state yourself:** I have not audited how common single-reference matching is in planning or executable benchmarks, where validators such as VAL are standard. The paper shows the cost *if* a benchmark scores against one reference; it does not show that many do.

---

## 9. The history, told honestly (preregistration and what changed)

This is where examiners go for blood. Know it chronologically.

1. **Dead ends, archived.** An earlier "MGEV" prototype (hard-coded/synthetic) and an "AGY RSG" project (`research/archive_agy/`, `docs/PREREGISTRATION.md`: no LLM was ever run; oracle rejected every trace; "FCFS" was preemptive; 38/50 "invalid" traces were valid) were audited and **withdrawn** (commits "Audit and rebuild RSG study; withdraw AGY's GO"; SSR_PILOT_REPORT §2). Do not cite their results.
2. **RSG v2 (`docs/PREREGISTRATION_V2.md`, frozen 2026-10-02).** Question: does giving an LLM *judge* a reference trace make it reject other valid traces ("reference anchoring")? Its own leakage audit failed on concurrency splits (D2/D3); discrimination claims were restricted to scheduling. This is a different experiment (LLM judge, not reference-matching) whose Phase B is untouched; its code/simulator was reused.
3. **SSR pilot (`docs/research/SSR_PILOT_PREREG.md`, frozen 2026-10-02, before any model output).** Internal SHA-256-stamped freeze; **not** externally registered or independently time-stamped, and first committed together with the first runs. Kill criteria K0–K5; decision rule GREENLIGHT iff all pass; CONDITIONAL iff K0–K3 pass and K4/K5 fail for lack of power; KILL otherwise. K4 = "at least one model-level conclusion changes" with ≥ 70% bootstrap stability.
   - Deviations before any model output: D1 (K0 failed first; bank redesigned, threshold unchanged), D2 (K3 proxy definition).
   - D3 (after first outputs): (a) validator crash on trailing IDLE fixed; (b) **A_norm counted "reference + out-of-world token" as a match** — 5 of 1,152 outputs (0.4%, all mistral) affected; fixed. A defect of exactly this size had briefly *manufactured* a mistral > gemma2 ranking reversal. Moral you can quote: "at this sample size a ranking reversal can be manufactured by five outputs."
4. **Pilot verdict: CONDITIONAL** (K0–K3, K5 pass; K4 fails without adequate precision). No model ranking changed under the canonical reference (τ = 1.0); the qwen3 significance change did not reproduce in ≥ 70% of resamples (stability 0.10 and 0.13); evaluator effect CIs wider than ±0.05 for 5 of 6 pairs (≈ 65 worlds would be needed). Recommended follow-up, conditions fixed in advance: models above a competence floor (≥ 50% valid), ≥ 65 worlds, a stated-convention arm. **Done: stated-convention arm and a small competence arm. Not done: ≥ 50%-valid models, ≥ 65 worlds.**
5. **RCR protocol (post-hoc).** After seeing the pilot data the project was reframed: instead of one canonical reference, vary the reference over all of V(x). The 50,000-draw protocol, τ_b / reversal / recovery metrics, sensitivity grid, and later detection / near-tie / family / attenuation analyses were all designed after the data. They are **exploratory reanalysis of frozen generations** (PAPER_FINAL §9: "should be replicated before being treated as confirmatory").
6. **Audit and deviations D1–D10 (PAPER_FINAL §9).** Highlights:
   - D1 McNemar on cells → world-level sign-flip + Holm (fixes pseudoreplication).
   - D2 100 → 50,000 draws.
   - D3 tie-aware τ_b (no alphabetical tie-breaking).
   - D5 degenerate τ_b policy.
   - D6/D7 significance run on a **200-draw subsample** originally; the summary "no pair is significant" was true only for E1/E2 — E3 separates two pairs. Re-run on all 50,000 draws per evaluator; old claim **withdrawn** (C7 in the claims audit).
   - **D9 (2026-10-12)**: the RCR modules omitted rule D3(b) that the pilot scorer applies → 7 mistral outputs wrongly counted as E2 matches. After correction: E2 canonical mistral 3.47% → 1.74%; τ_b 0.490 → 0.618; reversal 18.61% → 17.56%; recovery 23.92% → 13.63%; uniform baseline 18.22% → 17.23%; near-tie share 86.4% → 85.6%; sync reversal 11.6% → 10.0%. Qualitative conclusions unchanged; canonical now reproduces the E3 ordering (before, mistral and gemma2 were swapped).
   - D10 attenuation / k-reference analyses added post hoc.
   - Bibliography: three arXiv IDs pointed to unrelated papers, "References Matter" had wrong title/authors; all references re-verified (`paper/references_verified.csv`, gated by `tests/test_references_verified.py`).
   - Novelty claims: "first"/"genuinely new" removed after finding Casola 2025 / Jeong 2026 / OTAP / LogicGraph.
7. **Second domain (Blocks World), preregistered internally, executed 2026-10-13** (`research/docs/SECOND_DOMAIN_PREREGISTRATION.md` + Addendum A; `paper/RCR_EMPIRICAL_DRAFT.md` §6): 24 planning tasks, same four models, 1,152 generations, 31 min 44 s, 0 errors. **It did not replicate the behavioural findings.** Models were at floor: valid 23 / 16 / 1 / 1 of 288 each (3.6% overall); registered criterion 4 (non-trivial competence) not met. H1 (attenuation identity) confirmed, r = 0.9855 on 16 non-zero cells — an algebraic identity; H2 (mean reversal ≥ 8%) **rejected** (4.63%); H3 not informative (no E3-separated pair, holds by construction); H4 not testable (smallest Holm p = 0.0975). Also a first run's logic error printed "CONFIRMED" for H3/H4 and an earlier draft called this "independent behavioural confirmation": both **corrected**. Seven deviations D0–D7 listed. Integrity caveat: the analysis script (23:20) was modified after the first qwen3 record (23:18:54), so blindness cannot be certified.

8. **Claude-family follow-up (2026-10-24, §8.4 above).** Preregistered internally before generation; H1–H3 supported, H4 not; H3's spread criterion is weak by construction; CLI deviations declared. Added after novelty check: HypoSpace, VTC-Bench, Shi et al. (ICLR 2026), Dristi and Dwyer, PROBE (the last verified from the arXiv abstract page only) make the area more crowded; the k-reference remedy is not novel as an idea.

**One line to memorise:** *the behavioural findings come from one 24-task OS benchmark (local models at the floor, Claude models above it); the second domain was uninformative because models were at floor; the preregistrations are internal; the metrics are post-hoc.*

---

## 10. Limitations (consolidated, all in the papers)

1. **One domain** for every behavioural claim (OS scheduling/sync/Banker's). Per-family numbers are within-benchmark, not replication.
2. **Low-accuracy regime.** E3 scores 6.6–30.9%; E2 under random reference 0.5–4.1%. With N = 24 only 2 of 6 pairs are separable even by the oracle. Most reversal mass is noise amplification in near-ties.
3. **Descriptive recovery/τ_b.** They measure sensitivity of point-estimate rankings against an ordering of which only two relations are statistically supported.
4. **E3 is a simulator, not a human gold standard.** Correct only insofar as validators are; E3's 100% adversarial accuracy is tautological.
5. **No external replication; second domain null (floor effect).**
6. **Competence ceiling:** best model gemma3:12b with n_valid = 42; olmo2 n_valid = 6; nothing bigger run.
7. **Post-hoc and internal.** RCR metrics defined after seeing data; preregistrations are internal freezes; 10 deviations.
8. **Curator model is parametric** (canonical-bias, similarity weights); real curation unknown.
9. **Remedy numbers are benchmark-specific** (k ≈ 25 rests on two significant pairs); attenuation law needs the one-match property.
10. **Scoring-rule bug history (D9):** a residual divergence between pilot scorer and RCR modules would shift E2; see §16 for one I found for E1.
11. **Conditional uncertainty.** The 99.99% miss rate is a count over reference draws, conditional on the frozen 24 worlds and the frozen generations (49,995 / 50,000, Wilson 95% [99.977%, 99.996%]); it carries no generation- or world-sampling uncertainty.
12. **Generation randomness** (temperature 0.7, 4 seeds) means score vectors are themselves noisy; reference-choice variation is integrated out exactly (DP), but model-sampling variation is not.
13. **Claude arm.** Provider-default sampling and CLI preamble; model-version drift can change a rerun; 5.5 models near ceiling so E3 cannot separate them; H3 spread test weak; no audit of how prevalent single-reference scoring is.

---

## 11. Reviewer-attack Q&A already in the repo (`paper/REVIEWER_ATTACK.md`)

| # | Attack | Short response |
|---|---|---|
| 1 | "Known already." | Conceded; contribution = exact enumeration + detection loss + near-tie location. |
| 2 | "Oracle is circular." | Independent `BankerSolver`/`validate_banker`, brute-force cross-check; residual: simulator ≠ human. |
| 3a–d | Stats: 200 draws; "no pair significant"; evaluator-effect inference; 86 degenerate draws | Re-run on all 50,000; claim withdrawn; direct bootstrap test; D5. (Note: the doc says 86, the paper says 87 — §16.) |
| 4 | Stated convention only 0.715→0.625; small n | Disclosure does not eliminate it; small n reported with CIs; no pooled capability claim. |
| 5 | "E3 is a tautology." | Conceded: "by construction"; the empirical content is the cost of not using it. |
| 6 | Curators pick canonical | 11 distributions; still 2.30% at p=0.95. |
| 7 | Near-ties / floor effect | Largely conceded; 85.6% in non-separated pairs. |
| 8 | Preregistration overstated; follow-up conditions not met | Conceded; "pre-specified (internal freeze)"; post-hoc and exploratory. |
| 9 | "Headline numbers changed between versions." | D9 bug, listed before/after; independent re-implementation agrees. |

---

## 12. The 12-minute talk track (≈ 9 slides)

| Min | Slide | Say | Show |
|---|---|---|---|
| 0:00–1:00 | **1. The question** | "When a task has many right answers, benchmarks pick one as gold. I measured what that does to conclusions." | `sched_01`: six valid orderings; qwen3 matches #0, gemma-style alternative would be marked wrong |
| 1:00–2:30 | **2. Setup** | 24 OS tasks (3 families), exact V(x) by enumeration, an executable validator E3 that never sees the reference; 4 local models × 3 renderings × 4 seeds = 1,152 outputs. Same prompt text said "any valid answer is accepted". | prompt box (§4.2), family table |
| 2:30–3:30 | **3. Three evaluators** | E1 exact string, E2 normalised trajectory vs one reference, E3 replay-and-check. E3's invariance is by construction. | `bank_01` example: gemma2 answer passes E3 16/16, E1/E2 1/16 |
| 3:30–5:00 | **4. Result 1: leaderboard** | 50,000 random gold vectors. E2 ranks reversed pairwise winners in 17% of vector pairs (exact 17.15%); τ_b 0.62 ± 0.35; E2 recovers the oracle ordering 13.6% of the time. The canonical choice looks fine; the others do not. | reversal bar chart; one worked draw (§5.5) |
| 5:00–6:30 | **5. Result 2: lost detection (the real finding)** | Oracle: qwen3 > llama and > mistral, Holm p = 0.013/0.018, in every draw. E2: detects in 5/50,000 draws. E2 keeps 12–18% of the true gap. | Table 3 + Table 4 |
| 6:30–7:30 | **6. Why** | E[E2] = E3/\|V\|: a valid answer matches a random gold with probability 1/\|V\|; tasks get re-weighted by 1/\|V\|. Honest: it's algebra. 85.6% of reversals live in pairs even the oracle can't separate. | formula + near-tie pie |
| 7:30–8:30 | **7. What to do** | Use a validator; else match against k references: k=25 restores ≈ 85% detection; inverse-\|V\| correction fixes bias, not variance. | Table 7 curve |
| 8:30–10:30 | **8. Follow-up above the floor** | Preregistered 4 predictions on 4 Claude models (73–99% valid). Held: floor gone, detection loss persists (3.0% detection), canonical inflation 2.3–3.3x. Failed: 1.5x ranking-distortion (1.43x). Reversal rate rises to 26.9%. | Table in §8.4 |
| 10:30–12:00 | **9. Limits and status** | One benchmark, N = 24; local models at floor, Claude models near ceiling; pilot verdict CONDITIONAL; metrics post-hoc; internal preregistration; a 24-task Blocks World replication did **not** replicate (floor effect, H2 rejected). Empirical case study; workshop-ready, TMLR target; prevalence of single-reference scoring unaudited. | the limitation list; "what would raise it" |

Delivery rules: say "by construction" for E3 before anyone else does; say "detection loss, not reordering" for the main finding; say "exploratory" for everything after the pilot; never say "first", "proves", "frontier" or "generalises"; say "three of four predictions held" rather than "confirmed".

---

## 13. How RCR connects to the RAG track

Both tracks ask the same meta-question: **does my evaluation metric measure the thing I think it measures, and how much do my conclusions depend on the evaluation choices?**

| | RAG evaluation (FINDINGS.md) | RCR |
|---|---|---|
| "Reference" | one ground-truth answer per question (`eval_set.json`) | one gold trace per task |
| Multi-valued truth | many correct paraphrases/coverages of the same fact | many valid traces |
| Reference-matching metric | `answer_correctness` (F1 over statement sets vs ground truth; A19: a *more complete* answer scored lower because extra true facts count as false positives; H5: ground truth is the ceiling) | E1/E2 |
| Reference-free metric | `faithfulness` (checks the answer against the *context*, not a gold) | E3 |
| Judge | stochastic LLM (qwen2.5:7b), self-preference bias controlled by using a different family | deterministic validator, no judge |
| Noise | run-to-run floor ≈ 0.027 answer_correctness (A20); only 4 effects exceeded it | Monte Carlo SE ≈ 0.0016 on τ_b; exact DP removes sampling error over references |
| Metric that lies | `faithfulness` rewards refusal (A1); `context_entity_recall` unreliable (A15) | E2 under random reference collapses toward zero |
| Biggest lesson | defect fixes and prompt (+0.111, +0.092) ≫ retrieval-technique choice | reference choice ≫ model differences in the weak-model regime |

Good one-liners: "In RAG the reference is incomplete; in RCR the reference is one of many. Same failure: a single reference confuses 'different' with 'wrong'." And "In RAG I could not remove the judge's noise, so I measured it (0.027); in RCR I could remove the judge entirely because the domain is formal."

Differences to state out loud: RCR is exact (enumerated V(x), deterministic validator); RAG eval cannot enumerate valid answers and relies on an LLM judge; the RCR phenomena were **not** shown to transfer to RAG.

---

## 14. Reproduction commands

All from repo root. `PYTHONPATH=.` and the repo's `.venv`.

```bash
PYTHONPATH=. .venv/bin/pytest tests -q                      # 1,304 passed in ~30 s (my run, 2026-10-24)
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION   # rcr_summary.json (50k draws, sequential loop: slow)
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_extended_analysis      # extended_analysis.json (~2.5 min)
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_kref_analysis          # kref_attenuation.json
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_exact_dp_analysis      # exact_dp_analysis.json
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_uncertainty_and_error_audit
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcr_reference_distribution_sensitivity
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_stated_convention
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_competence_pilot
```

**Warning (from the project's own notes and my run):** running `pytest` or the analyses rewrites artifact provenance (git SHA/timestamps) and can trip the raw-SHA consistency gate in `tests/test_consistency_gate.py`. Run the tests *before* the analyses and re-sync `paper/REPRODUCIBILITY.md` hashes if you edit any gated file. My test run rewrote `research/pilot_second_domain/results/blocks_world_pilot.json` (the only file under `research/` or `paper/` touched in the last 20 minutes); that directory is untracked in git, so I could not diff it. What I did **not** do: re-run the 50,000-draw protocols; I verified numbers by reading the stored artifacts and recomputing selected quantities (listed in §16).

Seeds: world generation 20261003; trace bank 20261004; main 50k loop 20261005; sensitivity 20261007; extended 20261016 (draws) / 20261017 (flips, bootstrap); k-reference 20261020/20261021.

---

## 15. Hostile examiner questions (with strong, honest answers)

**Q1. "Reference choice affecting rankings is already known. What is new?"**
Nothing about the *existence* of the effect; I say so in §1 and §8 of the paper (Casola 2025; Jeong 2026; Kulshreshtha 2026 is a direct neighbour). What I add is a setting where V(x) is enumerated exactly and a deterministic validator gives the true ranking, so reference choice becomes a controlled factor and I can measure things the human-reference papers cannot: detection loss (reference matching misses a real, oracle-significant difference in 99.99% of draws), where the instability lives (85.6% in near-ties), and the exact attenuation mechanism.

**Q2. "Your E3 is a tautology; τ_b = 1 is not a result."**
Agreed, and the abstract says "by construction". The result is the cost of not using E3: how much of the real signal a single reference destroys.

**Q3. "Your oracle is my simulator's opinion. How do I know V(x) is right?"**
Three checks: enumerated sets are re-verified member by member through the rule and constraint checkers; scheduling/sync validation delegates to `validators.py` written separately from the enumerators; Banker's uses an independent solver and brute-force permutation search for all 8 specs; plus hand audits of 9 worlds. Residual risk is a shared misreading of a rule; I state that E3 is not a human gold standard.

**Q4. "Four sub-10B models at 7–31% accuracy is a toy."**
Yes. It limits power (only 2 of 6 pairs separable) and is why most reversal mass is in near-ties. It is a reason the paper is a scoped case study. It does not remove the exact algebra: the attenuation 1/|V| applies at any accuracy, and I measured it.

**Q5. "Is 17.56% the share of rankings that get overturned?"**
No, and the paper warns against that reading. 85.6% of the reversal mass sits in pairs the oracle cannot separate at N = 24. The defensible statement is: reference choice makes weak orderings arbitrary and strongly attenuates real differences.

**Q6. "Nobody uses a random gold. The canonical reference reproduces the oracle ordering exactly."**
True: under R_canonical E2's ordering equals E3's. So I tested non-uniform curators: even when the canonical reference is chosen 95% of the time, E2 reversals are still 2.30%, and they vanish only as p → 1. The deeper point is that the canonical gold is one of V(x)'s members chosen by enumeration order, not by quality; if the benchmark had picked another, the same models would be scored differently. And at the canonical reference the *scores* are still attenuated (qwen3 13.2% under E2 vs 30.9% under E3).

**Q7. "Why is the main finding detection loss rather than ranking flips?"**
Because the expected gap sign essentially never flips (it just shrinks to 12–18%), and the winner reversals are concentrated where the oracle sees no difference. With a 1/|V| attenuation, true differences become too small to detect at N = 24: E2 reaches significance in 5/50,000 draws.

**Q8. "The attenuation law is an identity. You presented it as a result."**
It is algebra and the paper says "close to an identity" and the draft says "elementary". What the data adds is the premise check: all 179 valid generations match exactly one reference and no invalid one matches any, so the identity applies exactly here (r = 1.000). Value: it predicts attenuation from |V| before running models, and licenses the remedies.

**Q9. "You changed the numbers (τ_b 0.490 → 0.618, 18.61% → 17.56%, 23.92% → 13.63%). Why should I trust any of them?"**
Because the change is traceable to one rule: the RCR modules omitted preregistered rule D3(b), so 7 mistral outputs with out-of-world entities were counted as matches. Every before/after is listed in Deviation 9; an independent vectorised implementation (different RNG) agrees with the corrected loop within Monte Carlo error; an exact DP gives 17.15%; the test suite pins the values (432 tests, claims manifest of 53 claims gated against the JSON). It also shows the fragility: five outputs can manufacture a ranking reversal at this scale, which is itself a point in the paper's favour.

**Q10. "The pilot you preregistered returned CONDITIONAL. You then redefined the study. Isn't that p-hacking/HARKing?"**
The RCR protocol and everything after is post-hoc and labelled exploratory in §9 (D8, D10). The preregistration is also only an internal hash freeze, first committed with the runs, not externally registered. I do not claim confirmation. I claim a descriptive, exactly-computable analysis of frozen data, to be replicated. The two follow-up conditions the pilot named (competence floor, ≥ 65 worlds) were not met, and I list that as a limitation.

**Q11. "Did you try a second domain? Does it replicate?"**
Yes, Blocks World planning, 24 tasks, 1,152 generations. It did not replicate the behavioural findings: models were at floor (23/16/1/1 valid of 288), the mean reversal was 4.63% against a registered 8% threshold (H2 rejected), and no model pair was oracle-separated, so H3 is uninformative and H4 untestable. Only the 1/|V| identity "replicated", which is algebra. An earlier draft overstated this and was corrected. I report it as an uninformative null caused by competence, not a refutation.

**Q12. "Detection of 99.99% misses: that's 49,995 draws of the same 24 worlds, not 50,000 independent experiments."**
Correct. It is conditional on the frozen 24 worlds and frozen generations; it integrates over *reference choice* exactly but contains no sampling uncertainty over worlds or generations (draft §7, item 6). Wilson 95% [99.977%, 99.996%] only reflects the draw count.

**Q13. "Non-significance is not equivalence."**
Agreed; the audit doc guardrail says exactly that. It is a statement about power: under E2 the expected gap is ~15% of the oracle gap, and N = 24 cannot see it.

**Q14. "What is the statistical unit? You have 1,152 outputs."**
The world (N = 24). Variants and seeds are nested; I average the 12 generations per (model, world) then sign-flip across worlds. Cell-level McNemar (N = 288) was withdrawn as pseudoreplication.

**Q15. "Sign-flip with 20,000 flips on 24 worlds: is that exact?"**
It is a Monte Carlo approximation of the randomisation distribution (2^24 ≈ 16.8M possible sign vectors), p-value = (count + 1)/(20,001), two-sided on |mean|. Differences are integer multiples of 1/12, scaled to integers so ≥ comparisons are exact. Minimum attainable raw p ≈ 5×10⁻⁵.

**Q16. "Your Holm correction is across 6 pairs per draw; what about the 50,000 draws?"**
Draws are not hypotheses; they are Monte Carlo samples of the reference vector, and I report the *distribution* of decisions across them.

**Q17. "τ_b ± 0.351: is that uncertainty?"**
No: it is the SD across reference draws. The SE of the mean (0.0016) reflects Monte Carlo error only. The reversal estimator's SE is 0.00091 once the six pairs' dependence is accounted for (VIF 1.62), and the exact DP value 17.15% lies within one SE of the 17.18% MC value.

**Q18. "Why not just use an LLM judge?"**
LLM judges have their own documented biases (self-preference, Wataoka 2024) and are non-deterministic. Where a deterministic validator exists, E3 is strictly better; the paper's recommendation (i) is to prefer it. An LLM judge would also not be reference-independent if shown a reference (that was the earlier RSG experiment, not this one).

**Q19. "Stated convention reduced FRR only from 0.715 to 0.625, within CI. What are you claiming?"**
Only that stating the tie-break did not eliminate noncanonical valid outputs (110/1,152 remain, 62.5% of valid outputs still rejected). I do not claim a significant change.

**Q20. "Why exclude 87 draws from τ_b?"**
τ_b is undefined when exactly one of the two score vectors is constant (e.g. all four models score 0 under a random reference but not under canonical). Predeclared policy D5: exclude and count them (0.17%); including them as 0 moves the mean by 0.001. Note for E1 the number excluded is much larger (4,020, 8.0%), because E1 scores are almost all zero.

**Q21. "Is the k=25 recommendation general?"**
No. It rests on two oracle-significant pairs among 24 worlds and four models; thresholds are benchmark-specific. The general advice is to enumerate V(x) or match against many references, and to report detection power.

**Q22. "What if two different references normalise to the same string (so the one-match property fails)?"**
Then E[E2] > E3/|V| and the law is inexact; the paper says so. In this benchmark the property holds exactly (0 valid outputs match more than one reference). The sync family is the only one with a formal equivalence relation (Mazurkiewicz traces); I sample uniformly over raw valid traces as the transparent baseline (formal note §9).

**Q23. "Why did scheduling show 0% reversal?"**
Because three of four models solve none of its 8 worlds under any evaluator, so no pair has anything to reverse. It is uninformative, not reassuring.

**Q24. "How does this relate to your RAG project?"**
Same meta-problem: in RAG, `answer_correctness` is reference matching and penalises a more complete answer (A19); `faithfulness` is reference-free but rewards refusal (A1). I measured the RAG judge's run-to-run noise floor (0.027) instead of removing it. RCR is the clean formal-domain case where the reference-free validator exists. I make no claim that the effect sizes transfer.

**Q25. "What would change your mind / what's missing?"**
A second domain where the oracle separates at least one model pair (stronger models or better prompting, more tasks), ideally externally registered before generation; ≥ 65 OS worlds; at least one model above ~12B. Until then, single-domain case study.

**Q26. "Your E1 numbers: are they comparable to the pilot's strict match?"**
Not exactly: see §16 item 4. In the RCR modules E1 compares against the canonical-formatted reference string, so it cannot match renamed (v1) or table-format (v2) outputs; recomputed, only 16 of 1,152 outputs can ever match under RCR-E1 vs 32 under the pilot's A_strict. E2/E3, which carry the headline claims, are unaffected. I would flag it as a known limitation of E1.

**Q27. "Is the 85.6% sensitive to your choice of what counts as 'separated'?"**
Yes: it depends on Holm-adjusted p < 0.05 at N = 24. Two pairs separate (adj p 0.0126, 0.0175), the next smallest is 0.1998. The statement is "of E2's reversal mass, 85.6% is in pairs E3 cannot separate at this N", not "in truly equal pairs".

**Q28. "Why should we believe your tests?"**
1,304 tests pass, including an exhaustive oracle reference-invariance test, valid-space checks, an extended-analysis test file (17 tests), a bibliography gate, and a consistency gate that matches manuscript numbers, claims manifest (53 claims), JSON artifacts and file SHA-256 hashes. Passing tests is evidence of reproducibility, not of scientific sufficiency (readiness memo says exactly this).

---

### 15.x New hostile questions after the Claude-family arm

**Q. "You said weak models were the problem; now what?"** The follow-up answers it for the main findings: with 73–99% valid outputs the detection loss is still there (3.0%) and the reversal rate is higher (26.9%). It does not remove the single-benchmark limit.

**Q. "H3 passed, so models differ in canonical bias?"** No. The preregistered spread test is positive by construction (max minus min of noisy estimates) and the per-model CIs overlap; I claim only CIF > 1 for every model (2.26–3.30).

**Q. "One of your four hypotheses failed. Is the story still intact?"** Yes: H4 asked for a 1.5x distortion of the canonical ranking and got 1.43x. The paper's claim is about detection loss and reference-choice instability, not canonical ranking distortion. I report it as a failure.

**Q. "Is the Claude arm comparable to the local arm?"** No, by declaration: provider-default sampling, repeat index rather than seed, fixed CLI preamble. It is a separate experiment.

**Q. "Is it preregistered?"** Internally frozen with the hash recorded in the run manifest, before generation; not externally registered. I recommend uploading it to OSF/AsPredicted.

**Q. "How many benchmarks actually score against one reference?"** I have not audited this, and for planning benchmarks validators are common. This is the biggest open risk; the paper measures the cost of single-reference matching where it is used.

**Q. "Conceptual or empirical?"** Empirical measurement and methodology. The only analytic piece is E[E2] = E3/|V(x)|, which is near-algebra and which I call that.

**Q. "Is it publishable?"** Workshop-ready; TMLR is the realistic journal target; I cannot promise acceptance. A second domain with competent models and at least 65 tasks is what would raise it.

---

## 16. Claims I could not reproduce / inconsistencies found in the repo

Verified by reading the files and recomputing as stated. None changes the E2/E3 headline results, but each is a place an examiner could catch you.

| # | Issue | Evidence | What to say / do |
|---|---|---|---|
| 1 | **E1 in the RCR modules is format-confounded.** It compares the model's text to `F.format_steps(world, ref)` in the default arrow style with canonical names, so it can never match variant v1 (renamed entities) or v2 (table output). Recomputed: canonical-reference E1 hits = 16 (v0) / 0 (v1) / 0 (v2) of 384 each; the pilot's `A_strict` (`scoring.py` uses `render.reference_text`, which respects variant style/names) = 16 / 14 / 2. | `rcrc/analysis.py`, `rcr_extended_analysis.py` (`fmt_refs`), `scoring.py`. Paper Table 1 E1 canonical qwen3 4.86% vs pilot A_strict qwen3 9.0% | E1-based numbers (τ_b 0.769, 4.66% reversal, 2.86% recovery, "E1 misses 100%") understate E1. Treat E2/E3 as the headline; do not defend E1 as "strict canonical matching". |
| 2 | **Tie-handling note is wrong that the two recovery estimands agree.** `TIE_HANDLING_ANALYSIS.md` says "no numerical difference" because the oracle has no ties; but the two estimands also differ when the *draw* has ties (47.4% of draws have ≥ 1 tied pair). Recomputed on the same 50,000 draws: tie-aware 13.50% vs alphabetical-list-equality 17.08%. | recomputed with `rcr_extended_analysis` tensors; `reference_distribution_sensitivity.csv` uniform E2 recovery = 17.29% | The "E2 E3-Recovery" column of Table 2 (17.29% uniform) is a **different, more lenient estimand** than the Table 1 headline (13.63%). Quote 13.63% (tie-aware); do not compare the columns. |
| 3 | **Two manuscripts disagree.** `paper/PAPER_FINAL.md` (hash-gated in REPRODUCIBILITY) says no second domain exists ("main outstanding step"), has reversal 17.56% MC, and cites 20 references without Kulshreshtha 2026. `paper/RCR_EMPIRICAL_DRAFT.md` (v3) has the Blocks World study, exact DP 17.15%, the novelty-neighbour paper, and the readiness verdict. | `PAPER_FINAL.md` §10 item 5, §11; `RCR_EMPIRICAL_READINESS.md` | Present the v3 draft's picture (including the null second domain). Do not claim "no second domain was attempted". |
| 4 | **Stale numbers in `FINAL_RESEARCH_STATUS.md`:** uniform 18.22% (now 17.23%), p=0.50 11.73%, p=0.80 7.67%, p=0.95 2.69%, similarity 17.72%; reversal share 86.4% (now 85.6%); sync 11.6% (now 10.0%); retention "10–18%" (now 12–18%); "401/401" tests. Also `RCR_EVIDENCE_AUDIT` says 418/424; I got 432. `REVIEWER_ATTACK` says "44-claim manifest" and "86 draws"; manifest has 53 claims; paper says 87. | files named | Use `PAPER_FINAL`/JSON values; mention test count as "432 on 2026-10-24". |
| 5 | **E1 degenerate draws undisclosed.** For E1, τ_b is valid in only 45,980 of 50,000 draws (4,020 = 8.0% degenerate), but Table 1's footnote discusses only E2's 87. | `rcr_summary.json` E1 `kendall_tau_n_valid_draws` | Say it if asked about E1's τ_b. |
| 6 | **Stated-convention arm's own analysis returns mechanical verdict GREENLIGHT** (K0–K5 all pass; K4 passes via criterion (ii) significance change), not CONDITIONAL. The paper only reports the FRR from that arm and says the pilot verdict was CONDITIONAL. | `stated_convention/analysis.json` (`criteria`, `decision`), `REPORT.md` line 22 | Know it before a reviewer finds it. It is a different arm run after the pilot, K4(ii) significance stability is based on the weak models, and the main paper does not rely on the K-gates. |
| 7 | **"Canonical exact matches 4.4% → 5.7%"** (PAPER_FINAL §5) are `A_norm` (normalised match) rates, 4.4% (pilot) and 5.7% (stated arm). The strict exact rate is 2.8% → 3.1%. | `stated_convention/REPORT.md` pooled row | Say "canonical normalised matches". |
| 8 | **README path error.** README layout lists `research/ssr_pilot/runs_stated_conv/`; actual directory is `runs_stated_convention/`. README names the project "Aether"; manuscript/notes use "GoldFlip" as working name. | `ls research/ssr_pilot` | Cosmetic. |
| 9 | **Retention range quoted three ways.** Abstract: "15–16% of the true gap"; Table 4 and README: 12–18%; `FINAL_RESEARCH_STATUS`, `rcr_kref_analysis.py` docstring: 10–18%. Resolution (audit doc §5.4): 15–16% for the two separated pairs; 12–18% across pairs with substantial gaps. | audit doc | Quote both with their denominators. |
| 10 | **Attenuation law r = 1.000 is not independent evidence** (an identity once one-match holds). | §7.1 | Say "identity; the data confirms the premise". |
| 11 | **Process caveat in the second domain:** analysis script mtime 23:20 > first qwen3 record 23:18:54. | `RCR_EMPIRICAL_DRAFT` §6.0 | Do not claim blind analysis there. |
| 12 | **Side effect of my verification:** `pytest` rewrote `research/pilot_second_domain/results/blocks_world_pilot.json` (untracked). Re-sync hashes if a consistency test is later run. | file mtime | Noted so you are not surprised. |

**Things I verified and found consistent:** Table 1 scores, 17.56% / 13.63% / 2.86%, 0.6177 ± 0.3505 (n = 49,913, 87 degenerate), Table 3 adj p-values (0.0126, 0.0175, 0.1998, 0.7948), E2 miss 0.9999, Tables 4–7 values against `extended_analysis.json` and `kref_attenuation.json`, near-tie shares (85.6% / 78.6%), family reversals (21.0% / 10.0% / 0%), Table 2 against the CSV, stated-convention and competence values, 179 valid / 51 canonical-match counts, and a full pytest pass (432).

---

## 17. Glossary

- **World / task (x):** one OS exercise instance (e.g. `sched_01`).
- **V(x):** all rule- and constraint-satisfying answers. |V(x)| is its size.
- **Reference / gold:** one answer in V(x) used for matching.
- **Reference vector R:** a choice of one reference per world.
- **Canonical reference:** first valid trace in enumeration order (listed order, arrivals before requeued process, lowest-index thread / safe process).
- **E1/E2/E3:** exact-string / normalised-trajectory / executable-validator evaluators.
- **FRR_norm (false rejection rate):** P(E2 rejects | E3 accepts), pooled, world-clustered bootstrap CI.
- **Reversal probability:** chance that the pairwise winner flips between two random reference vectors; 2p₊p₋.
- **Oracle recovery:** share of draws whose induced ordering equals E3's, ties included.
- **τ_b:** Kendall's rank correlation with tie correction.
- **Holm correction:** step-down multiple-comparison control across the 6 model pairs.
- **Sign-flip (randomisation) test:** paired test that randomly flips signs of the 24 world differences.
- **K0–K5:** the pilot's pre-specified kill criteria (integrity, disagreement size, surface robustness, proxy attack, changes-a-conclusion, multi-family).
- **CONDITIONAL:** K0–K3 pass, K4/K5 fail for lack of power.
- **Match-any (k-reference):** pass if the output matches any of k sampled references.
- **Horvitz–Thompson correction:** multiply by |V| to remove attenuation bias; unbiased but high-variance.
- **D1…D10:** the numbered deviation log in PAPER_FINAL §9.

---

# Part B: The RAG chatbot (OS Tutor), concise

> Short on purpose. Full detail (stage-by-stage inputs, judge prompts, worked example, hostile Q&A) is in `docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md`; background in `LEARNING_GUIDE.md`; evidence in `FINDINGS.md`. I do not claim the RAG part is novel: it is an engineering project plus an honest evaluation.

## B1. What it is, in one paragraph

A RAG tutor for an operating-systems course. Course slides, PDFs and notes are chunked into small child chunks that carry their parent slide or page; BGE-large embeddings go into a FAISS index; a question retrieves top-k children, optionally reranks, expands each to its parent, fills a prompt and calls llama3 (via Ollama, temperature 0). A tutoring layer on top asks Socratic questions and offers follow-up chips. Policy (which concept, whether an answer is right, what comes next) is deterministic, unit-tested code; the model only phrases text. We then measured it with RAGAS (judge qwen2.5:7b, a different family from the generator).

```
raw pptx/pdf/docx -> extract -> chunk (child + parent) -> bge-large-en-v1.5 -> FAISS IndexFlatIP (+ BM25)
question -> (multi-query | HyDE)? -> top-k children -> (cross-encoder rerank)? -> expand to parent (cap 400 tokens)
         -> prompt (few_shot) -> llama3 -> answer
eval: 26-question golden set -> retrieval metrics (no LLM) + RAGAS (7 metrics)
```

## B2. The numbers to remember (answer_correctness, from FINDINGS A16-A20)

| Number | Meaning |
|---|---|
| **+0.111** | gain from fixing defects (chunking, parent expansion, eval set) |
| **+0.092** | few_shot prompt over strict prompt (0.664 to 0.756) |
| **0.027** | run-to-run noise: same config scored 0.7752 then 0.7478 |
| **0.067** | spread across eight retrieval/rerank variants, i.e. about the noise |
| **26** | golden-set questions, so differences of a few hundredths are not resolvable |

One sentence: *technique choice moved the score about as much as re-running the same config; fixing bugs and rewording one prompt moved it three to four times more.*

## B3. Findings worth saying out loud

- BM25 looked terrible; the cause was our chunker, not BM25.
- `faithfulness` rewards refusal (a non-answer is perfectly "faithful"), so it is not a quality score.
- `answer_correctness` punishes a more complete answer (extra true facts count as false positives); ground truth is the ceiling.
- Three retrieval refinements were tried and refuted (A6, A9, A10); the reranking and multi-query gains are **not established**.
- `context_entity_recall` and the completeness composite were unreliable here.

## B4. Limitations (say them first)

1. 26 questions, one course, one corpus (measurements were on the 22-document July corpus; 37 files now, unmeasured).
2. 7B judge, never validated against hand labels. One run per configuration, no significance tests.
3. The measured prompt (few_shot) is not the production chat prompt (Socratic teaching prompt), and the RAGAS numbers do not measure the tutoring layer. Check that `src/config.py` defaults match the config whose table you quote.
4. Questions are recall of course material, so prompt conclusions do not generalise to derivation tasks.

## B5. Two-minute track and quick Q&A

**Two-minute track.** (1) A grounded OS tutor, Socratic by design. (2) Pipeline in one breath: small chunks to match, parent to read, FAISS, llama3 at temperature 0. (3) We measured instead of tuning: defects and one prompt mattered most, retrieval techniques sat inside the 0.027 noise. (4) Limits: 26 questions, unvalidated 7B judge. (5) Bridge to the paper: same lesson, an evaluation choice (a judge, a gold reference) can matter more than the thing being compared.

| Question | Short answer |
|---|---|
| Is this novel? | No. Standard RAG; the contribution is the measurement discipline. |
| Why small chunks plus parents? | Small chunks match precisely; the parent gives the reader enough context. |
| Why a different judge family? | To limit self-preference bias. |
| Did reranking help? | Not established; inside the noise. |
| Is faithfulness a quality metric? | No; it rewards refusal. |
| How do you know the tutor works? | These metrics do not measure it; its policy is unit-tested, learning gain is unmeasured. |

**Bridge to Part A.** In RAG the reference is incomplete; in RCR it is one of many. Same failure: a single reference confuses "different" with "wrong". RCR phenomena were not shown to transfer to RAG.
