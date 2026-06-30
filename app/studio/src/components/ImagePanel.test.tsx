import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ImageModelInfo } from "../types";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// Mock the api boundary so the panel mounts without any network.
const generateImage = vi.fn();
vi.mock("../api", () => ({
  generateImage: (...args: unknown[]) => generateImage(...args),
}));

import ImagePanel from "./ImagePanel";

const MODELS: ImageModelInfo[] = [
  { id: "flux-schnell", label: "FLUX.1-schnell", note: "Photoreal · 2–4 step", default: true },
  { id: "z-image-turbo", label: "Z-Image-Turbo", note: "Fast · great text · 8-step" },
  { id: "flux2-klein-4b", label: "FLUX.2 Klein 4B", note: "Modern · Apache-2.0" },
];

describe("ImagePanel model selector", () => {
  it("renders an accessible select with one option per image model, defaulting to default:true", () => {
    render(<ImagePanel imageModels={MODELS} onGenerated={vi.fn()} />);
    const select = screen.getByLabelText("Image model") as HTMLSelectElement;
    const labels = Array.from(select.options).map((o) => o.textContent);
    expect(labels).toEqual(["FLUX.1-schnell", "Z-Image-Turbo", "FLUX.2 Klein 4B"]);
    expect(select.value).toBe("flux-schnell");
  });

  it("passes the chosen model id to generateImage", async () => {
    generateImage.mockResolvedValue({
      url: "/media/images/a.png",
      prompt: "a cat",
      seed: 1,
      seconds: 0.9,
      model: "z-image-turbo",
    });
    const onGenerated = vi.fn();
    render(<ImagePanel imageModels={MODELS} onGenerated={onGenerated} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the image/i), {
      target: { value: "a cat" },
    });
    fireEvent.change(screen.getByLabelText("Image model"), { target: { value: "z-image-turbo" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => expect(generateImage).toHaveBeenCalledWith("a cat", { model: "z-image-turbo" }));
    await waitFor(() => expect(onGenerated).toHaveBeenCalled());
  });

  it("disables the select while a generation is in flight", async () => {
    let resolve!: (v: unknown) => void;
    generateImage.mockReturnValue(new Promise((r) => (resolve = r)));
    render(<ImagePanel imageModels={MODELS} onGenerated={vi.fn()} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the image/i), {
      target: { value: "a cat" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    const select = screen.getByLabelText("Image model") as HTMLSelectElement;
    await waitFor(() => expect(select.disabled).toBe(true));
    resolve({ url: "/media/images/a.png", prompt: "a cat", seed: 1, seconds: 0.1, model: "flux-schnell" });
    await waitFor(() => expect(select.disabled).toBe(false));
  });
});
