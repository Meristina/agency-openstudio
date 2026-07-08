import { describe, expect, it } from "vitest";
import { contextLabelView, hasResumableDraft, isLiveRun, recentMissionsView } from "./homeModel";
import type { MissionSummary } from "../../types";

const missions: MissionSummary[] = [
  { mission_id: "m1", goal: " Live campaign ", delivered: false, verdict: "in-progress" },
  { mission_id: "m2", goal: "Sponsor deck", delivered: true, verdict: "PASS" },
  { mission_id: "m3", goal: "Broken video", delivered: false, verdict: "VETO" },
  { mission_id: "m4", goal: "Extra 1" },
  { mission_id: "m5", goal: "Extra 2" },
  { mission_id: "m6", goal: "Extra 3" },
];

describe("homeModel", () => {
  it("maps recent missions without exposing machine tokens", () => {
    const view = recentMissionsView(missions, { runId: "m1", status: "running", updatedAt: 1 });
    expect(view).toHaveLength(5);
    expect(view.map((item) => item.label)).toEqual(["Live campaign", "Sponsor deck", "Broken video", "Extra 1", "Extra 2"]);
    expect(view.map((item) => item.statusKey)).toEqual(["home.recent.inProgress", "home.recent.delivered", "home.recent.failedVerdict", "home.recent.inProgress", "home.recent.inProgress"]);
    expect(view.map((item) => item.target)).toEqual(["#/missions", "#/library?deliverable=m2", "#/library?deliverable=m3", "#/library?deliverable=m4", "#/library?deliverable=m5"]);
    // The live-followed run (m1) is not deletable; the saved missions are (FR-008).
    expect(view.map((item) => item.deletable)).toEqual([false, true, true, true, true]);
    expect(view.some((item) => item.label === "m1" || item.label === "VETO")).toBe(false);
  });

  it("flags an empty/whitespace goal for localized fallback instead of raw English", () => {
    const view = recentMissionsView(
      [
        { mission_id: "m0", goal: "   ", delivered: false },
        { mission_id: "m1", goal: "Real goal", delivered: false },
      ],
      null,
    );
    expect(view[0]).toMatchObject({ label: "", untitled: true });
    expect(view[1]).toMatchObject({ label: "Real goal", untitled: false });
  });

  it("detects resumable drafts and live runs", () => {
    expect(hasResumableDraft(null)).toBe(false);
    expect(hasResumableDraft({ version: 1, stepIndex: 0, answers: {} })).toBe(false);
    expect(hasResumableDraft({ version: 1, stepIndex: 1, answers: { intent: "Launch" } })).toBe(true);
    expect(isLiveRun({ mission_id: "m1" }, { runId: "r1", missionId: "m1", status: "running", updatedAt: 1 })).toBe(true);
    expect(isLiveRun({ mission_id: "m1" }, { runId: "m1", status: "done", updatedAt: 1 })).toBe(false);
  });

  it("composes context labels", () => {
    expect(contextLabelView({ client: "Acme", project: "Rebrand", campaign: "Launch" }).text).toBe("Acme / Rebrand / Launch");
    expect(contextLabelView({ client: null, project: null, campaign: null }).text).toBeNull();
  });
});
