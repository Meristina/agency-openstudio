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

export interface VerifyEvent {
  phase: "verify";
  iteration: number;
  status: "start" | "done";
  ok?: boolean;
  rate?: number | null;
  checked?: number;
}

/**
 * Wave 3 — one multimodal asset render, streamed from `assets.render` after a clean
 * PASS (cli_engine emits these inside the worker scope, before the `done` sentinel).
 * `start` opens a render; `done` carries the served `url`; `failed`/`skipped` carry a
 * `reason`. `kind` mirrors the marker type (`image` | `tts` | `video`). `video` is the
 * Wave-6 seedance brick — a cloud render, emitted on the same `asset` phase as the local
 * image/tts renders (only when the mission opted into cloud video).
 */
export interface AssetEvent {
  phase: "asset";
  status: "start" | "done" | "failed" | "skipped";
  kind: "image" | "tts" | "video";
  url?: string;
  reason?: string;
}

/**
 * One entry of the persisted render manifest (`dossier.assets`, mirrored verbatim in
 * the terminal `done` frame). `ok` entries carry a served `url` + render metadata;
 * `failed`/`skipped` entries carry a `reason` instead. Field names track `assets.render`.
 */
export interface AssetManifestItem {
  type: "image" | "tts" | "video";
  status: "ok" | "failed" | "skipped";
  url?: string;
  reason?: string;
  /** image/video — the model that rendered it. */
  model?: string;
  /** tts-only — the voice that spoke it. */
  voice?: string;
  seconds?: number;
  /** image/video — the verbatim prompt (the caption). */
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
 * Wave 6 — visual RAG (PixelRAG), streamed once at the start of a mission when the user opted
 * in (the `visual` flag). Same start→done→skipped shape as `retrieval` — the matched image
 * captions flow through the same RAG pipeline — so `sources` are the matched captions
 * {title, doc_id}. `skipped` carries a `reason` (no images ingested, or the [visual] extra
 * absent). Absent entirely on a run without the flag. This phase is a pure-local vector lookup
 * (any off-machine captioning happened earlier, at image-upload time).
 */
export interface VisualEvent {
  phase: "visual";
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

/**
 * Wave 6 — persona doctrine, streamed once at the start of a mission when the user opted in
 * (the `personas` flag). `start` opens the phase; `done` carries the department keys that
 * received a curated persona (its own `depts` shape, like `mcp_tools`' `servers`, not
 * hits/sources); `skipped` carries a `reason` (no personas curated, or a read failure — the
 * doctrine is best-effort, the mission still runs). Absent on a run without the flag.
 */
export interface PersonaEvent {
  phase: "persona";
  status: "start" | "done" | "skipped";
  depts?: string[];
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

/** Terminal frame the server appends if the worker raised. When the interrupted run left a
 * checkpoint on disk, `resumable` is true and `checkpoint` names it, so the GUI can offer to
 * resume the mission from its last completed phase instead of losing the work. */
export interface ErrorEvent {
  phase: "error";
  message: string;
  resumable?: boolean;
  checkpoint?: string | null;
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
  | VerifyEvent
  | AssetEvent
  | RetrievalEvent
  | VisualEvent
  | WebSearchEvent
  | McpEvent
  | McpToolsEvent
  | KnowledgeEvent
  | PersonaEvent
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

export type Family =
  | "image"
  | "video"
  | "visual"
  | "embedding"
  | "kg-extraction"
  | "stt"
  | "tts"
  | "production-tools"
  | "mcp";

export type CostClass = "free" | "paid" | "free_paid";
export type Availability = "available" | "unavailable";

export interface CapabilityEntry {
  id: string;
  label: string;
  family: Family;
  cost: CostClass;
  availability: Availability;
  reason: string | null;
  enablement: string | null;
  tier: string | null;
  note: string;
  default: boolean;
  key_env: string | null;
}

export interface CapabilityFamilyView {
  family: Family;
  selectable: boolean;
  entries: CapabilityEntry[];
  selected: string | null;
  selected_stale: boolean;
  env_override: string | null;
  active: string;
}

export interface CapabilityInventory {
  families: CapabilityFamilyView[];
  generated_at: string;
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

/** One ingested image (GET /api/visual → docs; POST /api/visual returns one). Mirrors DocMeta —
 * the VLM caption is the `title`, retrieved into missions like a document excerpt. */
export interface VisualMeta {
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
  verification?: MissionVerification;
  /** Wave 3: the multimodal render manifest, present only on asset-bearing missions. */
  assets?: AssetManifestItem[];
  [k: string]: unknown;
}

export interface SourceRecord {
  url: string;
  status: "resolved" | "ambiguous" | "unresolved" | "unverified" | "unverifiable";
  detail: string;
  depts: string[];
}

export interface CycleVerification {
  iteration: number;
  ok: boolean;
  resolve: boolean;
  rate: number | null;
  truncated: number;
  per_dept: Record<string, { counted: number; min: number; ok: boolean }>;
  sources: SourceRecord[];
  missing: string[];
}

export interface MissionVerification {
  min_sources: number;
  resolve: boolean;
  cycles: CycleVerification[];
  final: CycleVerification;
}

/** The Inspector's final verdict token for a dossier, or null if none recorded. */
export function lastVerdict(d: Dossier): string | null {
  const verdicts = d.verdicts ?? [];
  return verdicts.length ? verdicts[verdicts.length - 1].verdict ?? null : null;
}

/**
 * Whether a URL from untrusted content (mission sources, web-search results) is safe to put in
 * an href — only http(s), never `javascript:`/`data:`/`blob:`. Single home for this invariant so
 * the timeline chips and the dossier source links stay in lockstep (used by both).
 */
export function isSafeHttpUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
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
