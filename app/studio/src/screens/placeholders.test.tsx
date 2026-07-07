import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import { routes } from "../shell/router";
import { NotFound } from "../ui/states";
import { PlaceholderScreen } from "./placeholders";

afterEach(() => {
  cleanup();
  window.location.hash = "";
});

describe("placeholders", () => {
  it("renders every placeholder route with a way home", () => {
    const placeholders = routes.filter((route) => route.status === "placeholder");
    expect(placeholders.map((route) => route.id)).not.toContain("brief");
    expect(placeholders.map((route) => route.id)).not.toContain("import");
    expect(placeholders.map((route) => route.id)).toEqual([]);
    for (const route of placeholders) {
      cleanup();
      render(<I18nProvider><PlaceholderScreen id={route.id} /></I18nProvider>);
      expect(screen.getByRole("heading")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Back home" }));
      expect(window.location.hash).toBe("#/");
    }
  });

  it("renders not found", () => {
    render(<I18nProvider><NotFound /></I18nProvider>);
    expect(screen.getByText("Screen not found")).toBeTruthy();
  });
});
