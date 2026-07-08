import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { listMissions } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { PREFS_KEY } from "../../i18n/catalog";
import { ClientContextProvider } from "../../shell/ClientContext";
import { expectNamedInteractives } from "../../testing/a11y";
import { BRIEF_DRAFT_KEY } from "../brief/briefDraft";
import { FOLLOW_POINTER_KEY } from "../missions/followPointer";
import Home from "./Home";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn(async () => ({ clients: [{ name: "Acme", missions: 1, projects: [{ name: "Rebrand", missions: 1, campaigns: [{ name: "Launch", missions: 1 }] }] }] })),
  listMissions: vi.fn(async () => []),
}));

function renderHome() {
  return render(<I18nProvider><ClientContextProvider><Home /></ClientContextProvider></I18nProvider>);
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorage.clear();
  window.location.hash = "";
});

describe("Home", () => {
  it("starts a brief with byte-identical intent routing", async () => {
    renderHome();
    expect(screen.getByRole("heading", { name: "What do you want to produce?" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Intent"), { target: { value: " event plan " } });
    fireEvent.click(screen.getByRole("button", { name: "Start brief" }));
    expect(window.location.hash).toBe("#/brief?intent=event%20plan");
    window.location.hash = "";
    fireEvent.change(screen.getByLabelText("Intent"), { target: { value: " " } });
    fireEvent.click(screen.getByRole("button", { name: "Start brief" }));
    expect(window.location.hash).toBe("#/brief");
    await waitFor(() => expect(screen.getByText("No recent work yet.")).toBeTruthy());
  });

  it("renders French start copy", () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ locale: "fr" }));
    renderHome();
    expect(screen.getByRole("heading", { name: "Que voulez-vous produire ?" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Démarrer le brief" })).toBeTruthy();
  });

  it("resumes draft and opens recent missions by state", async () => {
    localStorage.setItem(BRIEF_DRAFT_KEY, JSON.stringify({ version: 1, stepIndex: 1, answers: { intent: "Draft" } }));
    localStorage.setItem(FOLLOW_POINTER_KEY, JSON.stringify({ runId: "m1", status: "running", updatedAt: 1 }));
    vi.mocked(listMissions).mockResolvedValueOnce([
      { mission_id: "m1", goal: "Live work", delivered: false, verdict: "in-progress" },
      { mission_id: "m2", goal: "Finished work", delivered: true, verdict: "PASS" },
      { mission_id: "m3", goal: "Needs care", delivered: false, verdict: "VETO" },
      { mission_id: "m4", goal: "Four" },
      { mission_id: "m5", goal: "Five" },
      { mission_id: "m6", goal: "Six" },
    ]);
    renderHome();
    fireEvent.click(screen.getByRole("button", { name: "Resume draft" }));
    expect(window.location.hash).toBe("#/brief");
    await waitFor(() => expect(screen.queryByText("Six")).toBeNull());
    // Anchor at start so these match the item's OPEN button (name = "<label> <status>"),
    // not the per-item delete button (name = "Delete — <label>").
    fireEvent.click(screen.getByRole("button", { name: /^Live work/ }));
    expect(window.location.hash).toBe("#/missions");
    fireEvent.click(screen.getByRole("button", { name: /^Finished work/ }));
    expect(window.location.hash).toBe("#/library?deliverable=m2");
    fireEvent.click(screen.getByRole("button", { name: /^Needs care/ }));
    expect(window.location.hash).toBe("#/library?deliverable=m3");
    fireEvent.click(screen.getByRole("button", { name: "See all work" }));
    expect(window.location.hash).toBe("#/library");
    expectNamedInteractives();
  });

  it("keeps start usable when recent work fails", async () => {
    vi.mocked(listMissions).mockRejectedValueOnce(new Error("down"));
    renderHome();
    fireEvent.click(screen.getByRole("button", { name: "Start brief" }));
    expect(window.location.hash).toBe("#/brief");
    await waitFor(() => expect(screen.getByText("Recent work could not be loaded. You can still start a new brief.")).toBeTruthy());
    expect(screen.queryByText("No recent work yet.")).toBeNull();
  });

  it("renders shortcuts and read-only context", async () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ clientContext: { client: "Acme", project: "Rebrand", campaign: "Launch" } }));
    renderHome();
    expect(screen.getByText("Acme / Rebrand / Launch")).toBeTruthy();
    for (const [name, target] of [["Library", "#/library"], ["Import", "#/import"], ["Models", "#/models"]] as const) {
      fireEvent.click(screen.getByRole("button", { name }));
      expect(window.location.hash).toBe(target);
    }
  });

  it("renders no-context label", () => {
    renderHome();
    expect(screen.getByText("Scoped to")).toBeTruthy();
    expect(screen.getByText("No context selected")).toBeTruthy();
  });
});
