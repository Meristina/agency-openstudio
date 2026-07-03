// Visual tab (Wave 6 — visual RAG / PixelRAG): upload images, list them, delete them.
// Each image is captioned by a vision-language model, and the caption is embedded + stored in a
// SQLite vector store; each mission then retrieves the captions most relevant to its goal and
// cites them (see the "Visual docs" step in the mission timeline). Captioning is LOCAL by
// default — the "Caption in the cloud" consent below is the studio's ONLY off-machine data flow.

import { useCallback, useEffect, useRef, useState } from "react";
import { deleteVisual, listVisual, uploadVisual } from "../api";
import type { VisualMeta } from "../types";

export default function VisualDocsPanel() {
  const [docs, setDocs] = useState<VisualMeta[]>([]);
  const [busy, setBusy] = useState(false);
  const [cloud, setCloud] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocs(await listVisual());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0 || busy) return;
      setBusy(true);
      setError(null);
      try {
        // Ingest sequentially — the server captions on the single warm ModelManager, so
        // parallel uploads would just serialize on its lock anyway.
        for (const file of Array.from(files)) {
          await uploadVisual(file, { cloud });
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        // Refresh even on a mid-batch failure, so images captioned BEFORE the failing one show
        // up — otherwise the user re-uploads them, and with cloud consent that re-sends the
        // image off-machine a second time.
        await refresh();
        setBusy(false);
        if (inputRef.current) inputRef.current.value = ""; // allow re-selecting the same file
      }
    },
    [busy, cloud, refresh],
  );

  const onDelete = useCallback(
    async (id: string) => {
      setError(null);
      try {
        await deleteVisual(id);
        await refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [refresh],
  );

  return (
    <section className="panel">
      <h2>Visual documents</h2>
      <p className="hint">
        Uploaded images are captioned by a vision model, embedded locally, and retrieved into each
        mission as sourced excerpts — for screenshots, charts, and diagrams the text pipeline can't
        read.
      </p>
      <div className="row">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          aria-label="Upload images"
          disabled={busy}
          onChange={(e) => void onFiles(e.target.files)}
        />
        <span className="hint">{busy ? "Captioning…" : "png · jpg · webp · local VLM · Metal"}</span>
      </div>
      <label
        className="toggle"
        title="Caption these images with the cloud vision model instead of the local one. This is the studio's only off-machine data flow — the images leave your Mac. Requires an API key in the server environment."
      >
        <input
          type="checkbox"
          checked={cloud}
          disabled={busy}
          onChange={(e) => setCloud(e.target.checked)}
        />
        Caption in the cloud (images leave this Mac)
      </label>
      {error && <p className="error">{error}</p>}

      <ul className="missions">
        {docs.length === 0 && <li className="muted">No images ingested yet.</li>}
        {docs.map((d) => (
          <li key={d.id}>
            <div className="mission-item doc-item">
              <span className="mission-item-head">
                <span className="goal-text">{d.title}</span>
                <span className="badge pending">{d.n_chunks} chunk{d.n_chunks === 1 ? "" : "s"}</span>
              </span>
              <code className="doc-file">{d.filename}</code>
            </div>
            <button className="ghost" aria-label={`Delete ${d.filename}`} onClick={() => void onDelete(d.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
