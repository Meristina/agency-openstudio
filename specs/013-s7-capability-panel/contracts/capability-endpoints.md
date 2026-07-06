# Contract — Capability Endpoints (EXISTING, consumed read-only by S7)

**Status**: Pre-existing Brick 4 contract (done `6e71879` / #6). **S7 changes none of it** — this
document pins what S7 depends on so the frontend is verified against the real server behavior.
No endpoint, shape, status code, or precedence below is added or modified by S7.

## GET `/api/capabilities[?refresh=1]`

- **Handler**: `agency_studio/server.py:854` → `_handle_capabilities` (`:1791`).
- **Purpose**: Return the passive capability inventory (all families, all entries, resolved
  active model, stored selection, env override). `?refresh=1` forces a re-probe.
- **Response 200** (`CapabilityInventory`):
  ```jsonc
  {
    "generated_at": "<iso-8601>",
    "families": [
      {
        "family": "image",              // Family code — NEVER rendered raw by S7
        "selectable": true,             // true → S7 renders a chooser; false → read-only status
        "selected": "flux2-klein-4b",   // operator's stored standing default, or null (= built-in default)
        "selected_stale": false,        // stored selection no longer available
        "env_override": null,           // env var NAME currently overriding, or null
        "active": "flux-schnell",       // resolved active model id (env > selection > default)
        "entries": [
          {
            "id": "flux-schnell",       // form value only — NEVER rendered raw by S7
            "label": "FLUX schnell",    // product name — shown as-is
            "family": "image",
            "cost": "free",             // "free" | "paid" | "free_paid"
            "availability": "available",// "available" | "unavailable"
            "reason": null,             // raw code when unavailable — NEVER rendered raw
            "enablement": null,         // prose hint when unavailable
            "tier": "LOCAL",            // LOCAL | LOCAL_GPU | API — NEVER rendered raw
            "note": "…",
            "default": true,
            "key_env": null             // paid entries: env var NAME to set — NAME only, NEVER a value
          }
        ]
      }
    ]
  }
  ```
- **S7 consumption**: read-only via `fetchCapabilities(refresh)` (`app/studio/src/api.ts:287`).
  S7 renders plain-language derivations only (see `capability-panel-model.md`); it never renders
  `family`, `entry.id`, `tier`, `reason`, or a `key_env` value.

## PUT `/api/capabilities/selection`

- **Handler**: `agency_studio/server.py:918` → `_handle_select_capability` (`:1796`).
- **Request**: `{ "family": "<Family>", "id": "<entry id>" }`.
- **Effect**: Sets the family's **standing default** in the existing `SelectionStore`
  (`agency_studio/capabilities.py:403`) and invalidates the lazy singletons bound to that family
  (`_invalidate_selection_consumers`, `:1818`) so the choice is applied on the **next production**
  (no live hot-swap of an already-warm model).
- **Response 200**: the updated `CapabilityFamilyView` (same shape as one `families[]` element).
- **S7 consumption**: `selectCapability(family, id)` (`api.ts:293`). S7 only offers **available**
  options (an unavailable option is never selectable — FR-008).

## DELETE `/api/capabilities/selection/{family}`

- **Handler**: `agency_studio/server.py:934` → `_handle_clear_capability` (`:1809`).
- **Effect**: Removes the family's stored selection → the built-in default resumes; also
  invalidates the family's lazy consumers.
- **Response**: 200/204.
- **S7 consumption**: `clearCapability(family)` (`api.ts:304`) — the "go back to the built-in
  default" action (FR-005).

## Inherited invariants S7 relies on (unchanged)

- **Precedence**: env > selection > default. A non-null `env_override` means the environment is in
  force regardless of `selected` (S7 surfaces this honestly — FR-007).
- **Secrets**: `key_env` is a variable **name**; the API never returns a key value and S7 never
  renders/accepts one (FR-010; Constitution VI).
- **No S7 mutation of server behavior**: probing/aggregation logic, the `SelectionStore` shape,
  and the precedence are untouched (FR-018). No new endpoint is added by S7.
