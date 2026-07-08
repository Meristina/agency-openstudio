export const FOLLOW_POINTER_KEY = "agency.studio.followPointer.v1";

export interface FollowPointer {
  runId: string;
  status: "running" | "done" | "cancelled" | "error";
  missionId?: string | null;
  resumable?: boolean;
  checkpoint?: string | null;
  // Which endpoint owns this run's checkpoint, persisted so a resume survives a full page reload —
  // the in-memory session kind resets to "mission" on reload, which would 404 a recipe checkpoint.
  resumeKind?: "mission" | "recipe";
  updatedAt: number;
}

function valid(value: unknown): value is FollowPointer {
  if (!value || typeof value !== "object") return false;
  const pointer = value as Partial<FollowPointer>;
  return typeof pointer.runId === "string" && ["running", "done", "cancelled", "error"].includes(String(pointer.status));
}

export function record(pointer: Omit<FollowPointer, "updatedAt">): FollowPointer {
  const next = { ...pointer, updatedAt: Date.now() };
  try {
    localStorage.setItem(FOLLOW_POINTER_KEY, JSON.stringify(next));
  } catch {
    // storage unavailable/full (quota, Safari private mode) — persistence is
    // best-effort, matching read()'s tolerance; never break the mission flow.
  }
  return next;
}

export function read(): FollowPointer | null {
  try {
    const parsed = JSON.parse(localStorage.getItem(FOLLOW_POINTER_KEY) || "null") as unknown;
    return valid(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function clear(): void {
  localStorage.removeItem(FOLLOW_POINTER_KEY);
}
