import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { runMission } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import type { MissionEvent } from "../../types";
import { expectNamedInteractives } from "../../testing/a11y";
import { missionSession } from "../session/missionSession";
import { record } from "./followPointer";
import MissionTimeline from "./MissionTimeline";

vi.mock("../../api", () => ({
  runMission: vi.fn(async (_goal: string, onEvent: (event: MissionEvent) => void) => {
    onEvent({ phase: "run", run_id: "r1" });
    onEvent({ phase: "websearch", status: "done", hits: 2, sources: [] });
    onEvent({ phase: "route", status: "done", route: ["product"] });
    onEvent({ phase: "dept", dept: "product", status: "start" });
    onEvent({ phase: "dept", dept: "product", status: "done" });
    onEvent({ phase: "inspect", iteration: 1, verdict: "PASS" });
  }),
  cancelMission: vi.fn(async () => true),
  getMission: vi.fn(async () => ({})),
  fetchMissionPdf: vi.fn(async () => new Blob()),
}));

afterEach(() => {
  cleanup();
  missionSession.reset();
  localStorage.clear();
  vi.clearAllMocks();
  window.location.hash = "";
});

function renderTimeline() {
  return render(<I18nProvider><MissionTimeline /></I18nProvider>);
}

describe("MissionTimeline", () => {
  it("renders an empty state when nothing is active", () => {
    renderTimeline();
    expect(screen.getByRole("heading", { name: "Mission timeline" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Start a brief" }));
    expect(window.location.hash).toBe("#/brief");
  });

  it("follows a live session, expands detail, and exposes an aria-live update", async () => {
    renderTimeline();
    await missionSession.launch({ goal: "g", opts: { webSearch: false, video: false, assets: false } });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Gathering facts" })).toBeTruthy());
    expect(screen.getByRole("heading", { name: "Teams at work" })).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: "Show detail" })[0]);
    expect(screen.getByText("Sources checked")).toBeTruthy();
    expect(document.querySelector("[aria-live='polite']")?.textContent).toMatch(/Gathering facts/);
    expectNamedInteractives();
  });

  it("shows a plain error with a way forward when a launch never streams", async () => {
    vi.mocked(runMission).mockImplementationOnce(async () => { throw new Error("the installed agency-kit has no mission-resume support"); });
    renderTimeline();
    await missionSession.launch({ goal: "g", opts: { webSearch: false, video: false, assets: false } });
    // No run id ever arrived ⇒ a launch/resume rejection: a plain error + retry, never labelled
    // "connection lost", and the raw server reason (which names the engine/kit) never leaks.
    await waitFor(() => expect(screen.getByRole("button", { name: "Return to brief" })).toBeTruthy());
    expect(screen.queryByText(/connection stopped/i)).toBeNull();
    expect(document.body.textContent).not.toMatch(/agency-kit/i);
  });

  it("keeps a calm connection-lost state after streaming began", async () => {
    vi.mocked(runMission).mockImplementationOnce(async (_goal: string, onEvent: (event: MissionEvent) => void) => {
      onEvent({ phase: "run", run_id: "r9" });
      onEvent({ phase: "route", status: "done", route: ["product"] });
      throw new Error("network dropped");
    });
    renderTimeline();
    await missionSession.launch({ goal: "g", opts: { webSearch: false, video: false, assets: false } });
    // A run id arrived, then the stream dropped ⇒ connection-lost, stages preserved.
    await waitFor(() => expect(screen.getByText(/connection stopped/i)).toBeTruthy());
  });

  it("shows resume offer from a reload pointer", () => {
    record({ runId: "r2", status: "error", resumable: true, checkpoint: "c1" });
    renderTimeline();
    expect(screen.getByRole("heading", { name: "Production can be resumed" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(screen.getByText("No production is running right now.")).toBeTruthy();
  });
});
