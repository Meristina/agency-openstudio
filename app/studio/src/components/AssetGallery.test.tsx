import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import AssetGallery from "./AssetGallery";
import type { AssetManifestItem } from "../types";

afterEach(cleanup);

describe("<AssetGallery>", () => {
  it("renders nothing for an absent or empty manifest", () => {
    const { container } = render(<AssetGallery items={undefined} />);
    expect(container.firstChild).toBeNull();
    const { container: c2 } = render(<AssetGallery items={[]} />);
    expect(c2.firstChild).toBeNull();
  });

  it("renders an ok image as an <img> captioned with its prompt + model meta", () => {
    const items: AssetManifestItem[] = [
      { type: "image", status: "ok", url: "/media/missions/m1/images/a.png", model: "flux-schnell", seconds: 3, prompt: "a bold hero banner" },
    ];
    render(<AssetGallery items={items} />);
    const img = screen.getByAltText("a bold hero banner") as HTMLImageElement;
    expect(img.getAttribute("src")).toBe("/media/missions/m1/images/a.png");
    expect(screen.getByText(/flux-schnell · 3s/)).toBeTruthy();
  });

  it("renders an ok tts entry as an <audio> player", () => {
    const items: AssetManifestItem[] = [
      { type: "tts", status: "ok", url: "/media/missions/m1/audio/a.wav", voice: "af_heart", seconds: 4, text: "welcome" },
    ];
    const { container } = render(<AssetGallery items={items} />);
    expect(container.querySelector("audio")?.getAttribute("src")).toBe("/media/missions/m1/audio/a.wav");
  });

  it("surfaces failed/skipped renders as residual rows with their reason", () => {
    const items: AssetManifestItem[] = [
      { type: "image", status: "failed", reason: "Metal OOM" },
      { type: "tts", status: "skipped", reason: "cancelled" },
    ];
    const { container } = render(<AssetGallery items={items} />);
    // No media elements for non-ok entries — they never reached a served url.
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("audio")).toBeNull();
    expect(container.textContent).toContain("failed — Metal OOM");
    expect(container.textContent).toContain("skipped — cancelled");
  });
});
