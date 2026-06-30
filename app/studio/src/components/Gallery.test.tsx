import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Gallery from "./Gallery";
import type { GalleryItem } from "../types";

describe("Gallery", () => {
  it("shows an empty-state message with no items", () => {
    render(<Gallery items={[]} />);
    expect(screen.getByText(/nothing generated yet/i)).toBeTruthy();
  });

  it("renders an image item as an <img> with the prompt as alt text", () => {
    const items: GalleryItem[] = [
      { kind: "image", url: "/media/images/a.png", label: "a cat", seconds: 1.2 },
    ];
    render(<Gallery items={items} />);
    const img = screen.getByAltText("a cat") as HTMLImageElement;
    expect(img.getAttribute("src")).toBe("/media/images/a.png");
  });

  it("renders an audio item with an <audio> element", () => {
    const items: GalleryItem[] = [
      { kind: "audio", url: "/media/audio/a.wav", label: "hello", seconds: 0.4 },
    ];
    const { container } = render(<Gallery items={items} />);
    const audio = container.querySelector("audio");
    expect(audio?.getAttribute("src")).toBe("/media/audio/a.wav");
  });
});
