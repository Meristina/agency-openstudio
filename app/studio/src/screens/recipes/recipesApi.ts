import type { MissionEvent } from "../../types";

export interface Recipe {
  id: string;
  kind: "composed" | "production";
  name_key: string;
  desc_key: string;
  required_inputs: Array<{ key: string; label_key: string }>;
  stages: Array<{ kind: string; tier: "local" | "cloud"; label_key: string }>;
}

function parseFrame(frame: string): MissionEvent | null {
  const line = frame.split("\n").find((item) => item.startsWith("data:"));
  if (!line) return null;
  try {
    return JSON.parse(line.slice(5).trim()) as MissionEvent;
  } catch {
    return null;
  }
}

async function errorText(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { error?: string };
    if (data.error) return data.error;
  } catch {
    /* ignore */
  }
  return `HTTP ${res.status}`;
}

export async function listRecipes(): Promise<Recipe[]> {
  const res = await fetch("/api/recipes");
  if (!res.ok) throw new Error(`GET /api/recipes -> ${res.status}`);
  const data = (await res.json()) as { recipes?: Recipe[] };
  return data.recipes ?? [];
}

async function streamRecipe(
  body: Record<string, unknown>,
  onEvent: (event: MissionEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/recipe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw new Error(await errorText(res));
  if (!res.body) throw new Error("POST /api/recipe failed");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const event = parseFrame(buffer.slice(0, sep));
      buffer = buffer.slice(sep + 2);
      if (event) onEvent(event);
    }
  }
  const tail = parseFrame(buffer);
  if (tail) onEvent(tail);
}

export async function startRecipe(
  recipeId: string,
  subject: string,
  onEvent: (event: MissionEvent) => void,
  opts: { signal?: AbortSignal; cloudOptins?: string[] } = {},
): Promise<void> {
  return streamRecipe(
    { recipe_id: recipeId, subject, inputs: { subject }, cloud_optins: opts.cloudOptins ?? [] },
    onEvent, opts.signal);
}

export async function resumeRecipe(
  runId: string,
  onEvent: (event: MissionEvent) => void,
  opts: { signal?: AbortSignal } = {},
): Promise<void> {
  // Resume a checkpointed recipe run: the server reconstructs recipe/subject/opt-ins from the
  // pinned checkpoint (POST /api/recipe {resume_from}); the client need only name the checkpoint.
  return streamRecipe({ resume_from: runId }, onEvent, opts.signal);
}

export async function cancelRecipe(runId: string): Promise<boolean> {
  const res = await fetch(`/api/recipe/${encodeURIComponent(runId)}/cancel`, { method: "POST", signal: AbortSignal.timeout(4000) });
  return res.status === 202;
}
