import { describe, expect, it } from "vitest";
import { groupTimeline, runStatus } from "./timeline";
import type { MissionEvent } from "./types";

describe("groupTimeline", () => {
  it("returns an empty model for no events", () => {
    const m = groupTimeline([]);
    expect(m).toEqual({ route: null, depts: [], synth: [], inspect: [], assets: [], terminal: null });
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

  it("reports 'running' once a route/dept has arrived but no terminal yet", () => {
    const m = groupTimeline([
      { phase: "route", status: "done", route: ["solve"] },
      { phase: "dept", dept: "solve", status: "start" },
    ]);
    expect(m.terminal).toBeNull();
    expect(runStatus(m)).toBe("running");
  });

  it("captures an error terminal", () => {
    const m = groupTimeline([{ phase: "error", message: "engine crashed" }]);
    expect(m.terminal).toEqual({ kind: "error", message: "engine crashed" });
    expect(runStatus(m)).toBe("error");
  });

  it("folds the run-id frame as a control handle, not a visible step", () => {
    const m = groupTimeline([
      { phase: "run", run_id: "a".repeat(32) },
      { phase: "route", status: "done", route: ["solve"] },
    ]);
    // The run frame contributes no step; only the route shows.
    expect(m).toEqual({ route: ["solve"], depts: [], synth: [], inspect: [], assets: [], terminal: null });
  });

  it("folds an asset render phase: start→done pairs into ok steps with the served url", () => {
    const m = groupTimeline([
      { phase: "inspect", iteration: 1, verdict: "PASS" },
      { phase: "asset", status: "start", kind: "image" },
      { phase: "asset", status: "done", kind: "image", url: "/media/a.png" },
      { phase: "asset", status: "start", kind: "tts" },
      { phase: "asset", status: "done", kind: "tts", url: "/media/a.wav" },
    ]);
    expect(m.assets).toEqual([
      { kind: "image", status: "ok", url: "/media/a.png", reason: null },
      { kind: "tts", status: "ok", url: "/media/a.wav", reason: null },
    ]);
  });

  it("folds a failed render (reason, no url) and a skipped marker (no preceding start)", () => {
    const m = groupTimeline([
      { phase: "asset", status: "start", kind: "image" },
      { phase: "asset", status: "failed", kind: "image", reason: "Metal OOM" },
      { phase: "asset", status: "skipped", kind: "tts", reason: "cancelled" },
    ]);
    expect(m.assets).toEqual([
      { kind: "image", status: "failed", url: null, reason: "Metal OOM" },
      { kind: "tts", status: "skipped", url: null, reason: "cancelled" },
    ]);
  });

  it("closes the most recent open render of a kind (sequential per modality)", () => {
    const m = groupTimeline([
      { phase: "asset", status: "start", kind: "image" },
      { phase: "asset", status: "done", kind: "image", url: "/media/1.png" },
      { phase: "asset", status: "start", kind: "image" },
      { phase: "asset", status: "done", kind: "image", url: "/media/2.png" },
    ]);
    expect(m.assets).toEqual([
      { kind: "image", status: "ok", url: "/media/1.png", reason: null },
      { kind: "image", status: "ok", url: "/media/2.png", reason: null },
    ]);
  });

  it("captures a cancelled terminal", () => {
    const m = groupTimeline([
      { phase: "run", run_id: "b".repeat(32) },
      { phase: "route", status: "done", route: ["solve"] },
      { phase: "cancelled" },
    ]);
    expect(m.terminal).toEqual({ kind: "cancelled" });
    expect(runStatus(m)).toBe("cancelled");
  });
});
