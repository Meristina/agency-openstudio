"""Single source of truth for the 9-department roster.

Imported by the keyword router (`router.keyword_classify`) and the CLI engine
(`cli_engine`) so the department names and order are defined once and can't drift
across modules.

Adding a new department: add one row to _ROSTER **and** one entry to
DEPT_DEPENDENCIES (its upstream edges). The dependency graph + `dependency_layers`
are the canonical ordering model the engine runs against (and the tests pin);
post-refactor the engine executes departments sequentially, so they have no live
parallel-scheduler consumer — they remain the documented, tested ordering contract.
"""

# Canonical ordered list — execution order matters for the pipeline.
# `solve` leads: problem-solving is the foundational diagnosis (problem definition,
# root cause, solution direction) that every other department builds against.
DEPT_NAMES: tuple = (
    "solve", "product", "marketing", "finance",
    "comms", "data", "ops", "people", "tech",
)

# Fast membership test used by cli_engine._route_via_cli and --dry-run.
VALID_DEPTS: frozenset = frozenset(DEPT_NAMES)

# Explicit dependency graph: dept -> the upstream depts whose output it consumes.
#
# This is the SINGLE place that decides the canonical ordering model. The layering
# helper (`dependency_layers`) groups a routed dept list into waves from these
# edges: depts with no unmet dependency form a wave, then feed the next. No runtime
# consumer schedules them in parallel today — the engine runs them sequentially —
# but the graph stays the authoritative, tested ordering contract.
#
# `solve` is the FOUNDATIONAL diagnosis: it frames the problem, root cause, and
# solution direction FIRST, and every other department is wired to consume it —
# so each non-solve dept lists `solve` as an upstream dependency. The edge is
# transitively redundant (everything reaches solve through product) but kept
# EXPLICIT so the graph documents that every department builds against the
# diagnosis. When `solve` is not routed, its edges are dropped (see
# `dependency_layers`) and the rest of the pipeline is unaffected.
#
# Two invariants the tests enforce:
#   1. Every edge points BACKWARD in DEPT_NAMES order, so the canonical order
#      above is always a valid topological linearisation — sequential execution
#      stays correct, parallel is purely an optimisation over it.
#   2. Keep edges MINIMAL and REAL: a dept depends on another only when it
#      genuinely needs that output as a prerequisite, not merely "everything
#      upstream". Over-declaring edges silently serialises the pipeline.
DEPT_DEPENDENCIES: dict = {
    "solve":     (),                                  # foundational diagnosis — no upstream
    "product":   ("solve",),                          # builds against the diagnosis
    "marketing": ("product", "solve"),                # positions / launches the product
    "finance":   ("product", "marketing", "solve"),   # business case & pricing build on the GTM
    "comms":     ("product", "marketing", "solve"),   # PR / press build on product + positioning
    "data":      ("product", "solve"),                # data products & pipelines for the product
    "ops":       ("product", "solve"),                # operationalises the product
    "people":    ("product", "solve"),                # staffs the org around the product
    "tech":      ("product", "solve"),                # architects / builds for the product
}


def dependency_layers(route) -> list:
    """Group a routed department list into ordered execution waves.

    Topological layering (Kahn by layers): each returned wave is a list of
    departments whose dependencies — restricted to departments also present in
    ``route`` — are all satisfied by earlier waves. Departments inside a wave are
    mutually independent and may run concurrently; waves themselves run in order.
    Within a wave, departments keep DEPT_NAMES order for deterministic output.

    A dependency on a department NOT in the route is dropped (e.g. ``comms`` waits
    only on ``product`` when ``marketing`` was never routed). The route is
    de-duplicated, keeping first occurrence.

    Raises ValueError on an unknown department or an unsatisfiable cycle.
    """
    seen: set = set()
    ordered = []
    for dept in route:                       # de-dupe, preserve first occurrence
        if dept not in seen:
            seen.add(dept)
            ordered.append(dept)

    unknown = [d for d in ordered if d not in VALID_DEPTS]
    if unknown:
        raise ValueError(f"unknown department(s) in route: {unknown}")

    route_set = set(ordered)
    done: set = set()
    remaining = [d for d in DEPT_NAMES if d in route_set]  # canonical order
    waves = []
    while remaining:
        wave = [
            d for d in remaining
            if all(dep in done for dep in DEPT_DEPENDENCIES[d] if dep in route_set)
        ]
        if not wave:  # no progress possible -> a cycle, or a dep on a missing dept
            raise ValueError(f"unsatisfiable dependency cycle in route: {remaining}")
        waves.append(wave)
        done.update(wave)
        remaining = [d for d in remaining if d not in done]
    return waves

# (name, one-line role, grade, optional-kit)
_ROSTER: tuple = (
    ("product",   "Full product lifecycle — discovery, roadmaps, JTBD, PMF, prioritisation, specs, scope",                     "elite",    "product-kit"),
    ("marketing", "Campaigns, content, positioning, brand, launch comms, SEO, growth, analytics",                             "elite",    "marketing-kit"),
    ("solve",     "Problem-solving, root-cause analysis, decision intelligence, architecture, algorithms",                    "elite",    "solve-kit"),
    ("finance",   "Business case, pricing, P&L, cash flow, commercial pipeline, closing, investor reporting, RevOps",         "elite",    "finance-kit"),
    ("comms",     "Corporate comms, PR/media, crisis management, public affairs B2G, ESG/CSRD, events",                       "elite",    "comms-kit"),
    ("data",      "Data strategy, engineering pipelines, analytics/BI, ML/LLMOps, data quality, data products",              "elite",    "data-kit"),
    ("ops",       "Process optimisation, PMO, procurement B2G, EU compliance (NIS2, AI Act, DORA ICT), risk mapping",         "elite",    "ops-kit"),
    ("people",    "Org design, talent acquisition, L&D, performance, compensation, DEI, culture, people analytics",           "elite",    "people-kit"),
    ("tech",      "Architecture, DevOps/IaC, security (OWASP, SOC2, zero trust), engineering excellence, DORA metrics",      "elite",    "tech-kit"),
)


def dept_list_text(indent: str = "  ") -> str:
    """Render the roster as a text block for inclusion in agent instruction strings."""
    return "\n".join(
        f"{indent}- {name:<12} : {role}  ({kit})"
        for name, role, _grade, kit in _ROSTER
    )
