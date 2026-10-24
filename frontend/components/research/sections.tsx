import styles from "./research.module.css";
import { BarList, EffectChart, PipelineDiagram } from "./charts";
import {
  DEFECTS,
  EFFECTS,
  METRICS,
  PROMPTS_A17,
  PROMPTS_A19,
  RCR_CONTRIBUTIONS,
  RCR_FAMILY,
  RCR_KREF,
  RCR_MODEL_SCORES,
  RCR_PAIRWISE_DETECTION,
  RCR_SENSITIVITY,
  REFUSAL_ROWS,
  REFUTED,
  RETRIEVAL_COLS,
  RETRIEVAL_ROWS,
  RETRIEVAL_SRC,
  STAGE_INPUTS,
  SWEEP_A16,
  SWEEP_POSTFIX,
} from "./data";

function Src({ children }: { children: React.ReactNode }) {
  return <p className={styles.src}>source: {children}</p>;
}

export function Hero() {
  return (
    <header className={styles.hero}>
      <div className={styles.heroText}>
      <div className={styles.eyebrow}>Research · OS Tutor RAG</div>
      <h1>What we measured, and what the measurements overturned</h1>
      <p className={styles.lede}>
        The tutor answers from 37 course files (lecture decks, OSTEP chapters, handouts). Behind it sits a case study: a retrieval-augmented
        pipeline evaluated with a local judge, where most of what we expected to matter did not, and the biggest wins
        were bugs and the wording of one prompt. A second track asks whether OS benchmarks with several correct answers
        can be graded fairly at all.
      </p>
      </div>
      <div className={styles.stats}>
        <div className={styles.stat}>
          <div className={styles.statValue}>+0.111</div>
          <div className={styles.statLabel}>answer_correctness from repairing defects, 4x the noise floor (FINDINGS A20)</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statValue}>+0.092</div>
          <div className={styles.statLabel}>from two worked examples in the prompt, more than the whole retrieval sweep (A17)</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statValue}>±0.027</div>
          <div className={styles.statLabel}>run-to-run noise on one identical config; below this is not a result (A20)</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statValue}>17.56%</div>
          <div className={styles.statLabel}>pairwise model winners flipped by changing only the gold reference (RCR, rcr_summary.json)</div>
        </div>
      </div>
    </header>
  );
}

