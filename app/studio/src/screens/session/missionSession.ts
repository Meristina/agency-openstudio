import { cancelMission, runMission } from "../../api";
import type { MissionEvent } from "../../types";
import type { MissionDraft } from "../brief/composeMission";
import { resumeRecipe as resumeRecipeApi, startRecipe } from "../recipes/recipesApi";

type State = {
  status: "idle" | "launching" | "running" | "cancelled" | "failed" | "done";
  runId: string | null;
  events: MissionEvent[];
  error: string | null;
};

const state: State = { status: "idle", runId: null, events: [], error: null };
const listeners = new Set<(state: State) => void>();
let controller: AbortController | null = null;
// Which run this session last drove, so a generic resume() dispatches to the right endpoint —
// a recipe resumes via POST /api/recipe (mission resume would 404 on a recipe checkpoint).
let lastKind: "mission" | "recipe" = "mission";

function publish() {
  for (const listener of listeners) listener({ ...state, events: [...state.events] });
}

// Shared drive loop for a recipe run (fresh launch or resume): the two differ only in the API call.
async function driveRecipe(apiCall: (onEvent: (event: MissionEvent) => void, signal?: AbortSignal) => Promise<void>) {
  if (state.status === "launching" || state.status === "running") return state;
  controller = new AbortController();
  Object.assign(state, { status: "launching", runId: null, events: [], error: null });
  lastKind = "recipe";
  publish();
  try {
    await apiCall((event) => {
      state.events.push(event);
      if (event.phase === "run") {
        state.runId = event.run_id;
        state.status = "running";
      }
      publish();
    }, controller.signal);
    if (state.status !== "idle") state.status = "done";
  } catch (error) {
    const current = state.status as State["status"];
    if (current === "launching" || current === "running") {
      if ((error as { name?: string } | null)?.name === "AbortError") {
        state.status = "cancelled";
        state.error = null;  // a user-initiated cancel is not an error (matches launch())
      } else {
        state.status = "failed";
        state.error = error instanceof Error ? error.message : "Launch failed";
      }
    }
  }
  publish();
  return state;
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
    lastKind = "mission";
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
  async launchRecipe(recipeId: string, subject: string, cloudOptins: string[] = []) {
    return driveRecipe((onEvent, signal) => startRecipe(recipeId, subject, onEvent, { signal, cloudOptins }));
  },
  async resumeRecipe(runId: string) {
    // Restart a checkpointed recipe at its failed stage — the server replays the completed mission
    // (never re-running it) and resumes downstream. Same drive loop as a fresh recipe launch.
    return driveRecipe((onEvent, signal) => resumeRecipeApi(runId, onEvent, { signal }));
  },
  async resume(runId: string) {
    // Dispatch to the endpoint that owns this checkpoint: a recipe run resumes via POST /api/recipe
    // (the mission resume path 404s a recipe checkpoint). `lastKind` is live for the immediate
    // resume — the common case where the failed run's "Resume" button is clicked in the same session.
    if (lastKind === "recipe") return this.resumeRecipe(runId);
    // Mission: send an EMPTY goal — the server reconstructs it from the checkpoint envelope, and a
    // non-empty goal that disagrees is rejected with 409. After a reload we don't have the original
    // goal, so empty is the only correct value here.
    return this.launch({ goal: "", opts: { webSearch: false, video: false, assets: false, resumeFrom: runId } });
  },
  async cancel() {
    controller?.abort();
    return state.runId ? cancelMission(state.runId) : false;
  },
  reset() {
    controller?.abort();
    controller = null;
    lastKind = "mission";
    Object.assign(state, { status: "idle", runId: null, events: [], error: null });
    publish();
  },
};
