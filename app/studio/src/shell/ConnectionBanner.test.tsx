import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchTaxonomy } from "../api";
import { I18nProvider } from "../i18n/I18nProvider";
import ConnectionBanner from "./ConnectionBanner";

vi.mock("../api", () => ({ fetchTaxonomy: vi.fn() }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe("ConnectionBanner", () => {
  it("shows only transport failures", async () => {
    vi.mocked(fetchTaxonomy).mockRejectedValueOnce(new TypeError("Failed to fetch"));
    render(<I18nProvider><ConnectionBanner /></I18nProvider>);
    expect((await screen.findByRole("status")).textContent).toContain("unreachable");

    cleanup();
    vi.mocked(fetchTaxonomy).mockRejectedValueOnce(new Error("GET /api/taxonomy -> 500"));
    render(<I18nProvider><ConnectionBanner /></I18nProvider>);
    await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
  });

  it("clears after retry success", async () => {
    vi.mocked(fetchTaxonomy).mockRejectedValueOnce(new TypeError("Failed to fetch")).mockResolvedValue({ clients: [] });
    render(<I18nProvider><ConnectionBanner retryMs={1} /></I18nProvider>);
    expect(await screen.findByRole("status")).toBeTruthy();
    await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
  });
});
