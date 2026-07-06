import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getMission, listMissions } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import { expectNamedInteractives } from "../../testing/a11y";
import DeliverableLibrary from "./DeliverableLibrary";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn(async () => ({ clients: [{ name: "Acme", missions: 2, projects: [{ name: "Rebrand", missions: 2, campaigns: [{ name: "Launch", missions: 1 }] }] }] })),
  listMissions: vi.fn(async () => [
    { mission_id: "20260701-a", goal: "Sponsor deck", delivered: true, verdict: "PASS", client: "Acme", project: "Rebrand", campaign: "Launch" },
    { mission_id: "20260702-b", goal: "Broken video", delivered: false, verdict: "VETO", client: "Acme", project: "Rebrand" },
  ]),
  getMission: vi.fn(async (id: string) => ({ mission_id: id, goal: id === "20260702-b" ? "Broken video" : "Sponsor deck", delivered: "body", verdicts: [{ verdict: "PASS" }] })),
  assignMission: vi.fn(async () => ({ client: "Acme", project: "Rebrand", campaign: null })),
  fetchMissionPdf: vi.fn(async () => new Blob()),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorage.clear();
});

function renderLibrary(search = "") {
  return render(<I18nProvider><ClientContextProvider><DeliverableLibrary search={search} /></ClientContextProvider></I18nProvider>);
}

describe("DeliverableLibrary", () => {
  it("renders grouped cards, filters, previews, opens detail, and supports deep links", async () => {
    renderLibrary("deliverable=20260701-a");
    await waitFor(() => expect(screen.getByRole("heading", { name: "Deliverable library" })).toBeTruthy());
    expect(screen.getAllByText("Acme").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Sponsor deck").length).toBeGreaterThan(0);
    await waitFor(() => expect(getMission).toHaveBeenCalledWith("20260701-a"));
    expect(screen.getAllByRole("heading", { name: "Sponsor deck" }).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("Search title, client, project, or campaign"), { target: { value: "broken" } });
    expect(screen.getByText("Broken video")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("All outcomes"), { target: { value: "successful" } });
    expect(screen.getByText("No deliverables match this search.")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: "Clear" }).at(-1)!);
    expect(screen.getAllByText("Sponsor deck").length).toBeGreaterThan(0);

    fireEvent.click(screen.getAllByRole("button", { name: "Preview" })[0]);
    await waitFor(() => expect(screen.getByLabelText("Preview")).toBeTruthy());
    expectNamedInteractives();
  });

  it("shows first-run and load-failure states", async () => {
    vi.mocked(listMissions).mockResolvedValueOnce([]);
    renderLibrary();
    await waitFor(() => expect(screen.getByRole("heading", { name: "No deliverables yet" })).toBeTruthy());
    cleanup();
    vi.mocked(listMissions).mockRejectedValueOnce(new Error("down"));
    renderLibrary();
    await waitFor(() => expect(screen.getByText("The library could not be loaded. Check that the local studio service is running.")).toBeTruthy());
  });
});
