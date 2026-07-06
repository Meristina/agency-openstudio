import { describe, expect, it } from "vitest";
import { availableFormats, friendlyFilename, hasMedia } from "./exportModel";

const deliverable = { id: "20260706-demo", title: "Sponsor deck" };

describe("exportModel", () => {
  it("derives format availability from media and pdf capability", () => {
    expect(availableFormats({ hasMedia: true, pdfCapable: true }).map((f) => f.state)).toEqual(["available", "available", "available"]);
    expect(availableFormats({ hasMedia: false, pdfCapable: true })[1].state).toBe("no-media-to-pack");
    expect(availableFormats({ hasMedia: true, pdfCapable: false })[0].state).toBe("unavailable-here");
  });

  it("detects usable media from the dossier manifest", () => {
    expect(hasMedia({ assets: [{ type: "image", status: "ok", url: "/media/missions/m1/a.png" }] })).toBe(true);
    expect(hasMedia({ assets: [{ type: "image", status: "failed" }] })).toBe(false);
  });

  it("returns friendly single-deliverable filenames", () => {
    expect(friendlyFilename(deliverable, "fullBundle")).toBe("sponsor-deck-bundle.zip");
  });
});
