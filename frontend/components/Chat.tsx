"use client";

import { useEffect, useRef, useState } from "react";
import { fetchModels, postChat } from "@/lib/api";
import { streamSSE } from "@/lib/sse";
import {
  deriveTitle,
  loadActiveId,
  loadSessions,
  makeSession,
  saveActiveId,
  saveSessions,
} from "@/lib/sessionStore";
import type { ChatMessage, ChatSession, DetailLevel, Source } from "@/lib/types";
import ModelSelect from "./ModelSelect";
import DetailToggle from "./DetailToggle";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import Sidebar from "./Sidebar";

const LAST_MODEL_KEY = "os-tutor:last-model";

function newId(): string {
  return crypto.randomUUID();
}

export default function Chat({
  apiToken,
  onLogout,
}: {
  apiToken?: string;
  /** Present only when auth is on and a real session exists -- renders a
   * "Sign out" control. */
  onLogout?: () => void;
}) {
  const [sessions, setSessions] = useState<Record<string, ChatSession>>({});
  const [activeId, setActiveId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  const [models, setModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelLoadError, setModelLoadError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const [detailLevel, setDetailLevel] = useState<DetailLevel>("undergrad");
  const [input, setInput] = useState("");
  // Sessions with a request in flight -- tracked per-session (not one global
  // flag) so switching to another chat while one streams doesn't block it.
  const [streamingIds, setStreamingIds] = useState<Set<string>>(new Set());
  const abortControllers = useRef<Map<string, AbortController>>(new Map());

  const scrollRef = useRef<HTMLDivElement>(null);

  // Restore persisted sessions (migrating the old single-thread format if
  // needed) on mount. Must happen in an effect, not a lazy useState
  // initializer, so server-rendered and first client render match.
  useEffect(() => {
    const restored = loadSessions();
    const restoredIds = Object.keys(restored);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (restoredIds.length === 0) {
      const fresh = makeSession();
      setSessions({ [fresh.id]: fresh });
      setActiveId(fresh.id);
    } else {
      setSessions(restored);
      const storedActive = loadActiveId();
      setActiveId(storedActive && restored[storedActive] ? storedActive : restoredIds[0]);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    saveSessions(sessions);
  }, [sessions, hydrated]);

  useEffect(() => {
    if (!hydrated || !activeId) return;
    saveActiveId(activeId);
  }, [activeId, hydrated]);

  // Load the model list once on mount, preferring whichever model was last
  // used (if it's still available) over just the first one returned.
  useEffect(() => {
    fetchModels(apiToken)
      .then((list) => {
        setModels(list);
        if (list.length > 0) {
          let lastUsed: string | null = null;
          try {
            lastUsed = localStorage.getItem(LAST_MODEL_KEY);
          } catch {
            // ignore
          }
          setSelectedModel(lastUsed && list.includes(lastUsed) ? lastUsed : list[0]);
        }
      })
      .catch((err: Error) => setModelLoadError(err.message))
      .finally(() => setModelsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedModel) return;
    try {
      localStorage.setItem(LAST_MODEL_KEY, selectedModel);
    } catch {
      // ignore
    }
  }, [selectedModel]);

  const messages = (activeId && sessions[activeId]?.messages) || [];

  // Keep the view scrolled to the latest message as content streams in.
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function updateSessionMessages(
    sessionId: string,
    updater: (messages: ChatMessage[]) => ChatMessage[],
  ) {
    setSessions((prev) => {
      const session = prev[sessionId];
      if (!session) return prev;
      return {
        ...prev,
        [sessionId]: { ...session, messages: updater(session.messages) },
      };
    });
  }

  function setStreaming(sessionId: string, value: boolean) {
    setStreamingIds((prev) => {
      const next = new Set(prev);
      if (value) next.add(sessionId);
      else next.delete(sessionId);
      return next;
    });
  }

  // Keyed by an explicit sessionId (not "whichever is active right now") so
  // switching chats mid-stream doesn't corrupt or lose the response --
  // it keeps writing into the session it was actually asked about.
  async function runQuestion(sessionId: string, question: string, assistantId: string) {
    const controller = new AbortController();
    abortControllers.current.set(sessionId, controller);
    setStreaming(sessionId, true);

    function updateAssistant(patch: Partial<ChatMessage>) {
      updateSessionMessages(sessionId, (msgs) =>
        msgs.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)),
      );
    }

    // Clear any prior error/content so a retry/regenerate starts fresh.
    updateAssistant({ content: "", error: undefined, sources: undefined, streaming: true });

    try {
      const response = await postChat(
        {
          session_id: sessionId,
          question,
          model_name: selectedModel!,
          detail_level: detailLevel,
        },
        apiToken,
        controller.signal,
      );

      let content = "";
      await streamSSE(response, (evt) => {
        if (evt.event === "token") {
          const { token } = JSON.parse(evt.data) as { token: string };
          content += token;
          updateAssistant({ content });
        } else if (evt.event === "sources") {
          const sources = JSON.parse(evt.data) as Source[];
          updateAssistant({ sources, streaming: false });
        } else if (evt.event === "error") {
          const { error } = JSON.parse(evt.data) as { error: string };
          updateAssistant({ error, streaming: false });
        }
        // Anything else (e.g. sse-starlette keep-alive pings) is ignored.
      });

      updateAssistant({ streaming: false });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // Deliberate stop -- keep whatever streamed so far, no error banner.
        updateAssistant({ streaming: false });
      } else {
        updateAssistant({
          streaming: false,
          error: err instanceof Error ? err.message : "Something went wrong contacting the backend.",
        });
      }
    } finally {
      abortControllers.current.delete(sessionId);
      setStreaming(sessionId, false);
    }
  }

  function handleSend() {
    const question = input.trim();
    if (!question || !selectedModel || !activeId || streamingIds.has(activeId)) return;

    const userMessage: ChatMessage = { id: newId(), role: "user", content: question };
    const assistantId = newId();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
    };

    setSessions((prev) => {
      const session = prev[activeId];
      if (!session) return prev;
      // Only auto-derive a title from the first question if the user hasn't
      // already renamed this chat themselves (including renaming it before
      // sending anything) -- a manual rename always wins.
      const shouldAutoTitle = session.messages.length === 0 && session.title === "New chat";
      return {
        ...prev,
        [activeId]: {
          ...session,
          title: shouldAutoTitle ? deriveTitle(question) : session.title,
          updatedAt: Date.now(),
          messages: [...session.messages, userMessage, assistantMessage],
        },
      };
    });
    setInput("");
    void runQuestion(activeId, question, assistantId);
  }

  function handleStop() {
    if (!activeId) return;
    abortControllers.current.get(activeId)?.abort();
  }

  // Resend the question behind a message in place -- used both for a
  // network-error retry (don't make the student retype anything) and for
  // "regenerate" on a normal completed answer.
  function rerunFrom(assistantMessageId: string) {
    if (!activeId || streamingIds.has(activeId)) return;
    const index = messages.findIndex((m) => m.id === assistantMessageId);
    if (index <= 0) return;
    const userMessage = messages[index - 1];
    if (userMessage.role !== "user") return;
    void runQuestion(activeId, userMessage.content, assistantMessageId);
  }

  function handleRenameSession(id: string, title: string) {
    setSessions((prev) => {
      const session = prev[id];
      if (!session) return prev;
      return { ...prev, [id]: { ...session, title } };
    });
  }

  function handleNewChat() {
    const fresh = makeSession();
    setSessions((prev) => ({ ...prev, [fresh.id]: fresh }));
    setActiveId(fresh.id);
    setInput("");
  }

  function handleDeleteSession(id: string) {
    setSessions((prev) => {
      const next = { ...prev };
      delete next[id];
      if (Object.keys(next).length === 0) {
        const fresh = makeSession();
        next[fresh.id] = fresh;
        if (activeId === id) setActiveId(fresh.id);
      } else if (activeId === id) {
        const newest = Object.values(next).sort((a, b) => b.updatedAt - a.updatedAt)[0];
        setActiveId(newest.id);
      }
      return next;
    });
    abortControllers.current.get(id)?.abort();
  }

  const isActiveStreaming = !!activeId && streamingIds.has(activeId);
  const sendDisabled = isActiveStreaming || !selectedModel || !activeId;
  const sortedSessions = Object.values(sessions).sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <div className="flex h-dvh">
      {hydrated && activeId && (
        <Sidebar
          sessions={sortedSessions}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={handleNewChat}
          onDelete={handleDeleteSession}
          onRename={handleRenameSession}
        />
      )}

      <div className="flex flex-col h-dvh mx-auto w-full max-w-3xl">
        <header className="flex items-center justify-between gap-4 px-4 py-3 border-b border-[var(--color-border)]">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">OS Tutor</h1>
            <p className="text-xs text-[var(--color-muted-foreground)]">
              Grounded answers from the course material
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ModelSelect
              models={models}
              loading={modelsLoading}
              loadError={modelLoadError}
              value={selectedModel}
              onChange={setSelectedModel}
            />
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors cursor-pointer"
              >
                Sign out
              </button>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="max-w-xl mx-auto mt-10 text-center space-y-4">
              <h2 className="text-base font-semibold tracking-tight">
                A grounded tutor, not a search engine
              </h2>
              <p className="text-sm text-[var(--color-muted-foreground)] leading-relaxed">
                Answers are drawn only from the actual course material — lecture
                slides and reading sections — and every reply cites which ones
                it used. It's a flexible conversation, not a rigid script: ask
                for an overview and you'll get one directly, but for a genuinely
                deep or multi-step idea it'll teach incrementally with a
                comprehension check, the way a good tutor would.
              </p>
              <p className="text-sm text-[var(--color-muted-foreground)]">
                Ask a question about the operating systems course to get started.
              </p>
            </div>
          )}
          {messages.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              onRetry={m.role === "assistant" && m.error ? () => rerunFrom(m.id) : undefined}
              onRegenerate={
                m.role === "assistant" && !m.error && !m.streaming
                  ? () => rerunFrom(m.id)
                  : undefined
              }
            />
          ))}
          <div ref={scrollRef} />
        </div>

        <div className="px-4 pb-4 pt-2 border-t border-[var(--color-border)] space-y-3">
          <DetailToggle value={detailLevel} onChange={setDetailLevel} />
          <Composer
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={sendDisabled}
            isStreaming={isActiveStreaming}
            onStop={handleStop}
            placeholder={
              !selectedModel ? "Waiting for a model to load…" : "Ask about the course…"
            }
          />
        </div>
      </div>
    </div>
  );
}
