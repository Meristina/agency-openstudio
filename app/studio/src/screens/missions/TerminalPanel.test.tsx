import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchMissionPdf } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { missionSession } from "../session/missionSession";
import TerminalPanel from "./TerminalPanel";

vi.mock("../../api", () => ({
  getMission: vi.fn(async () => ({})),
  fetchMissionPdf: vi.fn(async () => new Blob()),
  runMission: vi.fn(async () => {}),
  cancelMission: vi.fn(async () => true),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorage.clear();
});

describe("TerminalPanel", () => {
  it("opens the deliverable and actually downloads the PDF on completion", async () => {
    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    render(<I18nProvider><TerminalPanel terminal={{ kind: "done", verdict: "PASS", missionId: "m1", path: "x", residualRisk: null }} /></I18nProvider>);

    // "Open details" routes to S4's permanent library home — not a no-op.
    fireEvent.click(screen.getByRole("button", { name: "Open details" }));
    expect(window.location.hash).toBe("#/library?deliverable=m1");

    // "Download PDF" fetches the blob AND delivers it to the user (object URL created), not discarded.
    fireEvent.click(screen.getByRole("button", { name: "Download PDF" }));
    await waitFor(() => expect(fetchMissionPdf).toHaveBeenCalledWith("m1"));
    await waitFor(() => expect(createObjectURL).toHaveBeenCalled());
    vi.unstubAllGlobals();
  });

  it("resumes a recoverable pointer and shows a stopped terminal", async () => {
    const resume = vi.spyOn(missionSession, "resume").mockResolvedValueOnce(missionSession.snapshot());
    render(<I18nProvider><TerminalPanel terminal={null} pointer={{ runId: "r1", status: "error", resumable: true, checkpoint: "c", updatedAt: 1 }} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Resume" }));
    await waitFor(() => expect(resume).toHaveBeenCalledWith("r1"));
    cleanup();
    render(<I18nProvider><TerminalPanel terminal={{ kind: "cancelled" }} /></I18nProvider>);
    expect(screen.getByRole("heading", { name: "Production stopped" })).toBeTruthy();
  });
});
