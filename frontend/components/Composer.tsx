"use client";

import { useRef } from "react";
import type { KeyboardEvent } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
  placeholder?: string;
  /** True while the active session has a response streaming in -- swaps the
   * Send button for a Stop button. */
  isStreaming?: boolean;
  onStop?: () => void;
}

export default function Composer({
  value,
  onChange,
  onSend,
  disabled,
  placeholder,
  isStreaming,
  onStop,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSend();
    }
  }

  return (
    <div className="flex items-end gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2 shadow-sm">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? "Ask about the course…"}
        rows={1}
        className="flex-1 resize-none bg-transparent px-2 py-2 outline-none text-[var(--color-foreground)] placeholder:text-[var(--color-muted-foreground)] max-h-40 [field-sizing:content]"
      />
      {isStreaming ? (
        <button
          type="button"
          onClick={onStop}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-medium cursor-pointer hover:bg-[var(--color-danger-soft)] hover:text-[var(--color-danger)] transition-colors"
        >
          Stop
        </button>
      ) : (
        <button
          type="button"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="rounded-lg bg-[var(--color-accent)] text-[var(--color-accent-foreground)] px-4 py-2 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer hover:opacity-90 transition-opacity"
        >
          Send
        </button>
      )}
    </div>
  );
}
