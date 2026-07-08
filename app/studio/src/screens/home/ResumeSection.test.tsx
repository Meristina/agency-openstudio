import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { FOLLOW_POINTER_KEY } from "../missions/followPointer";
import ResumeSection from "./ResumeSection";

vi.mock("../../api", () => ({
  listMissions: vi.fn(),
  deleteMission: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorage.clear();
});

const missions = [
  { mission_id: "m1", goal: "First goal", route: [], iteration: 0, verdict: "PASS", delivered: true },
  { mission_id: "m2", goal: "Second goal", route: [], iteration: 0, verdict: "PASS", delivered: true },
];

function renderReady(list: unknown[] = missions) {
  vi.mocked(api.listMissions).mockResolvedValue(list as never);
  return render(<I18nProvider><ResumeSection /></I18nProvider>);
}

describe("ResumeSection — delete a recent mission", () => {
  it("deletes an item after confirmation and removes only it from the list (US1)", async () => {
    vi.mocked(api.deleteMission).mockResolvedValue(undefined);
    renderReady();
    await screen.findByText("First goal");

    fireEvent.click(screen.getByRole("button", { name: "Delete — First goal" }));
    // Confirmation appears; only "confirm" triggers the request.
    expect(screen.getByText("Delete this permanently? This can't be undone.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(api.deleteMission).toHaveBeenCalledWith("m1"));
    await waitFor(() => expect(screen.queryByText("First goal")).toBeNull());
    expect(screen.getByText("Second goal")).toBeTruthy();
  });

  it("does NOT delete when the confirmation is cancelled (US2)", async () => {
    vi.mocked(api.deleteMission).mockResolvedValue(undefined);
    renderReady();
    await screen.findByText("First goal");

    fireEvent.click(screen.getByRole("button", { name: "Delete — First goal" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(api.deleteMission).not.toHaveBeenCalled();
    expect(screen.getByText("First goal")).toBeTruthy();
  });

  it("keeps the item and shows an error when deletion fails (FR-006)", async () => {
    vi.mocked(api.deleteMission).mockRejectedValue(new Error("boom"));
    renderReady();
    await screen.findByText("First goal");

    fireEvent.click(screen.getByRole("button", { name: "Delete — First goal" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Could not delete"));
    expect(screen.getByText("First goal")).toBeTruthy();
  });

  it("offers no delete control for the live-followed run (FR-008)", async () => {
    localStorage.setItem(FOLLOW_POINTER_KEY, JSON.stringify({ runId: "m1", status: "running", updatedAt: 1 }));
    renderReady();
    await screen.findByText("First goal");
    // m1 is live → no delete trigger; m2 (saved) still has one.
    expect(screen.queryByRole("button", { name: "Delete — First goal" })).toBeNull();
    expect(screen.getByRole("button", { name: "Delete — Second goal" })).toBeTruthy();
  });

  it("clears a follow pointer that referenced the deleted mission (FR-007)", async () => {
    vi.mocked(api.deleteMission).mockResolvedValue(undefined);
    // A DONE pointer (not running, so m1 stays deletable) that still references m1.
    localStorage.setItem(FOLLOW_POINTER_KEY, JSON.stringify({ runId: "m1", status: "done", missionId: "m1", updatedAt: 1 }));
    renderReady();
    await screen.findByText("First goal");

    fireEvent.click(screen.getByRole("button", { name: "Delete — First goal" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(localStorage.getItem(FOLLOW_POINTER_KEY)).toBeNull());
  });

  it("labels the delete control in French", async () => {
    vi.spyOn(navigator, "language", "get").mockReturnValue("fr-FR");
    renderReady();
    await screen.findByText("First goal");
    expect(screen.getByRole("button", { name: "Supprimer — First goal" })).toBeTruthy();
  });
});
