import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import Home from "./Home";

afterEach(() => {
  cleanup();
  window.location.hash = "";
});

describe("Home", () => {
  it("renders the magic-box question and carries intent to brief", () => {
    render(<I18nProvider><Home /></I18nProvider>);
    expect(screen.getByRole("heading", { name: "What do you want to produce?" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Intent"), { target: { value: "event plan" } });
    fireEvent.click(screen.getByRole("button", { name: "Start brief" }));
    expect(window.location.hash).toBe("#/brief?intent=event%20plan");
  });
});
