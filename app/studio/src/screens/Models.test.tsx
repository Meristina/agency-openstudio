import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../i18n/I18nProvider";
import Models from "./Models";

// A paid, key-gated cloud entry — the exact case that would tempt a secret input.
// Keys stay env-only (FR-015), so the screen must render it without any key field.
const inventory = {
  generated_at: "now",
  families: [
    {
      family: "image",
      selectable: true,
      selected: null,
      selected_stale: false,
      env_override: null,
      active: "mlx",
      entries: [
        {
          id: "seedance",
          label: "Seedance (cloud)",
          family: "image",
          cost: "paid",
          availability: "unavailable",
          reason: "API key not set",
          enablement: "Set $AGENCY_STUDIO_VIDEO_API_KEY in the environment",
          tier: "API",
          note: "Cloud image provider",
          default: false,
          key_env: "AGENCY_STUDIO_VIDEO_API_KEY",
        },
      ],
    },
  ],
};

vi.mock("../api", () => ({
  fetchCapabilities: vi.fn(() => Promise.resolve(inventory)),
  selectCapability: vi.fn(),
  clearCapability: vi.fn(),
}));

afterEach(cleanup);

describe("Models", () => {
  it("embeds capabilities under a localized title without secret inputs", async () => {
    render(<I18nProvider><Models /></I18nProvider>);
    expect(screen.getByRole("heading", { name: "Models and capabilities" })).toBeTruthy();
    // The key-gated entry actually renders, so the no-secret assertions below
    // exercise a populated panel rather than an empty one.
    expect((await screen.findAllByText("Seedance (cloud)")).length).toBeGreaterThan(0);
    expect(screen.queryByLabelText(/key|secret/i)).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
  });
});
