import type { Answer } from "./questionSets";

export const BRIEF_DRAFT_KEY = "studio.briefDraft.v1";

export type BriefDraft = {
  version: 1;
  answers: Record<string, Answer>;
  stepIndex: number;
  useImportedMaterial?: boolean;
};

export function loadBriefDraft(storage: Storage = localStorage): BriefDraft | null {
  try {
    const parsed = JSON.parse(storage.getItem(BRIEF_DRAFT_KEY) || "null") as BriefDraft | null;
    return parsed?.version === 1 && parsed.answers && Number.isInteger(parsed.stepIndex) ? parsed : null;
  } catch {
    return null;
  }
}

export function saveBriefDraft(answers: Record<string, Answer>, stepIndex: number, storage: Storage = localStorage, useImportedMaterial = false): void {
  storage.setItem(BRIEF_DRAFT_KEY, JSON.stringify({ version: 1, answers, stepIndex, ...(useImportedMaterial ? { useImportedMaterial } : {}) } satisfies BriefDraft));
}

export function discardBriefDraft(storage: Storage = localStorage): void {
  storage.removeItem(BRIEF_DRAFT_KEY);
}
