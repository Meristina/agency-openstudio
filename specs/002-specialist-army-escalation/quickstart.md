# Quickstart: The Specialist Army Plays

## Run a marketing mission with the army (default behavior once shipped)

```bash
# Escalation is ON by default — nothing to configure.
agency run "Position and launch our B2B analytics product in the EU market"

# Console shows the escalation steps inside the marketing department:
#   [claude-code] routing... marketing
#   [claude-code] marketing: selecting specialists... officer-2-strategy + soldier-stp, soldier-positioning
#   [claude-code] marketing: commander-marketing... done
#   [claude-code] marketing: officer-2-strategy... done
#   [claude-code] marketing: soldier-stp... done
#   ...
```

## Read the trace in the dossier

```bash
agency missions                          # find the mission id
cat missions/<id>/dossier.md             # or the JSON store entry
```

Look for the `escalation` block: per department — `budget`, `consumed`, `est_tokens`
(advisory), the router's `selection` with a rationale per specialist, and one
`invocations` entry per specialist call (task + output, or an explicit `skipped` reason).

## Opt out / tune the budget

```bash
agency run "quick sanity mission" --no-escalation        # today's doctrine-only behavior
agency run "big launch" --escalation-budget 10           # allow a deeper chain
agency run "tiny check" --escalation-budget 0            # ≡ --no-escalation
```

From the studio, the mission request accepts an optional field (default on):

```json
{ "goal": "…", "escalation": { "enabled": false } }
```

## Event / comms mission (virtual officers)

```bash
agency run "Plan the product launch event in Paris for 300 B2B guests"
# comms department fields phase-officers from its commander doctrine
# (e.g. comms/O6-events, traced with virtual: true) + shared soldiers.
```

## Run the offline suite (merge gate)

```bash
cd agencykit && pytest tests/ -q            # includes test_escalation.py — no network,
                                            # no CLI, no Node, no GPU
pytest tests/ -q                            # studio suite at repo root (passthrough test)
```

Key assertions to know about:
- `escalation=None` reproduces today's calls byte-for-byte (the Principle X regression).
- `consumed <= budget` in every trace; skips are explicit.
- Veto-loop behavior is asserted identical with escalation on and off.
