import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchTaxonomy } from "../api";
import { I18nProvider } from "../i18n/I18nProvider";
import { ClientContextProvider, ClientContextSelector } from "./ClientContext";

vi.mock("../api", () => ({ fetchTaxonomy: vi.fn() }));

const taxonomy = { clients: [{ name: "Acme", missions: 1, projects: [{ name: "Rebrand", missions: 1, campaigns: [{ name: "Launch", missions: 1 }] }] }] };

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

describe("ClientContext", () => {
  it("lists hierarchy, clears deeper picks, and persists", async () => {
    vi.mocked(fetchTaxonomy).mockResolvedValue(taxonomy);
    render(<I18nProvider><ClientContextProvider><ClientContextSelector /></ClientContextProvider></I18nProvider>);
    await waitFor(() => expect(screen.getByRole("option", { name: "Acme" })).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Client"), { target: { value: "Acme" } });
    fireEvent.change(screen.getByLabelText("Project"), { target: { value: "Rebrand" } });
    fireEvent.change(screen.getByLabelText("Campaign"), { target: { value: "Launch" } });
    expect(localStorage.getItem("agency-studio.prefs")).toContain("Launch");
    fireEvent.change(screen.getByLabelText("Client"), { target: { value: "" } });
    expect((screen.getByLabelText("Project") as HTMLSelectElement).value).toBe("");
  });

  it("handles empty taxonomy", async () => {
    vi.mocked(fetchTaxonomy).mockResolvedValue({ clients: [] });
    render(<I18nProvider><ClientContextProvider><ClientContextSelector /></ClientContextProvider></I18nProvider>);
    expect(await screen.findByRole("option", { name: "No clients yet" })).toBeTruthy();
  });

  it("keeps a persisted context that the loaded taxonomy still contains", async () => {
    localStorage.setItem("agency-studio.prefs", JSON.stringify({ clientContext: { client: "Acme", project: "Rebrand", campaign: "Launch" } }));
    vi.mocked(fetchTaxonomy).mockResolvedValue(taxonomy);
    render(<I18nProvider><ClientContextProvider><ClientContextSelector /></ClientContextProvider></I18nProvider>);
    await waitFor(() => expect(screen.getByRole("option", { name: "Acme" })).toBeTruthy());
    expect((screen.getByLabelText("Client") as HTMLSelectElement).value).toBe("Acme");
    expect((screen.getByLabelText("Project") as HTMLSelectElement).value).toBe("Rebrand");
    expect((screen.getByLabelText("Campaign") as HTMLSelectElement).value).toBe("Launch");
    expect(localStorage.getItem("agency-studio.prefs")).toContain("Launch");
  });

  it("drops stale persisted context", async () => {
    localStorage.setItem("agency-studio.prefs", JSON.stringify({ clientContext: { client: "Gone", project: "Old", campaign: "Old" } }));
    vi.mocked(fetchTaxonomy).mockResolvedValue({ clients: [] });
    render(<I18nProvider><ClientContextProvider><ClientContextSelector /></ClientContextProvider></I18nProvider>);
    await waitFor(() => expect((screen.getByLabelText("Client") as HTMLSelectElement).value).toBe(""));
    expect((screen.getByLabelText("Project") as HTMLSelectElement).value).toBe("");
  });
});
