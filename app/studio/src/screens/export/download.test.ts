import { describe, expect, it, vi } from "vitest";
import { downloadBlob } from "./download";

describe("download", () => {
  it("downloads a blob with the chosen filename", () => {
    const click = vi.fn();
    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const oldCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag) => {
      const el = oldCreate(tag);
      if (tag === "a") el.click = click;
      return el;
    });
    downloadBlob(new Blob(["x"]), "file.zip");
    expect(click).toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});
