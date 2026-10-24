import styles from "./research.module.css";
import { NOISE_FLOOR, type Effect } from "./data";

/** Diverging bar chart of effect sizes with the benchmark's noise band drawn
 * behind every bar. HTML/CSS rather than SVG so labels stay readable on a
 * phone. */
export function EffectChart({ effects }: { effects: Effect[] }) {
  const half = 0.12; // axis runs -0.12 .. +0.12
  const pct = (v: number) => (Math.abs(v) / half) * 50;
  const bandWidth = pct(NOISE_FLOOR) * 2;
  return (
    <div>
      <div className={styles.bars} role="list">
        {effects.map((e) => {
          const positive = e.delta >= 0;
          const colour = !e.established
            ? styles.fillMuted
            : positive
              ? ""
              : styles.fillDanger;
          return (
            <div className={styles.barRow} role="listitem" key={e.label}>
              <div className={styles.barLabel}>
                {e.label}
                <div className={styles.barNote}>
                  {e.note} · {e.src}
                </div>
              </div>
              <div className={styles.effectTrack} aria-hidden>
                <div className={styles.noiseBand} style={{ left: `${50 - bandWidth / 2}%`, width: `${bandWidth}%` }} />
                <div className={styles.zeroLine} />
                <div
                  className={`${styles.effectBar} ${styles.fill} ${colour}`}
                  style={
                    positive
                      ? { left: "50%", width: `${pct(e.delta)}%` }
                      : { left: `${50 - pct(e.delta)}%`, width: `${pct(e.delta)}%` }
                  }
                />
              </div>
              <div className={styles.barValue}>
                {e.delta > 0 ? "+" : "−"}
                {Math.abs(e.delta).toFixed(3)}
                <span className="sr-only"> {e.established ? "established" : "not established"}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div className={styles.legend}>
        <span>
          <span className={`${styles.swatch} ${styles.swatchNoise}`} />
          run-to-run noise ±{NOISE_FLOOR}
        </span>
        <span>
          <span className={styles.swatch} style={{ background: "var(--accent)" }} />
          established gain
        </span>
        <span>
          <span className={styles.swatch} style={{ background: "var(--danger)" }} />
          established loss
        </span>
        <span>
          <span className={`${styles.swatch} ${styles.fillMuted}`} />
          inside the noise: not established
        </span>
      </div>
    </div>
  );
}

export interface BarDatum {
  label: string;
  value: number;
  note?: string;
  display?: string;
  tone?: "accent" | "muted" | "danger";
}

/** Horizontal bars on a 0..max scale. */
export function BarList({ rows, max = 1, digits = 3 }: { rows: BarDatum[]; max?: number; digits?: number }) {
  return (
    <div className={styles.bars} role="list">
      {rows.map((r) => (
        <div className={styles.barRow} role="listitem" key={r.label}>
          <div className={styles.barLabel}>
            {r.label}
            {r.note ? <div className={styles.barNote}>{r.note}</div> : null}
          </div>
          <div className={styles.track} aria-hidden>
            <div
              className={`${styles.fill} ${r.tone === "muted" ? styles.fillMuted : r.tone === "danger" ? styles.fillDanger : ""}`}
              style={{ width: `${Math.min(100, (r.value / max) * 100)}%` }}
            />
          </div>
          <div className={styles.barValue}>{r.display ?? r.value.toFixed(digits)}</div>
        </div>
      ))}
    </div>
  );
}

function Arrow({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) {
  // Short head drawn as a small triangle pointing along the segment.
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const hx = x2 - ux * 7;
  const hy = y2 - uy * 7;
  const px = -uy * 4;
  const py = ux * 4;
  return (
    <g>
      <line className={styles.dArrow} x1={x1} y1={y1} x2={hx} y2={hy} />
      <polygon className={styles.dArrowHead} points={`${x2},${y2} ${hx + px},${hy + py} ${hx - px},${hy - py}`} />
    </g>
  );
}

function Box({
  x, y, w = 104, h = 56, title, sub, kind = "box",
}: {
  x: number; y: number; w?: number; h?: number; title: string; sub: string;
  kind?: "box" | "accent" | "optional";
}) {
  const cls = kind === "accent" ? styles.dBoxAccent : kind === "optional" ? styles.dBoxOptional : styles.dBox;
  return (
    <g>
      <rect className={cls} x={x} y={y} width={w} height={h} rx={9} />
      <text className={styles.dText} x={x + w / 2} y={y + 23} textAnchor="middle">{title}</text>
      <text className={styles.dSub} x={x + w / 2} y={y + 40} textAnchor="middle">{sub}</text>
    </g>
  );
}

/** Serving path on top, evaluation path underneath. */
export function PipelineDiagram() {
  const top = 46;
  const xs = [0, 124, 248, 372, 496, 620, 744, 868];
  const mid = top + 28;
  return (
    <svg
      className={styles.diagram}
      viewBox="0 0 972 330"
      role="img"
      aria-label="RAG pipeline: ingest, chunk, embed and index, retrieve, optional rerank, parent expansion, generate, answer. Below it the evaluation path: golden set, pipeline run, RAGAS judge, seven metrics."
    >
      <text className={styles.dLane} x={0} y={24}>Serving path</text>
      <Box x={xs[0]} y={top} title="Ingest" sub="PPTX · PDF · DOCX" />
      <Box x={xs[1]} y={top} title="Chunk" sub="child + parent" />
      <Box x={xs[2]} y={top} title="Embed + index" sub="bge-large · FAISS" />
      <Box x={xs[3]} y={top} title="Retrieve" sub="dense (+HyDE/MQ)" kind="accent" />
      <Box x={xs[4]} y={top} title="Rerank" sub="optional · off" kind="optional" />
      <Box x={xs[5]} y={top} title="Expand" sub="child → parent" />
      <Box x={xs[6]} y={top} title="Generate" sub="llama3 · few_shot" kind="accent" />
      <Box x={xs[7]} y={top} title="Answer" sub="+ cited sources" />
      {xs.slice(0, -1).map((x, i) => (
        <Arrow key={i} x1={x + 104} y1={mid} x2={xs[i + 1]} y2={mid} />
      ))}

      <text className={styles.dLane} x={0} y={170}>Evaluation path</text>
      <Box x={0} y={192} w={150} title="Golden set" sub="26 Q + ground truth" />
      <Box x={246} y={192} w={170} title="Pipeline run" sub="answer + contexts per Q" kind="accent" />
      <Box x={512} y={192} w={190} title="RAGAS judge" sub="qwen2.5:7b + bge-small" kind="accent" />
      <Box x={798} y={192} w={174} title="7 metrics / question" sub="mean, NaN-safe" />
      <Arrow x1={150} y1={220} x2={246} y2={220} />
      <Arrow x1={416} y1={220} x2={512} y2={220} />
      <Arrow x1={702} y1={220} x2={798} y2={220} />
      <Arrow x1={xs[6] + 52} y1={top + 56} x2={xs[6] + 52} y2={130} />
      <line className={styles.dArrow} x1={xs[6] + 52} y1={130} x2={331} y2={130} />
      <Arrow x1={331} y1={130} x2={331} y2={192} />

      <Box x={246} y={272} w={456} h={50} title="retrieval_eval: recall@k · full_recall@k · MRR" sub="side path: scores Retrieve alone, no LLM, seconds per config" kind="optional" />
    </svg>
  );
}