export function Pipeline() {
  return (
    <section id="pipeline" className={styles.section} aria-labelledby="h-pipeline">
      <h2 id="h-pipeline">The pipeline</h2>
      <p className={styles.sectionLede}>
        Every stage is a config switch (<span className={styles.mono}>src/config.py</span>), which is what made it
        possible to ablate them one at a time. Small chunks are matched, but the larger slide or page they came from is
        what the model reads.
      </p>
      <div className={styles.card}>
        <div className={styles.scroll}>
          <PipelineDiagram />
        </div>
        <Src>src/pipeline.py, src/evaluation.py, eval/retrieval_eval.py. Dashed boxes: reranking is optional and off by default (no reliable benefit measured); retrieval_eval is a side path.</Src>
      </div>
      <h3>What goes in and what comes out, per stage</h3>
      <div className={styles.card}>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Stage</th>
                <th>Input</th>
                <th>Output</th>
              </tr>
            </thead>
            <tbody>
              {STAGE_INPUTS.map((s) => (
                <tr key={s.stage}>
                  <td><strong>{s.stage}</strong></td>
                  <td>{s.input}</td>
                  <td>{s.output}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Src>src/config.py defaults (top_k 10, rerank top_n 8, max_parent_tokens 400, temperature 0.0), src/retrieval/*, src/context_expansion.py</Src>
      </div>
    </section>
  );
}

export function TutorLayer() {
  const rows: [string, string, string][] = [
    ["Concept state", "UNKNOWN to MASTERED, six levels", "Moves only through graded answers; a model suggestion is clamped to one level up and never reaches UNDERSTOOD."],
    ["Which question", "Chosen from the state", "After an explanation: predict or apply first. In a quiz: recall, understanding, application, analysis."],
    ["Wrong answer", "Hint, then scaffold, then explanation", "A misconception is probed with a question first; the correction comes only after two misses."],
    ["Student says 'just tell me' or 'skip'", "Always honoured", "The answer is shown or the question dropped, with no penalty."],
    ["Student is lost or stuck", "Simpler explanation, then full", "Detected by patterns, not a model; distress and off-topic messages get fixed, kind replies."],
    ["Student knows nothing", "Path, starters, course map", "Every answer ends with follow-up chips; each chip is a complete message."],
  ];
  return (
    <section id="tutor" className={styles.section} aria-labelledby="h-tutor">
      <h2 id="h-tutor">The tutoring layer</h2>
      <p className={styles.sectionLede}>
        The pipeline decides what the course says. A second layer, <code>src/tutor/</code>, decides how a tutor behaves.
        Following the LabTutor project, the rule is that policy lives in code and the model only phrases: code can be
        tested, a prompt cannot. Most tutoring turns therefore need no retrieval and no model call.
      </p>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Decision</th>
            <th>How it is made</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([a, b, c]) => (
            <tr key={a}>
              <td>{a}</td>
              <td>{b}</td>
              <td>{c}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3 id="tutor-example">A real exchange</h3>
      <div className={styles.callout}>
        <p>
          <strong>Student:</strong> test my understanding of deadlock
        </p>
        <p>
          <strong>Tutor:</strong> Question 1 of 3: List the four conditions necessary for deadlock.
        </p>
        <p>
          <strong>Student:</strong> mutual exclusion, hold and wait, no preemption and circular wait
        </p>
        <p>
          <strong>Tutor:</strong> That&apos;s right. Question 2 of 3: Why does breaking just one of the four conditions
          prevent deadlock?
        </p>
        <p>
          <strong>Student:</strong> no idea
        </p>
        <p>
          <strong>Tutor:</strong> That&apos;s completely fine, you don&apos;t need to know this already. An easier way in:
          what does &apos;necessary condition&apos; mean? If one necessary ingredient is missing, can the result happen?
        </p>
      </div>
      <p>
        <strong>How it was checked.</strong> 800+ automated tests: every authored question&apos;s model answer must pass its
        own answer key, no answer of &quot;I don&apos;t know&quot; may ever be graded correct, scripted dialogues cover the new-student,
        hint, skip, quiz and misconception paths, and the chat endpoint is tested with stubbed retrieval. There is no
        learning study and no RAGAS-style score for pedagogy; that is a stated limit, not a result.
      </p>
      <Src>src/tutor/*, tests/tutor/*, docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md (the chat turn and tutoring layer section)</Src>
    </section>
  );
}

export function Evaluation() {
  return (
    <section id="evaluation" className={styles.section} aria-labelledby="h-eval">
      <h2 id="h-eval">How a number is produced</h2>
      <p className={styles.sectionLede}>
        A golden set of 26 questions, each with a reference answer and the slides or pages it can be answered from.
        Retrieval is scored directly against those pages with no model involved. Answers are scored by RAGAS using a
        different model family than the generator, to avoid self-preference.
      </p>
      <div className={styles.grid2}>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Generator</p>
          <p className={styles.cardSub}>llama3 via Ollama, temperature 0.0, few_shot prompt</p>
          <p className={styles.cardTitle}>Judge</p>
          <p className={styles.cardSub}>qwen2.5:7b via Ollama, sequential calls, plus bge-small embeddings on CPU</p>
          <p className={styles.cardTitle}>Row sent to the judge</p>
          <p className={styles.cardSub}>
            <span className={styles.mono}>{"{question, answer, contexts[], ground_truth}"}</span>
          </p>
          <Src>src/config.py, src/evaluation.py (score_pipeline)</Src>
        </div>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Why two passes</p>
          <p className={styles.cardSub}>
            Generate every answer first, then judge every answer. The generator and judge cannot share an 8 GB GPU, so
            this costs 2 model loads per run instead of 2 per question.
          </p>
          <p className={styles.cardTitle}>Cost per run</p>
          <p className={styles.cardSub}>
            One few_shot run: 52 generation calls and 420 judge calls, about 16 judge calls per question. The USD cost
            is hypothetical: token counts priced at GPT-4.1 and GPT-4o-mini rates; nothing was billed.
          </p>
          <Src>eval/pipeline_runs.xlsx (sheet prompt_few_shot), src/token_tracking.py</Src>
        </div>
      </div>
      <h3>The seven metrics</h3>
      <div className={styles.card}>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Side</th>
                <th>Sees</th>
                <th>How it is computed</th>
                <th>Judge calls</th>
              </tr>
            </thead>
            <tbody>
              {METRICS.map((m) => (
                <tr key={m.name}>
                  <td className={styles.mono}>{m.name}</td>
                  <td>
                    <span className={`${styles.pill} ${m.side === "retrieval" ? styles.pillRetr : styles.pillGen}`}>{m.side}</span>
                  </td>
                  <td>{m.sees}</td>
                  <td>{m.how}</td>
                  <td className={styles.mono}>{m.calls}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Src>ragas 0.1.14 source (ragas/metrics/_*.py in the project venv); call counts consistent with 420 judge calls / 26 questions in pipeline_runs.xlsx</Src>
      </div>
      <p className={`${styles.callout}`}>
        Almost every finding follows from one fact: <strong>answer_correctness is an F1 over statements</strong>. A
        shorter answer has fewer true positives, and a more complete answer than the reference is penalised as false
        positives. The reference answer, not the pipeline, is the ceiling (HYPOTHESES H5).
      </p>
    </section>
  );
}

export function Findings() {
  const best = (idx: number) => Math.max(...RETRIEVAL_ROWS.map((r) => r.values[idx]));
  return (
    <section id="findings" className={styles.section} aria-labelledby="h-findings">
      <h2 id="h-findings">Findings</h2>
      <p className={styles.sectionLede}>
        All figures below were measured on the July corpus of 22 documents from 10 source files. The corpus has since
        grown to 37 files, and none of these numbers transfer to it without re-measurement (FINDINGS correction note,
        2026-09-30).
      </p>

      <h3 id="noise">1. Effect sizes against the noise floor</h3>
      <div className={styles.card}>
        <p className={styles.cardTitle}>Change in answer_correctness</p>
        <p className={styles.cardSub}>
          The same config scored twice gave 0.7752 and 0.7478. Only bars that clear the hatched band are results.
        </p>
        <EffectChart effects={EFFECTS} />
        <Src>FINDINGS A20 (table), A16, A17, A19</Src>
      </div>

      <h3>2. Defects that were masquerading as results</h3>
      <ul className={styles.list}>
        {DEFECTS.map((d) => (
          <li className={styles.listItem} key={d.id}>
            <span className={styles.listId}>{d.id}</span>
            <strong>{d.title}.</strong> {d.effect}
          </li>
        ))}
      </ul>
      <Src>FINDINGS F1, F2, F9, F10, F13, F15, A11, A18</Src>

      <h3>3. Retrieval: no technique dominates</h3>
      <div className={styles.card}>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Technique</th>
                {RETRIEVAL_COLS.map((c) => (
                  <th className={styles.num} key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {RETRIEVAL_ROWS.map((r) => (
                <tr key={r.name}>
                  <td>{r.name}</td>
                  {r.values.map((v, i) => (
                    <td className={`${styles.num} ${v === best(i) ? styles.best : ""}`} key={i}>
                      {v.toFixed(3)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={styles.cardSub} style={{ marginTop: 12 }}>
          HyDE buys breadth (best full@5) at the cost of precision (worst R@1). Multi-query buys precision (best R@1).
          Dense is the best all-rounder and needs no LLM call.
        </p>
        <Src>{RETRIEVAL_SRC}</Src>
      </div>

      <h3>4. The eight-variant sweeps</h3>
      <div className={styles.grid2}>
        <div className={styles.card}>
          <p className={styles.cardTitle}>First focused sweep, strict prompt</p>
          <p className={styles.cardSub}>answer_correctness, spread 0.055 across variants</p>
          <BarList
            rows={SWEEP_A16.map((v) => ({
              label: v.name,
              value: v.ansCorr,
              note: `${v.calls} calls · ${v.cost} hypothetical`,
            }))}
          />
          <Src>FINDINGS A16. Cheapest strong config won; the two most expensive placed fifth and seventh.</Src>
        </div>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Re-run after the fixes, few_shot prompt</p>
          <p className={styles.cardSub}>answer_correctness, spread 0.067</p>
          <BarList
            rows={SWEEP_POSTFIX.map((v) => ({ label: v.name, value: v.ansCorr, note: `faithfulness ${v.faith.toFixed(3)}` }))}
            digits={4}
          />
          <Src>eval/comparison_results.md. Single run per variant; two scorings of the top row differ by 0.027.</Src>
        </div>
      </div>

      <h3>5. The prompt outweighed every retrieval choice</h3>
      <div className={styles.grid2}>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Three prompts, one fixed config</p>
          <p className={styles.cardSub}>answer_correctness (faithfulness in the note)</p>
          <BarList
            rows={PROMPTS_A17.map((p) => ({
              label: p.name,
              value: p.ansCorr,
              note: `faithfulness ${p.faith.toFixed(3)}`,
              tone: p.name.startsWith("part") ? "danger" : p.name.startsWith("strict") ? "muted" : "accent",
            }))}
          />
          <Src>FINDINGS A17. Two worked examples aligned the shape of the answer: +0.092.</Src>
        </div>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Chain-of-thought lost it again</p>
          <p className={styles.cardSub}>Reasoning first shortened answers 27%, and lost statements are lost recall</p>
          <BarList
            rows={PROMPTS_A19.map((p) => ({
              label: p.name,
              value: p.ansCorr,
              note: `${p.words} words on average · faithfulness ${p.faith.toFixed(4)}`,
              display: p.ansCorr.toFixed(4),
              tone: p.name.startsWith("cot") ? "danger" : "accent",
            }))}
            digits={4}
          />
          <Src>FINDINGS A19. few_shot won 14 of 26 questions against cot&apos;s 10.</Src>
        </div>
      </div>

      <h3>6. Faithfulness rewards refusal</h3>
      <div className={styles.card}>
        <p className={styles.cardSub}>
          When retrieval fails the model says the context has no answer. That is zero unsupported claims, so
          faithfulness is perfect while correctness collapses. A pipeline that refuses everything scores 1.0.
        </p>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Technique</th>
                <th className={styles.num}>Refusal rate</th>
                <th className={styles.num}>Faithfulness</th>
                <th className={styles.num}>answer_correctness</th>
              </tr>
            </thead>
            <tbody>
              {REFUSAL_ROWS.map((r) => (
                <tr key={r.name}>
                  <td>{r.name}</td>
                  <td className={styles.num}>{r.refusal.toFixed(1)}%</td>
                  <td className={styles.num}>{r.faith.toFixed(3)}</td>
                  <td className={styles.num}>{r.ansCorr.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={styles.cardSub} style={{ marginTop: 12 }}>
          dense has the lowest faithfulness yet the second-highest correctness. Correlation of answer_correctness with
          faithfulness is +0.092, with context_recall +0.409.
        </p>
        <Src>FINDINGS A1, A2</Src>
      </div>

      <h3>7. Hypotheses the data refuted</h3>
      <ul className={styles.list}>
        {REFUTED.map((r) => (
          <li className={styles.listItem} key={r.id}>
            <span className={styles.listId}>{r.id}</span>
            <strong>{r.claim}.</strong> <span style={{ color: "var(--muted-foreground)" }}>{r.measured}</span>
          </li>
        ))}
      </ul>
      <Src>FINDINGS.md and HYPOTHESES.md</Src>
    </section>
  );
}

export function Caveats() {
  return (
    <section id="caveats" className={styles.section} aria-labelledby="h-caveats">
      <h2 id="h-caveats">What this does not show</h2>
      <ul className={styles.list}>
        <li className={styles.listItem}>
          <strong>26 questions, one course.</strong> Differences of a few hundredths are not resolvable at this size.
        </li>
        <li className={styles.listItem}>
          <strong>A 7B judge.</strong> qwen2.5:7b is a different family from the generator on purpose, but it is a
          small local model. A hand-labelled check of the judge was explicitly parked and is not done.
        </li>
        <li className={styles.listItem}>
          <strong>One run per configuration.</strong> The only variance estimate is the 0.027 from two scorings of one
          config, so the reranking and multi-query gains are not established.
        </li>
        <li className={styles.listItem}>
          <strong>context_entity_recall is unreliable here.</strong> It compares exact strings of LLM-extracted
          entities, so &quot;Ready&quot; and &quot;ready&quot; do not match (A15). The completeness composite is polluted by it.
        </li>
        <li className={styles.listItem}>
          <strong>The tutoring behaviour is not scored by RAGAS.</strong> The study evaluates the answer pipeline. The
          Socratic layer is tested by deterministic unit tests, not by a learning study.
        </li>
        <li className={styles.listItem}>
          <strong>Costs are hypothetical.</strong> Local runs, priced at published API rates for comparison only.
        </li>
      </ul>
      <Src>FINDINGS.md &quot;Caveats that must appear in the formal write-up&quot;, A15, A20</Src>
    </section>
  );
}

export function Rcr() {
  return (
    <section id="rcr" className={styles.section} aria-labelledby="h-rcr">
      <h2 id="h-rcr">Second track: Reference-Choice Robustness</h2>
      <p className={styles.sectionLede}>
        A different question about the same kind of measurement. Suppose an OS benchmark checks a model&apos;s
        scheduling or deadlock answer against one stored &quot;gold&quot; solution, but several different solutions are
        all correct. Does the leaderboard depend on which correct solution happened to be stored?
      </p>
      <div className={styles.callout}>
        Plain language: if three different schedules are all valid, a model that writes a valid but different one is
        marked wrong. We enumerated every valid solution for 24 OS tasks, then re-graded 1,152 model outputs under 50,000
        random choices of which valid solution is &quot;gold&quot;.
      </div>
      <div className={styles.stats}>
        <div className={styles.stat}>
          <div className={styles.statValue}>0.618</div>
          <div className={styles.statLabel}>Kendall τb between rankings under random vs canonical reference, ±0.351 (rcr_summary.json, E2)</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statValue}>17.56%</div>
          <div className={styles.statLabel}>pairwise winner reversals under normalized matching (rcr_summary.json)</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statValue}>13.63%</div>
          <div className={styles.statLabel}>draws where normalized matching recovers the reference-independent ranking; 2.86% for exact matching</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statValue}>85.6%</div>
          <div className={styles.statLabel}>of reversal mass sits in model pairs the validator itself cannot separate (extended_analysis.json)</div>
        </div>
      </div>

      <h3>The 3 Core Research Contributions</h3>
      <div className={styles.grid2} style={{ gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
        {RCR_CONTRIBUTIONS.map((c) => (
          <div key={c.id} className={styles.card}>
            <p className={styles.cardTitle}>
              <span className={styles.mono} style={{ color: "var(--accent)", marginRight: 8 }}>#{c.id}</span>
              {c.title}
            </p>
            <p className={styles.cardSub}>{c.summary}</p>
            <div className={styles.callout} style={{ marginTop: 12, fontSize: 13 }}>
              <strong>Measured finding:</strong> {c.finding}
            </div>
          </div>
        ))}
      </div>
      <Src>paper/PAPER_FINAL.md §1 & §4 · paper/CLAIMS_AUDIT_FINAL.md</Src>

      <h3>Model vs Model Benchmark Scores across Evaluators</h3>
      <div className={styles.card}>
        <p className={styles.cardSub}>
          Evaluated across 1,152 generations (288 per model) on 24 formal OS tasks. Notice how E1 and E2 drastically penalize models due to False Rejection (FRR) of valid noncanonical answers, while E3 tests executable correctness directly.
        </p>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Model</th>
                <th className={styles.num}>E1 (Exact Match)</th>
                <th className={styles.num}>E2 (Normalized)</th>
                <th className={styles.num}>E3 (Semantic Oracle)</th>
                <th className={styles.num}>False Rejection Rate (FRR)</th>
              </tr>
            </thead>
            <tbody>
              {RCR_MODEL_SCORES.map((m) => (
                <tr key={m.model}>
                  <td className={styles.mono}><strong>{m.model}</strong></td>
                  <td className={styles.num}>{m.e1Exact}</td>
                  <td className={styles.num}>{m.e2Norm}</td>
                  <td className={styles.num} style={{ color: "var(--accent)", fontWeight: 600 }}>{m.e3Oracle}</td>
                  <td className={styles.num} style={{ color: "var(--danger, #ef4444)" }}>{m.frr}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Src>paper/FINAL_STATISTICS.md Table 1 · research/ssr_pilot/results/rcrc/rcr_summary.json</Src>
      </div>

      <h3>Monte Carlo Pairwise Model-vs-Model Detection (50,000 Draws)</h3>
      <div className={styles.card}>
        <p className={styles.cardSub}>
          World-level paired sign-flip permutation tests (20,000 sign flips) with Holm-Bonferroni correction evaluated across all 50,000 reference sets. While the simulator (E3) consistently detects Qwen 3 8B as statistically superior to Llama 3.1 and Mistral, standard single-reference matching misses the true difference in ≥99.99% of draws.
        </p>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Model Pair</th>
                <th className={styles.num}>Oracle (E3) p-value</th>
                <th>Oracle Decision</th>
                <th className={styles.num}>E1 Mean p-value</th>
                <th className={styles.num}>E1 Miss Rate</th>
                <th className={styles.num}>E2 Mean p-value</th>
                <th className={styles.num}>E2 Miss Rate</th>
              </tr>
            </thead>
            <tbody>
              {RCR_PAIRWISE_DETECTION.map((p) => (
                <tr key={p.pair}>
                  <td className={styles.mono}>{p.pair}</td>
                  <td className={styles.num} style={{ fontWeight: 600 }}>{p.oracleP}</td>
                  <td>
                    <span style={{ 
                      color: p.decision.includes("better") ? "var(--accent)" : "var(--muted-foreground)",
                      fontWeight: p.decision.includes("better") ? 600 : 400
                    }}>
                      {p.decision}
                    </span>
                  </td>
                  <td className={styles.num}>{p.e1P}</td>
                  <td className={styles.num} style={{ color: p.e1MissRate !== "—" ? "var(--danger, #ef4444)" : "inherit" }}>
                    {p.e1MissRate}
                  </td>
                  <td className={styles.num}>{p.e2P}</td>
                  <td className={styles.num} style={{ color: p.e2MissRate !== "—" ? "var(--danger, #ef4444)" : "inherit" }}>
                    {p.e2MissRate}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Src>paper/TABLES/table3_significance_detection.md · research/ssr_pilot/results/rcrc/extended_analysis.json</Src>
      </div>

      <div className={styles.grid2}>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Reversal rate if the curator favours the canonical answer</p>
          <p className={styles.cardSub}>E2 pairwise reversal (%) as the chance p of picking the canonical reference rises</p>
          <BarList
            rows={RCR_SENSITIVITY.map((r) => ({ label: r.label, value: r.value, display: `${r.value.toFixed(2)}%` }))}
            max={20}
          />
          <Src>research/ssr_pilot/results/rcrc/reference_distribution_sensitivity.csv</Src>
        </div>
        <div className={styles.card}>
          <p className={styles.cardTitle}>Where the reversals live, by task family</p>
          <p className={styles.cardSub}>E2 pairwise reversal (%). Scheduling is 0 because three of four models solve none of its worlds.</p>
          <BarList
            rows={RCR_FAMILY.map((r) => ({ label: r.label, value: r.value, display: `${r.value.toFixed(2)}%` }))}
            max={25}
          />
          <Src>research/ssr_pilot/results/rcrc/extended_analysis.json (by_family)</Src>
        </div>
      </div>

      <div className={styles.card}>
        <p className={styles.cardTitle}>Matching against k references restores detection</p>
        <p className={styles.cardSub}>
          Share of draws that detect the two differences the validator finds (qwen3:8b over llama3.1:8b and over
          mistral:7b-instruct). The attenuation law E[E2] = E3 / |V(x)| held with r = 1.000 over 42 model-task cells.
        </p>
        <div className={styles.scroll}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>k references</th>
                {RCR_KREF.map((r) => (
                  <th className={styles.num} key={r.k}>{r.k}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>qwen3 beats llama3.1</td>
                {RCR_KREF.map((r) => (
                  <td className={styles.num} key={r.k}>{(r.llama * 100).toFixed(0)}%</td>
                ))}
              </tr>
              <tr>
                <td>qwen3 beats mistral</td>
                {RCR_KREF.map((r) => (
                  <td className={styles.num} key={r.k}>{(r.mistral * 100).toFixed(0)}%</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
        <Src>research/ssr_pilot/results/rcrc/kref_attenuation.json (k_reference, attenuation_law)</Src>
      </div>

      <p className={styles.callout + " " + styles.calloutWarn}>
        <strong>Scope.</strong> One 24-world benchmark and four sub-10B models at low accuracy. The preregistered pilot
        verdict was CONDITIONAL, and the RCR analyses are a post-hoc reanalysis of the same frozen generations, so they
        need replication on a second domain before being treated as confirmatory (paper/PAPER_FINAL.md, sections 9 and
        10).
      </p>
    </section>
  );
}

export function RunIt() {
  return (
    <section id="run" className={styles.section} aria-labelledby="h-run">
      <h2 id="h-run">Run it yourself</h2>
      <p className={styles.sectionLede}>
        Retrieval metrics need no model server. RAGAS runs need Ollama with the generator and judge pulled.
      </p>
      <h3>RAG evaluation</h3>
      <pre className={styles.code}>{`# retrieval only: recall@k, full_recall@k, MRR (seconds per config)
PYTHONPATH=. .venv/bin/python -m eval.retrieval_eval
PYTHONPATH=. .venv/bin/python -m eval.retrieval_eval --include-llm-techniques

# quick smoke test of the RAGAS sweep: 3 questions, 2 variants
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --quick

# the focused sweep, then prompts and temperatures on one fixed config
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --focused
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --prompts few_shot cot
PYTHONPATH=. .venv/bin/python -m eval.ragas_eval --temperatures 0.0 0.2`}</pre>
      <Src>eval/retrieval_eval.py and eval/ragas_eval.py argument parsers</Src>
      <h3>RCR</h3>
      <pre className={styles.code}>{`PYTHONPATH=. .venv/bin/pytest tests/ -v
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION
PYTHONPATH=. .venv/bin/python -m research.ssr_pilot.analyze_stated_convention`}</pre>
      <Src>README.md quick start; paper/REPRODUCIBILITY.md for all nine steps and SHA-256 checksums</Src>
      <h3>The full write-ups</h3>
      <ul className={styles.list}>
        <li className={styles.listItem}><span className={styles.mono}>FINDINGS.md</span> every defect and analysis, with measurements</li>
        <li className={styles.listItem}><span className={styles.mono}>HYPOTHESES.md</span> the queue, with falsification criteria</li>
        <li className={styles.listItem}><span className={styles.mono}>paper/PAPER_FINAL.md</span> the RCR manuscript</li>
        <li className={styles.listItem}><span className={styles.mono}>docs/GUIDE_PART2_RAG_CHATBOT_PIPELINE.md</span> the chatbot pipeline, end to end, with a worked example</li>
        <li className={styles.listItem}><span className={styles.mono}>docs/GUIDE_PART1_RESEARCH_PAPER.md</span> the research paper (RCR), end to end</li>
      </ul>
    </section>
  );
}
