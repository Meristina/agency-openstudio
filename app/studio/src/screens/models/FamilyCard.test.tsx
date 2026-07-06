import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { clearCapability, selectCapability } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { toCapabilityViews } from "./capabilityModel";
import FamilyCard from "./FamilyCard";
import { sampleInventory } from "./testData";

vi.mock("../../api", () => ({
  fetchCapabilities: vi.fn(async () => sampleInventory()),
  selectCapability: vi.fn(async () => sampleInventory().families[0]),
  clearCapability: vi.fn(async () => undefined),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderFamily(index = 0, onInventory = vi.fn()) {
  const view = toCapabilityViews(sampleInventory())[index];
  render(<I18nProvider><FamilyCard family={view} onInventory={onInventory} /></I18nProvider>);
  return { view, onInventory };
}

describe("FamilyCard", () => {
  it("shows read-only families without a chooser and keeps key hints name-only", () => {
    renderFamily(7);
    expect(screen.getByRole("heading", { name: "Production tools" })).toBeTruthy();
    expect(screen.queryByRole("radio")).toBeNull();
    cleanup();
    renderFamily(0);
    expect(screen.getByText("Cloud Image")).toBeTruthy();
    expect(screen.getByText("Set AGENCY_IMAGE_KEY in the environment to enable this.")).toBeTruthy();
    expect(screen.queryAllByRole("textbox", { name: /key|secret/i })).toHaveLength(0);
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("chooses an available model and confirms it applies next production", async () => {
    renderFamily(1);
    fireEvent.click(screen.getByLabelText(/Studio Video/));
    await waitFor(() => expect(selectCapability).toHaveBeenCalledWith("video", "video-studio"));
    expect(await screen.findByText("Saved. This applies on your next production.")).toBeTruthy();
    // An unavailable option is not offered as a selectable radio.
    expect(screen.queryByRole("radio", { name: /Cloud Video/ })).toBeNull();
  });

  it("reverts to the built-in default only when a selection is set", async () => {
    // Default (no selection) → revert is disabled (no useless clear call).
    renderFamily(1);
    expect((screen.getByRole("button", { name: /Built-in default/ }) as HTMLButtonElement).disabled).toBe(true);
    cleanup();
    // A stored selection → revert is enabled and clears it.
    const inv = sampleInventory();
    inv.families[1] = { ...inv.families[1], selected: "video-studio" };
    const view = toCapabilityViews(inv)[1];
    render(<I18nProvider><FamilyCard family={view} onInventory={vi.fn()} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: /Built-in default/ }));
    await waitFor(() => expect(clearCapability).toHaveBeenCalledWith("video"));
  });

  it("reports env-override and stale states honestly, naming the model in force", async () => {
    renderFamily(2);
    expect(screen.getByText("The environment variable AGENCY_VISUAL_MODEL is deciding this capability right now (Local Vision is in force).")).toBeTruthy();
    expect(screen.getByText("The previous choice is unavailable; Local Vision is in force.")).toBeTruthy();
    // Choosing under an override must NOT claim it applies next production — the env var still wins.
    fireEvent.click(screen.getByLabelText(/Local Vision/));
    expect(await screen.findByText("Saved, but AGENCY_VISUAL_MODEL keeps deciding this until it is unset.")).toBeTruthy();
    expect(screen.queryByText("Saved. This applies on your next production.")).toBeNull();
  });

  it("keeps prior state visible on save failure", async () => {
    vi.mocked(selectCapability).mockRejectedValueOnce(new Error("nope"));
    renderFamily(1);
    fireEvent.click(screen.getByLabelText(/Studio Video/));
    expect(await screen.findByText("The capability panel could not be loaded. Your previous choices are unchanged.")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Built-in default/ })).toBeTruthy();
  });
});
