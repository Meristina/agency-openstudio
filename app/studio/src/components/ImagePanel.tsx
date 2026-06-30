// Image tab: a prompt → FLUX.1-schnell (local, Metal) → a generated image added to
// the session gallery. All inference is local; nothing leaves the machine.

import { useState } from "react";
import { generateImage } from "../api";
import type { GalleryItem } from "../types";

export default function ImagePanel({ onGenerated }: { onGenerated: (item: GalleryItem) => void }) {
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onGenerate = async () => {
    const p = prompt.trim();
    if (!p || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await generateImage(p);
      onGenerated({ kind: "image", url: result.url, label: result.prompt, seconds: result.seconds });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

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
        <button onClick={() => void onGenerate()} disabled={busy || !prompt.trim()}>
          {busy ? "Generating…" : "Generate"}
        </button>
        <span className="hint">FLUX.1-schnell · local · Metal</span>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
