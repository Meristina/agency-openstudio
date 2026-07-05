# API Contract: Capabilities & Selection

Served by the existing stdlib handler in `agency_studio/server.py`. All routes:
loopback-only bind, JSON responses via `_send_json` / `_send_error_json`
(`{"error": "..."}` shape), no CORS headers, no key values anywhere (FR-013).
Offline tests stub the registries, the OpenMontage probe, `mcp.json`, env, and the
data dir (FR-014).

## GET /api/capabilities

Full inventory + selection state. Query: `?refresh=1` forces the OpenMontage
subprocess re-probe (otherwise the per-process cache serves it).

**200 response** (shape; entries abbreviated):

```json
{
  "families": [
    {
      "family": "image",
      "selectable": true,
      "selected": "flux2-klein-4b",
      "selected_stale": false,
      "env_override": null,
      "active": "flux2-klein-4b",
      "entries": [
        {
          "id": "flux-schnell",
          "label": "FLUX.1-schnell",
          "family": "image",
          "cost": "free",
          "availability": "unavailable",
          "reason": "missing_extra",
          "enablement": "pip install 'agency-studio[media]'",
          "tier": null,
          "note": "Photoreal · 2–4 step",
          "default": true,
          "key_env": null
        }
      ]
    },
    {
      "family": "video",
      "selectable": true,
      "selected": null,
      "selected_stale": false,
      "env_override": "AGENCY_STUDIO_VIDEO_BACKEND",
      "active": "seedance-2.0",
      "entries": [
        {
          "id": "seedance-2.0",
          "label": "Seedance 2.0",
          "family": "video",
          "cost": "paid",
          "availability": "available",
          "reason": null,
          "enablement": null,
          "tier": null,
          "note": "cloud video",
          "default": true,
          "key_env": "AGENCY_STUDIO_VIDEO_API_KEY"
        }
      ]
    },
    {
      "family": "production-tools",
      "selectable": false,
      "selected": null,
      "selected_stale": false,
      "env_override": null,
      "active": "",
      "entries": [
        {
          "id": "image_selector",
          "label": "image_selector",
          "family": "production-tools",
          "cost": "free_paid",
          "availability": "available",
          "reason": null,
          "enablement": null,
          "tier": "hybrid",
          "note": "",
          "default": false,
          "key_env": null
        }
      ]
    },
    {
      "family": "mcp",
      "selectable": false,
      "selected": null,
      "selected_stale": false,
      "env_override": null,
      "active": "",
      "entries": []
    }
  ],
  "generated_at": "2026-07-05T02:00:00Z"
}
```

**Guarantees** (map to spec):

- Every family always present, even with zero available entries (edge case 1) —
  `entries` may be empty only for `mcp` with an empty/missing `mcp.json`.
- OpenMontage probe failure ⇒ `production-tools` carries a single family-level
  pseudo-entry with `reason: "catalog_error"` (edge case 2); other families
  unaffected.
- `unavailable` entries ALWAYS carry non-null `reason` + `enablement` (SC-002).
- No response field ever contains an API key value; `key_env` is the variable name
  only (SC-007).
- `env_override` non-null exactly when the family's env var is set (FR-010);
  `selected_stale` true when the persisted id is unknown or unavailable (FR-011).

**Errors**: none expected in normal operation — a broken selection store or catalog
degrades into the payload, never a 5xx (SC-005).

## PUT /api/capabilities/selection

Persist one family default (FR-006, FR-008).

**Request**: `{"family": "image", "id": "flux2-klein-4b"}`

**Responses**:

| status | body | when |
|---|---|---|
| 200 | the updated `CapabilityFamilyView` for that family | entry valid + available; store written atomically; takes effect for the next operation (no restart) |
| 400 | `{"error": "unknown family 'x'"}` | family not recognized |
| 400 | `{"error": "family 'production-tools' is inventory-only"}` | non-selectable family (clarifications) |
| 400 | `{"error": "unknown entry 'x' for family 'image'"}` | id not in that family's registry |
| 409 | `{"error": "entry unavailable", "reason": "missing_extra", "enablement": "pip install 'agency-studio[media]'"}` | entry exists but is unavailable — refusal with reason + step (FR-008, never silent) |

## DELETE /api/capabilities/selection/{family}

Clear one family's persisted selection → resolution falls back to env/default.

| status | when |
|---|---|
| 204 | cleared (idempotent: also when nothing was selected) |
| 400 | unknown or non-selectable family |

## Resolution contract (internal, not HTTP)

`capabilities.resolve(family) -> entry_id` implements FR-009:

1. family's env var set → validate against registry, **raise on unknown id**
   (fail-loud, matches `default_video_model()` today) → return it;
2. else persisted selection present AND entry currently available → return it
   (stale/unknown selections are skipped silently — FR-011);
3. else the family's built-in default (`DEFAULT_IMAGE_MODEL`, …) — with no env and
   no selection this path is **byte-identical to today** (FR-009 scenario 3,
   Constitution X).

## GUI contract (app/studio)

- `api.ts`: `fetchCapabilities(refresh?)`, `selectCapability(family, id)`,
  `clearCapability(family)` — thin fetch wrappers over the three routes, typed by
  the mirrors in `types.ts`.
- `Capabilities.tsx`: renders every family; unavailable entries show reason +
  enablement inline and are not selectable (clicking surfaces the 409 payload's
  reason — FR-008/US2-AS3); active env override renders a visible banner
  (FR-010/US3-AS2); stale selections render flagged (FR-011/US2-AS4).
