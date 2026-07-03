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
  { id: "flux2-klein-4b", label: "FLUX.2 Klein 4B", note: "Modern · Apache-2.0" },
  { id: "boogu-base", label: "Boogu-Image 0.1 (experimental)", note: "Highest quality · slow · experimental" },
];

describe("ImagePanel model selector", () => {
  it("renders an accessible select with one option per image model, defaulting to default:true", () => {
    render(<ImagePanel imageModels={MODELS} onGenerated={vi.fn()} />);
    const select = screen.getByLabelText("Image model") as HTMLSelectElement;
    const labels = Array.from(select.options).map((o) => o.textContent);
    expect(labels).toEqual(["FLUX.1-schnell", "FLUX.2 Klein 4B", "Boogu-Image 0.1 (experimental)"]);
    expect(select.value).toBe("flux-schnell");
  });

  it("passes the chosen model id to generateImage", async () => {
    generateImage.mockResolvedValue({
      url: "/media/images/a.png",
      prompt: "a cat",
      seed: 1,
      seconds: 0.9,
      model: "flux2-klein-4b",
    });
    const onGenerated = vi.fn();
    render(<ImagePanel imageModels={MODELS} onGenerated={onGenerated} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the image/i), {
      target: { value: "a cat" },
    });
    fireEvent.change(screen.getByLabelText("Image model"), { target: { value: "flux2-klein-4b" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    // Model is threaded through; resolution defaults to the server's own 1024² (so a
    // default generation stays behaviourally identical), and steps stay "auto" (omitted).
    await waitFor(() =>
      expect(generateImage).toHaveBeenCalledWith("a cat", {
        model: "flux2-klein-4b",
        width: 1024,
        height: 1024,
      }),
    );
    await waitFor(() => expect(onGenerated).toHaveBeenCalled());
  });

  it("defaults resolution to 1024² and steps to Auto", () => {
    render(<ImagePanel imageModels={MODELS} onGenerated={vi.fn()} />);
    expect((screen.getByLabelText("Resolution") as HTMLSelectElement).value).toBe("1024");
    expect((screen.getByLabelText("Steps") as HTMLSelectElement).value).toBe("auto");
  });

  it("passes the chosen resolution and step count to generateImage", async () => {
    generateImage.mockResolvedValue({
      url: "/media/images/b.png",
      prompt: "a dog",
      seed: 2,
      seconds: 1.1,
      model: "flux-schnell",
    });
    render(<ImagePanel imageModels={MODELS} onGenerated={vi.fn()} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the image/i), {
      target: { value: "a dog" },
    });
    fireEvent.change(screen.getByLabelText("Resolution"), { target: { value: "512" } });
    fireEvent.change(screen.getByLabelText("Steps"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() =>
      expect(generateImage).toHaveBeenCalledWith("a dog", {
        model: "flux-schnell",
        width: 512,
        height: 512,
        steps: 2,
      }),
    );
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
