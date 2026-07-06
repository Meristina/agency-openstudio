import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getMission, listMissions } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import { expectNamedInteractives } from "../../testing/a11y";
import Export from "./Export";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn(async () => ({ clients: [{ name: "Acme", missions: 1, projects: [] }] })),
  listMissions: vi.fn(async () => [
    { mission_id: "m1", goal: "Sponsor deck", delivered: true, verdict: "PASS", client: "Acme" },
    { mission_id: "m2", goal: "Still running", delivered: false, verdict: "in-progress" },
  ]),
  getMission: vi.fn(async (id: string) => ({ mission_id: id, goal: "Sponsor deck", delivered: "x", assets: [{ status: "ok", url: "/media/missions/m1/a.png" }] })),
  fetchMissionPdf: vi.fn(async () => new Blob()),
  fetchMissionMediaZip: vi.fn(async () => new Blob()),
  fetchMissionBundle: vi.fn(async () => new Blob()),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorage.clear();
});

function renderExport() {
  return render(<I18nProvider><ClientContextProvider><Export /></ClientContextProvider></I18nProvider>);
}

describe("Export", () => {
  it("lists finished deliverables and opens a keyboard-operable panel", async () => {
    renderExport();
    expect(await screen.findByRole("heading", { name: "Export" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Sponsor deck/ })).toBeTruthy();
    expect(screen.queryByText("Still running")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Sponsor deck/ }));
    await waitFor(() => expect(getMission).toHaveBeenCalledWith("m1"));
    expect(screen.getByText("A polished document")).toBeTruthy();
    expectNamedInteractives();
  });

  it("shows empty and connection-lost states", async () => {
    vi.mocked(listMissions).mockResolvedValueOnce([]);
    renderExport();
    expect(await screen.findByRole("heading", { name: "Nothing to export yet" })).toBeTruthy();
    cleanup();
    vi.mocked(listMissions).mockRejectedValueOnce(new Error("down"));
    renderExport();
    expect(await screen.findByText("Export could not connect to the local studio service.")).toBeTruthy();
  });
});
