import { afterEach, describe, expect, it, vi } from "vitest";
import { assignMission, cancelMission, fetchTaxonomy, getMission, getPersonaStats, listMissions, runMission } from "./api";
import type { MissionEvent } from "./types";

const realFetch = global.fetch;
afterEach(() => {
  global.fetch = realFetch;
  vi.restoreAllMocks();
});

/** A ReadableStream that emits the given string chunks then closes. */
function sseStream(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(enc.encode(c));
      controller.close();
    },
  });
}

function stubFetch(res: Partial<Response>): void {
  global.fetch = vi.fn().mockResolvedValue(res) as unknown as typeof fetch;
}

async function collect(chunks: string[]): Promise<MissionEvent[]> {
  stubFetch({ ok: true, status: 200, body: sseStream(chunks) });
  const got: MissionEvent[] = [];
  await runMission("a goal", (e) => got.push(e));
  return got;
}

describe("runMission SSE parsing", () => {
  it("parses multiple complete frames in order", async () => {
    const got = await collect([
      'data: {"phase":"route","status":"done","route":["solve"]}\n\n' +
        'data: {"phase":"done","mission_id":"m1","verdict":"PASS","path":"/p","residual_risk":null}\n\n',
    ]);
    expect(got.map((e) => e.phase)).toEqual(["route", "done"]);
    expect(got[0]).toMatchObject({ route: ["solve"] });
  });

  it("reassembles a frame split across stream chunks", async () => {
    const frame = 'data: {"phase":"dept","dept":"solve","status":"start"}\n\n';
    const mid = Math.floor(frame.length / 2);
    const got = await collect([frame.slice(0, mid), frame.slice(mid)]);
    expect(got).toEqual([{ phase: "dept", dept: "solve", status: "start" }]);
  });

  it("flushes a final frame that lacks the trailing blank line", async () => {
    const got = await collect(['data: {"phase":"error","message":"boom"}']);
    expect(got).toEqual([{ phase: "error", message: "boom" }]);
  });

  it("ignores non-data lines and blank frames", async () => {
    const got = await collect([
      ": keep-alive comment\n\n" + 'data: {"phase":"synth","iteration":1,"status":"start"}\n\n',
    ]);
    expect(got).toEqual([{ phase: "synth", iteration: 1, status: "start" }]);
  });

  it("throws when the response is not ok", async () => {
    stubFetch({ ok: false, status: 500, body: null });
    await expect(runMission("g", () => {})).rejects.toThrow(/500/);
  });

  it("throws when the response is ok but has no body", async () => {
    stubFetch({ ok: true, status: 200, body: null });
    await expect(runMission("g", () => {})).rejects.toThrow(/no response body/);
  });

  it("sends web_search/mcp/knowledge false by default and true when opted in", async () => {
    // A fresh stream per call — a ReadableStream can only be read once.
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve({ ok: true, status: 200, body: sseStream([]) }),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await runMission("g", () => {});
    expect(JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)).toMatchObject({
      goal: "g", web_search: false, mcp: false, knowledge: false, mcp_tools: false, personas: false, visual: false, video: false, assets: true,
    });

    await runMission("g", () => {}, { webSearch: true, mcp: true, knowledge: true, mcpTools: true, personas: true, visual: true, video: true });
    expect(JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)).toMatchObject({
      web_search: true, mcp: true, knowledge: true, mcp_tools: true, personas: true, visual: true, video: true, assets: true,
    });
  });

  it("omits resume_from by default and sends it (with the goal) when resuming", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve({ ok: true, status: 200, body: sseStream([]) }),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await runMission("g", () => {});
    expect(JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)).not.toHaveProperty("resume_from");

    await runMission("g", () => {}, { resumeFrom: "c".repeat(32) });
    expect(JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)).toMatchObject({
      goal: "g", resume_from: "c".repeat(32),
    });
  });

  it("sends taxonomy fields when supplied and omits empty fields", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve({ ok: true, status: 200, body: sseStream([]) }),
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await runMission("g", () => {}, { client: "Acme", project: "", campaign: "Spring" });
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body).toMatchObject({ client: "Acme", campaign: "Spring" });
    expect(body).not.toHaveProperty("project");
  });
});

describe("getPersonaStats", () => {
  it("returns the persona-store stats", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({ total: 2, enabled: 1, by_dept: { product: { enabled: 1, names: ["pm"] } } }) });
    expect(await getPersonaStats()).toEqual({ total: 2, enabled: 1, by_dept: { product: { enabled: 1, names: ["pm"] } } });
  });

  it("throws on a non-ok response", async () => {
    stubFetch({ ok: false, status: 503 });
    await expect(getPersonaStats()).rejects.toThrow(/503/);
  });
});

describe("listMissions / getMission", () => {
  it("listMissions returns the missions array", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({ missions: [{ mission_id: "m1" }] }) });
    expect(await listMissions()).toEqual([{ mission_id: "m1" }]);
  });

  it("listMissions throws on a non-ok response", async () => {
    stubFetch({ ok: false, status: 503 });
    await expect(listMissions()).rejects.toThrow(/503/);
  });

  it("getMission throws on a non-ok response", async () => {
    stubFetch({ ok: false, status: 404 });
    await expect(getMission("nope")).rejects.toThrow(/404/);
  });

  it("listMissions sends filters as query params", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ missions: [] }) });
    global.fetch = fetchMock as unknown as typeof fetch;
    await listMissions({ client: "Acme", project: "Rebrand" });
    expect(fetchMock).toHaveBeenCalledWith("/api/missions?client=Acme&project=Rebrand");
  });

  it("fetchTaxonomy returns the tree", async () => {
    stubFetch({ ok: true, status: 200, json: async () => ({ clients: [{ name: "Acme", missions: 1, projects: [] }] }) });
    expect(await fetchTaxonomy()).toEqual({ clients: [{ name: "Acme", missions: 1, projects: [] }] });
  });

  it("assignMission posts the override and returns attribution", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ attribution: { client: "Acme", project: "Rebrand", campaign: null } }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;
    expect(await assignMission("m1", { client: "Acme" })).toEqual({ client: "Acme", project: "Rebrand", campaign: null });
    expect(fetchMock).toHaveBeenCalledWith("/api/mission/m1/assign", expect.objectContaining({ method: "POST" }));
  });
});

describe("cancelMission", () => {
  it("POSTs to the cancel endpoint and returns true on 202", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ status: 202 });
    global.fetch = fetchMock as unknown as typeof fetch;
    const runId = "a".repeat(32);
    expect(await cancelMission(runId)).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/mission/${runId}/cancel`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("returns false when the run is unknown/finished (404)", async () => {
    global.fetch = vi.fn().mockResolvedValue({ status: 404 }) as unknown as typeof fetch;
    expect(await cancelMission("b".repeat(32))).toBe(false);
  });
});
