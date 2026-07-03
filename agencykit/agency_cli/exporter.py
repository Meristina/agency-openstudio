"""Export a mission deliverable to PDF.

WeasyPrint (pure Python, HTML → PDF) — no ATS constraints, just clean layout.
Optional dependency: `pip install -e "[pdf]"`.

Strips the YAML front-matter added by store.save() before converting to HTML.
"""

import re
from pathlib import Path

# Wave 3 — markdown image/link forms `assets.rewrite_delivered` emits for a rendered
# asset: `![caption](/media/<rel>)` (image embed) and `[label](/media/<rel>)` (audio
# link). The `/media/<rel>` URL is a Studio *server route*, not an on-disk path, so a
# PDF render orphans it unless we resolve it back to the file under the assets root.
_MEDIA_IMG = re.compile(r"!\[([^\]]*)\]\((/media/[^)\s]+)\)")
_MEDIA_LINK = re.compile(r"\[([^\]]*)\]\((/media/[^)\s]+)\)")
_MEDIA_PREFIX = "/media/"


def export_pdf(mission_id: str, assets_root=None) -> Path:
    """Convert ~/.agency/missions/<mission_id>/deliverable.md to PDF.

    Returns the path to the generated PDF. Raises FileNotFoundError if the
    deliverable doesn't exist, ImportError if WeasyPrint/Markdown aren't installed.

    ``assets_root`` (Studio only) is the directory the ``/media`` route serves from
    (``<project>/studio_assets``). When given, any ``/media/<rel>`` reference in the
    deliverable is resolved to its on-disk file so generated images embed in the PDF
    (audio becomes a caption — a PDF can't play sound), and WeasyPrint is locked to a
    url_fetcher that only loads ``file://`` resources inside that root — so a raw
    ``![x](file:///etc/passwd)`` / ``<img src=http://…>`` in the (partly untrusted)
    deliverable can't pull arbitrary local files or make outbound requests during render.
    Defaults to None ⇒ the call is byte-identical to standalone agency-kit (no asset
    rewriting, no base_url, default fetcher).
    """
    try:
        import weasyprint
    except ImportError:
        raise ImportError('WeasyPrint not installed. Run:  pip install -e ".[pdf]"')

    try:
        import markdown as _md
    except ImportError:
        raise ImportError('Markdown not installed. Run:  pip install -e ".[pdf]"')

    from agency_kit.store import missions_dir, strip_frontmatter

    md_path = missions_dir() / mission_id / "deliverable.md"
    if not md_path.exists():
        raise FileNotFoundError(f"deliverable.md not found for mission: {mission_id}")

    content = strip_frontmatter(md_path.read_text(encoding="utf-8"))
    if assets_root is not None:
        content = _localize_assets(content, Path(assets_root))

    html_body = _md.markdown(content, extensions=["tables", "fenced_code"])
    html = _wrap_html(html_body)

    out = md_path.parent / "deliverable.pdf"
    if assets_root is not None:
        # Localized assets are already absolute file:// URIs (no base_url needed); the
        # fetcher confines every resource load to the asset root, closing the file://
        # disclosure + http(s) SSRF surface on the untrusted deliverable text.
        html_obj = weasyprint.HTML(string=html, url_fetcher=_asset_only_fetcher(Path(assets_root).resolve()))
    else:
        html_obj = weasyprint.HTML(string=html)  # standalone: byte-identical to pre-Wave-3
    html_obj.write_pdf(str(out))
    return out


def _asset_only_fetcher(root: Path):
    """A WeasyPrint ``url_fetcher`` that permits ONLY ``file://`` URLs resolving inside
    ``root`` (the localized assets, already vetted by ``_localize_assets``). Every other
    scheme/host — an ``http(s)`` SSRF/beacon, or a ``file://`` to an arbitrary local file
    spliced into the untrusted deliverable via raw markdown — is refused, so rendering an
    attacker-influenced deliverable can't read outside the asset root or reach the network.
    """
    from urllib.parse import unquote, urlparse

    def _fetch(url: str):
        parsed = urlparse(url)
        if parsed.scheme != "file":
            raise ValueError(f"PDF render blocked a non-file resource URL: {parsed.scheme}:")
        try:
            resolved = Path(unquote(parsed.path)).resolve()
            resolved.relative_to(root)
        except (ValueError, OSError):
            raise ValueError("PDF render blocked a file URL outside the asset root")
        import weasyprint  # only reached once the URL is vetted in-root
        return weasyprint.default_url_fetcher(url)

    return _fetch


def _localize_assets(content: str, assets_root: Path) -> str:
    """Rewrite ``/media/<rel>`` references so a PDF render can resolve them.

    Images become absolute ``file://`` URIs (WeasyPrint rasterizes them into the PDF);
    audio links become a plain ``label — filename`` caption, since a PDF can't play
    sound. A reference that escapes ``assets_root`` or points at a missing file is
    dropped to its caption text rather than left as a broken/dangling link. Pure: no
    writes, never raises on a malformed reference.
    """
    try:
        root = assets_root.resolve()
    except OSError:
        return content

    def _on_disk(url: str):
        """Resolve a ``/media/<rel>`` URL to its file under ``root``, or None if it
        escapes the root or doesn't exist (defence in depth, though the refs are ours)."""
        rel = url[len(_MEDIA_PREFIX):]
        try:
            target = (root / rel).resolve()
            target.relative_to(root)
        except (ValueError, OSError):
            return None
        return target if target.is_file() else None

    def _image(match: "re.Match") -> str:
        caption, url = match.group(1), match.group(2)
        target = _on_disk(url)
        # Drop a broken embed to its caption so the PDF shows text, not a missing-image box.
        return f"![{caption}]({target.as_uri()})" if target else caption

    content = _MEDIA_IMG.sub(_image, content)

    def _link(match: "re.Match") -> str:
        label, url = match.group(1), match.group(2)
        target = _on_disk(url)
        name = target.name if target else url.rsplit("/", 1)[-1]
        return f"{label} — {name}"

    # Image embeds were already rewritten above (their URLs are now file://, so this
    # /media-only link pass leaves them untouched and only catches the audio links).
    return _MEDIA_LINK.sub(_link, content)


def _wrap_html(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.65;
      color: #1a1a1a;
    }}
    h1 {{ font-size: 19pt; color: #111; border-bottom: 2px solid #333; padding-bottom: 5px; margin-top: 0; }}
    h2 {{ font-size: 14pt; color: #222; margin-top: 22px; border-bottom: 1px solid #ddd; padding-bottom: 3px; }}
    h3 {{ font-size: 12pt; color: #333; margin-top: 16px; }}
    h4 {{ font-size: 11pt; color: #444; margin-top: 12px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f2f2f2; font-weight: 600; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-size: 9.5pt; font-family: 'Courier New', monospace; }}
    pre {{ background: #f4f4f4; padding: 12px; border-radius: 4px; overflow: auto; font-size: 9.5pt; }}
    pre code {{ background: none; padding: 0; }}
    blockquote {{ border-left: 3px solid #aaa; margin: 0 0 12px 0; padding: 4px 0 4px 16px; color: #555; }}
    ul, ol {{ padding-left: 20px; }}
    li {{ margin-bottom: 3px; }}
    a {{ color: #0055aa; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 16px 0; }}
    @page {{
      size: A4;
      margin: 2cm 2.2cm 2.2cm 2.2cm;
      @bottom-right {{
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #999;
      }}
    }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
