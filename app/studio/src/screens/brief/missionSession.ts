import { cancelMission, runMission } from "../../api";
import type { MissionEvent } from "../../types";
import type { MissionDraft } from "./composeMission";

type State = {
  status: "idle" | "launching" | "running" | "failed" | "done";
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
      state.status = "done";
      publish();
    } catch (error) {
      state.status = "failed";
      const message = error instanceof Error ? error.message : "Launch failed";
      state.error = /blocker|capabilit|409/i.test(message) ? `Production is blocked. ${message}` : message;
      publish();
    }
    return state;
  },
  async cancel() {
    controller?.abort();
    return state.runId ? cancelMission(state.runId) : false;
  },
  reset() {
    Object.assign(state, { status: "idle", runId: null, events: [], error: null });
    controller = null;
    publish();
  },
};
