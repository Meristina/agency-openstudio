import { en } from "../../i18n/en";
import type { Brief, Question } from "./questionSets";
import { questionSets } from "./questionSets";

export type MissionDraft = {
  goal: string;
  opts: {
    webSearch: boolean;
    video: boolean;
    assets: boolean;
    client?: string;
    project?: string;
    campaign?: string;
  };
};

export function cleanAttachmentName(name: string): string {
  const clean = name.trim();
  if (!clean || clean.length > 80 || /[<>]/.test(clean)) throw new Error("Invalid client name");
  return clean;
}

function answerText(value: unknown): string {
  if (typeof value === "string") return value.trim();
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (value && typeof value === "object" && "other" in value) return String(value.other).trim();
  if (value && typeof value === "object" && "id" in value) return String(value.id).trim();
  return "";
}

export function composeMission(brief: Brief): MissionDraft {
  const set = questionSets[brief.deliverableType];
  const lines = [
    `Intent: ${brief.intent}`,
    `Deliverable: ${brief.deliverableType}`,
    `Deliverable language: Write the deliverable in ${brief.deliverableLanguage}.`,
  ];
  const byId = new Map<string, Question>(set.questions.map((question) => [question.id, question]));
  for (const [id, value] of Object.entries(brief.answers)) {
    if (["intent", "deliverableType", "deliverableLanguage", "research"].includes(id)) continue;
    const text = answerText(value);
    const question = byId.get(id);
    if (text && question) lines.push(`${en[question.labelKey]}: ${text}`);
  }
  return {
    goal: lines.join("\n"),
    opts: {
      webSearch: brief.research,
      video: brief.deliverableType === "video",
      assets: brief.deliverableType === "video",
      ...(brief.attachment?.client ? { client: cleanAttachmentName(brief.attachment.client) } : {}),
      ...(brief.attachment?.project ? { project: cleanAttachmentName(brief.attachment.project) } : {}),
      ...(brief.attachment?.campaign ? { campaign: cleanAttachmentName(brief.attachment.campaign) } : {}),
    },
  };
}
