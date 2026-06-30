// Typed client for the stdlib Studio server. In dev these paths are proxied to
// the Python server by Vite (see vite.config.ts); in the built GUI they are
// same-origin because server.py serves dist/.

import type { Dossier, MissionEvent, MissionSummary } from "./types";

export async function listMissions(): Promise<MissionSummary[]> {
  const res = await fetch("/api/missions");
  if (!res.ok) throw new Error(`GET /api/missions → ${res.status}`);
  const data = (await res.json()) as { missions: MissionSummary[] };
  return data.missions ?? [];
}

// Load one saved dossier by id (used by the history click-through in App.tsx).
export async function getMission(id: string): Promise<Dossier> {
  const res = await fetch(`/api/mission/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`GET /api/mission/${id} → ${res.status}`);
  return (await res.json()) as Dossier;
}

/**
 * Run a mission and stream its progress.
 *
 * The endpoint is a POST returning `text/event-stream`, so EventSource can't be
 * used. We read the response body as a stream and split on the SSE frame
 * delimiter (`\n\n`), parsing each `data:` line into a MissionEvent and handing
 * it to `onEvent`. Resolves when the server closes the stream.
 *
 * Pass an AbortSignal to cancel an in-flight run (closes the connection).
 */
export async function runMission(
  goal: string,
  onEvent: (event: MissionEvent) => void,
  opts: { engine?: string; signal?: AbortSignal } = {},
): Promise<void> {
  const res = await fetch("/api/mission", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, engine: opts.engine ?? "claude-code" }),
    signal: opts.signal,
  });
  if (!res.ok || !res.body) {
    const detail = res.ok ? "no response body" : `status ${res.status}`;
    throw new Error(`POST /api/mission failed — ${detail}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line. Keep the trailing partial.
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const event = parseFrame(frame);
      if (event) onEvent(event);
    }
  }
  // Flush any final frame the stream ended on without a trailing blank line.
  const tail = parseFrame(buffer);
  if (tail) onEvent(tail);
}

/** Parse one SSE frame ("data: {...}") into a MissionEvent, or null. */
function parseFrame(frame: string): MissionEvent | null {
  const line = frame
    .split("\n")
    .find((l) => l.startsWith("data:"));
  if (!line) return null;
  const json = line.slice("data:".length).trim();
  if (!json) return null;
  try {
    return JSON.parse(json) as MissionEvent;
  } catch {
    return null;
  }
}
