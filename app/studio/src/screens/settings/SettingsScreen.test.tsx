import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import { expectNamedInteractives } from "../../testing/a11y";
import SettingsScreen from "./SettingsScreen";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({ clients: [] }),
  getSystemInfo: vi.fn().mockResolvedValue({ version: "1.2.3", dataDir: "/tmp/studio" }),
  fetchCapabilities: vi.fn().mockResolvedValue({ families: [], generated_at: "now" }),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
});

describe("SettingsScreen", () => {
  it("renders the three settings sections with named controls", () => {
    render(<I18nProvider><ClientContextProvider><SettingsScreen /></ClientContextProvider></I18nProvider>);
    expect(screen.getByRole("heading", { name: "Settings" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Preferences" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "System" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Reset" })).toBeTruthy();
    expectNamedInteractives();
  });
});
