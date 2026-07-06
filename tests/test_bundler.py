import copy
import zipfile

import pytest

from agency_studio import bundler


def _names(path):
    with zipfile.ZipFile(path) as zf:
        return sorted(zf.namelist())


def test_build_media_zip_confines_and_sanitizes(tmp_path):
    assets = tmp_path / "studio_assets"
    media = assets / "missions" / "m1" / "images"
    media.mkdir(parents=True)
    (media / "hero.png").write_bytes(b"img")
    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    (media / "leak.txt").symlink_to(secret)

    path = bundler.build_media_zip("m1", assets)

    assert _names(path) == ["images/hero.png"]


def test_build_media_zip_empty_signals_no_media(tmp_path):
    with pytest.raises(bundler.NoMediaError):
        bundler.build_media_zip("m1", tmp_path)


def test_build_media_zip_cleans_temp_on_failure(monkeypatch, tmp_path):
    import glob
    import os
    import tempfile

    # A media file that vanishes before zf.write reads it → assembly raises mid-way.
    monkeypatch.setattr(bundler, "_media_files", lambda *_a, **_kw: [(tmp_path / "gone.png", "gone.png")])
    before = set(glob.glob(os.path.join(tempfile.gettempdir(), "agency-export-*.zip")))

    with pytest.raises(OSError):
        bundler.build_media_zip("m1", tmp_path / "studio_assets")

    after = set(glob.glob(os.path.join(tempfile.gettempdir(), "agency-export-*.zip")))
    assert after == before  # the temp zip was not orphaned


def test_sources_markdown_and_empty_sources():
    assert "Example" in bundler.sources_markdown({"sources": [{"title": "Example", "url": "https://example.com", "accessed": "2026-07-06"}]})
    assert "No sources" in bundler.sources_markdown({"sources": []})


def test_build_bundle_contains_pdf_media_sources_and_no_raw_dossier(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_kit import store

    dossier = {"mission_id": "m1", "project_root": store.canonical_project_root(tmp_path), "delivered": "x", "sources": ["https://example.com"]}
    original = copy.deepcopy(dossier)
    store.save(dossier)
    assets = tmp_path / "studio_assets"
    media = assets / "missions" / "m1"
    media.mkdir(parents=True)
    (media / "hero.png").write_bytes(b"img")
    pdf = tmp_path / "out.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr("agency_cli.exporter.export_pdf", lambda _mid, **_kw: pdf)

    path = bundler.build_bundle("m1", assets)

    assert _names(path) == ["deliverable.pdf", "media/hero.png", "sources.md"]
    with zipfile.ZipFile(path) as zf:
        assert "dossier.json" not in zf.namelist()
        assert "https://example.com" in zf.read("sources.md").decode()
    assert dossier == original


def test_build_bundle_wraps_assembly_failure(monkeypatch, tmp_path):
    # A media file that vanishes between scan and zf.write raises FileNotFoundError mid-
    # assembly; build_bundle must surface it as BundleAssemblyError so the handler reports a
    # 500 (packaging failure) rather than a 404 that would falsely claim "no deliverable".
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_kit import store

    store.save({"mission_id": "m1", "project_root": store.canonical_project_root(tmp_path), "delivered": "x"})
    pdf = tmp_path / "out.pdf"
    pdf.write_bytes(b"%PDF")
    monkeypatch.setattr("agency_cli.exporter.export_pdf", lambda _mid, **_kw: pdf)
    monkeypatch.setattr(bundler, "_media_files", lambda *_a, **_kw: [(tmp_path / "gone.png", "gone.png")])

    with pytest.raises(bundler.BundleAssemblyError):
        bundler.build_bundle("m1", tmp_path / "studio_assets")
    assert not isinstance(bundler.BundleAssemblyError(), FileNotFoundError)  # would map to 404


def test_build_bundle_propagates_missing_pdf_extra(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from agency_kit import store

    store.save({"mission_id": "m1", "project_root": store.canonical_project_root(tmp_path), "delivered": "x"})
    monkeypatch.setattr("agency_cli.exporter.export_pdf", lambda *_a, **_kw: (_ for _ in ()).throw(ImportError("install pdf")))

    with pytest.raises(ImportError):
        bundler.build_bundle("m1", tmp_path / "studio_assets")
