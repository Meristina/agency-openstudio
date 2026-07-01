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

/**
 * Wave 3 — one multimodal asset render, streamed from `assets.render` after a clean
 * PASS (cli_engine emits these inside the worker scope, before the `done` sentinel).
 * `start` opens a render; `done` carries the served `url`; `failed`/`skipped` carry a
 * `reason`. `kind` mirrors the marker type (`image` | `tts`).
 */
export interface AssetEvent {
  phase: "asset";
  status: "start" | "done" | "failed" | "skipped";
  kind: "image" | "tts";
  url?: string;
  reason?: string;
}

/**
 * One entry of the persisted render manifest (`dossier.assets`, mirrored verbatim in
 * the terminal `done` frame). `ok` entries carry a served `url` + render metadata;
 * `failed`/`skipped` entries carry a `reason` instead. Field names track `assets.render`.
 */
export interface AssetManifestItem {
  type: "image" | "tts";
  status: "ok" | "failed" | "skipped";
  url?: string;
  reason?: string;
  /** image-only — the model that rendered it. */
  model?: string;
  /** tts-only — the voice that spoke it. */
  voice?: string;
  seconds?: number;
  /** image-only — the verbatim prompt (the caption). */
  prompt?: string;
  /** tts-only — the verbatim narration text. */
  text?: string;
}

/**
 * Wave 4 — RAG retrieval, streamed once at the start of a mission when the user has
 * ingested documents. `start` opens the phase; `done` carries how many chunks were
 * retrieved plus their source labels; `skipped` carries a `reason` (missing extra or a
 * store failure — retrieval is best-effort, the mission still runs). Absent entirely on a
 * mission run with no ingested documents.
 */
export interface RetrievalEvent {
  phase: "retrieval";
  status: "start" | "done" | "skipped";
  hits?: number;
  sources?: Array<{ title: string; doc_id: string }>;
  reason?: string;
}

/**
 * Wave 5 — web search, streamed once at the start of a mission when the user opted in
 * (the `web_search` flag). `start` opens the phase; `done` carries how many results were
 * fetched plus their {title, url}; `skipped` carries a `reason` (missing [web] extra or a
 * network failure — web search is best-effort, the mission still runs). Absent entirely on
 * a mission run without the flag.
 */
export interface WebSearchEvent {
  phase: "websearch";
  status: "start" | "done" | "skipped";
  hits?: number;
  sources?: Array<{ title: string; url: string }>;
  reason?: string;
}

/**
 * Wave 5 — MCP resources, streamed once at the start of a mission when the user opted in
 * (the `mcp` flag). `start` opens the phase; `done` carries how many resources were read
 * plus their {name, server}; `skipped` carries a `reason` (no config, missing [mcp] extra,
 * or a connection failure — MCP is best-effort, the mission still runs). Absent entirely on
 * a mission run without the flag.
 */
export interface McpEvent {
  phase: "mcp";
  status: "start" | "done" | "skipped";
  hits?: number;
  sources?: Array<{ name: string; server: string }>;
  reason?: string;
}

/**
 * Wave 6 — MCP tool-calling, streamed once at mission start when the user opted in (the
 * `mcp_tools` flag). `start` opens the setup; `done` carries the server names whose tools were
 * handed to the engine (via `--mcp-config`); `skipped` carries a `reason` (no enabled servers,
 * a malformed config, or an older agency-kit without the hook — best-effort, the mission still
 * runs). Distinct from the Wave-5 `mcp` (read-only resources) phase. Absent without the flag.
 */
export interface McpToolsEvent {
  phase: "mcp_tools";
  status: "start" | "done" | "skipped";
  servers?: string[];
  reason?: string;
}

/**
 * Wave 6 — knowledge graph, streamed once at the start of a mission when the user opted in
 * (the `knowledge` flag). `start` opens the phase; `done` carries how many entities the goal
 * matched plus their {label, kind}; `skipped` carries a `reason` (missing [kg] extra or a
 * read failure — the graph is best-effort, the mission still runs). Absent entirely on a
 * mission run without the flag.
 */
export interface KnowledgeEvent {
  phase: "graph";
  status: "start" | "done" | "skipped";
  hits?: number;
  sources?: Array<{ label: string; kind: string }>;
  reason?: string;
}

/** Terminal frame the server appends once the worker returns. */
export interface DoneEvent {
  phase: "done";
  mission_id: string | null;
  verdict: string | null;
  path: string;
  residual_risk?: string | null;
  /** Wave 3: the render manifest + partial-render summary (empty for non-asset runs). */
  assets?: AssetManifestItem[];
  assets_rendered?: number;
  assets_total?: number;
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
  | AssetEvent
  | RetrievalEvent
  | WebSearchEvent
  | McpEvent
  | McpToolsEvent
  | KnowledgeEvent
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
  /** The image-model id the server actually used for this generation. */
  model: string;
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

/** One selectable image model in the registry (GET /api/models → image_models). */
export interface ImageModelInfo {
  id: string;
  label: string;
  note: string;
  default?: boolean;
}

/** One selectable embedding model in the registry (GET /api/models → embed_models). */
export interface EmbedModelInfo {
  id: string;
  label: string;
  note: string;
  ndim: number;
  default?: boolean;
}

/** GET /api/models — which model is currently warm, the selectable image-model
 * registry, the embedding-model registry, and the configured stt/tts model ids. */
export interface ModelsStatus {
  resident: string | null;
  image_models: ImageModelInfo[];
  embed_models?: EmbedModelInfo[];
  models: Record<string, string>;
}

/** One ingested document (GET /api/docs → docs; POST /api/docs returns one). */
export interface DocMeta {
  id: string;
  filename: string;
  title: string;
  n_chunks: number;
  created: number;
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
  /** Wave 3: the multimodal render manifest, present only on asset-bearing missions. */
  assets?: AssetManifestItem[];
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
