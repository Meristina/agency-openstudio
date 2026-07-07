import { PREFS_KEY } from "../../i18n/catalog";
import type { CatalogKey } from "../../i18n/catalog";
import { BRIEF_DRAFT_KEY } from "../brief/briefDraft";
import { ASSOCIATION_KEY } from "../import/associationStore";
import { FOLLOW_POINTER_KEY } from "../missions/followPointer";
import { familyNameKey } from "../models/capabilityModel";
import type { CapabilityInventory, SystemInfo } from "../../types";

export type ConnectionState = "connected" | "offline" | "unknown";

export interface ModelSummaryItem {
  familyKey: CatalogKey;
  choiceLabel: string;
}

export interface SystemStatusView {
  connection: ConnectionState;
  version: string | null;
  dataLocation: string | null;
  modelSummary: ModelSummaryItem[];
}

// Explicit allowlist (not a prefix sweep): the studio's preference keys use
// inconsistent prefixes, and a broad wildcard clear could wipe unrelated same-origin
// data. Any new user-preference key must be added here so Reset covers it.
export const PREFERENCE_KEYS = [PREFS_KEY, ASSOCIATION_KEY, BRIEF_DRAFT_KEY, FOLLOW_POINTER_KEY] as const;

export function clearLocalPreferences(storage: Pick<Storage, "removeItem"> | null | undefined): void {
  if (!storage) return;
  try {
    for (const key of PREFERENCE_KEYS) storage.removeItem(key);
  } catch {
    // localStorage can be blocked (private mode); a no-op keeps reset safe.
  }
}

export function deriveModelSummary(capabilities: CapabilityInventory | null): ModelSummaryItem[] {
  return (capabilities?.families ?? [])
    .filter((family) => family.selectable)
    .map((family) => {
      // Prefer the chosen model's label; if the selection is stale (not in entries),
      // fall back to the resolved active model's label — never a raw id for the user.
      const chosenId = family.selected ?? family.active;
      const entry = family.entries.find((item) => item.id === chosenId)
        ?? family.entries.find((item) => item.id === family.active);
      return {
        familyKey: familyNameKey(family.family),
        choiceLabel: entry?.label ?? family.active,
      };
    });
}

export function deriveSystemView(
  info: SystemInfo | null,
  capabilities: CapabilityInventory | null,
  reachable: boolean | null,
): SystemStatusView {
  return {
    connection: reachable == null ? "unknown" : reachable ? "connected" : "offline",
    version: info?.version ?? null,
    dataLocation: info?.dataDir ?? null,
    modelSummary: deriveModelSummary(capabilities),
  };
}
