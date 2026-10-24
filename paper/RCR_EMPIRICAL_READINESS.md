# Publication Readiness: RCR Empirical Methodology Paper (v3)

**Assessed draft:** `paper/RCR_EMPIRICAL_DRAFT.md` (the pre-confirmatory v2 text is preserved only inside `RCR_EMPIRICAL_FINAL_EVIDENCE_v3.zip`)
**Date:** 2026-10-14
**Supersedes:** the v2 readiness memo, which described the second-domain study as an independent behavioral confirmation. That description was wrong, and this memo replaces it.

---

## 1. Verdict

| Target | Verdict |
|---|---|
| **Workshop / specialized benchmarking venue** | **CONDITIONALLY READY**, as a single-domain case study with the scoping in the current draft |
| **Main-track conference (ACL / EMNLP / NeurIPS D&B)** | **NOT READY** |

"Conditionally" means the draft must be submitted as claimed here: the behavioral evidence is one 24-world OS benchmark, and the second-domain study is reported as an uninformative null. If a reviewer reads the Blocks World study as replication, the conditions are not met.

Passing tests (432 passed, §6) is evidence of reproducibility. It is not evidence of scientific sufficiency.

---

## 2. What the evidence supports

Three evidence sets, never pooled:

| Set | What it supports |
|---|---|
| **OS study** (24 worlds, 1,152 frozen generations) | Exact reversal probability 17.1518% (DP); 99.99% detection miss (49,995 / 50,000 reference draws; Wilson 95% [99.977%, 99.996%]); 85.6% of reversal mass in oracle-unseparated pairs; ~15–16% margin retention for the two separated pairs |
| **Blocks World pilot** (6 worlds, *synthetic* candidates) | Implementation check of the enumerator and evaluators. **No behavioral claim** |
| **Blocks World confirmatory** (24 tasks, 1,152 *actual* generations, all executed) | Arithmetic identity holds (H1). Registered reversal threshold missed (H2: 4.63% vs 8%). H3 and H4 **untestable** (no oracle-separated pair). No behavioral replication |

### Blocks World confirmatory results

| | Result |
|---|---|
| Execution | 1,152 / 1,152 present, 0 errors, 0 empty, 31 min 44 s |
| Reference spaces | 24 / 24 independently verified (separate IDDFS implementation; identical plan *sets*) |
| Valid generations | 23 (`qwen3:8b`), 16 (`gemma2:9b`), 1 (`llama3.1:8b`), 1 (`mistral:7b-instruct`): 41 of 1,152 (3.6%) |
| H1 | Confirmed: $r=0.9855$ (16 non-zero cells), median ratio 1.000. An algebraic identity; low information |
| H2 | **Rejected**: 4.63% (generation-bootstrap 95% [0.003%, 7.93%]; task-bootstrap [0%, 6.89%]; never ≥ 8% under any canonical-bias level) |
| H3 | **Not informative**: 100% holds by construction |
| H4 | **Not testable**: smallest Holm $p=0.0975$ |
| Preregistered criterion 4 (non-trivial competence) | **Not met** |

---

## 3. Corrections made in this pass

| # | Prior claim | Finding | Action |
|---|---|---|---|
| 1 | H3 "CONFIRMED" | No oracle-separated pair; share is 100% by construction | Relabeled NOT INFORMATIVE |
| 2 | H4 "CONFIRMED (vacuously)" | Undefined with no separated pair | Relabeled NOT TESTABLE; analyzer fixed |
| 3 | H1 $r=0.988$ "across all cells" | Protocol specifies non-zero cells: $r=0.9855$, $n=16$ | Both reported; code fixed |
| 4 | "qwen3 and gemma2 avoid floor effects"; "independent behavioral confirmation" | `qwen3` solves Tier 1 once in 96; 27.8% reversal rests on 23 vs 16 valid generations in a pair the oracle cannot separate | Removed |
| 5 | "findings replicated across two domains" | Only the identity replicated | Removed |
| 6 | "We prove" the $1/\lvert V\rvert$ identity | Elementary algebra; contradicts the no-new-theory framing | Reworded |
| 7 | Abstract: "Delta-method SE = 0.00173" | No source artifact. Supported figure is the joint-covariance SE 0.000906 | Replaced |
| 8 | "All 24 reference spaces independently verified" | Was asserted, not implemented | Verifier written and tested (`verify_reference_spaces.py`) |
| 9 | Prereg "5–6 h" feasibility | Actual 31 min 44 s | Addendum A |
| 10 | Tests "418" | Now 432 | Updated |

### Statistical formulas, rechecked (OS study)

I derived these from the kernel and did not accept the prior report. Kernel $h(R_1,R_2)=\mathbf 1\{M_1>0\}\mathbf 1\{M_2<0\}+\mathbf 1\{M_1<0\}\mathbf 1\{M_2>0\}$, symmetric and Bernoulli, with $\theta=2p_+p_-$.

- $U=2N_+N_-/(M(M-1))$ is exactly the fraction of discordant pairs ✔
- $\zeta_1=p_+p_-(p_++p_--4p_+p_-)$, $\zeta_2=\theta(1-\theta)$ ✔
- $\mathrm{Var}(U)=\frac{4(M-2)}{M(M-1)}\zeta_1+\frac{2}{M(M-1)}\zeta_2$ ✔ (Hoeffding, $m=2$)
- Six-pair mean variance uses the full $6\times6$ $\Sigma_1$ (shared reference vectors), VIF = 1.62 ✔
- `uncertainty_audit.json` reproduces exactly on re-run. Aggregate $z=+0.278$: the MC-vs-DP gap is sampling noise **for that estimator**, which I checked directly rather than assumed.
- The 99.99% is 49,995 / 50,000 draws. It is conditional on the frozen 24 worlds and generations and contains no generation-sampling uncertainty. The draft now states this.

---

## 4. Remaining weaknesses (why not higher)

1. **Single domain for all behavioral claims.** The second domain is a null caused by model competence, not a refutation and not a replication.
2. **$N=24$, four sub-10B models.** Limited power; 4 of 6 OS pairs are inseparable. "Absence of evidence" must not be read as equivalence.
3. **Post-hoc metrics and internal preregistration.** RCR metrics were defined after the OS data. Both preregistrations are internal protocols; the second-domain analysis script cannot be shown to predate the first model's outputs (last modified 23:20; first record 23:18:54).
4. **Deviation D0.** The implemented operator model differs from the registered one. It was fixed before generation, but it is still a departure from the registered text.
5. **Novelty.** Reference-set variation affecting rankings is published (Casola 2025; Kulshreshtha 2026; Feng 2026). The attenuation identity and the DP/U-statistic machinery are standard. The contribution is exhaustive enumeration in an executable domain plus the detection-loss and near-tie decomposition, measured on one benchmark.
6. **E1 ≡ E2 in Blocks World** (0 disagreements in 1,152 generations), so the evaluator contrast available in the OS study is absent here.
7. **No frontier or larger model, no external registration.**

## 5. What would raise the verdict

- A second domain in which the oracle separates at least one model pair (higher-competence models or few-shot prompting, plus more tasks), preferably registered externally *before* generation. This is a new study, not a rerun.
- ≥ 65 OS worlds, as already declared in the pilot's follow-up condition.
- At least one larger model.

## 6. Venue notes

- **Workshop (evaluation / benchmark quality):** appropriate. The honest negative second-domain result is a strength for this audience if presented as such.
- **Main track:** reviewers will reasonably call this a one-benchmark result built on an elementary identity. They will also point out the uninformative replication. Not recommended until §5 is done.
- Nothing here predicts acceptance anywhere.
