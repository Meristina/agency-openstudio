import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchMissionBundle, fetchMissionMediaZip, fetchMissionPdf } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import ExportPanel from "./ExportPanel";

vi.mock("../../api", () => ({
  fetchMissionPdf: vi.fn(async () => new Blob(["pdf"])),
  fetchMissionMediaZip: vi.fn(async () => new Blob(["zip"])),
  fetchMissionBundle: vi.fn(async () => new Blob(["bundle"])),
}));

vi.mock("./download", async () => {
  const actual = await vi.importActual<typeof import("./download")>("./download");
  return { ...actual, downloadBlob: vi.fn() };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const selected = { id: "m1", title: "Sponsor deck", dossier: { assets: [{ type: "image" as const, status: "ok" as const, url: "/media/a.png" }] } };

describe("ExportPanel", () => {
  it("produces document, media pack, and bundle downloads", async () => {
    render(<I18nProvider><ExportPanel deliverable={selected} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: /Prepare A polished document/ }));
    await waitFor(() => expect(fetchMissionPdf).toHaveBeenCalledWith("m1", expect.any(AbortSignal)));
    fireEvent.click(screen.getByRole("button", { name: /Prepare A media pack/ }));
    await waitFor(() => expect(fetchMissionMediaZip).toHaveBeenCalledWith("m1", expect.any(AbortSignal)));
    fireEvent.click(screen.getByRole("button", { name: /Prepare The whole bundle/ }));
    await waitFor(() => expect(fetchMissionBundle).toHaveBeenCalledWith("m1", expect.any(AbortSignal)));
    expect(screen.getAllByText("Ready to share.").length).toBe(3);
  });

  it("disables media when none is present and marks pdf-gated formats unavailable", async () => {
    render(<I18nProvider><ExportPanel deliverable={{ ...selected, dossier: { assets: [] } }} /></I18nProvider>);
    expect(screen.getByText("No media to pack.")).toBeTruthy();
    expect((screen.getByRole("button", { name: /Prepare A media pack/ }) as HTMLButtonElement).disabled).toBe(true);
    vi.mocked(fetchMissionPdf).mockRejectedValueOnce(new Error("GET /api/mission/pdf → 501: WeasyPrint not installed"));
    fireEvent.click(screen.getByRole("button", { name: /Prepare A polished document/ }));
    // One 501 proves the PDF capability is absent: the document AND the full bundle (both
    // render server-side PDF) become unavailable, so the user isn't sent to retry the bundle.
    await waitFor(() => expect(screen.getAllByText(/Not available on this machine/).length).toBe(2));
  });

  it("tracks busy state per format so concurrent downloads don't clear each other", async () => {
    let resolveDoc: (b: Blob) => void = () => {};
    vi.mocked(fetchMissionPdf).mockReturnValueOnce(new Promise<Blob>((r) => { resolveDoc = r; }));
    render(<I18nProvider><ExportPanel deliverable={selected} /></I18nProvider>);
    const docBtn = screen.getByRole("button", { name: /Prepare A polished document/ });
    const bundleBtn = screen.getByRole("button", { name: /Prepare The whole bundle/ });
    fireEvent.click(docBtn);
    await waitFor(() => expect((docBtn as HTMLButtonElement).disabled).toBe(true));
    // Document still in flight; the bundle download resolves and completes.
    fireEvent.click(bundleBtn);
    await waitFor(() => expect(fetchMissionBundle).toHaveBeenCalled());
    // The document must remain busy/disabled — the bundle finishing must not re-enable it.
    expect((docBtn as HTMLButtonElement).disabled).toBe(true);
    resolveDoc(new Blob(["pdf"]));
    await waitFor(() => expect((docBtn as HTMLButtonElement).disabled).toBe(false));
  });

  it("marks the media pack unavailable (not a retry) when media was pruned since production", async () => {
    render(<I18nProvider><ExportPanel deliverable={selected} /></I18nProvider>);
    vi.mocked(fetchMissionMediaZip).mockRejectedValueOnce(new Error("GET /api/mission/media.zip → 404: no media for mission 'm1'"));
    fireEvent.click(screen.getByRole("button", { name: /Prepare A media pack/ }));
    await waitFor(() => expect((screen.getByRole("button", { name: /Prepare A media pack/ }) as HTMLButtonElement).disabled).toBe(true));
    expect(screen.getByText("No media to pack.")).toBeTruthy();
    expect(screen.queryByText("Couldn't build that file. Try again.")).toBeNull();
  });

  it("shows retry copy for packaging failures and renders contents", async () => {
    vi.mocked(fetchMissionBundle).mockRejectedValueOnce(new Error("500"));
    render(<I18nProvider><ExportPanel deliverable={selected} /></I18nProvider>);
    expect(screen.getByText("PDF for reading or printing.")).toBeTruthy();
    expect(screen.getByText("PDF, media, and a readable sources list.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Prepare The whole bundle/ }));
    await waitFor(() => expect(screen.getByText("Couldn't build that file. Try again.")).toBeTruthy());
  });
});
