// Video tab: a prompt → the server's configured video backend (local OpenMontage Remotion
// or cloud Seedance, per $AGENCY_STUDIO_VIDEO_BACKEND) → a short rendered clip added to the
// session gallery. Unlike image/voice, the backend is install-selected (no per-generation
// model picker); the first local render also downloads a headless Chromium, so it is slow.

import { useState } from "react";
import { generateVideo } from "../api";
import type { GalleryItem } from "../types";

export default function VideoPanel({
  onGenerated,
}: {
  onGenerated: (item: GalleryItem) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onGenerate = async () => {
    const p = prompt.trim();
    if (!p || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await generateVideo(p);
      onGenerated({ kind: "video", url: result.url, label: result.prompt, seconds: result.seconds });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <h2>Generate video</h2>
      <textarea
        className="goal"
        rows={3}
        placeholder="Describe the short clip…"
        value={prompt}
        disabled={busy}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <div className="row">
        <button onClick={() => void onGenerate()} disabled={busy || !prompt.trim()}>
          {busy ? "Rendering…" : "Generate"}
        </button>
        <span className="hint">
          backend-selected · first local render downloads a headless browser (slow once)
        </span>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
