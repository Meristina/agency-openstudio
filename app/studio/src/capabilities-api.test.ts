import { afterEach, describe, expect, it, vi } from "vitest";
import { clearCapability, fetchCapabilities, selectCapability } from "./api";

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

describe("capabilities api", () => {
  it("fetches the inventory and refresh flag", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ families: [], generated_at: "now" }) });
    expect((await fetchCapabilities()).families).toEqual([]);
    expect(fn.mock.calls[0][0]).toBe("/api/capabilities");
    await fetchCapabilities(true);
    expect(fn.mock.calls[1][0]).toBe("/api/capabilities?refresh=1");
  });

  it("selects and clears a family default", async () => {
    const fn = stubFetch({ ok: true, status: 200, json: async () => ({ family: "image", selected: "flux-schnell" }) });
    await selectCapability("image", "flux-schnell");
    expect(fn.mock.calls[0][0]).toBe("/api/capabilities/selection");
    expect(JSON.parse((fn.mock.calls[0][1] as RequestInit).body as string)).toEqual({ family: "image", id: "flux-schnell" });

    stubFetch({ ok: true, status: 204 });
    await expect(clearCapability("image")).resolves.toBeUndefined();
  });

  it("surfaces refusal payloads", async () => {
    stubFetch({ ok: false, status: 409, json: async () => ({ error: "entry unavailable", reason: "missing_extra" }) });
    await expect(selectCapability("image", "x")).rejects.toThrow(/entry unavailable/);
  });
});
