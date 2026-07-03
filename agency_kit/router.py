"""agency-kit — keyword router.

A dependency-free keyword classifier. Reads a mission goal and returns the
ordered department list to deploy (solve / product / marketing / finance / comms /
data / ops / people / tech), in canonical (solve-first) order.

The engine path (`agency_cli/engines/cli_engine.py`) routes via the local agent
CLI and falls back to `keyword_classify` when the CLI returns unparseable output.
`agency run --dry-run` uses it directly to preview a route with no model call.
"""


def keyword_classify(goal: str) -> list:
    """Keyword heuristic — no model call. Returns an ordered department list.

    Solve leads when matched (problem-solving is the foundational diagnosis), then
    product → marketing → finance → comms → data → ops → people → tech, mirroring
    the canonical order in `departments.DEPT_NAMES`. Falls back to ``["product"]``
    when nothing matches.
    """
    lower = goal.lower()
    padded = f" {lower} "  # word-boundary guard for short tokens (bi, ml)
    depts = []
    # solve leads — problem-solving is the foundational diagnosis (canonical order).
    if any(w in lower for w in ("solve", "debug", "fix", "architect", "algorithm", "technical", "implement", "refactor")):
        depts.append("solve")
    if any(w in lower for w in ("product", "feature", "roadmap", "jtbd", "pmf", "discovery", "prioriti")):
        depts.append("product")
    if any(w in lower for w in ("market", "campaign", "content", "launch", "position", "seo", "brand")):
        depts.append("marketing")
    if any(w in lower for w in (
        "finance", "financ", "budget", "forecast", "roi", "pricing", "prix",
        "commercial", "pipeline", "closing", "contrat", "deal", "vente",
        "revenu", "chiffre d'affaires", "cash flow", "rentabilit", "p&l",
        "investor", "investisseur", "business case", "viabilit",
    )):
        depts.append("finance")
    if any(w in lower for w in (
        "comms", "communication", "press release", "communiqué", "crise",
        "crisis", "media relation", "esg", "csrd", "public affairs", "event comms",
        "événement", "réputation", "reputation", "porte-parole",
    )):
        depts.append("comms")
    if any(w in lower for w in (
        "data", "data pipeline", "warehouse", "analytics", "dashboard",
        "etl", "llm", "rag", "embedding", "dbt", "streaming", "lakehouse",
        "donnée", "données", "modèle de données",
    )) or any(f" {tok} " in padded for tok in ("bi", "ml")):
        depts.append("data")
    if any(w in lower for w in (
        "ops", "opérations", "process", "pmo", "procurement", "achat",
        "nis2", "ai act", "dora ict", "compliance", "conformité", "risque",
        "lean", "vsm", "bcp", "continuité",
    )):
        depts.append("ops")
    if any(w in lower for w in (
        "people", "rh", "hr", "talent", "recrutement", "recruiting",
        "org design", "onboarding", "formation", "l&d", "compensation",
        "salaire", "culture", "dei", "succession", "effectif",
    )):
        depts.append("people")
    if any(w in lower for w in (
        "tech", "architecture", "devops", "infrastructure", "cloud", "sécurité",
        "security", "kubernetes", "ci/cd", "iac", "terraform", "soc2",
        "owasp", "zero trust", "finops", "slo", "sli", "dora metrics",
    )):
        depts.append("tech")
    return depts or ["product"]
