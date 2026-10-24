"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatSession } from "@/lib/types";

interface Props {
  sessions: ChatSession[]; // pre-sorted, newest first
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
  /** Below the `sm` breakpoint the list is a slide-in drawer; this opens it. */
  open?: boolean;
  onClose?: () => void;
}

function SessionRow({
  session,
  active,
  onSelect,
  onDelete,
  onRename,
}: {
  session: ChatSession;
  active: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(session.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  function commit() {
    const trimmed = draft.trim();
    onRename(trimmed || session.title);
    setEditing(false);
  }

  return (
    <div
      className={`group flex items-center gap-1 rounded-md px-2 py-2 text-sm transition-colors ${
        editing ? "" : "cursor-pointer"
      } ${
        active
          ? "bg-[var(--color-accent-soft)] text-[var(--color-foreground)]"
          : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-surface)]"
      }`}
      onClick={editing ? undefined : onSelect}
    >
      {editing ? (
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") {
              setDraft(session.title);
              setEditing(false);
            }
          }}
          className="flex-1 min-w-0 rounded bg-[var(--color-surface)] border border-[var(--color-border)] px-1.5 py-0.5 text-sm outline-none"
        />
      ) : (
        <span
          className="flex-1 truncate"
          onDoubleClick={(e) => {
            e.stopPropagation();
            setEditing(true);
          }}
          title="Double-click to rename"
        >
          {session.title}
        </span>
      )}
      {!editing && (
        <div className="flex items-center sm:opacity-0 sm:group-hover:opacity-100 sm:focus-within:opacity-100 transition-opacity">
          <button
            type="button"
            aria-label="Rename chat"
            onClick={(e) => {
              e.stopPropagation();
              setEditing(true);
            }}
            className="text-xs px-1.5 py-0.5 rounded hover:bg-[var(--color-surface)] cursor-pointer"
          >
            ✎
          </button>
          <button
            type="button"
            aria-label="Delete chat"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="text-xs px-1.5 py-0.5 rounded hover:bg-[var(--color-danger-soft)] hover:text-[var(--color-danger)] cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ sessions, activeId, onSelect, onNew, onDelete, onRename, open = false, onClose }: Props) {
  // Esc closes the drawer (it only exists below `sm`).
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // The same list serves the fixed desktop column and the mobile drawer; in the
  // drawer, picking a chat or starting a new one also closes it.
  const list = (closeAfter: boolean) => (
    <>
      <div className="p-3">
        <button
          type="button"
          onClick={() => {
            onNew();
            if (closeAfter) onClose?.();
          }}
          className="w-full min-h-11 sm:min-h-0 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm font-medium hover:bg-[var(--color-accent-soft)] transition-colors cursor-pointer"
        >
          + New chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1">
        {sessions.map((s) => (
          <SessionRow
            key={s.id}
            session={s}
            active={s.id === activeId}
            onSelect={() => {
              onSelect(s.id);
              if (closeAfter) onClose?.();
            }}
            onDelete={() => onDelete(s.id)}
            onRename={(title) => onRename(s.id, title)}
          />
        ))}
      </div>
    </>
  );

  return (
    <>
      <div className="hidden sm:flex w-64 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface-2)]">
        {list(false)}
      </div>
      {open && (
        <div className="sm:hidden fixed inset-0 z-40 flex" role="dialog" aria-modal="true" aria-label="Your chats">
          <div className="flex w-72 max-w-[85vw] flex-col border-r border-[var(--color-border)] bg-[var(--color-surface-2)] shadow-xl pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
            <div className="flex items-center justify-between px-3 pt-3">
              <span className="text-sm font-semibold">Your chats</span>
              <button
                type="button"
                aria-label="Close chats"
                onClick={onClose}
                className="flex min-h-11 min-w-11 items-center justify-center rounded-md text-[var(--color-muted-foreground)] cursor-pointer"
              >
                ✕
              </button>
            </div>
            {list(true)}
          </div>
          <button type="button" aria-label="Close chats" onClick={onClose} className="flex-1 bg-black/40 cursor-pointer" />
        </div>
      )}
    </>
  );
}
