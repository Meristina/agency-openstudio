import { describe, expect, it } from "vitest";
import { groupTimeline } from "../../timeline";
import type { MissionEvent } from "../../types";
import { deptLabelKey, humanStages } from "./humanStages";

describe("humanStages", () => {
  it("returns no stages for an empty stream", () => {
    expect(humanStages(groupTimeline([]))).toEqual([]);
  });

  it("projects a representative run without raw internal keys", () => {
    const events: MissionEvent[] = [
      { phase: "websearch", status: "done", hits: 3, sources: [] },
      { phase: "route", status: "done", route: ["product", "odd_internal_key"] },
      { phase: "dept", dept: "product", status: "start" },
      { phase: "dept", dept: "product", status: "done" },
      { phase: "dept", dept: "odd_internal_key", status: "done" },
      { phase: "synth", iteration: 1, status: "done" },
      { phase: "inspect", iteration: 1, verdict: "REVISION" },
      { phase: "verify", iteration: 1, status: "done", ok: false, rate: 0.4 },
      { phase: "synth", iteration: 2, status: "done" },
      { phase: "inspect", iteration: 2, verdict: "PASS" },
      { phase: "verify", iteration: 2, status: "done", ok: true, rate: 1 },
    ];
    const stages = humanStages(groupTimeline(events));
    expect(stages.map((s) => s.key)).toEqual(["prepare", "departments", "synthesis", "inspection"]);
    expect(stages.find((s) => s.key === "inspection")?.iterations).toHaveLength(2);
    // A real department key maps to its plain-language label; an unknown key falls back to generic.
    expect(deptLabelKey("product")).toBe("missions.dept.product");
    expect(deptLabelKey("finance")).toBe("missions.dept.finance");
    expect(deptLabelKey("odd_internal_key")).toBe("missions.dept.generic");
    expect(JSON.stringify(stages)).not.toMatch(/odd_internal_key|websearch/);
  });

  it("reports a failed media render as failed, never as done", () => {
    const stages = humanStages(groupTimeline([
      { phase: "asset", status: "start", kind: "video" },
      { phase: "asset", status: "failed", kind: "video", reason: "render error" },
    ]));
    const media = stages.find((s) => s.key === "media");
    expect(media?.detail[0]?.state).toBe("failed");
  });

  it("marks department work running until all present teams finish", () => {
    const running = humanStages(groupTimeline([{ phase: "dept", dept: "product", status: "start" }]));
    expect(running.find((s) => s.key === "departments")?.state).toBe("running");
    const done = humanStages(groupTimeline([{ phase: "dept", dept: "product", status: "start" }, { phase: "dept", dept: "product", status: "done" }]));
    expect(done.find((s) => s.key === "departments")?.state).toBe("done");
  });
});
