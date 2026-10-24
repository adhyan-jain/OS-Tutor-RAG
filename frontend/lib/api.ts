import type { DetailLevel, TutorOverview, TutorProgress } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/** Builds an Authorization header when auth is on and a token is available;
 * an empty object (spreads to nothing) otherwise -- so this is a no-op when
 * NEXT_PUBLIC_AUTH_ENABLED is off, exactly as it is today. */
function authHeaders(apiToken?: string): Record<string, string> {
  return apiToken ? { Authorization: `Bearer ${apiToken}` } : {};
}

export async function fetchModels(apiToken?: string): Promise<string[]> {
  const res = await fetch(`${API_BASE}/models`, {
    headers: { ...authHeaders(apiToken) },
  });
  if (!res.ok) {
    throw new Error(`GET /models failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/** Ask the backend to load a model into memory so the first answer is not slow.
 * Best effort: a failure changes nothing for the student. */
export async function warmModel(model: string, apiToken?: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/models/warm`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders(apiToken) },
      body: JSON.stringify({ model_name: model }),
    });
  } catch {
    // ignore
  }
}

export interface ChatRequestBody {
  session_id: string;
  question: string;
  model_name: string;
  detail_level: DetailLevel;
  /** Guided mode: the tutor asks one short question after an answer and grades the reply. */
  socratic: boolean;
}

/** POSTs to /chat and returns the raw streaming Response for the caller to
 * parse as SSE. `signal` lets a caller abort an in-flight/streaming request
 * (the "Stop" button) -- fetch rejects with an AbortError, which streamSSE's
 * caller distinguishes from a real error. */
export async function postChat(
  body: ChatRequestBody,
  apiToken?: string,
  signal?: AbortSignal,
): Promise<Response> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(apiToken) },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    throw new Error(`POST /chat failed: ${res.status} ${res.statusText}`);
  }
  return res;
}

export async function fetchOverview(apiToken?: string): Promise<TutorOverview> {
  const res = await fetch(`${API_BASE}/tutor/overview`, { headers: { ...authHeaders(apiToken) } });
  if (!res.ok) throw new Error(`GET /tutor/overview failed: ${res.status}`);
  return res.json();
}

export async function fetchProgress(sessionId: string, apiToken?: string): Promise<TutorProgress> {
  const res = await fetch(`${API_BASE}/tutor/progress/${encodeURIComponent(sessionId)}`, {
    headers: { ...authHeaders(apiToken) },
  });
  if (!res.ok) throw new Error(`GET /tutor/progress failed: ${res.status}`);
  return res.json();
}

/** Best-effort: forget a thread's server-side history and tutoring state. */
export async function resetSession(sessionId: string, apiToken?: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/tutor/session/${encodeURIComponent(sessionId)}`, {
      method: "DELETE",
      headers: { ...authHeaders(apiToken) },
    });
  } catch {
    // non-fatal: the local copy is already gone
  }
}
