/**
 * Minimal SSE-over-fetch client.
 *
 * Browser `EventSource` can't send a POST body, and the backend needs one
 * (session_id/question/model_name/detail_level), so we drive the stream by
 * hand: fetch() with a ReadableStream body reader, decode chunks as they
 * arrive, and split on blank lines to find event frames. Each frame looks
 * like:
 *
 *   event: token
 *   data: {"token": "..."}
 *   <blank line>
 *
 * `data:` can in principle span multiple lines (per the SSE spec they're
 * joined with "\n"); we handle that even though this backend only ever sends
 * single-line JSON payloads. Lines starting with ":" are comments (this is
 * how sse-starlette's keep-alive pings can show up) and are ignored, and any
 * frame whose event type we don't recognize is simply skipped by the caller,
 * so periodic pings never confuse the UI.
 */

export interface SSEEvent {
  event: string;
  data: string;
}

export async function streamSSE(
  response: Response,
  onEvent: (evt: SSEEvent) => void,
): Promise<void> {
  if (!response.body) {
    throw new Error("Response has no readable body (no streaming support?)");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let result = extractFrame(buffer);
    while (result) {
      buffer = result.rest;
      const parsed = parseFrame(result.frame);
      if (parsed) onEvent(parsed);
      result = extractFrame(buffer);
    }
  }

  // Flush any trailing frame that arrived without a final blank line.
  const trailing = buffer.trim();
  if (trailing) {
    const parsed = parseFrame(trailing);
    if (parsed) onEvent(parsed);
  }
}

/** Pulls the next complete "\n\n"/"\r\n\r\n"-terminated frame off the buffer. */
function extractFrame(buffer: string): { frame: string; rest: string } | null {
  const nn = buffer.indexOf("\n\n");
  const rnrn = buffer.indexOf("\r\n\r\n");

  if (nn === -1 && rnrn === -1) return null;

  let idx: number;
  let sepLen: number;
  if (rnrn !== -1 && (nn === -1 || rnrn < nn)) {
    idx = rnrn;
    sepLen = 4;
  } else {
    idx = nn;
    sepLen = 2;
  }

  return { frame: buffer.slice(0, idx), rest: buffer.slice(idx + sepLen) };
}

function parseFrame(frame: string): SSEEvent | null {
  let eventType = "message";
  const dataLines: string[] = [];

  for (const rawLine of frame.split(/\r\n|\n/)) {
    if (rawLine === "" || rawLine.startsWith(":")) continue; // comment / keep-alive
    if (rawLine.startsWith("event:")) {
      eventType = rawLine.slice("event:".length).trim();
    } else if (rawLine.startsWith("data:")) {
      dataLines.push(rawLine.slice("data:".length).replace(/^ /, ""));
    }
  }

  if (dataLines.length === 0 && eventType === "message") return null;
  return { event: eventType, data: dataLines.join("\n") };
}
