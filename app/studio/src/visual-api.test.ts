import { afterEach, describe, expect, it, vi } from "vitest";
import { deleteVisual, listVisual, uploadVisual } from "./api";

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

describe("listVisual", () => {
  it("GETs /api/visual and returns the docs array", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({ docs: [{ id: "a", filename: "c.png", title: "A chart", n_chunks: 1, created: 1 }] }) });
    const docs = await listVisual();
    expect(docs).toHaveLength(1);
    expect(docs[0].filename).toBe("c.png");
  });

  it("returns [] when the payload has no docs", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({}) });
    expect(await listVisual()).toEqual([]);
  });
});

describe("uploadVisual", () => {
  it("POSTs the image bytes with the filename in the query (local, no cloud)", async () => {
    const fn = stubFetch({ ok: true, status: 201, json: async () => ({ id: "x", filename: "d.png", title: "Diagram", n_chunks: 1, created: 5 }) });
    const file = new File([new Uint8Array([1, 2, 3])], "d.png", { type: "image/png" });
    const meta = await uploadVisual(file);
    expect(meta.id).toBe("x");
    const [path, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/visual?filename=d.png");   // no &cloud=1 without explicit consent
    expect(init.method).toBe("POST");
    expect(init.body).toBe(file);
  });

  it("adds &cloud=1 only when the caller opts into off-machine captioning", async () => {
    const fn = stubFetch({ ok: true, status: 201, json: async () => ({ id: "x", filename: "d.png", title: "D", n_chunks: 1, created: 5 }) });
    const file = new File(["x"], "d.png", { type: "image/png" });
    await uploadVisual(file, { cloud: true });
    const [path] = fn.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/visual?filename=d.png&cloud=1");
  });

  it("surfaces the server's 501 install hint", async () => {
    stubFetch({ ok: false, status: 501, json: async () => ({ error: "install the visual-RAG extra:  pip install 'agency-studio[visual]'" }) });
    const file = new File(["x"], "a.png");
    await expect(uploadVisual(file)).rejects.toThrow(/visual/);
  });
});

describe("deleteVisual", () => {
  it("DELETEs /api/visual/{id}", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ deleted: "abc" }) });
    await deleteVisual("abc");
    const [path, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/visual/abc");
    expect(init.method).toBe("DELETE");
  });

  it("throws on a 404 (unknown image)", async () => {
    stubFetch({ ok: false, status: 404, json: async () => ({ error: "unknown image" }) });
    await expect(deleteVisual("nope")).rejects.toThrow(/404/);
  });
});
