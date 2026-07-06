import { describe, expect, it } from "vitest";
import type { MissionSummary, TaxonomyTree } from "../../types";
import { buildLibraryModel, classifyOutcome, placementOf } from "./libraryModel";

const taxonomy: TaxonomyTree = {
  clients: [{
    name: "Acme",
    missions: 2,
    projects: [{ name: "Rebrand", missions: 2, campaigns: [{ name: "Launch", missions: 1 }] }],
  }],
};

function mission(id: string, extra: Partial<MissionSummary> = {}): MissionSummary {
  return { mission_id: id, goal: "Launch plan", delivered: true, verdict: "PASS", ...extra };
}

describe("buildLibraryModel", () => {
  it("groups, dedupes, scopes, and keeps orphaned work visible as unassigned", () => {
    const model = buildLibraryModel([
      mission("20260701-a", { client: "Acme", project: "Rebrand", campaign: "Launch" }),
      mission("20260702-b"),
      mission("20260703-c", { client: "Ghost", project: "Gone" }),
      mission("20260701-a", { goal: "duplicate" }),
    ], taxonomy, { client: null, project: null, campaign: null }, { query: "", outcomeFilter: "all" });

    expect(model.total).toBe(3);
    expect(model.shelves[0].client).toBe("Acme");
    expect(model.shelves[0].projects[0].campaigns[0].deliverables[0].title).toBe("Launch plan");
    expect(model.unassigned.map((d) => d.placement.kind).sort()).toEqual(["orphaned", "unassigned"]);
    expect(JSON.stringify(model)).not.toContain("PASS");
    expect(JSON.stringify(model)).not.toContain("duplicate");
  });

  it("applies client scope, search, and outcome filter with the right empty flags", () => {
    const missions = [
      mission("20260701-a", { goal: "Sponsor deck", client: "Acme", project: "Rebrand", campaign: "Launch" }),
      mission("20260702-b", { goal: "Broken video", delivered: false, verdict: "VETO", client: "Acme", project: "Rebrand" }),
      mission("20260703-c", { goal: "Other client", client: "Other" }),
    ];

    expect(buildLibraryModel(missions, taxonomy, { client: "Acme", project: null, campaign: null }, { query: "launch", outcomeFilter: "all" }).total).toBe(1);
    expect(buildLibraryModel(missions, taxonomy, { client: "Acme", project: null, campaign: null }, { query: "", outcomeFilter: "needs-attention" }).total).toBe(1);
    const none = buildLibraryModel(missions, taxonomy, { client: "Acme", project: null, campaign: null }, { query: "missing", outcomeFilter: "all" });
    expect(none.isEmptyForQuery).toBe(true);
    expect(none.isEmptyFirstRun).toBe(false);
    expect(buildLibraryModel(missions, taxonomy, { client: "Missing", project: null, campaign: null }, { query: "", outcomeFilter: "all" }).isEmptyForContext).toBe(true);
  });

  it("classifies outcomes and resolves placements", () => {
    expect(classifyOutcome(mission("ok"))).toBe("successful");
    expect(classifyOutcome(mission("bad", { delivered: false, verdict: "VETO" }))).toBe("needs-attention");
    expect(placementOf(mission("x", { client: "Acme", project: "Rebrand", campaign: "Launch" }), taxonomy).kind).toBe("filed");
    expect(placementOf(mission("x", { client: "Acme", project: "Missing" }), taxonomy).kind).toBe("orphaned");
  });
});
