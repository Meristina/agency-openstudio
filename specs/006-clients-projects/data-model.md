# Data Model: Clients & Projects (Brick 6)

## Overview

The taxonomy is **derived state layered over the existing store**. Only two
things are ever written: (a) three optional fields inside a *new* mission's own
dossier, and (b) the side-band registry file. Clients, projects, and campaigns
have no records of their own — they exist as the distinct values observed
across resolved mission attributions (implicit creation, per spec assumptions).

## Stored shapes

### Dossier additions (new missions only — additive, all optional)

```json
{
  "...existing dossier fields...": "unchanged",
  "client":   "Acme",
  "project":  "Rebrand",
  "campaign": "Spring Launch"
}
```

- Type: string; absent when not supplied. Never written into pre-existing
  dossiers (FR-007 byte-identity).
- Written by the server post-completion via `store.save()` (research D1);
  carried through the checkpoint envelope so resume preserves them.

### Taxonomy registry — `~/.agency/taxonomy.json` (research D2)

```json
{
  "version": 1,
  "overrides": {
    "20260705-101500-000001-acme-rebrand": {
      "client": "Acme", "project": "Rebrand", "campaign": null
    }
  },
  "names": {
    "client:acme": "Acme",
    "project:acme/rebrand": "Rebrand",
    "campaign:acme/rebrand/spring launch": "Spring Launch"
  }
}
```

- `overrides`: mission_id → full attribution triple (campaign may be null).
  Setting an override replaces the triple; `clear` deletes the entry.
- `names`: normalized key → first-typed display form (FR-006).
- Missing/corrupt file resolves as an empty registry (never an error).
- Writes are atomic: tmp file + `os.replace` in the same directory.

## Validation rules (API boundary)

| Rule | Behavior |
|---|---|
| Trim whitespace; empty after trim | treated as absent (never an error) |
| Length > 120 chars | HTTP 400 |
| Control characters | HTTP 400 |
| Non-string JSON value | treated as absent (same tolerance as `_str_field`) |
| Campaign without project (at tag time) | allowed — missing levels fall back to defaults (spec edge case) |

## Derived entities

### MissionAttribution (resolved, never stored as such)

`resolve(dossier, registry) -> {client, project, campaign}`; resolution order
(clarified 2026-07-05):

1. `registry.overrides[mission_id]` — if present, wins entirely.
2. Dossier fields `client`/`project`/`campaign` — each used when present.
3. Derived defaults for whatever is still missing:
   - `project_root` stamp present → project = final path component of the
     canonical stamp, client = `"Studio"`, campaign = none.
   - No stamp → client = `"Studio"`, project = `"Unassigned"`, campaign = none.

Invariant: resolution is **total** — every readable dossier yields exactly one
attribution (FR-002, SC-002); corrupt dossiers are skipped like
`store.list_missions` does.

### Client / Project / Campaign (aggregates)

Identity = normalized name key, namespaced down the hierarchy (research D5).
Each segment is percent-escaped before joining (`%` → `%25`, `/` → `%2F`) so a
name containing the `/` separator cannot collide across levels (`a/b` + `c`
stays distinct from `a` + `b/c`); names remain unrestricted beyond the
validation rules above.

- Client key: `esc(casefold(trim(name)))`
- Project key: `<client key>/<esc(casefold(trim(name)))>` — same-named projects
  under different clients stay distinct (spec edge case).
- Campaign key: `<project key>/<esc(casefold(trim(name)))>`

Display name = `names[key]` when present, else the first-observed raw value
during the scan. Mission count = number of missions resolving to the node
(a client's count includes all its projects' missions).

## Relationships

```text
Client (implicit, "Studio" default) 1 ──▶ * Project ("<workspace dir>" / "Unassigned" defaults)
Project 1 ──▶ * Campaign (optional level)
Project 1 ──▶ * Mission  (via resolved attribution — exactly one project each)
Mission 1 ──▶ * Deliverable (existing; inherits the mission's attribution, FR-003)
Registry.overrides * ──▶ 1 Mission (by mission_id; may reference a pruned/absent
                                    mission — ignored at scan time, never an error)
```

## State transitions

Mission attribution states (per mission):

```text
DERIVED  ──(new mission tagged at start)──▶ FIELD-TAGGED
DERIVED  ──(POST assign)─────────────────▶ OVERRIDDEN
FIELD-TAGGED ──(POST assign)─────────────▶ OVERRIDDEN
OVERRIDDEN ──(POST assign {clear})───────▶ FIELD-TAGGED or DERIVED (whichever underlies)
```

No transition ever writes a pre-existing dossier; only the registry (and, once,
the new mission's own dossier) is written.

## Scale assumptions

Hundreds to low thousands of missions per machine (the store's own documented
assumption). The taxonomy scan is O(missions) JSON reads per request — the same
cost class as the existing `list_missions`; no index needed at this scale.
