// Pure folding of the raw MissionEvent stream into a structured timeline model.
// Kept free of React so it can be unit-tested directly (the SSE event order is
// the contract that matters, not the rendering).

import type { MissionEvent } from "./types";

export interface DeptStep {
  dept: string;
  done: boolean;
}

export interface SynthStep {
  iteration: number;
  done: boolean;
}

export interface InspectStep {
  iteration: number;
  verdict: string | null;
}

export interface AssetStep {
  kind: "image" | "tts";
  status: "running" | "ok" | "failed" | "skipped";
  url: string | null;
  reason: string | null;
}

export interface RetrievalStep {
  status: "running" | "done" | "skipped";
  hits: number | null;
  sources: Array<{ title: string; doc_id: string }>;
  reason: string | null;
}

export interface VisualStep {
  status: "running" | "done" | "skipped";
  hits: number | null;
  sources: Array<{ title: string; doc_id: string }>;
  reason: string | null;
}

export interface WebSearchStep {
  status: "running" | "done" | "skipped";
  hits: number | null;
  sources: Array<{ title: string; url: string }>;
  reason: string | null;
}

export interface McpStep {
  status: "running" | "done" | "skipped";
  hits: number | null;
  sources: Array<{ name: string; server: string }>;
  reason: string | null;
}

export interface KnowledgeStep {
  status: "running" | "done" | "skipped";
  hits: number | null;
  sources: Array<{ label: string; kind: string }>;
  reason: string | null;
}

export interface McpToolsStep {
  status: "running" | "done" | "skipped";
  servers: string[];
  reason: string | null;
}

export interface PersonaStep {
  status: "running" | "done" | "skipped";
  depts: string[];
  reason: string | null;
}

export type Terminal =
  | { kind: "done"; verdict: string | null; missionId: string | null; path: string; residualRisk: string | null }
  | { kind: "error"; message: string }
  | { kind: "cancelled" };

export interface TimelineModel {
  retrieval: RetrievalStep | null;
  visual: VisualStep | null;
  websearch: WebSearchStep | null;
  mcp: McpStep | null;
  mcpTools: McpToolsStep | null;
  graph: KnowledgeStep | null;
  persona: PersonaStep | null;
  route: string[] | null;
  depts: DeptStep[];
  synth: SynthStep[];
  inspect: InspectStep[];
  assets: AssetStep[];
  terminal: Terminal | null;
}

/**
 * Fold a best-effort pre-route phase (retrieval / websearch / mcp / graph — all the same
 * start→running, done→hits+sources, else→skipped+reason shape) into its single step.
 * Generic over the source element type so each phase keeps its own `sources` typing.
 */
function foldStep<S>(
  e: { status: "start" | "done" | "skipped"; hits?: number; sources?: S[]; reason?: string },
): { status: "running" | "done" | "skipped"; hits: number | null; sources: S[]; reason: string | null } {
  if (e.status === "start") return { status: "running", hits: null, sources: [], reason: null };
  if (e.status === "done") return { status: "done", hits: e.hits ?? 0, sources: e.sources ?? [], reason: null };
  return { status: "skipped", hits: null, sources: [], reason: e.reason ?? null };
}

