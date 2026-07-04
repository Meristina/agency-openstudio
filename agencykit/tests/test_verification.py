import pytest

from agency_cli import verification


def test_config_defaults_validation_and_dict_coercion():
    assert verification.VerificationConfig() == verification.VerificationConfig(min_sources=3, resolve=False)
    assert verification.coerce_config({"min_sources": "2", "resolve": 1}) == verification.VerificationConfig(
        min_sources=2, resolve=True
    )
    with pytest.raises(ValueError):
        verification.VerificationConfig(min_sources=-1)
    # bool is an int subclass: a malformed true/false must not silently become 1/0
    # and lower the threshold — it falls back to the default.
    assert verification.coerce_config({"min_sources": True}).min_sources == 3
    assert verification.coerce_config({"min_sources": False}).min_sources == 3


def test_extract_sources_attributes_depts_and_dedups_first_seen():
    records = verification.extract_sources(
        {"marketing": "A https://a.test/x. B https://b.test/y and literal `https://`", "product": "Again https://a.test/x"},
        "Synthesis cites https://c.test/z and https://b.test/y",
    )

    assert [r["url"] for r in records] == ["https://a.test/x", "https://b.test/y", "https://c.test/z"]
    assert records[0]["depts"] == ["marketing", "product"]
    assert records[1]["depts"] == ["marketing"]
    assert records[2]["depts"] == []


@pytest.mark.parametrize(
    ("url", "calls"),
    [
        ("http://example.com/x", 0),
        ("https://localhost/x", 0),
        ("https://127.0.0.1/x", 0),
        ("https://10.0.0.1/x", 0),
    ],
)
def test_policy_refusals_never_call_probe(monkeypatch, url, calls):
    seen = []
    monkeypatch.setattr(verification, "_head_probe", lambda u: seen.append(u) or (200, "HTTP 200"))

    status, detail, kind = verification.probe_url(url)

    assert (status, kind) == ("unresolved", "policy")
    assert "policy:" in detail
    assert len(seen) == calls


def test_redirect_hops_are_policy_checked_and_stay_head():
    handler = verification._PolicyRedirectHandler()
    req = verification.Request("https://example.com/x", method="HEAD")

    # A hop leaving the secure public web is refused before any fetch.
    for target in ("http://example.com/x", "https://127.0.0.1/x", "https://localhost/x"):
        with pytest.raises(verification._RedirectRefused):
            handler.redirect_request(req, None, 302, "Found", {}, target)

    # A policy-clean hop is followed — and the follow-up request is still a HEAD.
    follow = handler.redirect_request(req, None, 302, "Found", {}, "https://example.org/y")
    assert follow.get_method() == "HEAD"
    assert follow.full_url == "https://example.org/y"


def test_policy_refused_redirect_classifies_unresolved(monkeypatch):
    monkeypatch.setattr(
        verification, "_head_probe",
        lambda url: (verification._POLICY_REDIRECT, "policy: redirect refused: non-https"),
    )

    status, detail, kind = verification.probe_url("https://example.com/x")

    assert (status, kind) == ("unresolved", "policy")
    assert "redirect refused" in detail


@pytest.mark.parametrize(
    ("outcome", "status", "kind"),
    [
        ((200, "HTTP 200"), "resolved", "http"),
        ((302, "HTTP 302"), "resolved", "http"),
        ((404, "HTTP 404"), "unresolved", "http"),
        ((410, "HTTP 410"), "unresolved", "http"),
        ((401, "HTTP 401"), "ambiguous", "http"),
        ((403, "HTTP 403"), "ambiguous", "http"),
        ((405, "HTTP 405"), "ambiguous", "http"),
        ((429, "HTTP 429"), "ambiguous", "http"),
        ((500, "HTTP 500"), "ambiguous", "http"),
        ((None, "dns not found"), "unresolved", "nxdomain"),
        ((None, "timeout"), "ambiguous", "connection"),
    ],
)
def test_probe_classification_table(monkeypatch, outcome, status, kind):
    monkeypatch.setattr(verification, "_head_probe", lambda url: outcome)

    assert verification.probe_url("https://example.com/x") == (status, outcome[1], kind)


