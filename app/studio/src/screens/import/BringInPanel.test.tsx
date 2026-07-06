import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ingestDoc, uploadVisual } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import BringInPanel from "./BringInPanel";
import { getAssociation } from "./associationStore";

vi.mock("../../api", () => ({
  ingestDoc: vi.fn(),
  uploadVisual: vi.fn(),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

function renderPanel(onAccepted = vi.fn(), activeContext: { client?: string | null; project?: string | null; campaign?: string | null } = {}) {
  render(
    <I18nProvider>
      <BringInPanel activeContext={activeContext} onAccepted={onAccepted} />
    </I18nProvider>,
  );
  return { onAccepted, input: screen.getByLabelText("Bring in material") };
}

describe("BringInPanel", () => {
  it("brings in a document, confirms it, files it under the active client, and signals acceptance", async () => {
    vi.mocked(ingestDoc).mockResolvedValue({ id: "d1", filename: "brief.pdf", title: "Brief", n_chunks: 1, created: 1 });
    const { onAccepted, input } = renderPanel(vi.fn(), { client: "Acme" });

    fireEvent.change(input, { target: { files: [new File(["x"], "brief.pdf", { type: "application/pdf" })] } });

    expect(await screen.findByText("Material added.")).toBeTruthy();
    expect(ingestDoc).toHaveBeenCalledTimes(1);
    expect(uploadVisual).not.toHaveBeenCalled();
    expect(onAccepted).toHaveBeenCalledTimes(1);
    // Default association = the active client context (FR-006).
    expect(getAssociation("d1")).toEqual({ client: "Acme" });
  });

  it("captions an image LOCALLY by default — no cloud opt-in, no off-machine flag (FR-010)", async () => {
    vi.mocked(uploadVisual).mockResolvedValue({ id: "v1", filename: "mood.png", title: "Mood", n_chunks: 1, created: 1 });
    const { input } = renderPanel();

    fireEvent.change(input, { target: { files: [new File(["x"], "mood.png", { type: "image/png" })] } });

    await screen.findByText("Material added.");
    expect(uploadVisual).toHaveBeenCalledWith(expect.any(File), { cloud: false });
  });

  it("sends the image off-machine only after the explicit per-item cloud opt-in (FR-010)", async () => {
    vi.mocked(uploadVisual).mockResolvedValue({ id: "v2", filename: "mood.png", title: "Mood", n_chunks: 1, created: 1 });
    const { input } = renderPanel();

    fireEvent.click(screen.getByRole("checkbox"));
    expect(screen.getByText("This sends the image outside this machine.")).toBeTruthy();
    fireEvent.change(input, { target: { files: [new File(["x"], "mood.png", { type: "image/png" })] } });

    await screen.findByText("Material added.");
    expect(uploadVisual).toHaveBeenCalledWith(expect.any(File), { cloud: true });
  });

  it("rejects an unsupported kind with a plain reason and no network call (FR-012)", async () => {
    const { onAccepted, input } = renderPanel();

    fireEvent.change(input, { target: { files: [new File(["x"], "clip.mp4", { type: "video/mp4" })] } });

    expect((await screen.findByRole("alert")).textContent).toContain("documents and images only");
    expect(ingestDoc).not.toHaveBeenCalled();
    expect(uploadVisual).not.toHaveBeenCalled();
    expect(onAccepted).not.toHaveBeenCalled();
  });

  it("surfaces a 501 as the localized capability-absent state (FR-011)", async () => {
    vi.mocked(ingestDoc).mockRejectedValue(new Error("POST /api/docs → 501 install the [studio] extra"));
    const { onAccepted, input } = renderPanel();

    fireEvent.change(input, { target: { files: [new File(["x"], "brief.pdf", { type: "application/pdf" })] } });

    await waitFor(() => expect(screen.getByText(/Not available here\./)).toBeTruthy());
    expect(screen.getByText(/Open Models to enable it\./)).toBeTruthy();
    expect(onAccepted).not.toHaveBeenCalled();
  });
});
