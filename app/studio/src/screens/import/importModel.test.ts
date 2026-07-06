import { describe, expect, it } from "vitest";
import { buildImportModel, classifyBringInError, classifyFileKind } from "./importModel";

const doc = { id: "d1", filename: "brief.pdf", title: "Client brief", n_chunks: 1, created: 10 };
const visual = { id: "v1", filename: "mood.jpg", title: "", n_chunks: 1, created: 20 };

describe("buildImportModel", () => {
  it("merges, names, groups, scopes, and dedups imported material", () => {
    const model = buildImportModel([doc, doc], [visual], { d1: { client: "Acme", project: "Expo", campaign: "Launch" } }, { client: "Acme" });
    expect(model.total).toBe(1);
    expect(model.shelves[0].projects[0].campaigns[0].items[0]).toMatchObject({ id: "d1", kind: "document", name: "Client brief" });

    const all = buildImportModel([doc], [visual], {}, {});
    expect(all.total).toBe(2);
    expect(all.unassigned.map((item) => item.name)).toEqual(["mood.jpg", "Client brief"]);
  });
});

describe("bring-in classification", () => {
  it("keeps unsupported files client-side and maps common endpoint failures", () => {
    expect(classifyFileKind(new File(["x"], "clip.mp4", { type: "video/mp4" }))).toBe("unsupported");
    expect(classifyFileKind(new File(["x"], "brief.pdf", { type: "application/pdf" }))).toBe("document");
    expect(classifyFileKind(new File(["x"], "image.png", { type: "image/png" }))).toBe("image");
    expect(classifyBringInError(new Error("POST /api/visual → 501"), "image").status).toBe("capabilityAbsent");
    expect(classifyBringInError(new Error("POST /api/docs → 400"), "document").reason).toBe("import.reject.unreadable");
  });
});
