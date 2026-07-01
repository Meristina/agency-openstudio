import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import Timeline from "./Timeline";
import type { MissionEvent } from "../types";

afterEach(cleanup);

describe("<Timeline>", () => {
  it("shows the empty hint when there are no events", () => {
    const { container } = render(<Timeline events={[]} />);
    expect(container.textContent).toContain("No events yet");
  });

  it("renders route, departments, and the inspect verdict from the event stream", () => {
    const events: MissionEvent[] = [
      { phase: "route", status: "done", route: ["solve", "product"] },
      { phase: "dept", dept: "solve", status: "done" },
      { phase: "inspect", iteration: 1, verdict: "PASS" },
      { phase: "done", mission_id: "m1", verdict: "PASS", path: "/p", residual_risk: null },
    ];
    const { container } = render(<Timeline events={events} />);
    const text = container.textContent ?? "";
    expect(text).toContain("Route");
    expect(text).toContain("solve");
    expect(text).toContain("product");
    expect(text).toContain("Departments");
    expect(text).toContain("PASS");
    expect(text).toContain("m1");
  });

  it("renders the live asset phase with rendering / done / failed states", () => {
    const events: MissionEvent[] = [
      { phase: "route", status: "done", route: ["marketing"] },
      { phase: "inspect", iteration: 1, verdict: "PASS" },
      { phase: "asset", status: "start", kind: "image" },
      { phase: "asset", status: "done", kind: "image", url: "/media/a.png" },
      { phase: "asset", status: "start", kind: "tts" },
      { phase: "asset", status: "failed", kind: "tts", reason: "no voice" },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("Assets");
    expect(text).toContain("image");
    expect(text).toContain("narration");
    expect(text).toContain("failed — no voice");
  });

  it("renders the MCP tools phase with the configured servers", () => {
    const events: MissionEvent[] = [
      { phase: "mcp_tools", status: "start" },
      { phase: "mcp_tools", status: "done", servers: ["wiki", "db"] },
      { phase: "route", status: "done", route: ["product"] },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("MCP tools");
    expect(text).toContain("2 servers available to the engine");
    expect(text).toContain("wiki");
    expect(text).toContain("db");
  });

  it("renders a skipped MCP tools phase with its reason", () => {
    const events: MissionEvent[] = [
      { phase: "mcp_tools", status: "skipped", reason: "no enabled MCP servers configured" },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("MCP tools skipped — no enabled MCP servers configured");
  });

  it("renders the knowledge-graph phase with matched entities", () => {
    const events: MissionEvent[] = [
      { phase: "graph", status: "start" },
      { phase: "graph", status: "done", hits: 2, sources: [
        { label: "Widget Engine", kind: "entity" },
        { label: "Rust Toolchain", kind: "entity" },
      ] },
      { phase: "route", status: "done", route: ["product"] },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("Knowledge graph");
    expect(text).toContain("2 entities matched");
    expect(text).toContain("Widget Engine");
    expect(text).toContain("Rust Toolchain");
  });

  it("renders a skipped knowledge-graph phase with its reason", () => {
    const events: MissionEvent[] = [
      { phase: "graph", status: "skipped", reason: "knowledge-graph extra not installed" },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("knowledge graph skipped — knowledge-graph extra not installed");
  });

  it("renders the persona doctrine phase with the styled departments", () => {
    const events: MissionEvent[] = [
      { phase: "persona", status: "start" },
      { phase: "persona", status: "done", depts: ["marketing", "commander"] },
      { phase: "route", status: "done", route: ["marketing"] },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("Persona doctrine");
    expect(text).toContain("2 departments styled");
    expect(text).toContain("marketing");
    expect(text).toContain("commander");
  });

  it("renders a skipped persona doctrine phase with its reason", () => {
    const events: MissionEvent[] = [
      { phase: "persona", status: "skipped", reason: "no personas curated in the store" },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("persona doctrine skipped — no personas curated in the store");
  });

  it("renders the visual RAG phase with matched image captions", () => {
    const events: MissionEvent[] = [
      { phase: "visual", status: "start" },
      { phase: "visual", status: "done", hits: 1, sources: [{ title: "diagram.png", doc_id: "v1" }] },
      { phase: "route", status: "done", route: ["product"] },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("Visual docs");
    expect(text).toContain("1 image excerpt matched");
    expect(text).toContain("diagram.png");
  });

  it("renders a skipped visual RAG phase with its reason", () => {
    const events: MissionEvent[] = [
      { phase: "visual", status: "skipped", reason: "no images ingested" },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("visual retrieval skipped — no images ingested");
  });

  it("renders both iterations of a VETO→retry (Art. IX, never collapsed)", () => {
    const events: MissionEvent[] = [
      { phase: "route", status: "done", route: ["product"] },
      { phase: "synth", iteration: 1, status: "done" },
      { phase: "inspect", iteration: 1, verdict: "VETO" },
      { phase: "synth", iteration: 2, status: "done" },
      { phase: "inspect", iteration: 2, verdict: "PASS" },
    ];
    const text = render(<Timeline events={events} />).container.textContent ?? "";
    expect(text).toContain("VETO");
    expect(text).toContain("PASS");
  });
});
