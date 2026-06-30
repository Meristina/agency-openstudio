import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(cleanup); // no auto-cleanup (globals off) — unmount between tests

// Mock the API so App mounts without any network. Every export App imports is stubbed.
vi.mock("./api", () => ({
  listMissions: vi.fn().mockResolvedValue([]),
  getMission: vi.fn(),
  getModelsStatus: vi.fn().mockResolvedValue({ resident: null, models: {} }),
  runMission: vi.fn(),
  cancelMission: vi.fn(),
}));

import App from "./App";

describe("App tabs", () => {
  it("keeps every tabpanel mounted, toggling visibility via the hidden attribute", () => {
    render(<App />);
    const mission = document.getElementById("panel-mission");
    const image = document.getElementById("panel-image");
    const voice = document.getElementById("panel-voice");

    // All three panels exist in the DOM from the start (mounted, not conditionally rendered).
    expect(mission && image && voice).toBeTruthy();
    expect(mission!.hasAttribute("hidden")).toBe(false); // mission active by default
    expect(image!.hasAttribute("hidden")).toBe(true);
    expect(voice!.hasAttribute("hidden")).toBe(true);

    // Switching tabs only flips `hidden` — the mission panel stays mounted (so a
    // running mission and its Stop control are never torn down by a tab switch).
    fireEvent.click(screen.getByRole("tab", { name: "Image" }));
    expect(mission!.hasAttribute("hidden")).toBe(true);
    expect(image!.hasAttribute("hidden")).toBe(false);
    expect(document.getElementById("panel-mission")).toBe(mission); // same node, not remounted
  });

  it("wires each tab to its panel via aria-controls", () => {
    render(<App />);
    expect(screen.getByRole("tab", { name: "Image" }).getAttribute("aria-controls")).toBe("panel-image");
    expect(document.getElementById("panel-image")?.getAttribute("role")).toBe("tabpanel");
  });
});
