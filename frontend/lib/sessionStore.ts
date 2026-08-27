import type { ChatMessage, ChatSession } from "./types";

const SESSIONS_KEY = "os-tutor:sessions";
const ACTIVE_KEY = "os-tutor:active-session";

// Pre-multi-session storage keys (single thread per tab) -- migrated into
// the new format below the first time this loads, then left alone.
const LEGACY_MESSAGES_KEY = "os-tutor:messages";
const LEGACY_SESSION_ID_KEY = "os-tutor:session-id";

function newId(): string {
  return crypto.randomUUID();
}

export function deriveTitle(question: string): string {
  const trimmed = question.trim().replace(/\s+/g, " ");
  return trimmed.length > 48 ? `${trimmed.slice(0, 48)}…` : trimmed || "New chat";
}

export function makeSession(): ChatSession {
  return { id: newId(), title: "New chat", updatedAt: Date.now(), messages: [] };
}

/** Loads all sessions, migrating the old single-thread localStorage/
 * sessionStorage keys into the new format on first run so existing users
 * don't lose their conversation. Returns an empty map if nothing exists yet
 * or storage is unavailable/corrupt (never throws). */
export function loadSessions(): Record<string, ChatSession> {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    if (raw) return JSON.parse(raw) as Record<string, ChatSession>;

    // One-time migration from the pre-multi-session format.
    const legacyMessages = localStorage.getItem(LEGACY_MESSAGES_KEY);
    if (legacyMessages) {
      const messages = JSON.parse(legacyMessages) as ChatMessage[];
      const legacyId = sessionStorage.getItem(LEGACY_SESSION_ID_KEY) || newId();
      const firstQuestion = messages.find((m) => m.role === "user")?.content;
      const migrated: ChatSession = {
        id: legacyId,
        title: firstQuestion ? deriveTitle(firstQuestion) : "Previous chat",
        updatedAt: Date.now(),
        messages,
      };
      localStorage.removeItem(LEGACY_MESSAGES_KEY);
      return { [migrated.id]: migrated };
    }
  } catch {
    // corrupt/unavailable storage -- start fresh
  }
  return {};
}

export function saveSessions(sessions: Record<string, ChatSession>): void {
  try {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  } catch {
    // storage full/unavailable: non-fatal, sessions just won't persist
  }
}

export function loadActiveId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_KEY);
  } catch {
    return null;
  }
}

export function saveActiveId(id: string): void {
  try {
    localStorage.setItem(ACTIVE_KEY, id);
  } catch {
    // non-fatal
  }
}
