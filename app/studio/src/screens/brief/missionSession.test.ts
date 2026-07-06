import { afterEach, describe, expect, it, vi } from "vitest";
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
});
