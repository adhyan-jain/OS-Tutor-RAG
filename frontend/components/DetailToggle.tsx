"use client";

import { DETAIL_LEVELS, type DetailLevel } from "@/lib/types";

interface Props {
  value: DetailLevel;
  onChange: (level: DetailLevel) => void;
}

export default function DetailToggle({ value, onChange }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label="Detail level"
      className="inline-flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] p-1 gap-1"
    >
      {DETAIL_LEVELS.map((level) => {
        const active = level.value === value;
        return (
          <button
            key={level.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(level.value)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer ${
              active
                ? "bg-[var(--color-accent)] text-[var(--color-accent-foreground)]"
                : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
            }`}
          >
            {level.label}
          </button>
        );
      })}
    </div>
  );
}
