// Wire types — mirror the events emitted by agency-kit's `on_event` hook
// (cli_engine.py `_emit`) plus the two frames `server.py` adds itself (`done`,
// `error`). Keep these in lockstep with the server: every `phase` the GUI can
// receive is a member of MissionEvent.

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

export type MissionEvent =
  | RouteEvent
  | DeptEvent
  | SynthEvent
  | InspectEvent
  | DoneEvent
  | ErrorEvent;

/** A saved mission as returned by `GET /api/missions` (store.list_missions). */
export interface MissionSummary {
  mission_id: string;
  goal?: string;
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
