import type { CatalogKey } from "../../i18n/catalog";
import type { MissionSummary } from "../../types";
import type { BriefDraft } from "../brief/briefDraft";
import type { FollowPointer } from "../missions/followPointer";

export interface RecentMissionItem {
  key: string;
  /** Plain mission goal; empty when the mission has no goal (see `untitled`). Never a machine token. */
  label: string;
  /** True when `label` is empty and the consumer must render the localized `home.recent.untitled`. */
  untitled: boolean;
  statusKey: CatalogKey;
  target: string;
  /** True for a saved (terminal) mission that can be deleted; false for the live-followed run,
   * which is managed via cancel/resume, not deleted (FR-008). */
  deletable: boolean;
}

export interface ContextParts {
  client?: string | null;
  project?: string | null;
  campaign?: string | null;
}

const TERMINAL_FAIL = new Set(["FAIL", "FAILED", "VETO", "NEEDS_WORK", "NEEDS-ATTENTION", "NEEDS_ATTENTION"]);

function humanGoal(goal: unknown): { text: string; untitled: boolean } {
  const text = typeof goal === "string" ? goal.trim().replace(/\s+/g, " ") : "";
  if (!text) return { text: "", untitled: true };
  return { text: text.length > 80 ? `${text.slice(0, 77).trim()}...` : text, untitled: false };
}

export function isLiveRun(mission: MissionSummary, pointer: FollowPointer | null): boolean {
  if (!pointer || pointer.status !== "running") return false;
  return pointer.runId === mission.mission_id || pointer.missionId === mission.mission_id;
}

export function recentMissionsView(missions: MissionSummary[], pointer: FollowPointer | null): RecentMissionItem[] {
  return missions.slice(0, 5).map((mission) => {
    const live = isLiveRun(mission, pointer);
    const verdict = String(mission.verdict ?? "").toUpperCase();
    const goal = humanGoal(mission.goal);
    return {
      key: mission.mission_id,
      label: goal.text,
      untitled: goal.untitled,
      statusKey: mission.delivered ? "home.recent.delivered" : TERMINAL_FAIL.has(verdict) ? "home.recent.failedVerdict" : "home.recent.inProgress",
      target: live ? "#/missions" : `#/library?deliverable=${encodeURIComponent(mission.mission_id)}`,
      deletable: !live,
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
