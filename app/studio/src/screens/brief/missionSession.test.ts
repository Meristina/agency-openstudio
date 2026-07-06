import { afterEach, describe, expect, it, vi } from "vitest";
import { runMission } from "../../api";
import { missionSession } from "./missionSession";

vi.mock("../../api", () => ({
  runMission: vi.fn(async (_goal: string, onEvent: (event: { phase: "run"; run_id: string }) => void) => {
    onEvent({ phase: "run", run_id: "r1" });
  }),
  cancelMission: vi.fn(async () => true),
}));

afterEach(() => missionSession.reset());

describe("missionSession", () => {
  it("captures the run id and buffers events", async () => {
    await missionSession.launch({ goal: "g", opts: { webSearch: true, video: false, assets: false } });
    expect(missionSession.snapshot()).toMatchObject({ status: "done", runId: "r1", events: [{ phase: "run", run_id: "r1" }] });
  });

  it("notifies subscribers and survives unsubscribe", async () => {
    const seen: string[] = [];
    const unsubscribe = missionSession.subscribe((state) => seen.push(state.status));
    unsubscribe();
    await missionSession.launch({ goal: "g", opts: { webSearch: true, video: false, assets: false } });
    expect(seen).toEqual(["idle"]);
  });

  it("maps a deliberate abort to cancelled, not failed", async () => {
    vi.mocked(runMission).mockRejectedValueOnce(new DOMException("aborted", "AbortError"));
    await missionSession.launch({ goal: "g", opts: { webSearch: true, video: false, assets: false } });
    expect(missionSession.snapshot()).toMatchObject({ status: "cancelled", error: null });
  });

  it("reset aborts the in-flight run and stays idle over the late rejection", async () => {
    let signal: AbortSignal | undefined;
    vi.mocked(runMission).mockImplementationOnce((_goal, _onEvent, opts) => new Promise((_resolve, reject) => {
      signal = opts?.signal;
      opts?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
    }));
    const launched = missionSession.launch({ goal: "g", opts: { webSearch: true, video: false, assets: false } });
    missionSession.reset();
    await launched;
    expect(signal?.aborted).toBe(true);
    expect(missionSession.snapshot().status).toBe("idle");
  });
});
