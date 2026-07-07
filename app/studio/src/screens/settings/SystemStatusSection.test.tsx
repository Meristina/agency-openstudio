import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCapabilities, getSystemInfo } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { sampleInventory } from "../models/testData";
import SystemStatusSection from "./SystemStatusSection";

vi.mock("../../api", () => ({
  getSystemInfo: vi.fn(),
  fetchCapabilities: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

describe("SystemStatusSection", () => {
  it("renders connected system facts and model link", async () => {
    vi.mocked(getSystemInfo).mockResolvedValue({ version: "1.2.3", dataDir: "/tmp/studio" });
    vi.mocked(fetchCapabilities).mockResolvedValue(sampleInventory());
    render(<I18nProvider><SystemStatusSection /></I18nProvider>);
    await waitFor(() => expect(screen.getByText("Connected")).toBeTruthy());
    expect(screen.getByText("1.2.3")).toBeTruthy();
    expect(screen.getByText("/tmp/studio")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open model settings" }).getAttribute("href")).toBe("#/models");
    expect(document.body.textContent).not.toMatch(/secret|token|api[_ -]?key/i);
  });

  it("degrades honestly offline", async () => {
    vi.mocked(getSystemInfo).mockRejectedValue(new Error("down"));
    vi.mocked(fetchCapabilities).mockRejectedValue(new Error("down"));
    render(<I18nProvider><SystemStatusSection /></I18nProvider>);
    await waitFor(() => expect(screen.getByText("Offline")).toBeTruthy());
    expect(screen.getAllByText("Unknown").length).toBeGreaterThan(0);
  });

  it("stays connected when only capabilities fail", async () => {
    vi.mocked(getSystemInfo).mockResolvedValue({ version: "1.2.3", dataDir: "/tmp/studio" });
    vi.mocked(fetchCapabilities).mockRejectedValue(new Error("capabilities down"));
    render(<I18nProvider><SystemStatusSection /></I18nProvider>);
    // A capabilities failure must not mask a reachable server or the version it returned.
    await waitFor(() => expect(screen.getByText("Connected")).toBeTruthy());
    expect(screen.getByText("1.2.3")).toBeTruthy();
    expect(screen.getByText("/tmp/studio")).toBeTruthy();
  });
});
