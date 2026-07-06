import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchMissionPdf } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import type { Deliverable } from "./libraryModel";
import DeliverableActions from "./DeliverableActions";

vi.mock("../../api", () => ({
  fetchMissionPdf: vi.fn(async () => new Blob()),
  assignMission: vi.fn(async () => ({ client: "Acme", project: "Rebrand", campaign: null })),
}));

const deliverable: Deliverable = {
  id: "d1",
  title: "Deck",
  producedAt: null,
  outcome: "successful",
  placement: { kind: "unassigned", client: null, project: null, campaign: null },
  preview: null,
};
const taxonomy = { clients: [{ name: "Acme", missions: 1, projects: [{ name: "Rebrand", missions: 1, campaigns: [] }] }] };

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("DeliverableActions", () => {
  it("opens detail, downloads PDF, and renders no delete control", async () => {
    vi.stubGlobal("URL", { ...URL, createObjectURL: vi.fn(() => "blob:mock"), revokeObjectURL: vi.fn() });
    const onOpen = vi.fn();
    render(<I18nProvider><DeliverableActions deliverable={deliverable} taxonomy={taxonomy} onOpen={onOpen} onFiled={() => {}} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Open full detail" }));
    expect(onOpen).toHaveBeenCalledWith("d1");
    fireEvent.click(screen.getByRole("button", { name: "Download PDF" }));
    await waitFor(() => expect(fetchMissionPdf).toHaveBeenCalledWith("d1"));
    expect(screen.queryByRole("button", { name: /delete|remove/i })).toBeFalsy();
  });

  it("shows a helpful PDF failure and keeps actions usable", async () => {
    vi.mocked(fetchMissionPdf).mockRejectedValueOnce(new Error("no pdf"));
    render(<I18nProvider><DeliverableActions deliverable={deliverable} taxonomy={taxonomy} onOpen={() => {}} onFiled={() => {}} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Download PDF" }));
    await waitFor(() => expect(screen.getByText(/PDF download failed/)).toBeTruthy());
    expect(screen.getByRole("button", { name: "Open full detail" })).toBeTruthy();
  });
});
