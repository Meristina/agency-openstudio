import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCapabilities } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import Review from "./Review";
import type { Brief } from "./questionSets";

vi.mock("../../api", () => ({
  fetchCapabilities: vi.fn().mockResolvedValue({ generated_at: "now", families: [] }),
}));

const brief: Brief = {
  intent: "Make a plan",
  deliverableType: "research",
  sector: { id: "general" },
  answers: { intent: "Make a plan", deliverableLanguage: "en", researchAudience: "Board" },
  deliverableLanguage: "en",
  research: true,
  attachment: null,
  options: [],
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.mocked(fetchCapabilities).mockResolvedValue({ generated_at: "now", families: [] });
});

describe("Review", () => {
  it("shows answers, effective defaults, edit, and launch", () => {
    const onEdit = vi.fn();
    const onLaunch = vi.fn();
    render(<I18nProvider><Review brief={brief} onEdit={onEdit} onLaunch={onLaunch} /></I18nProvider>);
    expect(screen.getByText("Make a plan")).toBeTruthy();
    expect(screen.getByText("At least 3 sources")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: "Edit" })[0]);
    expect(onEdit).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(onLaunch).toHaveBeenCalled();
  });

  it("keeps the brief visible when launch fails", () => {
    render(<I18nProvider><Review brief={brief} error="Service unreachable" onEdit={() => {}} onLaunch={() => {}} /></I18nProvider>);
    expect(screen.getByRole("alert").textContent).toBe("Service unreachable");
    expect(screen.getByText("Make a plan")).toBeTruthy();
  });

  it("renders localized question labels, never raw answer ids (FR-007/FR-015)", () => {
    render(<I18nProvider><Review brief={brief} onEdit={() => {}} onLaunch={() => {}} /></I18nProvider>);
    expect(screen.getByText("Who will read it?")).toBeTruthy();
    expect(screen.queryByText("researchAudience")).toBeNull();
  });

  it("read-only mode shows the summary without edit or launch (FR-018)", () => {
    render(<I18nProvider><Review brief={brief} readOnly /></I18nProvider>);
    expect(screen.getByText("Make a plan")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Launch" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Edit" })).toBeNull();
  });

  it("labels available video work as on this machine and free", async () => {
    vi.mocked(fetchCapabilities).mockResolvedValue({
      generated_at: "now",
      families: [{ family: "video", selectable: true, entries: [{ id: "local", label: "Local video", family: "video", cost: "free", availability: "available", reason: null, enablement: null, tier: "LOCAL", note: "", default: true, key_env: null }], selected: "local", selected_stale: false, env_override: null, active: "local" }],
    });
    render(<I18nProvider><Review brief={{ ...brief, deliverableType: "video" }} onEdit={() => {}} onLaunch={() => {}} /></I18nProvider>);
    expect(await screen.findByText("Video rendering: on this machine (free)")).toBeTruthy();
  });

  it("blocks unavailable video work before launch", async () => {
    const onLaunch = vi.fn();
    vi.mocked(fetchCapabilities).mockResolvedValue({
      generated_at: "now",
      families: [{ family: "video", selectable: true, entries: [{ id: "local", label: "Local video", family: "video", cost: "free", availability: "unavailable", reason: "missing model", enablement: "Install a model", tier: "LOCAL", note: "", default: true, key_env: null }], selected: "local", selected_stale: false, env_override: null, active: "local" }],
    });
    render(<I18nProvider><Review brief={{ ...brief, deliverableType: "video" }} onEdit={() => {}} onLaunch={onLaunch} /></I18nProvider>);
    expect(await screen.findByText(/Install a model/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open models" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(onLaunch).not.toHaveBeenCalled();
  });

  it("requires acknowledgement for paid off-machine video", async () => {
    const onLaunch = vi.fn();
    vi.mocked(fetchCapabilities).mockResolvedValue({
      generated_at: "now",
      families: [{ family: "video", selectable: true, entries: [{ id: "cloud", label: "Cloud video", family: "video", cost: "paid", availability: "available", reason: null, enablement: null, tier: "API", note: "", default: false, key_env: "VIDEO_KEY" }], selected: "cloud", selected_stale: false, env_override: null, active: "cloud" }],
    });
    render(<I18nProvider><Review brief={{ ...brief, deliverableType: "video" }} onEdit={() => {}} onLaunch={onLaunch} /></I18nProvider>);
    expect(await screen.findByText("Video rendering: paid and off this machine")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(onLaunch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("checkbox", { name: /I understand/ }));
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(onLaunch).toHaveBeenCalled();
  });
});
