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

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  /** true while the assistant message is still streaming tokens in */
  streaming?: boolean;
  sources?: Source[];
  error?: string;
}
