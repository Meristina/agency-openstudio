// Wave 3 — the per-mission multimodal gallery, rendered from a dossier's persisted
// render manifest (`dossier.assets`). Unlike the Wave-2 session Gallery (which only
// ever holds successful generations), the manifest also records `failed`/`skipped`
// renders, so this surfaces partial-render state honestly rather than hiding it.

import type { AssetManifestItem } from "../types";

/** The caption for an `ok` entry: the verbatim prompt (image) or narration text (tts). */
function caption(item: AssetManifestItem): string {
  if (item.type === "image") return item.prompt || "generated image";
  return item.text || "generated narration";
}

/** The render metadata suffix (model/voice · Ns), shown under a successful asset. */
function meta(item: AssetManifestItem): string {
  const parts: string[] = [];
  if (item.type === "image" && item.model) parts.push(item.model);
  if (item.type === "tts" && item.voice) parts.push(item.voice);
  if (typeof item.seconds === "number") parts.push(`${item.seconds}s`);
  return parts.join(" · ");
}

export default function AssetGallery({ items }: { items?: AssetManifestItem[] }) {
  if (!items || items.length === 0) return null;
  const ok = items.filter((it) => it.status === "ok" && it.url);
  const other = items.filter((it) => it.status !== "ok" || !it.url);

  return (
    <section className="detail-list asset-gallery">
      <h4>Generated assets</h4>
      {ok.length > 0 && (
        <div className="gallery">
          {ok.map((item, i) => (
            <figure key={`${item.url}-${i}`} className="gallery-item">
              {item.type === "image" ? (
                <img src={item.url} alt={caption(item)} loading="lazy" />
              ) : (
                <audio controls src={item.url} />
              )}
              <figcaption title={caption(item)}>
                {caption(item)}
                {meta(item) ? <span className="muted"> · {meta(item)}</span> : null}
              </figcaption>
            </figure>
          ))}
        </div>
      )}
      {other.length > 0 && (
        <ul className="steps asset-residuals">
          {other.map((item, i) => (
            <li key={`${item.type}-${i}`} className="step">
              <span className="step-dot" /> {item.type === "image" ? "image" : "narration"}
              <span className="step-state">
                {item.status}
                {item.reason ? ` — ${item.reason}` : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
