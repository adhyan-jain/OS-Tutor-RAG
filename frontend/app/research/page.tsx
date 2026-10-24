import type { Metadata } from "next";
import Link from "next/link";
import styles from "@/components/research/research.module.css";
import { Caveats, Evaluation, Findings, Hero, Pipeline, Rcr, RunIt, TutorLayer } from "@/components/research/sections";

export const metadata: Metadata = {
  title: "Research · OS Tutor",
  description: "How the OS Tutor RAG pipeline was evaluated, what the measurements showed, and the reference-choice robustness study.",
};

const SECTIONS = [
  { id: "pipeline", label: "Pipeline" },
  { id: "tutor", label: "Tutor layer" },
  { id: "evaluation", label: "Evaluation" },
  { id: "findings", label: "Findings" },
  { id: "caveats", label: "Caveats" },
  { id: "rcr", label: "RCR" },
  { id: "run", label: "Run it" },
];

export default function ResearchPage() {
  return (
    <div className={styles.shell}>
      <div className={styles.topbar}>
        <div className={styles.topbarInner}>
          <Link href="/" className={styles.brand}>
            OS Tutor <span>/ research</span>
          </Link>
          <nav className={styles.nav} aria-label="Sections">
            {SECTIONS.map((s) => (
              <a key={s.id} href={`#${s.id}`}>
                {s.label}
              </a>
            ))}
          </nav>
          <Link href="/" className={styles.back}>
            Back to the tutor
          </Link>
        </div>
      </div>
      <main className={styles.main}>
        <Hero />
        <Pipeline />
        <TutorLayer />
        <Evaluation />
        <Findings />
        <Caveats />
        <Rcr />
        <RunIt />
      </main>
    </div>
  );
}
