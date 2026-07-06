import { describe, expect, it } from "vitest";
import type { CapabilityEntry, CapabilityInventory, Family } from "../../types";
import { costKind, familyNameKey, reasonHintKey, toCapabilityViews } from "./capabilityModel";

const families: Family[] = ["image", "video", "visual", "embedding", "kg-extraction", "stt", "tts", "production-tools", "mcp"];

function entry(extra: Partial<CapabilityEntry> = {}): CapabilityEntry {
  return {
    id: "local",
    label: "Local model",
    family: "image",
    cost: "free",
    availability: "available",
    reason: null,
    enablement: null,
    tier: "LOCAL",
    note: "note",
    default: true,
    key_env: null,
    ...extra,
  };
}

function inventory(): CapabilityInventory {
  return {
    generated_at: "now",
    families: families.map((family) => ({
      family,
      selectable: family !== "production-tools" && family !== "mcp",
      selected: null,
      selected_stale: false,
      env_override: null,
      active: `${family}-local`,
      entries: [entry({ id: `${family}-local`, family })],
    })),
  };
}

describe("capabilityModel", () => {
  it("maps all families to plain catalog keys and chooser/read-only display", () => {
    const views = toCapabilityViews(inventory());
    expect(views.map((view) => view.nameKey)).toEqual([
      "models.family.image",
      "models.family.video",
      "models.family.visual",
      "models.family.embedding",
      "models.family.kg",
      "models.family.stt",
      "models.family.tts",
      "models.family.tools",
      "models.family.mcp",
    ]);
    expect(views.filter((view) => view.displayKind === "chooser")).toHaveLength(7);
    expect(views.find((view) => view.family === "production-tools")?.displayKind).toBe("readonly");
    expect(familyNameKey("kg-extraction")).toBe("models.family.kg");
  });

  it("derives cost, status, override, stale, and env-name-only hints", () => {
    const inv = inventory();
    inv.families[0] = {
      family: "image",
      selectable: true,
      selected: "cloud",
      selected_stale: true,
      env_override: "AGENCY_IMAGE_MODEL",
      active: "local",
      entries: [
        entry({ id: "local", family: "image" }),
        entry({
          id: "cloud",
          label: "Cloud model",
          family: "image",
          cost: "paid",
          availability: "unavailable",
          reason: "API key not set",
          key_env: "AGENCY_IMAGE_KEY",
          default: false,
        }),
      ],
    };
    const view = toCapabilityViews(inv)[0];
    expect(costKind("free")).toBe("free_local");
    expect(costKind("paid")).toBe("paid_cloud");
    expect(costKind("free_paid")).toBe("free_or_paid");
    expect(reasonHintKey("missing_binary")).toBe("models.reason.missingBinary");
    expect(view.status.kind).toBe("ready_free_local");
    expect(view.isEnvOverridden).toBe(true);
    expect(view.envVarName).toBe("AGENCY_IMAGE_MODEL");
    expect(view.isStale).toBe(true);
    expect(view.options[1]).toMatchObject({
      costKind: "paid_cloud",
      available: false,
      keyConfigured: false,
      enablementHintKey: "models.reason.keyNotSet",
      envVarName: "AGENCY_IMAGE_KEY",
    });
    expect(JSON.stringify(view)).not.toContain("API key not set");
    expect(JSON.stringify(view)).not.toContain("LOCAL");
  });

  it("marks a family unavailable when no option is available", () => {
    const inv = inventory();
    inv.families[0].entries = [entry({ availability: "unavailable", reason: "gateway_down" })];
    const view = toCapabilityViews(inv)[0];
    expect(view.status.kind).toBe("not_available");
    expect(view.status.enablementHintKey).toBe("models.reason.gatewayDown");
  });

  it("reports keyConfigured only for options that actually use an environment key", () => {
    const inv = inventory();
    inv.families[0].entries = [
      entry({ id: "hybrid", cost: "free_paid", availability: "available", key_env: null }),
      entry({ id: "cloud", cost: "paid", availability: "available", key_env: "AGENCY_X_KEY" }),
      entry({ id: "local", cost: "free", availability: "available", key_env: null }),
    ];
    const [hybrid, cloud, local] = toCapabilityViews(inv)[0].options;
    expect(hybrid.keyConfigured).toBeNull(); // free-or-paid, keyless → no false "key configured"
    expect(cloud.keyConfigured).toBe(true);  // key-bearing + available → configured
    expect(local.keyConfigured).toBeNull();
  });

  it("derives the ready badge from an available option, never an unavailable active one", () => {
    const inv = inventory();
    inv.families[0] = {
      family: "image",
      selectable: true,
      selected: null,
      selected_stale: false,
      env_override: null,
      active: "local", // active but UNAVAILABLE
      entries: [
        entry({ id: "local", cost: "free", availability: "unavailable", reason: "missing_model_files", default: true }),
        entry({ id: "cloud", cost: "paid", availability: "available", key_env: "AGENCY_X_KEY", default: false }),
      ],
    };
    // The only usable option is paid cloud, so the badge must say cloud — not "ready free/local".
    expect(toCapabilityViews(inv)[0].status.kind).toBe("ready_cloud");
  });

  it("maps the server reason codes it can receive to plain hints (no silent generic fallback)", () => {
    expect(reasonHintKey("missing_extra")).toBe("models.reason.missingExtra");
    expect(reasonHintKey("unsupported_runtime")).toBe("models.reason.unsupportedRuntime");
    expect(reasonHintKey("catalog_error")).toBe("models.reason.catalogError");
  });
});
