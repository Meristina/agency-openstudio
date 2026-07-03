// Docs tab (Wave 4 — RAG / LocalDocs): upload documents, list them, delete them.
// Ingested docs are embedded locally and stored in a SQLite vector store; each mission
// then retrieves the excerpts most relevant to its goal and cites them in the deliverable
// (see the "Local docs" step in the mission timeline). All local — nothing leaves the Mac.

import { useCallback, useEffect, useRef, useState } from "react";
import { deleteDoc, ingestDoc, listDocs } from "../api";
import type { DocMeta } from "../types";

export default function DocsPanel() {
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocs(await listDocs());
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
        // Ingest sequentially — the server embeds on the single warm ModelManager, so
        // parallel uploads would just serialize on its lock anyway.
        for (const file of Array.from(files)) {
          await ingestDoc(file);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        // Refresh even on a mid-batch failure, so files ingested BEFORE the failing one show
        // up — otherwise they're invisible and the user re-uploads them, duplicating chunks
        // (the server dedups nothing; each upload gets a fresh id).
        await refresh();
        setBusy(false);
        if (inputRef.current) inputRef.current.value = ""; // allow re-selecting the same file
      }
    },
    [busy, refresh],
  );

  const onDelete = useCallback(
    async (id: string) => {
      setError(null);
      try {
        await deleteDoc(id);
        await refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [refresh],
  );

  return (
    <section className="panel">
      <h2>Local documents</h2>
      <p className="hint">
        Uploaded files are embedded locally and retrieved into each mission as sourced
        excerpts — nothing leaves the machine.
      </p>
      <div className="row">
        <input
          ref={inputRef}
          type="file"
          multiple
          aria-label="Upload documents"
          disabled={busy}
          onChange={(e) => void onFiles(e.target.files)}
        />
        <span className="hint">{busy ? "Ingesting…" : "PDF · docx · pptx · md · txt · local · Metal"}</span>
      </div>
      {error && <p className="error">{error}</p>}

      <ul className="missions">
        {docs.length === 0 && <li className="muted">No documents ingested yet.</li>}
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
