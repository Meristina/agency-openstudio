import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCapabilities } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import { expectNamedInteractives } from "../../testing/a11y";
import ModelsScreen from "./ModelsScreen";
import { sampleInventory } from "./testData";

vi.mock("../../api", () => ({
  fetchCapabilities: vi.fn(async () => sampleInventory()),
  selectCapability: vi.fn(),
  clearCapability: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorage.clear();
});

function renderScreen() {
  return render(<I18nProvider><ClientContextProvider><ModelsScreen /></ClientContextProvider></I18nProvider>);
}

describe("ModelsScreen", () => {
  it("loads all nine families in plain language and re-checks on demand", async () => {
    renderScreen();
    for (const name of ["Images", "Video", "Visual understanding", "Search and memory", "Knowledge extraction", "Transcription", "Voice and narration", "Production tools", "Integrations and connectors"]) {
      expect(await screen.findByRole("heading", { name })).toBeTruthy();
    }
    expect(screen.queryByText("image")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Re-check" }));
    await waitFor(() => expect(fetchCapabilities).toHaveBeenCalledWith(true));
    expectNamedInteractives();
  });

  it("renders error retry and per-family unavailable states", async () => {
    vi.mocked(fetchCapabilities).mockRejectedValueOnce(new Error("down"));
    renderScreen();
    expect(await screen.findByText("The capability panel could not be loaded. Your previous choices are unchanged.")).toBeTruthy();
    vi.mocked(fetchCapabilities).mockResolvedValueOnce(sampleInventory());
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Images" })).toBeTruthy();
    // A fully-unavailable family shows its "not available" badge plus a plain how-to-enable hint.
    expect(screen.getAllByText("Not available yet").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Download the required model files to enable this.").length).toBeGreaterThan(0);
  });
});
