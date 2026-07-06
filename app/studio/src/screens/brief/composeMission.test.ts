import { describe, expect, it } from "vitest";
import { composeMission } from "./composeMission";
import type { Brief } from "./questionSets";

const brief: Brief = {
  intent: "Launch in Casablanca",
  deliverableType: "video",
  sector: { id: "events" },
  answers: {
    intent: "Launch in Casablanca",
    deliverableType: "video",
    sector: "events",
    videoAudience: "Sponsors",
    constraints: "",
    deliverableLanguage: "en",
    research: true,
  },
  deliverableLanguage: "en",
  research: true,
  attachment: { client: "Acme", project: "Expo", campaign: null },
  options: [],
};

describe("composeMission", () => {
  it("keeps answers verbatim in deterministic labeled sections", () => {
    expect(composeMission(brief).goal).toMatchInlineSnapshot(`
      "Intent: Launch in Casablanca
      Deliverable: video
      Deliverable language: Write the deliverable in en.
      What field is this for?: events
      Who should watch it?: Sponsors"
    `);
  });

  it("sets only the brief-owned request fields", () => {
    expect(composeMission(brief).opts).toEqual({
      webSearch: true,
      video: true,
      assets: true,
      client: "Acme",
      project: "Expo",
    });
  });

  it("defaults research/strategy to no assets or paid off-machine work", () => {
    expect(composeMission({ ...brief, deliverableType: "research", research: true, attachment: null }).opts).toEqual({
      webSearch: true,
      video: false,
      assets: false,
    });
  });

  it("rejects invalid attachment names before launch", () => {
    expect(() => composeMission({ ...brief, attachment: { client: "<bad>" } })).toThrow(/Invalid client/);
  });
});
