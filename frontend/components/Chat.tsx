"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { UIEvent } from "react";
import { fetchModels, fetchOverview, fetchProgress, postChat, resetSession, warmModel } from "@/lib/api";
import { streamSSE } from "@/lib/sse";
import {
  deriveTitle,
  loadActiveId,
  loadSessions,
  makeSession,
  saveActiveId,
  saveSessions,
} from "@/lib/sessionStore";
import type { ChatMessage, ChatSession, DetailLevel, Source, TutorOverview, TutorProgress, TutorUI } from "@/lib/types";
import ModelSelect from "./ModelSelect";
import DetailToggle from "./DetailToggle";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import Sidebar from "./Sidebar";
import FollowUps from "./FollowUps";
import StarterPanel from "./StarterPanel";
import ProgressPill from "./ProgressPill";

const LAST_MODEL_KEY = "os-tutor:last-model";
const SOCRATIC_KEY = "os-tutor:socratic";

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
  // Guided mode: after an answer the tutor asks one short question and grades
  // the reply. Off = plain answers.
  const [socratic, setSocratic] = useState(true);
  const [overview, setOverview] = useState<TutorOverview | null>(null);
  const [progress, setProgress] = useState<TutorProgress | null>(null);
  const [input, setInput] = useState("");
  // Sessions with a request in flight -- tracked per-session (not one global
  // flag) so switching to another chat while one streams doesn't block it.
  const [streamingIds, setStreamingIds] = useState<Set<string>>(new Set());
  const abortControllers = useRef<Map<string, AbortController>>(new Map());

  const scrollRef = useRef<HTMLDivElement>(null);
  // Follow the stream only while the student is reading the bottom; if they scroll
  // up to re-read, new text must not yank the view away.
  const stickToBottom = useRef(true);
  // Below `sm`: chats live in a drawer, and the header/settings fold into toggles.
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Restore persisted sessions (migrating the old single-thread format if
  // needed) on mount. Must happen in an effect, not a lazy useState
  // initializer, so server-rendered and first client render match.
  useEffect(() => {
    const restored = loadSessions();
    const restoredIds = Object.keys(restored);
    /* eslint-disable react-hooks/set-state-in-effect -- one-time hydration from localStorage */
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
    /* eslint-enable react-hooks/set-state-in-effect */
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
    try {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (localStorage.getItem(SOCRATIC_KEY) === "off") setSocratic(false);
    } catch {
      // ignore
    }
    fetchOverview(apiToken)
      .then(setOverview)
      .catch(() => setOverview(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(SOCRATIC_KEY, socratic ? "on" : "off");
    } catch {
      // ignore
    }
  }, [socratic]);

  useEffect(() => {
    if (!hydrated || !activeId) return;
    fetchProgress(activeId, apiToken)
      .then(setProgress)
      .catch(() => setProgress(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeId, hydrated]);

  useEffect(() => {
    if (!selectedModel) return;
    try {
      localStorage.setItem(LAST_MODEL_KEY, selectedModel);
    } catch {
      // ignore
    }
    // Load the model now so the first answer is not a cold start.
    void warmModel(selectedModel, apiToken);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedModel]);

  const messages = useMemo(() => (activeId && sessions[activeId]?.messages) || [], [activeId, sessions]);
  const anyStreaming = streamingIds.size > 0;

  // Keep the view on the latest message as content streams in, unless the student
  // has scrolled up. "auto" while streaming (smooth scrolling lags behind tokens).
  useEffect(() => {
    if (!stickToBottom.current || messages.length === 0) return;
    scrollRef.current?.scrollIntoView({ behavior: anyStreaming ? "auto" : "smooth", block: "end" });
  }, [messages, anyStreaming]);

  function handleScroll(e: UIEvent<HTMLDivElement>) {
    const el = e.currentTarget;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
  }

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
    updateAssistant({ content: "", error: undefined, sources: undefined, ui: undefined, streaming: true });

    try {
      const response = await postChat(
        {
          session_id: sessionId,
          question,
          model_name: selectedModel!,
          detail_level: detailLevel,
          socratic,
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
        } else if (evt.event === "ui") {
          updateAssistant({ ui: JSON.parse(evt.data) as TutorUI });
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
      fetchProgress(sessionId, apiToken)
        .then(setProgress)
        .catch(() => undefined);
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
    sendMessage(input);
  }

  // Shared by the composer and by every suggested chip: a chip is a complete
  // message, so tapping it is exactly the same as typing it.
  function sendMessage(text: string) {
    const question = text.trim();
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
    stickToBottom.current = true; // sending always brings the student to the reply
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
    void resetSession(id, apiToken);
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
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />
      )}

      <div className="flex flex-col h-dvh min-w-0 flex-1">
        <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 px-3 sm:px-6 lg:px-10 py-3 border-b border-[var(--color-border)] pt-[max(0.75rem,env(safe-area-inset-top))]">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              aria-label="Open your chats"
              onClick={() => setDrawerOpen(true)}
              className="sm:hidden -ml-1 flex min-h-11 min-w-11 items-center justify-center rounded-md text-lg text-[var(--color-muted-foreground)] cursor-pointer"
            >
              ☰
            </button>
            <div className="min-w-0">
              <h1 className="text-lg font-semibold tracking-tight">OS Tutor</h1>
              <p className="hidden sm:block text-xs text-[var(--color-muted-foreground)]">
                Grounded answers from the course material
              </p>
            </div>
          </div>
          <button
            type="button"
            aria-label="Model and more"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            className="sm:hidden flex min-h-11 min-w-11 items-center justify-center rounded-md text-lg text-[var(--color-muted-foreground)] cursor-pointer"
          >
            ⋯
          </button>
          <div className={`${menuOpen ? "flex" : "hidden"} sm:flex basis-full sm:basis-auto flex-col sm:flex-row items-stretch sm:items-center gap-3`}>
            <a
              href="/research"
              className="text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
            >
              Research
            </a>
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
                className="text-left text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors cursor-pointer"
              >
                Sign out
              </button>
            )}
          </div>
        </header>

        <div onScroll={handleScroll} className="flex-1 overflow-y-auto overscroll-contain px-3 sm:px-6 lg:px-10 py-4 sm:py-6 space-y-4">
          {messages.length === 0 && <StarterPanel overview={overview} onPick={sendMessage} />}
          {messages.map((m, i) => (
            <div key={m.id}>
              <MessageBubble
                message={m}
                onRetry={m.role === "assistant" && m.error ? () => rerunFrom(m.id) : undefined}
                onRegenerate={
                  m.role === "assistant" && !m.error && !m.streaming
                    ? () => rerunFrom(m.id)
                    : undefined
                }
              />
              {m.role === "assistant" && m.ui && !m.error && i === messages.length - 1 && (
                <FollowUps ui={m.ui} onPick={sendMessage} disabled={isActiveStreaming} />
              )}
            </div>
          ))}
          <div ref={scrollRef} />
        </div>

        <div className="px-3 sm:px-6 lg:px-10 pb-[max(1rem,env(safe-area-inset-bottom))] pt-2 border-t border-[var(--color-border)] space-y-2 sm:space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
            <div className="flex items-center gap-2">
              <ProgressPill progress={progress} />
              <button
                type="button"
                aria-expanded={settingsOpen}
                onClick={() => setSettingsOpen((v) => !v)}
                className="sm:hidden min-h-11 rounded-md px-2 text-sm text-[var(--color-muted-foreground)] cursor-pointer"
              >
                {settingsOpen ? "Hide settings" : "Settings"}
              </button>
            </div>
            <div className={`${settingsOpen ? "flex" : "hidden"} sm:flex basis-full sm:basis-auto flex-wrap items-center justify-between gap-3`}>
              <DetailToggle value={detailLevel} onChange={setDetailLevel} />
              <label
                className="inline-flex min-h-11 sm:min-h-0 items-center gap-2 text-sm text-[var(--color-muted-foreground)] cursor-pointer select-none"
                title="When on, the tutor asks one short question after an answer and gives hints instead of just telling you."
              >
                <input
                  type="checkbox"
                  checked={socratic}
                  onChange={(e) => setSocratic(e.target.checked)}
                  className="accent-[var(--color-accent)]"
                />
                Guided questions
              </label>
            </div>
          </div>
          <Composer
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={sendDisabled}
            isStreaming={isActiveStreaming}
            onStop={handleStop}
            placeholder={
              !selectedModel
                ? "Waiting for a model to load…"
                : "Ask about operating systems, or answer the tutor…"
            }
          />
        </div>
      </div>
    </div>
  );
}
