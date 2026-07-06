import { afterEach, describe, expect, it } from "vitest";
import { navigate, parseHash, routes } from "./router";
import { en } from "../i18n/en";

afterEach(() => {
  window.location.hash = "";
});

describe("router", () => {
  it("contains the full inventory with distinct hashes and catalog title keys", () => {
    expect(routes.map((route) => route.id)).toEqual(["home", "brief", "missions", "library", "import", "export", "models", "settings", "console"]);
    expect(new Set(routes.map((route) => route.hash)).size).toBe(routes.length);
    for (const route of routes) expect(en[route.titleKey]).toBeTruthy();
    expect(routes.find((route) => route.id === "brief")?.status).toBe("shipped");
  });

  it("maps empty hash to home and unknown hash to notFound", () => {
    expect(parseHash("").route?.id).toBe("home");
    expect(parseHash("#/nope").notFound).toBe(true);
  });

  it("preserves brief search params and navigates", () => {
    expect(parseHash("#/brief?intent=hello").search).toBe("intent=hello");
    navigate("#/library");
    expect(parseHash().route?.id).toBe("library");
  });
});
