# Mission Console (`app/studio`)

React 19 + Vite + TypeScript GUI for Agency Studio. Talks to the stdlib Python
server (`agency_studio/server.py`) over HTTP/SSE.

## Develop

```bash
# 1. start the Python server (serves the API on 127.0.0.1:8765)
agency-studio                    # from the repo root

# 2. start the Vite dev server (HMR); /api is proxied to the server above
cd app/studio
npm install
npm run dev                      # → http://127.0.0.1:5173
```

The dev server proxies `/api/*` to `http://127.0.0.1:8765`. Override the target
with `AGENCY_STUDIO_API=http://127.0.0.1:9000 npm run dev`.

## Build (served by the Python server)

```bash
cd app/studio
npm run build                    # → app/studio/dist/
```

`agency_studio/server.py` serves `app/studio/dist/` automatically when it
exists, so after a build `agency-studio` serves the GUI same-origin (no proxy).

## Layout

- `src/types.ts` — wire types mirroring the server's SSE event frames.
- `src/api.ts` — typed client; `runMission` streams the POST SSE response.
- `src/App.tsx` — scaffold Console: new-mission box + live timeline + history.
