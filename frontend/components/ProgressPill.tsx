"use client";

import { useState } from "react";
import type { TutorProgress } from "@/lib/types";

/** How much of the course this chat has covered, and where the student stands
 * on each concept they have touched. A summary, not a grade: the states are
 * the tutor's best evidence so far. */
export default function ProgressPill({ progress }: { progress: TutorProgress | null }) {
  const [open, setOpen] = useState(false);
  if (!progress || progress.concepts.length === 0) return null;
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-xs text-[var(--color-muted-foreground)] cursor-pointer hover:text-[var(--color-foreground)]"
      >
        {progress.understood}/{progress.total} understood · {progress.concepts.length} explored
      </button>
      {open && (
        <ul className="absolute bottom-full left-0 mb-2 w-[min(16rem,calc(100vw-2rem))] max-h-64 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-sm shadow-lg z-10">
          {progress.concepts.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-3 px-2 py-1">
              <span>{c.name}</span>
              <span className="text-xs text-[var(--color-muted-foreground)]">{c.label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
