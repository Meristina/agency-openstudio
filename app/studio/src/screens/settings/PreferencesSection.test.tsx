import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PREFS_KEY } from "../../i18n/catalog";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import LanguageSwitch from "../../shell/LanguageSwitch";
import PreferencesSection from "./PreferencesSection";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({
    clients: [{ name: "Acme", missions: 0, projects: [{ name: "Rebrand", missions: 0, campaigns: [{ name: "Launch", missions: 0 }] }] }],
  }),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
});

function renderPrefs() {
  return render(<I18nProvider><ClientContextProvider><LanguageSwitch /><PreferencesSection /></ClientContextProvider></I18nProvider>);
}

describe("PreferencesSection", () => {
  it("uses the same locale source as the top bar", () => {
    renderPrefs();
    fireEvent.change(screen.getAllByLabelText("Language")[1], { target: { value: "fr" } });
    expect((screen.getAllByLabelText("Langue")[0] as HTMLSelectElement).value).toBe("fr");
    expect(JSON.parse(localStorage.getItem(PREFS_KEY) || "{}")).toMatchObject({ locale: "fr" });
  });

  it("persists and clears the default context", async () => {
    renderPrefs();
    await waitFor(() => expect(screen.getByRole("option", { name: "Acme" })).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Client"), { target: { value: "Acme" } });
    fireEvent.change(screen.getByLabelText("Project"), { target: { value: "Rebrand" } });
    fireEvent.change(screen.getByLabelText("Campaign"), { target: { value: "Launch" } });
    await waitFor(() => expect(JSON.parse(localStorage.getItem(PREFS_KEY) || "{}").clientContext).toMatchObject({ client: "Acme", project: "Rebrand", campaign: "Launch" }));
    fireEvent.click(screen.getByRole("button", { name: "Clear context" }));
    await waitFor(() => expect(JSON.parse(localStorage.getItem(PREFS_KEY) || "{}").clientContext).toEqual({}));
  });
});
