import { afterEach, describe, expect, it } from "vitest";
import { FOLLOW_POINTER_KEY, clear, read, record } from "./followPointer";

afterEach(() => localStorage.clear());

describe("followPointer", () => {
  it("stores exactly one non-secret pointer", () => {
    record({ runId: "r1", status: "running" });
    const next = record({ runId: "r2", status: "error", resumable: true, checkpoint: "c1" });
    expect(read()).toMatchObject({ runId: "r2", status: "error", resumable: true, checkpoint: "c1" });
    expect(JSON.parse(localStorage.getItem(FOLLOW_POINTER_KEY) || "{}")).toEqual(next);
    expect(Object.keys(next).sort()).toEqual(["checkpoint", "resumable", "runId", "status", "updatedAt"].sort());
  });

  it("clears and ignores malformed records", () => {
    record({ runId: "r1", status: "done", missionId: "m1" });
    clear();
    expect(read()).toBeNull();
    localStorage.setItem(FOLLOW_POINTER_KEY, "{");
    expect(read()).toBeNull();
  });
});
