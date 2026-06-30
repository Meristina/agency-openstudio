import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import MissionDetail from "./MissionDetail";
import type { Dossier } from "../types";

afterEach(cleanup);

describe("<MissionDetail>", () => {
  it("prompts when no dossier is selected", () => {
    const { container } = render(<MissionDetail dossier={null} />);
    expect(container.textContent).toContain("Select a mission");
  });

  it("renders http(s) sources as safe new-tab links", () => {
    const dossier: Dossier = {
      mission_id: "m1",
      goal: "demo",
      delivered: "body",
      sources: ["https://example.com/a", "http://example.org/b"],
    };
    const { container } = render(<MissionDetail dossier={dossier} />);
    const links = container.querySelectorAll<HTMLAnchorElement>("a.source-link");
    expect(links).toHaveLength(2);
    expect(links[0].getAttribute("href")).toBe("https://example.com/a");
    expect(links[0].getAttribute("target")).toBe("_blank");
    // No opener access, no referrer leak (studio security ethos).
    expect(links[0].getAttribute("rel")).toContain("noopener");
    expect(links[0].getAttribute("rel")).toContain("noreferrer");
  });

  it("leaves a non-URL source as plain text (no link)", () => {
    const dossier: Dossier = {
      mission_id: "m2",
      delivered: "body",
      sources: ["internal note, no url"],
    };
    const { container } = render(<MissionDetail dossier={dossier} />);
    expect(container.querySelector("a.source-link")).toBeNull();
    expect(container.textContent).toContain("internal note, no url");
  });

  it("renders the persisted asset manifest as a per-mission gallery", () => {
    const dossier: Dossier = {
      mission_id: "m3",
      goal: "demo",
      delivered: "body",
      assets: [
        { type: "image", status: "ok", url: "/media/missions/m3/images/a.png", model: "flux-schnell", prompt: "hero" },
        { type: "image", status: "failed", reason: "Metal OOM" },
      ],
    };
    const { container } = render(<MissionDetail dossier={dossier} />);
    expect(container.textContent).toContain("Generated assets");
    expect(container.querySelector("img")?.getAttribute("src")).toBe("/media/missions/m3/images/a.png");
    expect(container.textContent).toContain("failed — Metal OOM");
  });

  it("omits the asset section entirely for a non-asset mission", () => {
    const dossier: Dossier = { mission_id: "m4", goal: "demo", delivered: "body" };
    const { container } = render(<MissionDetail dossier={dossier} />);
    expect(container.textContent).not.toContain("Generated assets");
  });
});
