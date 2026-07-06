import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { listDocs, listVisual } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import Import from "./Import";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({ clients: [{ name: "Acme", missions: 0, projects: [] }] }),
  listDocs: vi.fn().mockResolvedValue([]),
  listVisual: vi.fn().mockResolvedValue([]),
  ingestDoc: vi.fn(),
  uploadVisual: vi.fn(),
  deleteDoc: vi.fn(),
  deleteVisual: vi.fn(),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
  vi.mocked(listDocs).mockResolvedValue([]);
  vi.mocked(listVisual).mockResolvedValue([]);
});

function renderImport() {
  return render(<I18nProvider><ClientContextProvider><Import /></ClientContextProvider></I18nProvider>);
}

describe("Import", () => {
  it("renders the first-run state and named controls", async () => {
    renderImport();
    expect(await screen.findByRole("heading", { name: "Imported material" })).toBeTruthy();
    expect(screen.getByText("No imported material yet")).toBeTruthy();
    expect(screen.getByLabelText("Bring in material")).toBeTruthy();
  });

  it("renders existing documents and images on shelves", async () => {
    vi.mocked(listDocs).mockResolvedValue([{ id: "d1", filename: "brief.pdf", title: "Brief", n_chunks: 1, created: 1 }]);
    vi.mocked(listVisual).mockResolvedValue([{ id: "v1", filename: "mood.jpg", title: "Mood", n_chunks: 1, created: 2 }]);
    renderImport();
    expect(await screen.findByText("Brief")).toBeTruthy();
    expect(screen.getByText("Mood")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Use these in a production" })).toBeTruthy();
  });

  it("shows a plain load error", async () => {
    vi.mocked(listDocs).mockRejectedValue(new Error("offline"));
    renderImport();
    await waitFor(() => expect(screen.getByRole("heading", { name: "Something went wrong." })).toBeTruthy());
    expect(screen.getByText(/Imported material could not be loaded/)).toBeTruthy();
  });

  it("rejects unsupported files without a network call", async () => {
    renderImport();
    const input = await screen.findByLabelText("Bring in material");
    fireEvent.change(input, { target: { files: [new File(["x"], "clip.mp4", { type: "video/mp4" })] } });
    expect((await screen.findByRole("alert")).textContent).toContain("documents and images only");
  });
});
