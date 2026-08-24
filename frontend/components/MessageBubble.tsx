"use client";

import type { ChatMessage } from "@/lib/types";
import SourcesPanel from "./SourcesPanel";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80ch] rounded-2xl px-4 py-3 leading-relaxed whitespace-pre-wrap break-words shadow-sm ${
          isUser
            ? "bg-[var(--color-user-bubble)] text-[var(--color-user-bubble-foreground)]"
            : "bg-[var(--color-assistant-bubble)] text-[var(--color-assistant-bubble-foreground)] border border-[var(--color-border)]"
        }`}
      >
        {message.error ? (
          <div className="rounded-md bg-[var(--color-danger-soft)] text-[var(--color-danger)] px-3 py-2 text-sm">
            {message.error}
          </div>
        ) : message.streaming && !message.content ? (
          <div className="flex items-center gap-1.5 py-1" role="status" aria-label="Waiting for a response">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted-foreground)] animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted-foreground)] animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted-foreground)] animate-bounce" />
          </div>
        ) : (
          <>
            <span>{message.content}</span>
            {message.streaming && (
              <span
                className="inline-block w-[0.5ch] ml-0.5 -mb-0.5 h-[1em] bg-[var(--color-accent)] animate-pulse align-middle"
                aria-hidden
              />
            )}
          </>
        )}

        {!message.streaming && !isUser && message.sources && (
          <SourcesPanel sources={message.sources} />
        )}
      </div>
    </div>
  );
}
