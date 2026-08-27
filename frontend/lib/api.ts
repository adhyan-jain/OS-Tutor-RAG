import type { DetailLevel } from "./types";

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

export interface ChatRequestBody {
  session_id: string;
  question: string;
  model_name: string;
  detail_level: DetailLevel;
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
