import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PREFS_KEY } from "../../i18n/catalog";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import { BRIEF_DRAFT_KEY } from "../brief/briefDraft";
import { ASSOCIATION_KEY } from "../import/associationStore";
import { FOLLOW_POINTER_KEY } from "../missions/followPointer";
import ResetSection from "./ResetSection";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({ clients: [] }),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.restoreAllMocks();
});

function renderReset() {
  return render(<I18nProvider><ClientContextProvider><ResetSection /></ClientContextProvider></I18nProvider>);
}

describe("ResetSection", () => {
  it("confirms before clearing local preference keys only", () => {
    const fetchSpy = vi.spyOn(window, "fetch");
    for (const key of [ASSOCIATION_KEY, BRIEF_DRAFT_KEY, FOLLOW_POINTER_KEY]) localStorage.setItem(key, "x");
    localStorage.setItem("selection-store", "keep");
    renderReset();

    fireEvent.click(screen.getByRole("button", { name: "Reset preferences" }));
    fireEvent.click(screen.getByRole("button", { name: "Reset preferences" }));

    // The one-off keys are gone; unrelated same-origin data survives.
    for (const key of [ASSOCIATION_KEY, BRIEF_DRAFT_KEY, FOLLOW_POINTER_KEY]) expect(localStorage.getItem(key)).toBeNull();
    expect(localStorage.getItem("selection-store")).toBe("keep");
    // Live reset re-seeds language back to its default (no reload needed); no server call.
    expect(JSON.parse(localStorage.getItem(PREFS_KEY) || "{}")).toMatchObject({ locale: "en" });
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(screen.getByText("Local preferences reset.")).toBeTruthy();
  });

  it("dismisses without changing storage", () => {
    localStorage.setItem(FOLLOW_POINTER_KEY, "x");
    renderReset();
    fireEvent.click(screen.getByRole("button", { name: "Reset preferences" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(localStorage.getItem(FOLLOW_POINTER_KEY)).toBe("x");
  });
});
