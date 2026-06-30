import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Agency Studio is local-first: the dev server binds loopback, and /api is
// proxied to the stdlib Python server (default 127.0.0.1:8765). The proxy keeps
// the browser same-origin in dev, so it rides the server's loopback CORS as-is.
//
// `build.outDir` is `dist/`, which `agency_studio/server.py` serves from
// `app/studio/dist` (see make_server). `.gitignore` already excludes it.
const API_TARGET = process.env.AGENCY_STUDIO_API ?? "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: false, // keep loopback Origin so server CORS accepts it
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
