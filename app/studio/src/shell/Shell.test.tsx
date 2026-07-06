import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import Shell from "./Shell";
import { expectNamedInteractives } from "../testing/a11y";

vi.mock("../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({ clients: [] }),
  listMissions: vi.fn().mockResolvedValue([]),
  assignMission: vi.fn().mockResolvedValue({ client: "Acme", project: "Rebrand", campaign: null }),
  getMission: vi.fn(),
  getModelsStatus: vi.fn().mockResolvedValue({ resident: null, image_models: [], models: {} }),
  listMcpServers: vi.fn().mockResolvedValue([]),
  getGraphStats: vi.fn().mockResolvedValue({ nodes: 0, edges: 0, top_entities: [] }),
  getPersonaStats: vi.fn().mockResolvedValue({ total: 0, enabled: 0, by_dept: {} }),
  listVisual: vi.fn().mockResolvedValue([]),
  runMission: vi.fn(),
  cancelMission: vi.fn(),
  fetchCapabilities: vi.fn().mockResolvedValue({ families: [], generated_at: "now" }),
  selectCapability: vi.fn(),
  clearCapability: vi.fn(),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  window.location.hash = "";
  vi.clearAllMocks();
});

function renderShell() {
  return render(<I18nProvider><Shell /></I18nProvider>);
}

describe("Shell", () => {
  it("lands on home and exposes every localized nav entry", () => {
    renderShell();
    expect(screen.getByRole("heading", { name: "What do you want to produce?" })).toBeTruthy();
    for (const name of ["Home", "Brief", "Missions", "Library", "Import", "Export", "Models", "Settings", "Console"]) {
      expect(screen.getByRole("link", { name })).toBeTruthy();
    }
    expect(screen.getByRole("link", { name: "Home" }).getAttribute("aria-current")).toBe("page");
    expectNamedInteractives();
  });

  it("reaches routes from nav, supports roving arrows, and renders the legacy console", async () => {
    renderShell();
    const home = screen.getByRole("link", { name: "Home" });
    home.focus();
    fireEvent.keyDown(screen.getByRole("navigation", { name: "Studio" }), { key: "ArrowRight" });
    expect(document.activeElement).toBe(screen.getByRole("link", { name: "Brief" }));
    fireEvent.click(screen.getByRole("link", { name: "Console" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Agency Studio" })).toBeTruthy());
  });

  it("hands home intent to the guided brief screen", async () => {
    renderShell();
    fireEvent.change(screen.getByLabelText("Intent"), { target: { value: "Launch plan" } });
    fireEvent.click(screen.getByRole("button", { name: "Start brief" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Guided brief" })).toBeTruthy());
    expect((screen.getByLabelText("Intent") as HTMLTextAreaElement).value).toBe("Launch plan");
  });
});
