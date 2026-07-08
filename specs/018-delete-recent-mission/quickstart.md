# Quickstart — Delete a recent mission

How to exercise the feature end-to-end once implemented.

## In the GUI

1. Launch the studio: `agency-studio` → open http://127.0.0.1:8765.
2. On the home screen, find the **Travaux récents / Recent work** panel (needs ≥1 saved mission;
   run one via the brief, or `agency run "..."` from the CLI).
3. Each recent item now shows a **delete** control next to the open control.
4. Activate delete → a confirmation appears. **Cancel** leaves the item untouched.
5. Activate delete → **Confirm** → the item disappears from the list without a page reload.
6. Reload the page and open **See all / Library** — the mission is absent there too.

## Verify the API directly

```bash
# List saved missions (grab a mission_id)
curl -s http://127.0.0.1:8765/api/missions | python3 -m json.tool | grep mission_id

# Delete one → 204
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE http://127.0.0.1:8765/api/mission/<mission_id>

# Deleting again / an unknown id → 404 (client treats both 204 and 404 as "gone")
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE http://127.0.0.1:8765/api/mission/<mission_id>

# Traversal id is rejected (404), never touches the filesystem
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "http://127.0.0.1:8765/api/mission/..%2f..%2fetc"
```

## Run the tests (offline)

```bash
# Backend endpoint + store (store dir monkeypatched to tmp_path — no network)
pytest tests/test_server.py -q -k delete_mission
cd agencykit && pytest tests/ -q -k "store and delete"

# Frontend
cd app/studio && npm run test -- ResumeSection
```

## Acceptance mapping

- FR-001/002 → steps 3-4 (distinct control + confirmation, cancel is a no-op)
- FR-003/004 → step 5 (permanent removal, no reload)
- FR-005 → step 6 (absent from Library too)
- FR-007 → after deleting a followed mission, no "resume" is offered
- FR-009 → second `curl` DELETE returns 404 with no error surfaced to the user
- Security → traversal `curl` returns 404, filesystem untouched
