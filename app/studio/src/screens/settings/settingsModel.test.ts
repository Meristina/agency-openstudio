import { describe, expect, it, vi } from "vitest";
import { PREFS_KEY } from "../../i18n/catalog";
import { BRIEF_DRAFT_KEY } from "../brief/briefDraft";
import { ASSOCIATION_KEY } from "../import/associationStore";
import { FOLLOW_POINTER_KEY } from "../missions/followPointer";
import { sampleInventory } from "../models/testData";
import { clearLocalPreferences, deriveModelSummary, deriveSystemView, PREFERENCE_KEYS } from "./settingsModel";

describe("settingsModel", () => {
  it("clears exactly the studio preference keys", () => {
    expect(PREFERENCE_KEYS).toEqual([PREFS_KEY, ASSOCIATION_KEY, BRIEF_DRAFT_KEY, FOLLOW_POINTER_KEY]);
    localStorage.setItem(PREFS_KEY, "x");
    localStorage.setItem(ASSOCIATION_KEY, "x");
    localStorage.setItem(BRIEF_DRAFT_KEY, "x");
    localStorage.setItem(FOLLOW_POINTER_KEY, "x");
    localStorage.setItem("selection-store", "keep");

    clearLocalPreferences(localStorage);

    for (const key of PREFERENCE_KEYS) expect(localStorage.getItem(key)).toBeNull();
    expect(localStorage.getItem("selection-store")).toBe("keep");
  });

  it("is safe when storage cannot remove", () => {
    expect(() => clearLocalPreferences({ removeItem: vi.fn(() => { throw new Error("blocked"); }) })).not.toThrow();
    expect(() => clearLocalPreferences(null)).not.toThrow();
  });

  it("derives system reachability and facts", () => {
    expect(deriveSystemView(null, null, null)).toMatchObject({ connection: "unknown", version: null, dataLocation: null });
    expect(deriveSystemView(null, null, false).connection).toBe("offline");
    expect(deriveSystemView({ version: "1.2.3", dataDir: "/tmp/studio" }, sampleInventory(), true)).toMatchObject({
      connection: "connected",
      version: "1.2.3",
      dataLocation: "/tmp/studio",
    });
  });

  it("summarizes selectable model families", () => {
    const summary = deriveModelSummary(sampleInventory());
    expect(summary.map((item) => item.familyKey)).toContain("models.family.image");
    expect(summary.map((item) => item.familyKey)).not.toContain("models.family.tools");
    expect(summary.find((item) => item.familyKey === "models.family.video")?.choiceLabel).toBe("Local Video");
    // Stale selection ('old-vision' not in entries) resolves to the active model's
    // label, never the raw id.
    expect(summary.find((item) => item.familyKey === "models.family.visual")?.choiceLabel).toBe("Local Vision");
  });
});
