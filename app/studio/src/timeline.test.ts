import { describe, expect, it } from "vitest";
import { groupTimeline, runStatus } from "./timeline";
import type { MissionEvent } from "./types";

describe("groupTimeline", () => {
  it("returns an empty model for no events", () => {
    const m = groupTimeline([]);
    expect(m).toEqual({ route: null, depts: [], synth: [], inspect: [], terminal: null });
    expect(runStatus(m)).toBe("idle");
  });

  it("folds a full route→dept→synth→inspect→done run in order", () => {
    const events: MissionEvent[] = [
      { phase: "route", status: "done", route: ["solve", "product"] },
      { phase: "dept", dept: "solve", status: "start" },
      { phase: "dept", dept: "solve", status: "done" },
      { phase: "dept", dept: "product", status: "start" },
      { phase: "dept", dept: "product", status: "done" },
      { phase: "synth", iteration: 1, status: "start" },
      { phase: "synth", iteration: 1, status: "done" },
      { phase: "inspect", iteration: 1, status: "start" },
      { phase: "inspect", iteration: 1, verdict: "PASS" },
      { phase: "done", mission_id: "m1", verdict: "PASS", path: "/p", residual_risk: null },
    ];
    const m = groupTimeline(events);
    expect(m.route).toEqual(["solve", "product"]);
    expect(m.depts).toEqual([
      { dept: "solve", done: true },
      { dept: "product", done: true },
    ]);
    expect(m.synth).toEqual([{ iteration: 1, done: true }]);
    expect(m.inspect).toEqual([{ iteration: 1, verdict: "PASS" }]);
    expect(m.terminal).toEqual({ kind: "done", verdict: "PASS", missionId: "m1", path: "/p", residualRisk: null });
    expect(runStatus(m)).toBe("done");
  });

  it("keeps both iterations on a VETO→retry (Art. IX visible, never collapsed)", () => {
    const events: MissionEvent[] = [
      { phase: "route", status: "done", route: ["product"] },
      { phase: "synth", iteration: 1, status: "done" },
      { phase: "inspect", iteration: 1, verdict: "VETO" },
      { phase: "synth", iteration: 2, status: "done" },
      { phase: "inspect", iteration: 2, verdict: "PASS" },
    ];
    const m = groupTimeline(events);
    expect(m.inspect).toEqual([
      { iteration: 1, verdict: "VETO" },
      { iteration: 2, verdict: "PASS" },
    ]);
  });

  it("captures an error terminal", () => {
    const m = groupTimeline([{ phase: "error", message: "engine crashed" }]);
    expect(m.terminal).toEqual({ kind: "error", message: "engine crashed" });
    expect(runStatus(m)).toBe("error");
  });
});
