# Quickstart: Verifiable Internet (Enforced Source Postcondition)

**Feature**: `003-verifiable-sources`

## Run the offline suites (no network, no CLI, no Node, no GPU)

```bash
# agencykit (brain) suite — includes the new verification tests
cd agencykit && pytest tests/ -q

# studio suite — includes the server verification-field tests
cd .. && pytest tests/ -q

# GUI tests
cd app/studio && npx vitest run
```

The liveness probe is a module seam (`agency_cli.verification`) monkeypatched in every
test — the suites make zero network calls.

## Try it from the CLI (validated engine: claude-code)

```bash
# Default: gate ON, offline — counts cited sources, min 3 per department
agency run "position and launch product X"

# Online verification: liveness-check every cited URL (dedicated network opt-in)
agency run "position and launch product X" --resolve-sources

# Stricter gate / disabled gate
agency run "…" --min-sources 5
agency run "…" --min-sources 0        # byte-identical pre-feature behavior
```

What you'll see: a `verify` step after each inspection; if a department cites fewer
counted sources than the minimum, the synthesis is re-run with the verification
failures as required fixes (existing veto loop). The mission folder's
`missions/<id>/dossier.md` gains a **Source verification** section (rate, per-dept
table, offending sources/claims).

## Try it from the studio GUI

```bash
agency-studio          # binds 127.0.0.1
cd app/studio && npm run dev
```

1. Launch a mission; optionally check **"Verify sources online"**.
2. Watch the timeline: a verify step follows each inspection.
3. Open the mission detail: verified-source rate headline (or
   "unverified — resolution not enabled" when the toggle was off), per-department
   counts, per-source statuses.

## Prove the headline done-conditions (SC-001 / SC-002)

```bash
# Offline demonstration used in tests: fake the engine so a department output cites
# nothing; assert the loop re-enters with verification fixes and the dossier's
# verification.final.ok is false with the offending department named.
cd agencykit && pytest tests/test_engine.py -k verification -q
```

Then load any completed mission in the GUI and confirm the rate is displayed — both
halves of the brick's definition of done.
