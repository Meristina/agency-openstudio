import type { CatalogKey } from "../../i18n/catalog";
import type { AssetStep, TimelineModel } from "../../timeline";

export type HumanStageKey = "prepare" | "departments" | "synthesis" | "inspection" | "media";
export type HumanState = "upcoming" | "running" | "done" | "skipped";
// Per-activity rows can also be "failed" (a failed media render); stages themselves never are.
export type HumanDetailState = "running" | "done" | "skipped" | "failed";

export interface HumanDetail {
  labelKey: CatalogKey;
  value: string | number | null;
  state: HumanDetailState;
}

export interface HumanIteration {
  round: number;
  verdict: string | null;
  verified: { ok: boolean; rate: number | null } | null;
}

export interface HumanStage {
  key: HumanStageKey;
  titleKey: CatalogKey;
  state: HumanState;
  detail: HumanDetail[];
  iterations?: HumanIteration[];
}

// The nine real department keys the mission loop emits (agency-kit route/dept events);
// any other key falls back to the generic label so a future department never leaks raw.
const deptKeys: Record<string, CatalogKey> = {
  product: "missions.dept.product",
  marketing: "missions.dept.marketing",
  solve: "missions.dept.solve",
  finance: "missions.dept.finance",
  comms: "missions.dept.comms",
  data: "missions.dept.data",
  ops: "missions.dept.ops",
  people: "missions.dept.people",
  tech: "missions.dept.tech",
};

function allDone(states: Array<{ status: "running" | "done" | "skipped" }>): HumanState {
  if (states.some((s) => s.status === "running")) return "running";
  return states.every((s) => s.status === "skipped") ? "skipped" : "done";
}

function count(value: { hits?: number | null; sources?: unknown[]; servers?: string[]; depts?: string[] } | null): number | null {
  if (!value) return null;
  return value.hits ?? value.sources?.length ?? value.servers?.length ?? value.depts?.length ?? null;
}

function assetValue(asset: AssetStep): CatalogKey {
  if (asset.kind === "tts") return "missions.asset.voice";
  if (asset.kind === "video") return "missions.asset.video";
  return "missions.asset.image";
}

export function deptLabelKey(dept: string): CatalogKey {
  return deptKeys[dept] ?? "missions.dept.generic";
}

export function humanStages(model: TimelineModel): HumanStage[] {
  const stages: HumanStage[] = [];
  const prepare = [
    ["missions.detail.sources", model.websearch],
    ["missions.detail.material", model.retrieval],
    ["missions.detail.visual", model.visual],
    ["missions.detail.knowledge", model.graph],
    ["missions.detail.context", model.mcp],
    ["missions.detail.tools", model.mcpTools],
    ["missions.detail.personas", model.persona],
  ] as const;
  const presentPrepare = prepare.filter(([, step]) => step);
  if (presentPrepare.length) {
    stages.push({
      key: "prepare",
      titleKey: "missions.stage.prepare",
      state: allDone(presentPrepare.map(([, step]) => step!)),
      detail: presentPrepare.map(([labelKey, step]) => ({ labelKey, value: count(step), state: step!.status })),
    });
  }

  if (model.route || model.depts.length) {
    stages.push({
      key: "departments",
      titleKey: "missions.stage.departments",
      state: model.depts.length && model.depts.every((d) => d.done) ? "done" : "running",
      detail: model.depts.map((d) => ({ labelKey: deptLabelKey(d.dept), value: null, state: d.done ? "done" : "running" })),
    });
  }

  if (model.synth.length) {
    stages.push({
      key: "synthesis",
      titleKey: "missions.stage.synthesis",
      state: model.synth.every((s) => s.done) ? "done" : "running",
      detail: model.synth.map((s) => ({ labelKey: "missions.detail.synthesis", value: s.iteration, state: s.done ? "done" : "running" })),
    });
  }

  if (model.inspect.length || model.verify.length) {
    const rounds = [...new Set([...model.inspect.map((i) => i.iteration), ...model.verify.map((v) => v.iteration)])].sort((a, b) => a - b);
    const iterations = rounds.map((round) => {
      const inspect = model.inspect.find((i) => i.iteration === round);
      const verify = model.verify.find((v) => v.iteration === round);
      return {
        round,
        verdict: inspect?.verdict ?? null,
        verified: verify?.status === "done" ? { ok: verify.ok ?? false, rate: verify.rate } : null,
      };
    });
    const latest = iterations.at(-1);
    stages.push({
      key: "inspection",
      titleKey: "missions.stage.inspection",
      state: latest?.verdict && (!model.verify.length || latest.verified) ? "done" : "running",
      detail: iterations.map((i) => ({ labelKey: "missions.round", value: i.round, state: i.verified || i.verdict ? "done" : "running" })),
      iterations,
    });
  }

  if (model.assets.length) {
    stages.push({
      key: "media",
      titleKey: "missions.stage.media",
      state: model.assets.some((a) => a.status === "running") ? "running" : "done",
      detail: model.assets.map((a) => ({ labelKey: "missions.detail.asset", value: assetValue(a), state: a.status === "running" ? "running" : a.status === "failed" ? "failed" : a.status === "skipped" ? "skipped" : "done" })),
    });
  }

  return stages;
}
