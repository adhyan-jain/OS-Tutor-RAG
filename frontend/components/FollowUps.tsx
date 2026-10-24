"use client";

import type { TutorUI } from "@/lib/types";

const STATE_DOT: Record<string, string> = {
  UNKNOWN: "bg-[var(--color-border)]",
  INTRODUCED: "bg-[var(--color-muted-foreground)]",
  ATTEMPTED: "bg-[var(--color-muted-foreground)]",
  PARTIALLY_UNDERSTOOD: "bg-[var(--color-accent)] opacity-60",
  UNDERSTOOD: "bg-[var(--color-accent)]",
  MASTERED: "bg-[var(--color-accent)]",
};

/** Suggested next messages under an assistant turn. Every chip is a complete
 * message, so tapping it is the same as typing it; only the latest turn's
 * chips are live. For a student who does not know what to ask, this is the
 * difference between an empty box and a next step. */
export default function FollowUps({
  ui,
  onPick,
  disabled,
}: {
  ui: TutorUI;
  onPick: (text: string) => void;
  disabled?: boolean;
}) {
  const asking = !!ui.question;
  return (
    <div className="mt-2 px-1 space-y-2 max-w-[80ch]">
      {(ui.concept || asking) && (
        <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--color-muted-foreground)]">
          {asking && ui.question && (
            <span className="rounded-full border border-[var(--color-accent)] bg-[var(--color-accent-soft)] px-2 py-0.5 font-medium text-[var(--color-accent)]">
              {ui.question.source === "quiz" ? "Quiz" : "Check yourself"}
              {ui.question.level ? ` · ${ui.question.level}` : ""}
            </span>
          )}
          {ui.concept && (
            <span className="inline-flex items-center gap-1.5" title={ui.concept.text}>
              <span className={`inline-block h-2 w-2 rounded-full ${STATE_DOT[ui.concept.state] ?? STATE_DOT.UNKNOWN}`} aria-hidden />
              {ui.concept.name} · {ui.concept.state_label}
            </span>
          )}
        </div>
      )}
      {ui.chips.length > 0 && (
        <div className="chip-in flex flex-col gap-2 sm:flex-row sm:flex-wrap" role="group" aria-label={asking ? "Ways to respond" : "Suggested follow-ups"}>
          {ui.chips.map((chip) => (
            <button
              key={chip}
              type="button"
              disabled={disabled}
              onClick={() => onPick(chip)}
              className="min-h-11 sm:min-h-0 rounded-2xl sm:rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 sm:px-3 py-2 sm:py-1.5 text-left text-sm leading-snug text-[var(--color-foreground)] transition-colors cursor-pointer hover:border-[var(--color-accent)] hover:bg-[var(--color-accent-soft)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {chip}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
