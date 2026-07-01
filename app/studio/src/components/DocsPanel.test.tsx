import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DocMeta } from "../types";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// Mock the api boundary so the panel mounts without any network.
const listDocs = vi.fn();
const ingestDoc = vi.fn();
const deleteDoc = vi.fn();
vi.mock("../api", () => ({
  listDocs: (...a: unknown[]) => listDocs(...a),
  ingestDoc: (...a: unknown[]) => ingestDoc(...a),
  deleteDoc: (...a: unknown[]) => deleteDoc(...a),
}));

import DocsPanel from "./DocsPanel";

const DOCS: DocMeta[] = [
  { id: "d1", filename: "report.pdf", title: "Annual Report", n_chunks: 12, created: 100 },
];

describe("DocsPanel", () => {
  it("lists ingested documents on mount", async () => {
    listDocs.mockResolvedValue(DOCS);
    render(<DocsPanel />);
    expect(await screen.findByText("Annual Report")).toBeTruthy();
    expect(screen.getByText("report.pdf")).toBeTruthy();
    expect(screen.getByText("12 chunks")).toBeTruthy();
  });

  it("shows an empty state when there are no documents", async () => {
    listDocs.mockResolvedValue([]);
    render(<DocsPanel />);
    expect(await screen.findByText("No documents ingested yet.")).toBeTruthy();
  });

  it("uploads a selected file then refreshes the list", async () => {
    listDocs.mockResolvedValueOnce([]).mockResolvedValueOnce(DOCS);
    ingestDoc.mockResolvedValue(DOCS[0]);
    render(<DocsPanel />);
    await screen.findByText("No documents ingested yet.");

    const input = screen.getByLabelText("Upload documents") as HTMLInputElement;
    const file = new File(["bytes"], "report.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(ingestDoc).toHaveBeenCalledTimes(1));
    expect((ingestDoc.mock.calls[0][0] as File).name).toBe("report.pdf");
    expect(await screen.findByText("Annual Report")).toBeTruthy();
  });

  it("deletes a document when its Delete button is clicked", async () => {
    listDocs.mockResolvedValueOnce(DOCS).mockResolvedValueOnce([]);
    deleteDoc.mockResolvedValue(undefined);
    render(<DocsPanel />);
    const del = await screen.findByLabelText("Delete report.pdf");
    fireEvent.click(del);
    await waitFor(() => expect(deleteDoc).toHaveBeenCalledWith("d1"));
    expect(await screen.findByText("No documents ingested yet.")).toBeTruthy();
  });

  it("surfaces an ingest error (e.g. the 501 install hint)", async () => {
    listDocs.mockResolvedValue([]);
    ingestDoc.mockRejectedValue(new Error("POST /api/docs → 501: install the local-docs extra"));
    render(<DocsPanel />);
    await screen.findByText("No documents ingested yet.");
    const input = screen.getByLabelText("Upload documents") as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["x"], "a.pdf")] } });
    expect(await screen.findByText(/install the local-docs extra/)).toBeTruthy();
  });
});
