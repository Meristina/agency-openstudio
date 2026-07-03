// Image tab: a prompt → a chosen local image model (mflux, Metal) → a generated
// image added to the session gallery. All inference is local; nothing leaves the
// machine. The model is picked per generation from the server's image_models registry.

import { useState } from "react";
import { generateImage } from "../api";
import type { GalleryItem, ImageModelInfo } from "../types";

/** Pick the registry's default model (default:true), else the first, else "". */
function defaultModelId(models: ImageModelInfo[]): string {
  return (models.find((m) => m.default) ?? models[0])?.id ?? "";
}

// Square output sizes offered in the GUI. 1024 is the server's own default, so leaving
// this at 1024 keeps a generation byte-identical to before this control existed; 512/768
// let a 16 GB Mac trade resolution for speed (fewer pixels → far less swap).
const SIZES = [512, 768, 1024] as const;
// Step counts. "auto" sends no `steps`, so the backend uses the chosen model's own default
// (schnell = few-step) — the pre-control behaviour. 2 is the fast floor schnell supports.
const STEP_CHOICES = ["auto", 2, 4] as const;
type StepChoice = (typeof STEP_CHOICES)[number];

export default function ImagePanel({
  imageModels,
  onGenerated,
}: {
  imageModels: ImageModelInfo[];
  onGenerated: (item: GalleryItem) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState(() => defaultModelId(imageModels));
  const [size, setSize] = useState<number>(1024);
  const [steps, setSteps] = useState<StepChoice>("auto");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Once the registry arrives (or changes), make sure the selection is still valid:
  // adopt the default when nothing is chosen yet OR the chosen id is no longer in the
  // list (else the <select> would render blank while we'd still POST a missing id).
  if (imageModels.length && !imageModels.some((m) => m.id === model)) {
    setModel(defaultModelId(imageModels));
  }

  const onGenerate = async () => {
    const p = prompt.trim();
    if (!p || busy) return;
    setBusy(true);
    setError(null);
    try {
      const opts: { model?: string; width: number; height: number; steps?: number } = {
        width: size,
        height: size,
      };
      if (model) opts.model = model;
      if (steps !== "auto") opts.steps = steps;
      const result = await generateImage(p, opts);
      onGenerated({ kind: "image", url: result.url, label: result.prompt, seconds: result.seconds });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const selected = imageModels.find((m) => m.id === model);

  return (
    <section className="panel">
      <h2>Generate image</h2>
      <textarea
        className="goal"
        rows={3}
        placeholder="Describe the image…"
        value={prompt}
        disabled={busy}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <div className="row">
        <label className="field">
          <span className="field-label">Model</span>
          <select
            className="model-select"
            aria-label="Image model"
            value={model}
            disabled={busy || imageModels.length === 0}
            onChange={(e) => setModel(e.target.value)}
          >
            {imageModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Resolution</span>
          <select
            className="model-select"
            aria-label="Resolution"
            value={size}
            disabled={busy}
            onChange={(e) => setSize(Number(e.target.value))}
          >
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}×{s}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Steps</span>
          <select
            className="model-select"
            aria-label="Steps"
            value={String(steps)}
            disabled={busy}
            onChange={(e) => {
              const v = e.target.value;
              setSteps(v === "auto" ? "auto" : (Number(v) as StepChoice));
            }}
          >
            {STEP_CHOICES.map((s) => (
              <option key={s} value={String(s)}>
                {s === "auto" ? "Auto" : s}
              </option>
            ))}
          </select>
        </label>
        <button onClick={() => void onGenerate()} disabled={busy || !prompt.trim()}>
          {busy ? "Generating…" : "Generate"}
        </button>
        <span className="hint">{selected ? `${selected.note} · local · Metal` : "local · Metal"}</span>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
