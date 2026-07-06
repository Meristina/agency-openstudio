import { afterEach, describe, expect, it } from "vitest";
import { clearAssociation, defaultOnAccept, getAssociation, pruneAssociations, setAssociation } from "./associationStore";

afterEach(() => localStorage.clear());

describe("associationStore", () => {
  it("defaults to unassigned, overwrites, clears, and defaults accepted material to active context", () => {
    expect(getAssociation("x")).toBeNull();
    setAssociation("x", { client: "Acme" });
    setAssociation("x", { client: "Beta", project: "Site" });
    expect(getAssociation("x")).toEqual({ client: "Beta", project: "Site" });
    clearAssociation("x");
    expect(getAssociation("x")).toBeNull();
    defaultOnAccept("x", { client: "Acme", campaign: "Launch" });
    expect(getAssociation("x")).toEqual({ client: "Acme", campaign: "Launch" });
  });

  it("prunes entries absent from known ids", () => {
    setAssociation("keep", { client: "Acme" });
    setAssociation("drop", { client: "Beta" });
    pruneAssociations(["keep"]);
    expect(getAssociation("keep")).toEqual({ client: "Acme" });
    expect(getAssociation("drop")).toBeNull();
  });
});
