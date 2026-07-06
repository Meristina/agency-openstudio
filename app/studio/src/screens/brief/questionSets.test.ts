import { describe, expect, it } from "vitest";
import { en } from "../../i18n/en";
import { fr } from "../../i18n/fr";
import { questionSets, type PartialBrief, type Question } from "./questionSets";

function allQuestions(): Question[] {
  return Object.values(questionSets).flatMap((set) => set.questions);
}

describe("brief question sets", () => {
  it("defines the three v1 deliverable sets", () => {
    expect(Object.keys(questionSets).sort()).toEqual(["research", "strategy", "video"]);
  });

  it("keeps only intent, deliverable type, and deliverable language required", () => {
    const required = allQuestions()
      .filter((question) => question.defaultValue === undefined && !question.skippable)
      .map((question) => question.id)
      .sort();
    expect([...new Set(required)]).toEqual(["deliverableLanguage", "deliverableType", "intent"]);
  });

  it("uses catalog keys present in EN and FR", () => {
    const keys = allQuestions().flatMap((question) => [
      question.labelKey,
      question.helpKey,
      ...(question.choices ?? []).map((choice) => choice.labelKey),
    ]).filter((key): key is keyof typeof en => Boolean(key));
    for (const key of keys) {
      expect(en[key]).toBeTruthy();
      expect(fr[key]).toBeTruthy();
    }
  });

  it("keeps relevance predicates deterministic", () => {
    const brief: PartialBrief = { deliverableType: "video", answers: { deliverableType: "video" } };
    for (const question of allQuestions().filter((candidate) => candidate.relevant)) {
      expect(question.relevant?.(brief)).toBe(question.relevant?.(structuredClone(brief)));
    }
  });
});
