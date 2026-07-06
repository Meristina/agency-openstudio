import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { en } from "./en";
import { fr } from "./fr";
import { I18nProvider, useI18n } from "./I18nProvider";
import { PREFS_KEY } from "./catalog";

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.restoreAllMocks();
});

function Probe() {
  const { locale, setLocale, t } = useI18n();
  return (
    <>
      <p>{locale}</p>
      <p>{t("state.comingSoon.title", { title: "Brief" })}</p>
      <button onClick={() => setLocale("fr")}>fr</button>
    </>
  );
}

describe("i18n", () => {
  it("keeps EN and FR catalogs complete", () => {
    expect(Object.keys(fr).sort()).toEqual(Object.keys(en).sort());
  });

  it("interpolates, defaults from browser language, and persists", () => {
    vi.spyOn(navigator, "language", "get").mockReturnValue("fr-FR");
    render(<I18nProvider><Probe /></I18nProvider>);
    expect(screen.getAllByText("fr").length).toBeGreaterThan(0);
    expect(screen.getByText(/Brief arrive/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "fr" }));
    expect(JSON.parse(localStorage.getItem(PREFS_KEY) || "{}")).toMatchObject({ locale: "fr" });
  });

  it("recovers from malformed prefs", () => {
    localStorage.setItem(PREFS_KEY, "{");
    render(<I18nProvider><Probe /></I18nProvider>);
    expect(screen.getByText("en")).toBeTruthy();
  });

  it("does not render raw keys", () => {
    render(<I18nProvider><Probe /></I18nProvider>);
    expect(document.body.textContent).not.toMatch(/\bnav\.|state\./);
  });

  it("keeps guided brief wording out of internal machinery terms", () => {
    const banned = /\b(department|engine|pipeline|flag|environment variable|api)\b/i;
    for (const catalog of [en, fr]) {
      for (const [key, value] of Object.entries(catalog)) {
        if (key.startsWith("brief.")) expect(value).not.toMatch(banned);
      }
    }
  });

  it("keeps missions wording localized without raw key leaks", () => {
    const banned = /\b(engine|pipeline|phase|flag|environment variable|websearch|dept|mcp_tools)\b/i;
    for (const catalog of [en, fr]) {
      for (const [key, value] of Object.entries(catalog)) {
        if (key.startsWith("missions.")) {
          expect(value).not.toMatch(banned);
          expect(value).not.toMatch(/^missions\./);
        }
      }
    }
  });
});
