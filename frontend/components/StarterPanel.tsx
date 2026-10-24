"use client";

import { useState } from "react";
import type { TutorOverview } from "@/lib/types";

/** Empty-chat panel for a student who knows nothing yet: a few questions to
 * tap, and the whole course as a short learning path grouped by unit. Tapping
 * anything sends it as a normal message. */
export default function StarterPanel({
  overview,
  onPick,
}: {
  overview: TutorOverview | null;
  onPick: (text: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const units = overview
    ? overview.path.reduce<Record<string, TutorOverview["path"]>>((acc, c) => {
        (acc[c.topic] ||= []).push(c);
        return acc;
      }, {})
    : {};

  return (
    <div className="max-w-xl mx-auto mt-4 sm:mt-10 space-y-5 text-center">
      <div className="space-y-2">
        <h2 className="text-base font-semibold tracking-tight">A grounded tutor, not a search engine</h2>
        <p className="text-sm text-[var(--color-muted-foreground)] leading-relaxed">
          Answers come from your actual course material, with sources. After an answer I&apos;ll ask one
          short question so you can check you&apos;ve really got it, and I&apos;ll give hints instead of
          just telling you. Not sure what to ask? Start with one of these.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row sm:flex-wrap justify-center gap-2">
        {(overview?.starters ?? [
          "I'm new to operating systems. Where should I start?",
          "What is an operating system and what does it actually do?",
        ]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onPick(s)}
            className="w-full sm:w-auto min-h-11 sm:min-h-0 rounded-2xl sm:rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 sm:px-3 py-2 sm:py-1.5 text-sm transition-colors cursor-pointer hover:border-[var(--color-accent)] hover:bg-[var(--color-accent-soft)]"
          >
            {s}
          </button>
        ))}
      </div>

      {overview && (
        <div className="text-left">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="mx-auto block text-sm text-[var(--color-accent)] underline underline-offset-2 cursor-pointer"
          >
            {open ? "Hide the course map" : "Show the course map"}
          </button>
          {open && (
            <div className="mt-3 space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
              {Object.entries(units).map(([unit, items]) => (
                <section key={unit}>
                  <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
                    {unit}
                  </h3>
                  <ul className="flex flex-wrap gap-1.5">
                    {items.map((c) => (
                      <li key={c.id}>
                        <button
                          type="button"
                          title={c.summary}
                          onClick={() => onPick(`Explain ${c.name} in simple words`)}
                          className="rounded-md bg-[var(--color-surface-2)] px-2 py-1 text-xs transition-colors cursor-pointer hover:bg-[var(--color-accent-soft)]"
                        >
                          {c.name}
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
