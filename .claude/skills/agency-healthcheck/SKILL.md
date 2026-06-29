---
description: Audit the agency-kit arborescence for stale department references — verifies all 9 departments are correctly wired across every key file.
argument-hint: "(no argument needed — audits the full repo)"
---

# /agency.healthcheck — agency-kit arborescence audit

Verifies that every key file in the repo correctly reflects the **9-department architecture**
(product · marketing · solve · finance · comms · data · ops · people · tech).
No mission required. Run after any structural change to the kit.

## Canonical 9-department list

```
product · marketing · solve · finance · comms · data · ops · people · tech
```

## Checklist — file by file

For each file below, read it and verify the items listed. Report ✅ clean or ❌ stale
with the exact line(s) to fix.

---

### Python engine — `agency_kit/`

| File | What to verify |
|---|---|
| `agency_kit/commander.py` | 9 `try/except` import guards; 9 `_HAS_*` flags; `classify` tool description lists all 9; docstring EXECUTE chain has all 9 branches |
| `agency_kit/inspector.py` | Docstring and instructions list 9 kits and 9 domains |
| `agency_kit/mission.py` | No hardcoded department list — fully generic |
| `agency_kit/models.py` | No department refs — purely model config |
| `agency_kit/parallel.py` | `_SEQUENTIAL_AFTER` lists 7 entries; `_get_commanders()` imports and returns all 9 pairs; docstring stages 1–9 present |
| `agency_kit/router.py` | `ROUTER_INSTRUCTIONS` lists all 9 departments; docstring correct |
| `agency_kit/store.py` | No department refs |
| `agency_kit/web.py` | No department refs |

---

### CLI — `agency_cli/`

| File | What to verify |
|---|---|
| `agency_cli/cli.py` | No hardcoded 4-dept list |
| `agency_cli/integrations.py` | Slash-command catalogue lists all 9 dept commands |
| `agency_cli/sync_payload.py` | No hardcoded dept list |

---

### Agent docs — `agents/` (root source)

| File | What to verify |
|---|---|
| `agents/commander-agency.md` | Frontmatter, table, chain-of-command diagram, EXECUTE steps — all 9 departments present |
| `agents/inspector-agency.md` | 9 kits, 9 domains listed |
| `agents/router-agency.md` | "nine departments", dept list (9), single-dept examples (9), valid dept array (9), no "all four/nine reflexively" |

**Sync invariant:** `agents/router-agency.md` must be byte-for-byte identical to
`agency_cli/payload/agents/router-agency.md` (enforced by `test_payload_router_matches_source`).

---

### Payload mirror — `agency_cli/payload/agents/`

Same 3 files as `agents/` above — must match root exactly after `agency sync`.

---

### Skills — `skills/`

| File | What to verify |
|---|---|
| `skills/cross-dept-synthesis/SKILL.md` | Frontmatter lists 9 departments |
| `skills/mission-dossier/SKILL.md` | `dept_outputs` schema has 9 entries |
| `skills/routing/SKILL.md` | "nine departments", 9-row table, 9-step pipeline, no reflexive "all nine" |
| `skills/routing/agents/openai.yaml` | `default_prompt` lists all 9 departments |

---

### Commands — `.agency/commands/`

12 commands must exist: `mission.md`, `frame.md`, `inspect.md`,
plus one per department: `product.md`, `marketing.md`, `solve.md`, `finance.md`,
`comms.md`, `data.md`, `ops.md`, `people.md`, `tech.md`.

Note: `goal` and `healthcheck` are Claude Code skills (`.claude/skills/`), not
agency-kit commands — they must NOT appear in `.agency/commands/`.

---

### Docs & config

| File | What to verify |
|---|---|
| `docs/ARCHITECTURE.md` | Overview, chain-of-command, routing table — all 9 departments |
| `README.md` | Intro, architecture diagram, routing table (9 rows), `[all]` comment, config table (9 kits), "nine kits" section, "Why nine kits" heading |
| `GUIDE.md` | §1 "nine optional", §2 diagram (9 commanders), §4 Phase 1 (9 depts), §5 dossier schema (9 dept_outputs), §8 catalogue (12 commands), §11 kit list (9) |
| `CLAUDE.md` | Test architecture note: "nine department kits" + all 9 listed |
| `.env.example` | Department overrides section: 9 kits with env var prefixes |
| `pyproject.toml` | 9 optional-dependency extras + `[all]` with 9 kits |
| `Roadmap.md` | Roadmap counts reflect actual done/pending state (not a stale ref — verify intent) |
| `.gitignore` | `missions/`, `.env`, `*.egg-info/` present |
| `requirements.txt` | Core dep only, no dept refs |
| `MANIFEST.in` | No dept refs |

---

### Tests — `tests/`

| File | What to verify |
|---|---|
| `tests/conftest.py` | Stub loop covers all 9: `("product","marketing","solve","finance","comms","data","ops","people","tech")` |
| `tests/test_structure.py` | `_HAS_*` flags check: all 9 flags listed |
| `tests/test_mission_harness.py` | Docstring says "nine department-kit stubs" |
| `tests/test_cli.py` | No hardcoded 4-dept list |

---

## Pass criteria

Every file above reports ✅. Then run:

```bash
pytest tests/ -v
```

All tests must pass (offline, no API key). If `test_payload_router_matches_source` fails,
run `agency sync` and re-test.

## Fail protocol

For each ❌ finding: state the file, the line number, the stale text, and the correct
replacement. Fix in-place, then re-verify that file before moving on.
