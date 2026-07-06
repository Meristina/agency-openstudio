import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import Models from "./Models";
import { sampleInventory } from "./models/testData";

vi.mock("../api", () => ({
  fetchCapabilities: vi.fn(() => Promise.resolve(sampleInventory())),
  selectCapability: vi.fn(),
  clearCapability: vi.fn(),
}));

afterEach(cleanup);

describe("Models", () => {
  it("renders the operator surface without secret inputs", async () => {
    render(<I18nProvider><Models /></I18nProvider>);
    expect(screen.getByRole("heading", { name: "Models and capabilities" })).toBeTruthy();
    expect(await screen.findByText("Cloud Image")).toBeTruthy();
    expect(screen.getByText("Set AGENCY_IMAGE_KEY in the environment to enable this.")).toBeTruthy();
    // No secret entry of any kind — catches text, password, or any labeled key/secret control.
    expect(screen.queryByLabelText(/key|secret/i)).toBeNull();
    expect(screen.queryAllByRole("textbox", { name: /key|secret/i })).toHaveLength(0);
    expect(screen.queryByRole("textbox")).toBeNull();
  });
});
