import type { CatalogKey } from "../../i18n/catalog";
import type { CapabilityEntry, CapabilityFamilyView, CapabilityInventory, CostClass, Family } from "../../types";

export type DisplayKind = "chooser" | "readonly";
export type CostKind = "free_local" | "paid_cloud" | "free_or_paid";
export type CapabilityStatusKind = "ready_free_local" | "ready_cloud" | "not_available";

export interface ModelOptionView {
  id: string;
  label: string;
  costKind: CostKind;
  available: boolean;
  isDefault: boolean;
  keyConfigured: boolean | null;
  enablementHintKey: CatalogKey | null;
  envVarName: string | null;
}

export interface CapabilityStatus {
  kind: CapabilityStatusKind;
  labelKey: CatalogKey;
  enablementHintKey: CatalogKey | null;
  envVarName: string | null;
}

export interface CapabilityView {
  family: Family;
  nameKey: CatalogKey;
  descriptionKey: CatalogKey;
  displayKind: DisplayKind;
  status: CapabilityStatus;
  options: ModelOptionView[];
  activeOptionId: string;
  selectedId: string | null;
  isEnvOverridden: boolean;
  envVarName: string | null;
  isStale: boolean;
}

const familyKeys: Record<Family, { name: CatalogKey; description: CatalogKey }> = {
  image: { name: "models.family.image", description: "models.familyDesc.image" },
  video: { name: "models.family.video", description: "models.familyDesc.video" },
  visual: { name: "models.family.visual", description: "models.familyDesc.visual" },
  embedding: { name: "models.family.embedding", description: "models.familyDesc.embedding" },
  "kg-extraction": { name: "models.family.kg", description: "models.familyDesc.kg" },
  stt: { name: "models.family.stt", description: "models.familyDesc.stt" },
  tts: { name: "models.family.tts", description: "models.familyDesc.tts" },
  "production-tools": { name: "models.family.tools", description: "models.familyDesc.tools" },
  mcp: { name: "models.family.mcp", description: "models.familyDesc.mcp" },
};

export function familyNameKey(family: Family): CatalogKey {
  return familyKeys[family].name;
}

export function familyDescriptionKey(family: Family): CatalogKey {
  return familyKeys[family].description;
}

export function costKind(cost: CostClass): CostKind {
  if (cost === "paid") return "paid_cloud";
  if (cost === "free_paid") return "free_or_paid";
  return "free_local";
}

export function reasonHintKey(reason: string | null): CatalogKey {
  if (reason === "missing_binary") return "models.reason.missingBinary";
  if (reason === "missing_model_files") return "models.reason.missingModelFiles";
  if (reason === "model_files_mismatch") return "models.reason.modelFilesMismatch";
  if (reason === "gateway_down") return "models.reason.gatewayDown";
  if (reason === "missing_extra") return "models.reason.missingExtra";
  if (reason === "unsupported_runtime") return "models.reason.unsupportedRuntime";
  if (reason === "catalog_error") return "models.reason.catalogError";
  if (reason === "API key not set") return "models.reason.keyNotSet";
  return "models.reason.generic";
}

function optionView(entry: CapabilityEntry): ModelOptionView {
  const kind = costKind(entry.cost);
  const available = entry.availability === "available";
  return {
    id: entry.id,
    label: entry.label,
    costKind: kind,
    available,
    isDefault: entry.default,
    // Only an option that actually uses an environment key can report a key state;
    // a keyless option (free/local, or a hybrid available via its free path) reports none.
    keyConfigured: entry.key_env ? available : null,
    enablementHintKey: available ? null : reasonHintKey(entry.reason),
    envVarName: entry.key_env,
  };
}

function familyStatus(family: CapabilityFamilyView): CapabilityStatus {
  const active = family.entries.find((entry) => entry.id === family.active);
  const available = family.entries.filter((entry) => entry.availability === "available");
  if (available.length === 0) {
    const blocked = family.entries[0] ?? null;
    return {
      kind: "not_available",
      labelKey: "models.status.notAvailable",
      enablementHintKey: blocked ? reasonHintKey(blocked.reason) : "models.reason.generic",
      envVarName: blocked?.key_env ?? null,
    };
  }
  // Base the ready badge on the option actually in force: the active entry only if it is
  // itself available, otherwise the first available option (never an unavailable "active").
  const inForce = active && active.availability === "available" ? active : available[0];
  const activeCost = costKind(inForce.cost);
  if (activeCost === "paid_cloud" || activeCost === "free_or_paid") {
    return { kind: "ready_cloud", labelKey: "models.status.readyCloud", enablementHintKey: null, envVarName: null };
  }
  return { kind: "ready_free_local", labelKey: "models.status.readyFreeLocal", enablementHintKey: null, envVarName: null };
}

export function toCapabilityViews(inventory: CapabilityInventory): CapabilityView[] {
  return inventory.families.map((family) => ({
    family: family.family,
    nameKey: familyNameKey(family.family),
    descriptionKey: familyDescriptionKey(family.family),
    displayKind: family.selectable ? "chooser" : "readonly",
    status: familyStatus(family),
    options: family.entries.map(optionView),
    activeOptionId: family.active,
    selectedId: family.selected,
    isEnvOverridden: family.env_override != null,
    envVarName: family.env_override,
    isStale: family.selected_stale,
  }));
}
