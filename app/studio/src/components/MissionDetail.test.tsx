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

  it("exports PDF via a button, not an <a href> navigation", () => {
    // The export must NOT be a plain navigation link: a 501/404 would replace the SPA with raw
    // JSON and, mid-mission, tear down the SSE stream (a server-side cancel). It's a button that
    // fetches a blob instead — so assert there is no anchor pointing at the pdf endpoint.
    const dossier: Dossier = { mission_id: "m5", goal: "demo", delivered: "body" };
    const { container } = render(<MissionDetail dossier={dossier} />);
    const btn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Export PDF"),
    );
    expect(btn).toBeTruthy();
    expect(container.querySelector('a[href*="/pdf"]')).toBeNull();
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

  it("renders source verification details when present", () => {
    const dossier: Dossier = {
      mission_id: "m6",
      goal: "demo",
      delivered: "body",
      verification: {
        min_sources: 3,
        resolve: true,
        cycles: [],
        final: {
          iteration: 1,
          ok: false,
          resolve: true,
          rate: 0.4,
          truncated: 1,
          per_dept: { marketing: { counted: 2, min: 3, ok: false } },
          sources: [{ url: "https://dead.test/a", status: "unresolved", detail: "HTTP 404", depts: ["marketing"] }],
          missing: ["Claim lacks a source"],
        },
      },
    };
    const text = render(<MissionDetail dossier={dossier} />).container.textContent ?? "";
    expect(text).toContain("Source verification");
    expect(text).toContain("40%");
    expect(text).toContain("marketing");
    expect(text).toContain("https://dead.test/a");
    expect(text).toContain("Claim lacks a source");
    expect(text).toContain("1 source not checked");
  });

  it("renders null verification rate as unverified and omits absent verification", () => {
    const offline: Dossier = {
      mission_id: "m7",
      delivered: "body",
      verification: {
        min_sources: 1,
        resolve: false,
        cycles: [],
        final: {
          iteration: 1,
          ok: true,
          resolve: false,
          rate: null,
          truncated: 0,
          per_dept: {},
          sources: [],
          missing: [],
        },
      },
    };
    expect(render(<MissionDetail dossier={offline} />).container.textContent).toContain(
      "unverified — resolution not enabled",
    );
    cleanup();
    // Resolution WAS enabled but the cycle degraded (outage / nothing checkable):
    // the copy must not claim the toggle was off. The two resolve fields deliberately
    // DISAGREE here to pin final.resolve (the cycle that produced the rate) as the
    // driver — a regression reading the mission-level field would fail this case.
    const degraded: Dossier = {
      ...offline,
      verification: {
        ...offline.verification!,
        resolve: false,
        final: { ...offline.verification!.final, resolve: true },
      },
    };
    expect(render(<MissionDetail dossier={degraded} />).container.textContent).toContain(
      "unverified — network unavailable or no checkable sources",
    );
    cleanup();
    expect(render(<MissionDetail dossier={{ delivered: "body" }} />).container.textContent).not.toContain("Source verification");
  });
});
