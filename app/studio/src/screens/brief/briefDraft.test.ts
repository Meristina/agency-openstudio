import { afterEach, describe, expect, it } from "vitest";
import { BRIEF_DRAFT_KEY, discardBriefDraft, loadBriefDraft, saveBriefDraft } from "./briefDraft";

afterEach(() => localStorage.clear());

describe("briefDraft", () => {
  it("saves and loads one versioned draft", () => {
    saveBriefDraft({ intent: "Plan", deliverableLanguage: "en" }, 2);
    expect(loadBriefDraft()).toEqual({ version: 1, answers: { intent: "Plan", deliverableLanguage: "en" }, stepIndex: 2 });
  });

  it("returns null for corrupt or wrong-version drafts", () => {
    localStorage.setItem(BRIEF_DRAFT_KEY, "{");
    expect(loadBriefDraft()).toBeNull();
    localStorage.setItem(BRIEF_DRAFT_KEY, JSON.stringify({ version: 2, answers: {}, stepIndex: 0 }));
    expect(loadBriefDraft()).toBeNull();
  });

  it("discard removes the single draft", () => {
    saveBriefDraft({ intent: "Plan" }, 1);
    discardBriefDraft();
    expect(localStorage.getItem(BRIEF_DRAFT_KEY)).toBeNull();
  });

  it("stores answers only, no secret-shaped fields", () => {
    saveBriefDraft({ intent: "Plan" }, 1);
    expect(localStorage.getItem(BRIEF_DRAFT_KEY)).not.toMatch(/key|secret|token|password/i);
  });
});