/** Fold the events received so far into a stable, render-ready model. */
export function groupTimeline(events: MissionEvent[]): TimelineModel {
  const model: TimelineModel = { retrieval: null, visual: null, websearch: null, mcp: null, mcpTools: null, graph: null, persona: null, route: null, depts: [], synth: [], inspect: [], assets: [], terminal: null };

  for (const e of events) {
    switch (e.phase) {
      case "run":
        // The run-id frame is a control handle (used for the cancel endpoint), not
        // a visible timeline step — fold nothing.
        break;
      // The three best-effort pre-route phases share one fold (foldStep). Each happens at
      // most once per mission, so a later frame just replaces the step.
      case "retrieval":
        model.retrieval = foldStep(e);
        break;
      case "visual":
        model.visual = foldStep(e);
        break;
      case "websearch":
        model.websearch = foldStep(e);
        break;
      case "mcp":
        model.mcp = foldStep(e);
        break;
      case "mcp_tools":
        // Its own shape (`servers`, not hits/sources), so it folds by hand rather than foldStep.
        if (e.status === "start") model.mcpTools = { status: "running", servers: [], reason: null };
        else if (e.status === "done") model.mcpTools = { status: "done", servers: e.servers ?? [], reason: null };
        else model.mcpTools = { status: "skipped", servers: [], reason: e.reason ?? null };
        break;
      case "graph":
        model.graph = foldStep(e);
        break;
      case "persona":
        // Its own shape (`depts`, not hits/sources), so it folds by hand like mcp_tools.
        if (e.status === "start") model.persona = { status: "running", depts: [], reason: null };
        else if (e.status === "done") model.persona = { status: "done", depts: e.depts ?? [], reason: null };
        else model.persona = { status: "skipped", depts: [], reason: e.reason ?? null };
        break;
      case "route":
        model.route = e.route;
        break;
      case "dept": {
        const step = model.depts.find((d) => d.dept === e.dept);
        if (step) step.done = step.done || e.status === "done";
        else model.depts.push({ dept: e.dept, done: e.status === "done" });
        break;
      }
      case "synth": {
        const step = model.synth.find((s) => s.iteration === e.iteration);
        if (step) step.done = step.done || e.status === "done";
        else model.synth.push({ iteration: e.iteration, done: e.status === "done" });
        break;
      }
      case "inspect": {
        const step = model.inspect.find((i) => i.iteration === e.iteration);
        if (step) step.verdict = e.verdict ?? step.verdict;
        else model.inspect.push({ iteration: e.iteration, verdict: e.verdict ?? null });
        break;
      }
      case "asset": {
        // `start` opens a render; the next `done`/`failed` of the same kind closes the
        // most recent open one (the render loop is strictly sequential per modality, so
        // last-open is the right match without an asset id). `skipped` never has a
        // preceding `start`, so it lands as its own terminal step.
        if (e.status === "start") {
          model.assets.push({ kind: e.kind, status: "running", url: null, reason: null });
          break;
        }
        if (e.status === "skipped") {
          model.assets.push({ kind: e.kind, status: "skipped", url: null, reason: e.reason ?? null });
          break;
        }
        const open = [...model.assets].reverse().find((a) => a.kind === e.kind && a.status === "running");
        const closed: AssetStep["status"] = e.status === "done" ? "ok" : "failed";
        if (open) {
          open.status = closed;
          open.url = e.url ?? null;
          open.reason = e.reason ?? null;
        } else {
          model.assets.push({ kind: e.kind, status: closed, url: e.url ?? null, reason: e.reason ?? null });
        }
        break;
      }
      case "done":
        model.terminal = {
          kind: "done",
          verdict: e.verdict,
          missionId: e.mission_id,
          path: e.path,
          residualRisk: e.residual_risk ?? null,
        };
        break;
      case "error":
        model.terminal = { kind: "error", message: e.message };
        break;
      case "cancelled":
        model.terminal = { kind: "cancelled" };
        break;
      default: {
        // Exhaustiveness guard: a new MissionEvent.phase becomes a compile error here.
        const _exhaustive: never = e;
        void _exhaustive;
        break;
      }
    }
  }
  return model;
}

/** Coarse run state derived from the events, for the header/status line. */
export function runStatus(model: TimelineModel): "idle" | "running" | "done" | "error" | "cancelled" {
  if (model.terminal?.kind === "error") return "error";
  if (model.terminal?.kind === "cancelled") return "cancelled";
  if (model.terminal?.kind === "done") return "done";
  if (model.retrieval || model.visual || model.websearch || model.mcp || model.mcpTools || model.graph || model.persona || model.route || model.depts.length) return "running";
  return "idle";
}
