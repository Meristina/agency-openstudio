import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// Mock the api boundary so the panel mounts without any network.
const generateVideo = vi.fn();
vi.mock("../api", () => ({
  generateVideo: (...args: unknown[]) => generateVideo(...args),
}));

import VideoPanel from "./VideoPanel";

describe("VideoPanel", () => {
  it("generates from a prompt and emits a video gallery item", async () => {
    generateVideo.mockResolvedValue({ url: "/media/videos/clip.mp4", prompt: "a teaser", seconds: 2, model: "remotion" });
    const onGenerated = vi.fn();
    render(<VideoPanel onGenerated={onGenerated} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the short clip/i), { target: { value: "a teaser" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => expect(generateVideo).toHaveBeenCalledWith("a teaser"));
    await waitFor(() =>
      expect(onGenerated).toHaveBeenCalledWith({ kind: "video", url: "/media/videos/clip.mp4", label: "a teaser", seconds: 2 }),
    );
  });

  it("shows an error and does not emit when generation fails", async () => {
    generateVideo.mockRejectedValue(new Error("remotion-composer dependencies are not installed"));
    const onGenerated = vi.fn();
    render(<VideoPanel onGenerated={onGenerated} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the short clip/i), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => expect(screen.getByText(/remotion-composer/)).toBeTruthy());
    expect(onGenerated).not.toHaveBeenCalled();
  });

  it("disables the button (and shows Rendering…) while a render is in flight", async () => {
    let resolve!: (v: unknown) => void;
    generateVideo.mockReturnValue(new Promise((r) => (resolve = r)));
    render(<VideoPanel onGenerated={vi.fn()} />);

    fireEvent.change(screen.getByPlaceholderText(/describe the short clip/i), { target: { value: "a teaser" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    const button = await screen.findByRole("button", { name: "Rendering…" });
    expect((button as HTMLButtonElement).disabled).toBe(true);
    resolve({ url: "/media/videos/clip.mp4", prompt: "a teaser", seconds: 1, model: "remotion" });
    await waitFor(() => expect(screen.getByRole("button", { name: "Generate" })).toBeTruthy());
  });

  it("keeps Generate disabled until there is a prompt", () => {
    render(<VideoPanel onGenerated={vi.fn()} />);
    expect((screen.getByRole("button", { name: "Generate" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
