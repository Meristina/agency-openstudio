# Quickstart: Clients & Projects (Brick 6)

Manual acceptance walkthrough once the brick is implemented. The offline suite
(`pytest` at repo root + `npm test` in `app/studio/`) is the merge gate; this
walkthrough is the human-eye check of the spec's done-when.

## 0. Prereqs

- Built GUI: `cd app/studio && npm install && npm run build`
- Start the studio from any workspace: `python -m agency_studio.cli --path .`
  (server binds `127.0.0.1` as always)

## 1. Tag a mission at start (User Story 1)

1. Open the studio, fill the mission brief.
2. Fill the new fields: Client "Acme", Project "Rebrand", Campaign
   "Spring Launch". (Leave engine/flags as usual; a dry local run is fine.)
3. Run the mission to completion.
4. Verify: `cat ~/.agency/missions/<mission_id>/dossier.json | python -m json.tool | grep -E '"client"|"project"|"campaign"'`
   shows the three fields; the `done` frame in the GUI shows the attribution.
5. Run a second mission with all three fields empty — confirm it behaves
   exactly as before the brick and lands under client "Studio", project named
   after your workspace directory (check via step 2 below).

## 2. Browse by client and by campaign (User Story 2)

1. `curl -s localhost:<port>/api/taxonomy | python -m json.tool` — expect
   "Acme" (with "Rebrand" → "Spring Launch") and "Studio" (with your
   workspace-named default project), each with correct mission counts.
2. In the GUI history, switch to grouped view: by client, drill into Acme →
   Rebrand → Spring Launch; then group by campaign.
3. `curl -s 'localhost:<port>/api/missions?client=Acme'` — only the tagged
   mission, with attribution columns. `?client=acme` (lowercase) returns the
   same (case-insensitive matching). `?client=Nobody` returns
   `{"missions": []}`.
4. Plain `curl -s localhost:<port>/api/missions` — identical shape/content to
   pre-brick behavior.

## 3. Old history folds in untouched (User Story 3)

1. Before upgrading (or using a copy of an old store): snapshot hashes —
   `find ~/.agency/missions -type f -exec shasum -a 256 {} \; | sort > /tmp/before.txt`
2. Browse `/api/taxonomy` and the grouped GUI — every old mission appears under
   the workspace-named default project (or "Unassigned" for stamp-less ones).
3. Re-hash into `/tmp/after.txt` and `diff /tmp/before.txt /tmp/after.txt` —
   empty diff (byte-identity, SC-003).

## 4. Re-assign a mission (override registry)

1. `curl -s -X POST localhost:<port>/api/mission/<old_id>/assign -d '{"client":"Acme","project":"Rebrand"}'`
2. Confirm the mission moved in `/api/taxonomy`, its dossier file hash is
   STILL unchanged, and `~/.agency/taxonomy.json` now holds the override.
3. `curl -s -X POST localhost:<port>/api/mission/<old_id>/assign -d '{"clear":true}'`
   — mission returns to its derived default group.

## 5. Offline gates

```bash
pytest                       # repo root — includes test_taxonomy.py,
                             # test_server_taxonomy.py (migration fixture +
                             # byte-identity assertion)
cd app/studio && npm test    # Vitest — form fields + TaxonomyBrowser
```

Both green with no network, no CLI agent, no GPU (Node only for the frontend
suite, per the existing frontend convention).
