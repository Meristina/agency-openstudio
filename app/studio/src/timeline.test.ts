import { describe, expect, it } from "vitest";
import { groupTimeline, runStatus } from "./timeline";
import type { MissionEvent } from "./types";

describe("groupTimeline", () => {
  it("returns an empty model for no events", () => {
    const m = groupTimeline([]);
    expect(m).toEqual({ retrieval: null, websearch: null, mcp: null, graph: null, route: null, depts: [], synth: [], inspect: [], assets: [], terminal: null });
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
    expect(m).toEqual({ retrieval: null, websearch: null, mcp: null, graph: null, route: ["solve"], depts: [], synth: [], inspect: [], assets: [], terminal: null });
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

  it("folds a retrieval start→done with hits and sources", () => {
    const m = groupTimeline([
      { phase: "run", run_id: "c".repeat(32) },
      { phase: "retrieval", status: "start" },
      { phase: "retrieval", status: "done", hits: 2, sources: [
        { title: "Solar", doc_id: "d1" }, { title: "Costs", doc_id: "d1" },
      ] },
      { phase: "route", status: "done", route: ["solve"] },
    ]);
    expect(m.retrieval).toEqual({
      status: "done", hits: 2,
      sources: [{ title: "Solar", doc_id: "d1" }, { title: "Costs", doc_id: "d1" }],
      reason: null,
    });
  });

  it("folds a skipped retrieval with its reason", () => {
    const m = groupTimeline([
      { phase: "retrieval", status: "skipped", reason: "local-docs extra not installed" },
    ]);
    expect(m.retrieval).toEqual({
      status: "skipped", hits: null, sources: [], reason: "local-docs extra not installed",
    });
    // Retrieval alone (before any route/dept) still reads as a running mission.
    expect(runStatus(m)).toBe("running");
  });

  it("folds a websearch start→done with hits and sources", () => {
    const m = groupTimeline([
      { phase: "run", run_id: "d".repeat(32) },
      { phase: "websearch", status: "start" },
      { phase: "websearch", status: "done", hits: 2, sources: [
        { title: "Solar 101", url: "https://a.example" }, { title: "", url: "https://b.example" },
      ] },
      { phase: "route", status: "done", route: ["solve"] },
    ]);
    expect(m.websearch).toEqual({
      status: "done", hits: 2,
      sources: [{ title: "Solar 101", url: "https://a.example" }, { title: "", url: "https://b.example" }],
      reason: null,
    });
  });

  it("folds a skipped websearch with its reason", () => {
    const m = groupTimeline([
      { phase: "websearch", status: "skipped", reason: "web-search extra not installed" },
    ]);
    expect(m.websearch).toEqual({
      status: "skipped", hits: null, sources: [], reason: "web-search extra not installed",
    });
    // Web search alone (before any route/dept) still reads as a running mission.
    expect(runStatus(m)).toBe("running");
  });

  it("folds an mcp start→done with hits and sources", () => {
    const m = groupTimeline([
      { phase: "run", run_id: "e".repeat(32) },
      { phase: "mcp", status: "start" },
      { phase: "mcp", status: "done", hits: 1, sources: [{ name: "Onboarding", server: "wiki" }] },
      { phase: "route", status: "done", route: ["solve"] },
    ]);
    expect(m.mcp).toEqual({
      status: "done", hits: 1, sources: [{ name: "Onboarding", server: "wiki" }], reason: null,
    });
  });

  it("folds a skipped mcp with its reason", () => {
    const m = groupTimeline([
      { phase: "mcp", status: "skipped", reason: "mcp extra not installed" },
    ]);
    expect(m.mcp).toEqual({
      status: "skipped", hits: null, sources: [], reason: "mcp extra not installed",
    });
    expect(runStatus(m)).toBe("running");
  });

  it("folds a graph start→done with entities and sources", () => {
    const m = groupTimeline([
      { phase: "run", run_id: "e".repeat(32) },
      { phase: "graph", status: "start" },
      { phase: "graph", status: "done", hits: 2, sources: [
        { label: "Widget Engine", kind: "entity" },
        { label: "Rust Toolchain", kind: "entity" },
      ] },
      { phase: "route", status: "done", route: ["solve"] },
    ]);
    expect(m.graph).toEqual({
      status: "done", hits: 2, sources: [
        { label: "Widget Engine", kind: "entity" },
        { label: "Rust Toolchain", kind: "entity" },
      ], reason: null,
    });
  });

  it("folds a skipped graph with its reason and reads as running", () => {
    const m = groupTimeline([
      { phase: "graph", status: "skipped", reason: "knowledge-graph extra not installed" },
    ]);
    expect(m.graph).toEqual({
      status: "skipped", hits: null, sources: [], reason: "knowledge-graph extra not installed",
    });
    expect(runStatus(m)).toBe("running");
  });
});
