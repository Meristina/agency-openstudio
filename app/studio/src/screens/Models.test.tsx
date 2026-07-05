import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import Models from "./Models";

vi.mock("../api", () => ({
  fetchCapabilities: vi.fn().mockResolvedValue({ families: [], generated_at: "now" }),
  selectCapability: vi.fn(),
  clearCapability: vi.fn(),
}));

afterEach(cleanup);

describe("Models", () => {
  it("embeds capabilities under a localized title without secret inputs", () => {
    render(<I18nProvider><Models /></I18nProvider>);
    expect(screen.getByRole("heading", { name: "Models and capabilities" })).toBeTruthy();
    expect(screen.queryByLabelText(/key|secret/i)).toBeNull();
  });
});
