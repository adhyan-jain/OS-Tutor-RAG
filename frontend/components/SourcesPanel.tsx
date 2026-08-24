"use client";

import { useState } from "react";
import type { Source } from "@/lib/types";

function describeMetadata(metadata: Record<string, unknown>): string | null {
  const parts: string[] = [];
  // Common keys we'd expect from a slide/section chunker; show whichever exist.
  const preferredKeys = ["slide", "slide_number", "page", "page_number", "section", "title"];
  for (const key of preferredKeys) {
    const value = metadata[key];
    if (value !== undefined && value !== null && value !== "") {
      const label = key.replace(/_/g, " ");
      parts.push(`${label} ${value}`);
    }
  }
  if (parts.length > 0) return parts.join(" · ");

  // Fall back to any remaining scalar fields so nothing useful gets hidden.
  const fallback = Object.entries(metadata)
    .filter(([, v]) => typeof v === "string" || typeof v === "number")
    .slice(0, 3)
    .map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`);
  return fallback.length > 0 ? fallback.join(" · ") : null;
}

export default function SourcesPanel({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2 text-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors cursor-pointer"
      >
        <span
          className={`inline-block transition-transform ${open ? "rotate-90" : ""}`}
          aria-hidden
        >
          ▸
        </span>
        Sources ({sources.length})
      </button>

      {open && (
        <ul className="mt-2 space-y-1.5">
          {sources.map((s) => {
            const meta = describeMetadata(s.metadata ?? {});
            return (
              <li
                key={s.chunk_id}
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2"
              >
                <div className="font-medium text-[var(--color-foreground)]">{s.doc_id}</div>
                <div className="text-[var(--color-muted-foreground)] text-xs mt-0.5">
                  {meta ? <span>{meta}</span> : null}
                  {meta ? " · " : ""}
                  score {s.score.toFixed(3)}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
