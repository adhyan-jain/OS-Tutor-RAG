"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/types";

/** Renders assistant answers as markdown (GitHub-flavored, so pipe tables
 * work) rather than raw text -- the model is instructed (see
 * src/generation/teaching_prompt.py) to use markdown, including tables, for
 * naturally tabular content, and this is what actually turns that into a
 * real table instead of literal pipe/dash characters. react-markdown copes
 * fine with a mid-stream, not-yet-complete markdown string (e.g. an
 * unclosed table row) -- it just renders its best partial interpretation of
 * what's arrived so far, never throws. */
function AssistantMarkdown({ content }: { content: string }) {
  return (
    <div className="prose-chat">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // A wide table shouldn't overflow the bubble or force the whole
          // page to scroll sideways -- give it its own horizontal scroll.
          table: ({ children }) => (
            <div className="table-scroll">
              <table>{children}</table>
            </div>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default function MessageBubble({
  message,
  onRetry,
}: {
  message: ChatMessage;
  /** Present only on an errored assistant message that has a retryable
   * question behind it -- resends that same question in place. */
  onRetry?: () => void;
}) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80ch] rounded-2xl px-4 py-3 leading-relaxed break-words shadow-sm ${
          isUser
            ? "bg-[var(--color-user-bubble)] text-[var(--color-user-bubble-foreground)]"
            : "bg-[var(--color-assistant-bubble)] text-[var(--color-assistant-bubble-foreground)] border border-[var(--color-border)]"
        }`}
      >
        {message.error ? (
          <div className="rounded-md bg-[var(--color-danger-soft)] text-[var(--color-danger)] px-3 py-2 text-sm space-y-2 whitespace-pre-wrap">
            <div>{message.error}</div>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="text-xs font-medium underline underline-offset-2 hover:opacity-80 cursor-pointer"
              >
                Retry
              </button>
            )}
          </div>
        ) : message.streaming && !message.content ? (
          <div className="flex items-center gap-1.5 py-1" role="status" aria-label="Waiting for a response">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted-foreground)] animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted-foreground)] animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted-foreground)] animate-bounce" />
          </div>
        ) : isUser ? (
          <span className="whitespace-pre-wrap">{message.content}</span>
        ) : (
          <>
            <AssistantMarkdown content={message.content} />
            {message.streaming && (
              <span
                className="inline-block w-[0.5ch] ml-0.5 -mb-0.5 h-[1em] bg-[var(--color-accent)] animate-pulse align-middle"
                aria-hidden
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
