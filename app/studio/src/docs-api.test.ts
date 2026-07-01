import { afterEach, describe, expect, it, vi } from "vitest";
import { deleteDoc, ingestDoc, listDocs } from "./api";

const realFetch = global.fetch;
afterEach(() => {
  global.fetch = realFetch;
  vi.restoreAllMocks();
});

function stubFetch(res: Partial<Response>): ReturnType<typeof vi.fn> {
  const fn = vi.fn().mockResolvedValue(res);
  global.fetch = fn as unknown as typeof fetch;
  return fn;
}

describe("listDocs", () => {
  it("GETs /api/docs and returns the docs array", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({ docs: [{ id: "a", filename: "r.pdf", title: "R", n_chunks: 3, created: 1 }] }) });
    const docs = await listDocs();
    expect(docs).toHaveLength(1);
    expect(docs[0].filename).toBe("r.pdf");
  });

  it("returns [] when the payload has no docs", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({}) });
    expect(await listDocs()).toEqual([]);
  });
});

describe("ingestDoc", () => {
  it("POSTs the file bytes with the filename in the query", async () => {
    const fn = stubFetch({ ok: true, status: 201, json: async () => ({ id: "x", filename: "notes.md", title: "Notes", n_chunks: 2, created: 5 }) });
    const file = new File([new Uint8Array([1, 2, 3])], "notes.md", { type: "text/markdown" });
    const meta = await ingestDoc(file);
    expect(meta.id).toBe("x");
    const [path, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/docs?filename=notes.md");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(file);
  });

  it("surfaces the server's 501 install hint", async () => {
    stubFetch({ ok: false, status: 501, json: async () => ({ error: "install the local-docs extra:  pip install 'agency-studio[studio]'" }) });
    const file = new File(["x"], "a.pdf");
    await expect(ingestDoc(file)).rejects.toThrow(/studio/);
  });
});

describe("deleteDoc", () => {
  it("DELETEs /api/docs/{id}", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ deleted: "abc" }) });
    await deleteDoc("abc");
    const [path, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/docs/abc");
    expect(init.method).toBe("DELETE");
  });

  it("throws on a 404 (unknown document)", async () => {
    stubFetch({ ok: false, status: 404, json: async () => ({ error: "unknown document" }) });
    await expect(deleteDoc("nope")).rejects.toThrow(/404/);
  });
});
