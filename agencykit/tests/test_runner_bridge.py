from agency_cli import runner_bridge
from agency_cli.verification import VerificationConfig


def _dossier(verification=None):
    d = {
        "goal": "demo",
        "route": ["marketing"],
        "iteration": 1,
        "verdicts": [{"verdict": "PASS"}],
        "delivered": "body",
        "sources": [],
    }
    if verification is not None:
        d["verification"] = verification
    return d


def test_resolve_verification_coercion_and_disable_rules():
    assert runner_bridge._resolve_verification(None) == VerificationConfig()
    assert runner_bridge._resolve_verification({"min_sources": "2", "resolve": 1}) == VerificationConfig(
        min_sources=2, resolve=True
    )
    assert runner_bridge._resolve_verification({"min_sources": 0, "resolve": False}) is None
    assert runner_bridge._resolve_verification({"min_sources": 0, "resolve": True}) == VerificationConfig(
        min_sources=0, resolve=True
    )
    assert runner_bridge._resolve_verification("junk") == VerificationConfig()


def test_dossier_md_renders_source_verification_section():
    md = runner_bridge._dossier_md("001-demo", _dossier({
        "min_sources": 3,
        "resolve": True,
        "cycles": [],
        "final": {
            "rate": 0.4,
            "truncated": 2,
            "per_dept": {"marketing": {"counted": 2, "min": 3, "ok": False}},
            "sources": [{"url": "https://dead.test/a", "status": "unresolved", "detail": "HTTP 404", "depts": ["marketing"]}],
            "missing": ["Claim lacks a source"],
        },
    }))

    assert "## Source verification" in md
    assert "Verified-source rate: 40%" in md
    assert "| marketing | 2 | 3 | no |" in md
    assert "https://dead.test/a (HTTP 404)" in md
    assert "Claim lacks a source" in md
    assert "2 sources not checked" in md


def test_dossier_md_omits_section_without_key_and_handles_offline_rate():
    base = runner_bridge._dossier_md("001-demo", _dossier())
    assert "## Source verification" not in base

    offline = runner_bridge._dossier_md("001-demo", _dossier({
        "min_sources": 1,
        "resolve": False,
        "cycles": [],
        "final": {
            "rate": None,
            "truncated": 0,
            "per_dept": {"marketing": {"counted": 1, "min": 1, "ok": True}},
            "sources": [{"url": "https://ok.test/a", "status": "unverified", "detail": "resolution not enabled", "depts": ["marketing"]}],
            "missing": [],
        },
    }))
    assert "unverified (resolution not enabled)" in offline

