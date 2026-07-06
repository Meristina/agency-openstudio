import { cancelMission, runMission } from "../../api";
import type { MissionEvent } from "../../types";
import type { MissionDraft } from "../brief/composeMission";

type State = {
  status: "idle" | "launching" | "running" | "cancelled" | "failed" | "done";
  runId: string | null;
  events: MissionEvent[];
  error: string | null;
};

const state: State = { status: "idle", runId: null, events: [], error: null };
const listeners = new Set<(state: State) => void>();
let controller: AbortController | null = null;

function publish() {
  for (const listener of listeners) listener({ ...state, events: [...state.events] });
}

export const missionSession = {
  snapshot: () => ({ ...state, events: [...state.events] }),
  subscribe(listener: (state: State) => void): () => void {
    listeners.add(listener);
    listener(this.snapshot());
    return () => {
      listeners.delete(listener);
    };
  },
  async launch(draft: MissionDraft) {
    if (state.status === "launching" || state.status === "running") return state;
    controller = new AbortController();
    Object.assign(state, { status: "launching", runId: null, events: [], error: null });
    publish();
    try {
      await runMission(draft.goal, (event) => {
        state.events.push(event);
        if (event.phase === "run") {
          state.runId = event.run_id;
          state.status = "running";
        }
        publish();
      }, { ...draft.opts, signal: controller?.signal });
      if (state.status !== "idle") state.status = "done";
      publish();
    } catch (error) {
      // reset() may have already returned the session to idle before this
      // rejection lands — a settled reset must not be overwritten.
      // The as-cast defeats TS's over-narrow flow analysis: the SSE callback
      // mutates state.status ("running") in ways this scope cannot see.
      const current = state.status as State["status"];
      if (current === "launching" || current === "running") {
        // DOMException is not an Error subclass in every runtime — match by name.
        if ((error as { name?: string } | null)?.name === "AbortError") {
          state.status = "cancelled";
          state.error = null;
        } else {
          state.status = "failed";
          const message = error instanceof Error ? error.message : "Launch failed";
          state.error = /blocker|capabilit|409/i.test(message) ? `Production is blocked. ${message}` : message;
        }
      }
      publish();
    }
    return state;
  },
  async resume(runId: string) {
    // Send an EMPTY goal: the server reconstructs the goal from the checkpoint envelope, and a
    // non-empty goal that disagrees with the pinned envelope goal is rejected with 409
    // ("checkpoint is for a different goal"). After a reload we don't have the original goal,
    // so empty is the only correct value here.
    return this.launch({ goal: "", opts: { webSearch: false, video: false, assets: false, resumeFrom: runId } });
  },
  async cancel() {
    controller?.abort();
    return state.runId ? cancelMission(state.runId) : false;
  },
  reset() {
    controller?.abort();
    controller = null;
    Object.assign(state, { status: "idle", runId: null, events: [], error: null });
    publish();
  },
};
