// Typed client for the stdlib Studio server. In dev these paths are proxied to
// the Python server by Vite (see vite.config.ts); in the built GUI they are
// same-origin because server.py serves dist/.

import type {
  DocMeta,
  Dossier,
  ImageResult,
  MissionEvent,
  MissionSummary,
  ModelsStatus,
  SpeechResult,
  TranscriptResult,
} from "./types";

/** Build an error message that surfaces the server's JSON `error` field when present
 * (e.g. a 501's "pip install 'agency-studio[media]'" hint), else just the status. */
async function errorText(res: Response, label: string): Promise<string> {
  try {
    const data = (await res.json()) as { error?: string };
    if (data.error) return `${label} → ${res.status}: ${data.error}`;
  } catch {
    /* body was not JSON — fall through to the bare status */
  }
  return `${label} → ${res.status}`;
}

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
 * Cancel an in-flight mission by its run id (the `run` SSE frame). Sets the run's
 * cancel flag server-side, which kills the in-flight engine subprocess before any
 * persistence. Resolves true on 202; false for any other status. The request is
 * time-bounded (so a wedged connection can't strand the Stop click) — a timeout or
 * network error rejects, and the caller falls back to aborting the fetch.
 */
export async function cancelMission(runId: string): Promise<boolean> {
  const res = await fetch(`/api/mission/${encodeURIComponent(runId)}/cancel`, {
    method: "POST",
    signal: AbortSignal.timeout(4000),
  });
  return res.status === 202;
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

// ── Wave 2 — local multimodal ────────────────────────────────────────────────

/** Generate an image from a prompt (POST /api/image). Optional steps/seed/size and
 * an optional image-model id; omitting `model` lets the server use its default. */
export async function generateImage(
  prompt: string,
  opts: { steps?: number; seed?: number; width?: number; height?: number; model?: string } = {},
): Promise<ImageResult> {
  const res = await fetch("/api/image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, ...opts }),
  });
  if (!res.ok) throw new Error(await errorText(res, "POST /api/image"));
  return (await res.json()) as ImageResult;
}

/** Synthesize speech from text (POST /api/tts). */
export async function synthesizeSpeech(text: string, voice?: string): Promise<SpeechResult> {
  const res = await fetch("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(voice ? { text, voice } : { text }),
  });
  if (!res.ok) throw new Error(await errorText(res, "POST /api/tts"));
  return (await res.json()) as SpeechResult;
}

/** Transcribe an audio clip (POST /api/stt). The blob's bytes are the request body;
 * its MIME type tells the server how to decode it. */
export async function transcribeAudio(audio: Blob): Promise<TranscriptResult> {
  const res = await fetch("/api/stt", {
    method: "POST",
    headers: { "Content-Type": audio.type || "audio/wav" },
    body: audio,
  });
  if (!res.ok) throw new Error(await errorText(res, "POST /api/stt"));
  return (await res.json()) as TranscriptResult;
}

/** Which local model is currently warm + the configured model ids (GET /api/models). */
export async function getModelsStatus(): Promise<ModelsStatus> {
  const res = await fetch("/api/models");
  if (!res.ok) throw new Error(await errorText(res, "GET /api/models"));
  return (await res.json()) as ModelsStatus;
}

// ── Wave 4 — RAG / LocalDocs ─────────────────────────────────────────────────

/** List the ingested documents (GET /api/docs). Works without the [studio] extra
 * (an un-built store just lists empty). */
export async function listDocs(): Promise<DocMeta[]> {
  const res = await fetch("/api/docs");
  if (!res.ok) throw new Error(await errorText(res, "GET /api/docs"));
  const data = (await res.json()) as { docs: DocMeta[] };
  return data.docs ?? [];
}

/** Ingest one document for RAG (POST /api/docs?filename=…). The file's bytes are the
 * request body; the filename rides in the query so the server picks the right converter.
 * A 501 (with an install hint) means the [studio] extra is absent. */
export async function ingestDoc(file: File): Promise<DocMeta> {
  const res = await fetch(`/api/docs?filename=${encodeURIComponent(file.name)}`, {
    method: "POST",
    headers: { "Content-Type": file.type || "application/octet-stream" },
    body: file,
  });
  if (!res.ok) throw new Error(await errorText(res, "POST /api/docs"));
  return (await res.json()) as DocMeta;
}

/** Delete an ingested document and its chunks (DELETE /api/docs/{id}). */
export async function deleteDoc(id: string): Promise<void> {
  const res = await fetch(`/api/docs/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await errorText(res, "DELETE /api/docs"));
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
