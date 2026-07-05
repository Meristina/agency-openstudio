# Contract — i18n catalog (shell ↔ child screens)

The single localization mechanism for every Brick 7 surface (spec FR-009). Child
screens add keys; they never add mechanisms.

## Shape

```ts
// i18n/catalog.ts — the ONLY place keys are declared
export type CatalogKey =
  | "nav.home" | "nav.brief" | "nav.missions" | "nav.library"
  | "nav.import" | "nav.export" | "nav.models" | "nav.settings" | "nav.console"
  | "home.question"            // "What do you want to produce?"
  | "state.loading" | "state.empty" | "state.error"
  | "state.comingSoon.title" | "state.comingSoon.body" | "state.backHome"
  | "state.notFound.title" | "state.notFound.body"
  | "conn.unreachable" | "conn.retrying"
  | "context.none" | "context.unassigned"
  | "lang.label" | "lang.en" | "lang.fr";
  // …child screens extend this union in their own cycles

// i18n/en.ts / i18n/fr.ts — typed complete: a missing key fails `tsc`
const en: Record<CatalogKey, string> = { /* … */ };
```

## Rules

1. **Keys**: dot-namespaced, lower camel per segment; first segment is the owning
   surface (`nav`, `home`, `brief`, `library`, `state`, `conn`, `context`, `lang`).
2. **Completeness**: `en.ts` and `fr.ts` are `Record<CatalogKey, string>` — both
   compile-time complete; a Vitest test additionally asserts key-set equality and
   that no rendered string leaks a raw key (SC-004).
3. **Fallback**: `t(key)` returns the `en` value when the active locale's value is
   missing at runtime (defensive path; should be unreachable given typing) — never a
   raw key, never empty (spec edge case).
4. **Interpolation**: `{name}` placeholders; `t(key, { name })` substitutes; a
   placeholder present in one language's string must be present in the other's.
5. **Persistence & default**: locale persisted in `localStorage` preferences;
   first-run default from `navigator.language` (`fr*` → `fr`, else `en`) (FR-008).
6. **Scope**: interface text only — deliverable/mission content language is a brief
   parameter owned by S2's spec, never coupled to the UI locale (FR-009a).
7. **English repository**: keys, code, and comments in English; only `fr.ts` values
   are French (Constitution XI).

## API surface

```ts
useI18n(): {
  locale: "en" | "fr";
  setLocale(l: "en" | "fr"): void;   // persists + re-renders in place
  t(key: CatalogKey, params?: Record<string, string | number>): string;
}
```
