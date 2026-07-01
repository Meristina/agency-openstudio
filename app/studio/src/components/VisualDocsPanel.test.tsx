import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { VisualMeta } from "../types";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// Mock the api boundary so the panel mounts without any network.
const listVisual = vi.fn();
const uploadVisual = vi.fn();
const deleteVisual = vi.fn();
vi.mock("../api", () => ({
  listVisual: (...a: unknown[]) => listVisual(...a),
  uploadVisual: (...a: unknown[]) => uploadVisual(...a),
  deleteVisual: (...a: unknown[]) => deleteVisual(...a),
}));

import VisualDocsPanel from "./VisualDocsPanel";

const IMAGES: VisualMeta[] = [
  { id: "v1", filename: "diagram.png", title: "A network diagram", n_chunks: 1, created: 100 },
];

describe("VisualDocsPanel", () => {
  it("lists ingested images on mount", async () => {
    listVisual.mockResolvedValue(IMAGES);
    render(<VisualDocsPanel />);
    expect(await screen.findByText("A network diagram")).toBeTruthy();
    expect(screen.getByText("diagram.png")).toBeTruthy();
    expect(screen.getByText("1 chunk")).toBeTruthy();
  });

  it("shows an empty state when there are no images", async () => {
    listVisual.mockResolvedValue([]);
    render(<VisualDocsPanel />);
    expect(await screen.findByText("No images ingested yet.")).toBeTruthy();
  });

  it("uploads a selected image locally (no cloud consent) then refreshes", async () => {
    listVisual.mockResolvedValueOnce([]).mockResolvedValueOnce(IMAGES);
    uploadVisual.mockResolvedValue(IMAGES[0]);
    render(<VisualDocsPanel />);
    await screen.findByText("No images ingested yet.");

    const input = screen.getByLabelText("Upload images") as HTMLInputElement;
    const file = new File(["bytes"], "diagram.png", { type: "image/png" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(uploadVisual).toHaveBeenCalledTimes(1));
    expect((uploadVisual.mock.calls[0][0] as File).name).toBe("diagram.png");
    // Default: local captioning — no off-machine consent.
    expect(uploadVisual.mock.calls[0][1]).toEqual({ cloud: false });
    expect(await screen.findByText("A network diagram")).toBeTruthy();
  });

  it("passes cloud:true only after the consent checkbox is ticked", async () => {
    listVisual.mockResolvedValue([]);
    uploadVisual.mockResolvedValue(IMAGES[0]);
    render(<VisualDocsPanel />);
    await screen.findByText("No images ingested yet.");

    fireEvent.click(screen.getByLabelText(/Caption in the cloud/));
    const input = screen.getByLabelText("Upload images") as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["x"], "a.png", { type: "image/png" })] } });

    await waitFor(() => expect(uploadVisual).toHaveBeenCalledTimes(1));
    expect(uploadVisual.mock.calls[0][1]).toEqual({ cloud: true });
  });

  it("deletes an image when its Delete button is clicked", async () => {
    listVisual.mockResolvedValueOnce(IMAGES).mockResolvedValueOnce([]);
    deleteVisual.mockResolvedValue(undefined);
    render(<VisualDocsPanel />);
    const del = await screen.findByLabelText("Delete diagram.png");
    fireEvent.click(del);
    await waitFor(() => expect(deleteVisual).toHaveBeenCalledWith("v1"));
    expect(await screen.findByText("No images ingested yet.")).toBeTruthy();
  });

  it("surfaces an upload error (e.g. the 501 install hint)", async () => {
    listVisual.mockResolvedValue([]);
    uploadVisual.mockRejectedValue(new Error("POST /api/visual → 501: install the visual-RAG extra"));
    render(<VisualDocsPanel />);
    await screen.findByText("No images ingested yet.");
    const input = screen.getByLabelText("Upload images") as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["x"], "a.png")] } });
    expect(await screen.findByText(/install the visual-RAG extra/)).toBeTruthy();
  });
});
