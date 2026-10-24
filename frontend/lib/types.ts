export type DetailLevel = "eli5" | "undergrad" | "exam_prep";

export const DETAIL_LEVELS: { value: DetailLevel; label: string }[] = [
  { value: "eli5", label: "ELI5" },
  { value: "undergrad", label: "Undergrad" },
  { value: "exam_prep", label: "Exam prep" },
];

export interface Source {
  chunk_id: string;
  doc_id: string;
  metadata: Record<string, unknown>;
  score: number;
}

export type Role = "user" | "assistant";

/** What the tutoring layer attaches to an assistant turn (the `ui` SSE event).
 * `chips` are complete messages: tapping one sends exactly that text. */
export interface TutorUI {
  kind: string; // answer | question | feedback | path | orientation | triage | quiz_summary
  chips: string[];
  concept?: { id: string; name: string; text: string; state: string; state_label: string };
  /** Present while a Socratic question is waiting for the student's answer. */
  question?: { id: string; type: string; level: string; concept: string; source: string };
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  /** true while the assistant message is still streaming tokens in */
  streaming?: boolean;
  sources?: Source[];
  ui?: TutorUI;
  error?: string;
}

export interface TutorOverview {
  starters: string[];
  path: { id: string; name: string; topic: string; summary: string }[];
}

export interface TutorProgress {
  concepts: { id: string; name: string; state: string; label: string; attempts: number }[];
  understood: number;
  total: number;
  quiz_active: boolean;
}

/** One conversation thread. `id` is the session_id sent to the backend
 * (also the key under which the backend keeps its own turn history for
 * multi-turn context) -- title is derived client-side from the first
 * question and is purely a UI label. */
export interface ChatSession {
  id: string;
  title: string;
  updatedAt: number;
  messages: ChatMessage[];
}
