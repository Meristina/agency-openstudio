// Wire types — mirror the events emitted by agency-kit's `on_event` hook
// (cli_engine.py `_emit`) plus the two frames `server.py` adds itself (`done`,
// `error`). Keep these in lockstep with the server: every `phase` the GUI can
// receive is a member of MissionEvent.

/** First frame of a run: the ephemeral run id, used to cancel via the explicit
 * POST /api/mission/{run_id}/cancel endpoint. */
export interface RunEvent {
  phase: "run";
  run_id: string;
}

export interface RouteEvent {
  phase: "route";
  status: "done";
  route: string[];
}

export interface DeptEvent {
  phase: "dept";
  dept: string;
  status: "start" | "done";
}

export interface SynthEvent {
  phase: "synth";
  iteration: number;
  status: "start" | "done";
}

/** Inspector emits twice per iteration: a `status:"start"`, then a `verdict`. */
export interface InspectEvent {
  phase: "inspect";
  iteration: number;
  status?: "start";
  verdict?: string;
}

/** Terminal frame the server appends once the worker returns. */
export interface DoneEvent {
  phase: "done";
  mission_id: string | null;
  verdict: string | null;
  path: string;
  residual_risk?: string | null;
}

/** Terminal frame the server appends if the worker raised. */
export interface ErrorEvent {
  phase: "error";
  message: string;
}

/** Terminal frame the server appends when an explicit cancel stopped the run
 * while the client was still connected (nothing was persisted). */
export interface CancelledEvent {
  phase: "cancelled";
}

export type MissionEvent =
  | RunEvent
  | RouteEvent
  | DeptEvent
  | SynthEvent
  | InspectEvent
  | DoneEvent
  | ErrorEvent
  | CancelledEvent;

// ── Wave 2 — local multimodal results (mirror server.py's media endpoints) ──

/** Result of POST /api/image — a generated image served under /media. */
export interface ImageResult {
  url: string;
  prompt: string;
  seed: number;
  seconds: number;
}

/** Result of POST /api/tts — generated speech served under /media. */
export interface SpeechResult {
  url: string;
  voice: string;
  seconds: number;
}

/** Result of POST /api/stt — a transcript of an uploaded audio clip. */
export interface TranscriptResult {
  text: string;
  seconds: number;
}

/** GET /api/models — which model is currently warm + the configured model ids. */
export interface ModelsStatus {
  resident: string | null;
  models: Record<string, string>;
}

/** One generated asset shown in the session gallery (image or audio). */
export interface GalleryItem {
  kind: "image" | "audio";
  url: string;
  label: string;
  seconds: number;
}

/** A saved mission as returned by `GET /api/missions` (store.list_missions). */
export interface MissionSummary {
  mission_id: string;
  goal?: string;
  route?: string[];
  /** Last verdict token, or "in-progress" / "—" for missions with no verdict yet. */
  verdict?: string;
  delivered?: boolean;
  [k: string]: unknown;
}

/** A full saved dossier as returned by `GET /api/mission/{id}` (store.load). */
export interface Dossier {
  mission_id?: string;
  goal?: string;
  route?: string[];
  delivered?: string;
  verdicts?: Array<{ verdict?: string; [k: string]: unknown }>;
  sources?: string[];
  decisions?: string[];
  open_to_verify?: string[];
  residual_risk?: string;
  [k: string]: unknown;
}

/** The Inspector's final verdict token for a dossier, or null if none recorded. */
export function lastVerdict(d: Dossier): string | null {
  const verdicts = d.verdicts ?? [];
  return verdicts.length ? verdicts[verdicts.length - 1].verdict ?? null : null;
}

/** Map a verdict token to its badge style class (shared by timeline + detail). */
export function verdictClass(verdict: string): "ok" | "veto" | "warn" {
  if (verdict === "PASS") return "ok";
  if (verdict === "VETO") return "veto";
  return "warn";
}

/**
 * Badge class for a history-summary verdict. Unlike `verdictClass`, the non-
 * terminal markers `store.list_missions` emits ("in-progress", "—", or none)
 * map to "pending" rather than the amber "warn" reserved for real fix verdicts.
 */
export function summaryVerdictClass(verdict?: string): "ok" | "veto" | "warn" | "pending" {
  if (!verdict || verdict === "in-progress" || verdict === "—") return "pending";
  return verdictClass(verdict);
}
