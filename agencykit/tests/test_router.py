"""Tests for the keyword router (`agency_kit.router.keyword_classify`).

This is the dependency-free fallback used by `agency run --dry-run` and by the
engine when its CLI routing returns unparseable output. The LLM `classify()` was
removed with the SDK path.
"""

from agency_kit.router import keyword_classify


def test_returns_list_and_defaults_to_product():
    assert keyword_classify("something with no keywords at all") == ["product"]


def test_detects_single_domain():
    assert keyword_classify("write a marketing campaign") == ["marketing"]
    assert keyword_classify("debug this crash") == ["solve"]


def test_solve_leads_when_matched():
    # solve is appended first (canonical order) when a solve keyword is present.
    route = keyword_classify("debug and then build a product feature")
    assert route[0] == "solve"
    assert "product" in route


def test_does_not_over_route_solve():
    """Guardrail: solve is problem-led — a create/brand/research goal must NOT pull in solve.

    NB: keyword_classify detects solve only via English tokens
    (solve/debug/fix/architect/algorithm/technical/implement/refactor). A naturally
    phrased problem goal (e.g. French "pourquoi perd-on 30% de clients") relies on the
    engine's CLI router, not this offline fallback — so the positive case uses a
    keyword-bearing goal.
    """
    # Negative — creation / branding never routes solve.
    assert "solve" not in keyword_classify(
        "étude de marché pour créer une application antigaspillage au Maroc"
    )
    assert "solve" not in keyword_classify(
        "branding pour Meristina avec un budget serré"
    )
    # Positive — detection still works when there genuinely is a problem to fix.
    assert "solve" in keyword_classify("debug our failing checkout flow")
