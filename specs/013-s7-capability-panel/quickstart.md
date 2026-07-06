# Quickstart — S7 Capability & Model Panel

**Feature**: Capability & Model Panel (Brick 7 · Screen S7) · **Branch**: `013-s7-capability-panel`

A developer orientation for implementing/reviewing S7. **Pure frontend** over the existing
Brick 4 endpoints — no server, endpoint, persistence, dependency, or pytest change.

## What S7 does

Replaces the **raw developer capability embed** on `#/models` with a plain-language, EN/FR,
WCAG-AA operator screen: *see what this machine can produce* (all 9 families) and *choose the
model* for the 7 selectable families (the 2 non-selectable families are read-only status). Local/
free is the default; cloud/paid is an explicit opt-in; keys stay environment-only (name shown,
never a value).

## Where it lives

```
app/studio/src/
  screens/models/
    ModelsScreen.tsx     # loads inventory, renders families, re-check, error/empty, machine-level
    FamilyCard.tsx       # per-family: chooser (selectable) or read-only (non-selectable); honesty notes
    ModelOption.tsx      # per-option: label, free/local vs paid/cloud, availability, default, key-name hint
    capabilityModel.ts   # PURE raw→plain transform (family map, cost, status, reason, override/stale, key NAME)
  screens/Models.tsx     # now renders <ModelsScreen /> (or Shell imports ModelsScreen directly)
  components/Capabilities.tsx   # UNCHANGED — developer Console keeps the raw panel (coexistence)
  i18n/{catalog,en,fr}.ts       # + models.* keys (see contracts/capability-panel-model.md §3)
  api.ts                        # UNCHANGED — reuse fetchCapabilities / selectCapability / clearCapability
```

The `models` route is already `status:"shipped"`, `taxonomyScoped:false` — **no router change**.

## Backend it consumes (already shipped — do not modify)

- `GET /api/capabilities[?refresh=1]` → `CapabilityInventory` (every field S7 needs already emitted:
  `selectable`, `active`, `env_override`, `selected`, `selected_stale`, per-entry `cost` /
  `availability` / `reason` / `enablement` / `default` / `key_env`).
- `PUT /api/capabilities/selection` `{family,id}` → set standing default (applied next production).
- `DELETE /api/capabilities/selection/{family}` → revert to built-in default.

See `contracts/capability-endpoints.md` (existing) and `contracts/capability-panel-model.md` (new).

## Build order (suggested)

1. `capabilityModel.ts` + `capabilityModel.test.ts` — the pure transform and its invariants
   (family map for all 9; cost/status/reason mapping; selectable→chooser vs readonly;
   env-override & stale honesty; enablement hint = env-var NAME only). All offline.
2. i18n keys — add `models.*` to `catalog.ts`, `en.ts`, `fr.ts` (EN/FR parity).
3. `ModelOption.tsx`, `FamilyCard.tsx`, `ModelsScreen.tsx` — render the model; wire
   `selectCapability` / `clearCapability` / `fetchCapabilities(true)`.
4. Point `screens/Models.tsx` (or Shell) at `ModelsScreen`; rewrite/relocate `Models.test.tsx`
   for the plain-language surface (preserve/strengthen the no-secret assertion).
5. Component tests (`ModelsScreen.test.tsx`, `FamilyCard.test.tsx`).

## Verify

```
cd app/studio
npm run test        # Vitest — model + screen + family + relocated Models tests
npm run build       # tsc + vite production build (typed CatalogKeys must resolve)
```

Manual smoke (optional, with the studio running at 127.0.0.1):
- Open `#/models`: every family named in plain language with a plain status; no raw model id /
  family code / MIME / path anywhere.
- A selectable family: change the model → "saved — applies on your next production"; revert to
  default; reload → choice persists.
- A paid/cloud option: marked paid/cloud, shows "set `$VAR` to enable" (name only), **no key
  field**; selecting it sends nothing.
- Set an env override for a family → the panel shows "your environment is deciding this one".
- Switch EN↔FR → every string follows immediately.
- Switch client context → panel content is identical (machine-level).

## Guardrails (must hold)

- No `api.ts`/server/persistence change; developer Console byte-identical.
- No secret entered/shown/stored/sent; `key_env` → variable **name** only.
- env>selection>default precedence honored and shown honestly (override / stale).
- Root pytest suite untouched and green; `npm run build` clean with typed catalog keys.
