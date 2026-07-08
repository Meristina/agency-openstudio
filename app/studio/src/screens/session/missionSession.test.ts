import { afterEach, describe, expect, it, vi } from "vitest";
import { runMission } from "../../api";
import { resumeRecipe, startRecipe } from "../recipes/recipesApi";
import { missionSession } from "./missionSession";

vi.mock("../../api", () => ({
  runMission: vi.fn(async (_goal: string, onEvent: (event: { phase: "run"; run_id: string }) => void) => {
    onEvent({ phase: "run", run_id: "r1" });
  }),
  cancelMission: vi.fn(async () => true),
}));

vi.mock("../recipes/recipesApi", () => ({
  startRecipe: vi.fn(async (_id: string, _subject: string, onEvent: (e: { phase: "run"; run_id: string }) => void) => {
    onEvent({ phase: "run", run_id: "rc0" });
  }),
  resumeRecipe: vi.fn(async (_runId: string, onEvent: (e: { phase: "run"; run_id: string }) => void) => {
    onEvent({ phase: "run", run_id: "rc1" });
  }),
}));

afterEach(() => { missionSession.reset(); vi.clearAllMocks(); });

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

  it("resumes through the existing launch path", async () => {
    await missionSession.resume("r0");
    // Empty goal so the server reconstructs it from the checkpoint (a non-empty mismatching goal 409s).
    expect(runMission).toHaveBeenCalledWith("", expect.any(Function), expect.objectContaining({ resumeFrom: "r0" }));
  });

  it("dispatches a resume to the recipe endpoint after a recipe run (not the mission path)", async () => {
    await missionSession.launchRecipe("full-campaign", "coffee", []);
    await missionSession.resume("rc1");
    expect(resumeRecipe).toHaveBeenCalledWith("rc1", expect.any(Function), expect.anything());
    // Never the mission resume path — that would 404 on a recipe checkpoint.
    expect(runMission).not.toHaveBeenCalled();
    expect(missionSession.snapshot()).toMatchObject({ status: "done", runId: "rc1" });
  });

  it("resumes a recipe via the recipe endpoint after a reload (persisted kind, not the reset session kind)", async () => {
    // Simulate a full page reload: no launch happened this session, so the live kind is the default
    // "mission". The follow pointer's persisted resumeKind ("recipe") must still route to /api/recipe.
    await missionSession.resume("rc1", "recipe");
    expect(resumeRecipe).toHaveBeenCalledWith("rc1", expect.any(Function), expect.anything());
    expect(runMission).not.toHaveBeenCalled();
  });

  it("routes launchRecipe through the recipe start endpoint", async () => {
    await missionSession.launchRecipe("cinematic", "a teaser", ["pipeline"]);
    expect(startRecipe).toHaveBeenCalledWith("cinematic", "a teaser", expect.any(Function),
      expect.objectContaining({ cloudOptins: ["pipeline"] }));
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
