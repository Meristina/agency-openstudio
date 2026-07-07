import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import Shell from "./Shell";

vi.mock("../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({ clients: [] }),
  listMissions: vi.fn().mockResolvedValue([]),
  fetchCapabilities: vi.fn().mockResolvedValue({ families: [], generated_at: "now" }),
  selectCapability: vi.fn(),
  clearCapability: vi.fn(),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  window.location.hash = "";
});

describe("LanguageSwitch", () => {
  it("switches chrome in place and persists", () => {
    render(<I18nProvider><Shell /></I18nProvider>);
    fireEvent.change(screen.getByLabelText("Language"), { target: { value: "fr" } });
    expect(screen.getByRole("link", { name: "Accueil" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Que voulez-vous produire ?" })).toBeTruthy();
    cleanup();
    render(<I18nProvider><Shell /></I18nProvider>);
    expect(screen.getByRole("link", { name: "Accueil" })).toBeTruthy();
  });
});
