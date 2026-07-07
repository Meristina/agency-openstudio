import type { CatalogKey } from "../../i18n/catalog";
import type { MissionSummary } from "../../types";
import type { BriefDraft } from "../brief/briefDraft";
import type { FollowPointer } from "../missions/followPointer";

export interface RecentMissionItem {
  key: string;
  label: string;
  statusKey: CatalogKey;
  target: string;
}

export interface ContextParts {
  client?: string | null;
  project?: string | null;
  campaign?: string | null;
}

const TERMINAL_FAIL = new Set(["FAIL", "FAILED", "VETO", "NEEDS_WORK", "NEEDS-ATTENTION", "NEEDS_ATTENTION"]);

function humanGoal(goal: unknown): string {
  const text = typeof goal === "string" ? goal.trim().replace(/\s+/g, " ") : "";
  if (!text) return "Recent production";
  return text.length > 80 ? `${text.slice(0, 77).trim()}...` : text;
}

export function isLiveRun(mission: MissionSummary, pointer: FollowPointer | null): boolean {
  if (!pointer || pointer.status !== "running") return false;
  return pointer.runId === mission.mission_id || pointer.missionId === mission.mission_id;
}

export function recentMissionsView(missions: MissionSummary[], pointer: FollowPointer | null): RecentMissionItem[] {
  return missions.slice(0, 5).map((mission) => {
    const live = isLiveRun(mission, pointer);
    const verdict = String(mission.verdict ?? "").toUpperCase();
    return {
      key: mission.mission_id,
      label: humanGoal(mission.goal),
      statusKey: mission.delivered ? "home.recent.delivered" : TERMINAL_FAIL.has(verdict) ? "home.recent.failedVerdict" : "home.recent.inProgress",
      target: live ? "#/missions" : `#/library?deliverable=${encodeURIComponent(mission.mission_id)}`,
    };
  });
}

function meaningful(value: unknown): boolean {
  if (typeof value === "string") return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (value && typeof value === "object") return Object.keys(value).length > 0;
  return value !== null && value !== undefined;
}

export function hasResumableDraft(draft: BriefDraft | null): boolean {
  return !!draft && Object.values(draft.answers ?? {}).some(meaningful);
}

export function contextLabelView(ctx: ContextParts): { text: string | null } {
  const text = [ctx.client, ctx.project, ctx.campaign].map((part) => part?.trim()).filter(Boolean).join(" / ");
  return { text: text || null };
}
