import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import { ComingSoon, Empty, ErrorState, Loading, NotFound } from "./states";

afterEach(() => {
  cleanup();
  window.location.hash = "";
});

describe("shared states", () => {
  it("renders localized state text", () => {
    render(<I18nProvider><Loading /><Empty /><ErrorState message="Boom" /></I18nProvider>);
    expect(screen.getByText("Loading...")).toBeTruthy();
    expect(screen.getByText("Nothing here yet.")).toBeTruthy();
    expect(screen.getByText("Boom")).toBeTruthy();
  });

  it("offers working back-home actions", () => {
    window.location.hash = "#/nope";
    render(<I18nProvider><ComingSoon titleKey="nav.brief" /><NotFound /></I18nProvider>);
    fireEvent.click(screen.getAllByRole("button", { name: "Back home" })[0]);
    expect(window.location.hash).toBe("#/");
    expect(document.body.textContent).not.toMatch(/\bstate\./);
  });
});
