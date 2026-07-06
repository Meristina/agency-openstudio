import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCapabilities, fetchTaxonomy, listDocs, listVisual, runMission } from "../../api";
import { I18nProvider } from "../../i18n/I18nProvider";
import { ClientContextProvider } from "../../shell/ClientContext";
import { expectNamedInteractives } from "../../testing/a11y";
import GuidedBrief from "./GuidedBrief";
import { saveBriefDraft } from "./briefDraft";
import { missionSession } from "../session/missionSession";

vi.mock("../../api", () => ({
  fetchTaxonomy: vi.fn().mockResolvedValue({ clients: [] }),
  fetchCapabilities: vi.fn().mockResolvedValue({ generated_at: "now", families: [] }),
  listDocs: vi.fn().mockResolvedValue([]),
  listVisual: vi.fn().mockResolvedValue([]),
  runMission: vi.fn(async (_goal: string, onEvent: (event: { phase: string; run_id: string }) => void) => {
    onEvent({ phase: "run", run_id: "r42" });
  }),
  cancelMission: vi.fn(async () => true),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  missionSession.reset();
  vi.clearAllMocks();
  vi.mocked(fetchTaxonomy).mockResolvedValue({ clients: [] });
  vi.mocked(fetchCapabilities).mockResolvedValue({ generated_at: "now", families: [] });
  vi.mocked(listDocs).mockResolvedValue([]);
  vi.mocked(listVisual).mockResolvedValue([]);
});

function renderBrief(search = "") {
  return render(<I18nProvider><ClientContextProvider><GuidedBrief search={search} /></ClientContextProvider></I18nProvider>);
}

function next() {
  fireEvent.click(screen.getByRole("button", { name: /Next|Suivant/ }));
}

describe("GuidedBrief US1 flow", () => {
  it("prefills intent from the route and leaves it editable", () => {
    renderBrief("intent=Launch%20plan");
    const intent = screen.getByLabelText("Intent") as HTMLTextAreaElement;
    expect(intent.value).toBe("Launch plan");
    fireEvent.change(intent, { target: { value: "Changed" } });
    expect(intent.value).toBe("Changed");
  });

  it("asks for intent when the route intent is absent or blank", () => {
    renderBrief("intent=%20%20");
    expect(screen.getByLabelText("Intent")).toBeTruthy();
    expect((screen.getByLabelText("Intent") as HTMLTextAreaElement).value).toBe("");
  });

  it("asks only type-relevant questions and preserves answers when moving back", () => {
    renderBrief("intent=Launch%20video");
    next();
    fireEvent.click(screen.getByRole("radio", { name: "Video" }));
    next();
    next();
    expect(screen.getByText("Who should watch it?")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Who should watch it?"), { target: { value: "Sponsors" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect((screen.getByLabelText("Who should watch it?") as HTMLInputElement).value).toBe("Sponsors");
  });

  it("accepts defaults through a complete brief", () => {
    renderBrief("intent=Market%20study");
    for (let i = 0; i < 12 && !screen.queryByRole("heading", { name: "Review" }); i += 1) next();
    expect(screen.getByRole("heading", { name: "Review" })).toBeTruthy();
    expect(screen.getByText("Market study")).toBeTruthy();
  });

  it("keeps deliverable language independent when interface language changes", () => {
    renderBrief("intent=Plan");
    for (let i = 0; i < 12 && !screen.queryByRole("radio", { name: "Français" }); i += 1) next();
    expect((screen.getByRole("radio", { name: "English" }) as HTMLInputElement).checked).toBe(true);
    fireEvent.click(screen.getByRole("radio", { name: "Français" }));
    expect((screen.getByRole("radio", { name: "Français" }) as HTMLInputElement).checked).toBe(true);
  });

  it("has named keyboard controls", () => {
    renderBrief("intent=Plan");
    expectNamedInteractives();
    expect(document.querySelector('input[type="password"]')).toBeNull();
  });

  it("flags over-limit answers in plain language instead of truncating", () => {
    renderBrief();
    fireEvent.change(screen.getByLabelText("Intent"), { target: { value: "x".repeat(4001) } });
    next();
    expect(screen.getByRole("alert").textContent).toBe("Shorten this answer before continuing.");
    expect((screen.getByLabelText("Intent") as HTMLTextAreaElement).value).toHaveLength(4001);
  });

  it("offers a free-text field for the 'other' sector (FR-004)", () => {
    renderBrief("intent=Plan");
    next();
    next();
    fireEvent.click(screen.getByRole("radio", { name: "Another field" }));
    fireEvent.change(screen.getByLabelText("Tell us the field"), { target: { value: "Padel" } });
    expect((screen.getByLabelText("Tell us the field") as HTMLInputElement).value).toBe("Padel");
  });
});

describe("GuidedBrief launch wiring (US2)", () => {
  function toReview() {
    renderBrief("intent=Market%20study");
    for (let i = 0; i < 12 && !screen.queryByRole("button", { name: "Launch" }); i += 1) next();
  }

  it("confirms the run and keeps the launched brief consultable (FR-018)", async () => {
    toReview();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(await screen.findByText(/Mission launched/)).toBeTruthy();
    expect(screen.getByText(/r42/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open missions" })).toBeTruthy();
    expect(screen.getByText("Market study")).toBeTruthy();
  });

  it("keeps the full brief and allows retry when the launch is rejected (FR-019)", async () => {
    vi.mocked(runMission).mockRejectedValueOnce(new Error("mission blocked: required capabilities unavailable"));
    toReview();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect((await screen.findByRole("alert")).textContent).toContain("mission blocked");
    expect(screen.getByRole("button", { name: "Launch" })).toBeTruthy();
    expect(screen.getByText("Market study")).toBeTruthy();
  });
});

describe("GuidedBrief attachment flow (US3)", () => {
  async function toAttachment() {
    renderBrief("intent=Client%20launch");
    for (let i = 0; i < 10 && !screen.queryByLabelText("Client"); i += 1) next();
    await screen.findByLabelText("Client");
  }

  async function finishAndLaunch() {
    for (let i = 0; i < 12 && !screen.queryByRole("button", { name: "Launch" }); i += 1) next();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    await screen.findByText(/Mission launched/);
  }

  it("attaches an existing client/project/campaign to the launch request", async () => {
    vi.mocked(fetchTaxonomy).mockResolvedValue({
      clients: [{ name: "Acme", missions: 0, projects: [{ name: "Expo", missions: 0, campaigns: [{ name: "Spring", missions: 0 }] }] }],
    });
    await toAttachment();
    fireEvent.change(screen.getByLabelText("Client"), { target: { value: "Acme" } });
    fireEvent.change(screen.getByLabelText("Project"), { target: { value: "Expo" } });
    fireEvent.change(screen.getByLabelText("Campaign"), { target: { value: "Spring" } });
    await finishAndLaunch();
    expect(vi.mocked(runMission).mock.calls.at(-1)?.[2]).toMatchObject({ client: "Acme", project: "Expo", campaign: "Spring" });
  });

  it("can skip attachment and launch unassigned", async () => {
    await toAttachment();
    fireEvent.click(screen.getByRole("button", { name: /Skip|Passer/ }));
    await finishAndLaunch();
    expect(vi.mocked(runMission).mock.calls.at(-1)?.[2]).not.toHaveProperty("client");
  });

  it("carries the shell's pre-selected client context into the launch by default", async () => {
    localStorage.setItem("agency-studio.prefs", JSON.stringify({ clientContext: { client: "Acme" } }));
    vi.mocked(fetchTaxonomy).mockResolvedValue({
      clients: [{ name: "Acme", missions: 0, projects: [] }],
    });
    await toAttachment();
    await finishAndLaunch();
    expect(vi.mocked(runMission).mock.calls.at(-1)?.[2]).toMatchObject({ client: "Acme" });
  });

  it("uses a new client name and survives taxonomy fetch failure", async () => {
    vi.mocked(fetchTaxonomy).mockRejectedValue(new Error("offline"));
    await toAttachment();
    expect(screen.getByText("Client list unavailable. You can still continue.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("New client"), { target: { value: "NewCo" } });
    await finishAndLaunch();
    expect(vi.mocked(runMission).mock.calls.at(-1)?.[2]).toMatchObject({ client: "NewCo" });
  });
});

describe("GuidedBrief draft flow (US5)", () => {
  it("offers resume or discard without silently overwriting", () => {
    saveBriefDraft({ intent: "Saved plan", deliverableType: "research", deliverableLanguage: "en" }, 2);
    renderBrief("intent=New%20plan");
    expect(screen.getByRole("heading", { name: "Resume draft?" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Resume" }));
    expect(screen.getByText("Step 3 of 9")).toBeTruthy();
  });

  it("leaves no stored draft after a mere visit or a discard (FR-021)", () => {
    renderBrief("intent=Just%20looking");
    expect(localStorage.getItem("studio.briefDraft.v1")).toBeNull();
    cleanup();
    saveBriefDraft({ intent: "Saved plan", deliverableType: "research", deliverableLanguage: "en" }, 2);
    renderBrief("intent=New%20plan");
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    expect(localStorage.getItem("studio.briefDraft.v1")).toBeNull();
  });

  it("discard starts clean and successful launch clears the draft", async () => {
    saveBriefDraft({ intent: "Saved plan", deliverableType: "research", deliverableLanguage: "en" }, 2);
    renderBrief("intent=New%20plan");
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    expect((screen.getByLabelText("Intent") as HTMLTextAreaElement).value).toBe("New plan");
    for (let i = 0; i < 12 && !screen.queryByRole("button", { name: "Launch" }); i += 1) next();
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    await screen.findByText(/Mission launched/);
    expect(localStorage.getItem("studio.briefDraft.v1")).toBeNull();
  });
});