def test_verify_cycle_gate_rate_truncation_cache_and_outage(monkeypatch):
    urls = [f"https://e.test/{i}" for i in range(55)]
    dept_outputs = {"product": "https://dead.test/a https://ok.test/a", "marketing": " ".join(urls)}
    calls = []

    def fake_probe(url):
        calls.append(url)
        if "dead" in url:
            return 404, "HTTP 404"
        return 200, "HTTP 200"

    monkeypatch.setattr(verification, "_head_probe", fake_probe)
    cache = {}

    report = verification.verify_cycle(
        1,
        ["marketing", "product"],
        dept_outputs,
        "synth cites https://ok.test/a",
        verification.VerificationConfig(min_sources=1, resolve=True),
        cache=cache,
    )

    assert report["truncated"] == 7
    assert len(report["sources"]) == verification.MAX_URLS_PER_CYCLE
    assert report["per_dept"]["marketing"]["ok"] is True
    assert report["per_dept"]["product"] == {"counted": 1, "min": 1, "ok": True}
    assert report["rate"] == pytest.approx(49 / 50)
    assert len(calls) == verification.MAX_URLS_PER_CYCLE

    verification.verify_cycle(
        2,
        ["marketing", "product"],
        dept_outputs,
        "",
        verification.VerificationConfig(min_sources=1, resolve=True),
        cache=cache,
    )
    assert len(calls) == verification.MAX_URLS_PER_CYCLE

    # Clamp-skips are never cached: a skip describes the cycle's time budget, not the
    # URL — a later cycle must be free to probe it.
    assert not any(kind == "timeout" for (_, _, kind) in cache.values())

    monkeypatch.setattr(verification, "_head_probe", lambda url: (None, "timeout"))
    degraded = verification.verify_cycle(
        3,
        ["marketing"],
        {"marketing": "https://one.test/a https://two.test/a"},
        "",
        verification.VerificationConfig(min_sources=2, resolve=True),
        cache={},
    )
    assert degraded["rate"] is None
    assert degraded["ok"] is True
    assert {s["status"] for s in degraded["sources"]} == {"unverified"}


def test_unchecked_citations_never_count_when_probes_ran(monkeypatch):
    # Padding hole: 60 cited URLs, every probed one is dead — the 10 beyond the cap
    # must not count toward the minimum just because they were never checked.
    monkeypatch.setattr(verification, "_head_probe", lambda url: (404, "HTTP 404"))
    flood = " ".join(f"https://fake.test/{i}" for i in range(60))

    report = verification.verify_cycle(
        1, ["marketing"], {"marketing": flood}, "",
        verification.VerificationConfig(min_sources=3, resolve=True), cache={},
    )

    assert report["per_dept"]["marketing"] == {"counted": 0, "min": 3, "ok": False}
    assert report["ok"] is False
    assert report["truncated"] == 10


def test_fair_cap_prevents_flood_starving_another_dept(monkeypatch):
    # One department floods 60 URLs; the other cites 3 good ones. Round-robin
    # allocation guarantees the small department's sources are all probed.
    monkeypatch.setattr(verification, "_head_probe", lambda url: (200, "HTTP 200"))
    dept_outputs = {
        "solve": " ".join(f"https://flood.test/{i}" for i in range(60)),
        "marketing": "https://a.test/1 https://a.test/2 https://a.test/3",
    }

    report = verification.verify_cycle(
        1, ["solve", "marketing"], dept_outputs, "",
        verification.VerificationConfig(min_sources=3, resolve=True), cache={},
    )

    assert report["per_dept"]["marketing"] == {"counted": 3, "min": 3, "ok": True}
    assert len(report["sources"]) == verification.MAX_URLS_PER_CYCLE
    assert report["truncated"] == 13


def test_verify_cycle_offline_and_min_sources_zero():
    report = verification.verify_cycle(
        1,
        ["marketing"],
        {"marketing": "https://a.test/x"},
        "",
        verification.VerificationConfig(min_sources=2, resolve=False),
    )
    assert report["rate"] is None
    assert report["ok"] is False
    assert report["per_dept"]["marketing"] == {"counted": 1, "min": 2, "ok": False}
    assert report["sources"][0]["status"] == "unverified"

    exempt = verification.verify_cycle(
        1,
        ["marketing"],
        {"marketing": ""},
        "",
        verification.VerificationConfig(min_sources=0, resolve=False),
    )
    assert exempt["ok"] is True
