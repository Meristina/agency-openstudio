import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { assignMission } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import type { Deliverable } from "./libraryModel";
import FilingControl from "./FilingControl";

vi.mock("../../api", () => ({
  assignMission: vi.fn(async () => ({ client: "Acme", project: "Rebrand", campaign: "Launch" })),
}));

const taxonomy = { clients: [{ name: "Acme", missions: 1, projects: [{ name: "Rebrand", missions: 1, campaigns: [{ name: "Launch", missions: 1 }] }] }] };
const deliverable: Deliverable = {
  id: "d1",
  title: "Deck",
  producedAt: null,
  outcome: "successful",
  placement: { kind: "unassigned", client: null, project: null, campaign: null },
  preview: null,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("FilingControl", () => {
  it("attaches, moves, and returns work to unassigned", async () => {
    const onFiled = vi.fn();
    render(<I18nProvider><FilingControl deliverable={deliverable} taxonomy={taxonomy} onFiled={onFiled} /></I18nProvider>);
    fireEvent.change(screen.getByLabelText("Client"), { target: { value: "Acme" } });
    fireEvent.change(screen.getByLabelText("Project"), { target: { value: "Rebrand" } });
    fireEvent.change(screen.getByLabelText("Campaign"), { target: { value: "Launch" } });
    fireEvent.click(screen.getByRole("button", { name: "File" }));
    await waitFor(() => expect(assignMission).toHaveBeenCalledWith("d1", { client: "Acme", project: "Rebrand", campaign: "Launch" }));
    expect(onFiled).toHaveBeenCalledWith("d1", { client: "Acme", project: "Rebrand", campaign: "Launch" });
    fireEvent.click(screen.getByRole("button", { name: "Return to unassigned" }));
    await waitFor(() => expect(assignMission).toHaveBeenCalledWith("d1", { clear: true }));
    expect(onFiled).toHaveBeenCalledWith("d1", null);
  });

  it("leaves prior placement intact on failure", async () => {
    vi.mocked(assignMission).mockRejectedValueOnce(new Error("no"));
    const onFiled = vi.fn();
    render(<I18nProvider><FilingControl deliverable={{ ...deliverable, placement: { kind: "filed", client: "Acme", project: "Rebrand", campaign: null } }} taxonomy={taxonomy} onFiled={onFiled} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Move" }));
    await waitFor(() => expect(screen.getByText("Filing could not be updated.")).toBeTruthy());
    expect(onFiled).not.toHaveBeenCalled();
  });
});
