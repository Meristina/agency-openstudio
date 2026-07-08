// Session gallery of locally-generated assets (images, audio, video). Items are served
// by the Studio server under /media; this holds only the in-session list.

import type { GalleryItem } from "../types";

export default function Gallery({ items }: { items: GalleryItem[] }) {
  if (items.length === 0) {
    return <p className="muted">Nothing generated yet this session.</p>;
  }
  return (
    <div className="gallery">
      {items.map((item) => (
        <figure key={item.url} className="gallery-item">
          {item.kind === "image" ? (
            <img src={item.url} alt={item.label} loading="lazy" />
          ) : item.kind === "video" ? (
            <video controls src={item.url} />
          ) : (
            <audio controls src={item.url} />
          )}
          <figcaption title={item.label}>
            {item.label}
            {typeof item.seconds === "number" ? ` · ${item.seconds}s` : ""}
          </figcaption>
        </figure>
      ))}
    </div>
  );
}
