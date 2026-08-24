"use client";

interface Props {
  models: string[];
  loading: boolean;
  loadError: string | null;
  value: string | null;
  onChange: (model: string) => void;
}

export default function ModelSelect({ models, loading, loadError, value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="model-select" className="text-sm text-[var(--color-muted-foreground)]">
        Model
      </label>
      <select
        id="model-select"
        className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
        value={value ?? ""}
        disabled={loading || models.length === 0}
        onChange={(e) => onChange(e.target.value)}
      >
        {loading && <option value="">Loading models…</option>}
        {!loading && models.length === 0 && <option value="">No models available</option>}
        {!loading &&
          models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
      </select>
      {loadError && <span className="text-xs text-[var(--color-danger)]">{loadError}</span>}
    </div>
  );
}
