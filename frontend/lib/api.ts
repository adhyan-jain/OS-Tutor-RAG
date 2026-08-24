import type { DetailLevel } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetchModels(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/models`);
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

/** POSTs to /chat and returns the raw streaming Response for the caller to parse as SSE. */
export async function postChat(body: ChatRequestBody): Promise<Response> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST /chat failed: ${res.status} ${res.statusText}`);
  }
  return res;
}
