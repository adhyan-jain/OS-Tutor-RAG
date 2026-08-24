"use client";

import { useEffect, useRef, useState } from "react";
import { fetchModels, postChat } from "@/lib/api";
import { streamSSE } from "@/lib/sse";
import type { ChatMessage, DetailLevel, Source } from "@/lib/types";
import ModelSelect from "./ModelSelect";
import DetailToggle from "./DetailToggle";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";

const MESSAGES_STORAGE_KEY = "os-tutor:messages";
const SESSION_STORAGE_KEY = "os-tutor:session-id";

function newId(): string {
  return crypto.randomUUID();
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const [models, setModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelLoadError, setModelLoadError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const [detailLevel, setDetailLevel] = useState<DetailLevel>("undergrad");
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Restore persisted chat history + per-tab session id on mount.
  // Session id lives in sessionStorage (per spec's "within this tab" reading);
  // the visible history lives in localStorage so a refresh restores it.
  useEffect(() => {
    try {
      // One-time restore from localStorage on mount; this must happen in an
      // effect (not a lazy useState initializer) so the server-rendered and
      // first client render match and hydration doesn't warn about
      // mismatched content.
      const storedMessages = localStorage.getItem(MESSAGES_STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (storedMessages) setMessages(JSON.parse(storedMessages));
    } catch {
      // corrupt/unavailable storage: start with an empty conversation
    }

    let sid = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!sid) {
      sid = newId();
      sessionStorage.setItem(SESSION_STORAGE_KEY, sid);
    }
    setSessionId(sid);
    setHydrated(true);
  }, []);

  // Persist history on every change, once the initial restore has happened
  // (otherwise we'd immediately overwrite stored history with the empty
  // initial state before it's loaded).
  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // storage full/unavailable: non-fatal, conversation just won't persist
    }
  }, [messages, hydrated]);

  // Load the model list once on mount.
  useEffect(() => {
    fetchModels()
      .then((list) => {
        setModels(list);
        if (list.length > 0) setSelectedModel(list[0]);
      })
      .catch((err: Error) => setModelLoadError(err.message))
      .finally(() => setModelsLoading(false));
  }, []);

  // Keep the view scrolled to the latest message as content streams in.
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  async function handleSend() {
    const question = input.trim();
    if (!question || !selectedModel || !sessionId || isStreaming) return;

    const userMessage: ChatMessage = { id: newId(), role: "user", content: question };
    const assistantId = newId();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setIsStreaming(true);

    function updateAssistant(patch: Partial<ChatMessage>) {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)),
      );
    }

    try {
      const response = await postChat({
        session_id: sessionId,
        question,
        model_name: selectedModel,
        detail_level: detailLevel,
      });

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

      // Safety net: if the stream ended without a "sources" or "error" event
      // (e.g. connection dropped mid-stream), don't leave the bubble stuck
      // in a permanent streaming state.
      updateAssistant({ streaming: false });
    } catch (err) {
      updateAssistant({
        streaming: false,
        error: err instanceof Error ? err.message : "Something went wrong contacting the backend.",
      });
    } finally {
      setIsStreaming(false);
    }
  }

  const sendDisabled = isStreaming || !selectedModel || !sessionId;

  return (
    <div className="flex flex-col h-dvh mx-auto w-full max-w-3xl">
      <header className="flex items-center justify-between gap-4 px-4 py-3 border-b border-[var(--color-border)]">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">OS Tutor</h1>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Grounded answers from the course material
          </p>
        </div>
        <ModelSelect
          models={models}
          loading={modelsLoading}
          loadError={modelLoadError}
          value={selectedModel}
          onChange={setSelectedModel}
        />
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-[var(--color-muted-foreground)] text-sm mt-16">
            Ask a question about the operating systems course to get started.
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
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
          placeholder={
            !selectedModel ? "Waiting for a model to load…" : "Ask about the course…"
          }
        />
      </div>
    </div>
  );
}
