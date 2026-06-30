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

export default function ImagePanel({
  imageModels,
  onGenerated,
}: {
  imageModels: ImageModelInfo[];
  onGenerated: (item: GalleryItem) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState(() => defaultModelId(imageModels));
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
      const result = await generateImage(p, model ? { model } : {});
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
        <button onClick={() => void onGenerate()} disabled={busy || !prompt.trim()}>
          {busy ? "Generating…" : "Generate"}
        </button>
        <span className="hint">{selected ? `${selected.note} · local · Metal` : "local · Metal"}</span>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
