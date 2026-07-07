import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../i18n/I18nProvider";
import { PREFS_KEY } from "../../i18n/catalog";
import RecipeCatalog from "./RecipeCatalog";
import type { Recipe } from "./recipesApi";

const SAMPLE: Recipe[] = [
  {
    id: "full-campaign", kind: "composed",
    name_key: "recipes.full_campaign.name", desc_key: "recipes.full_campaign.desc",
    required_inputs: [{ key: "subject", label_key: "recipes.input.subject" }],
    stages: [
      { kind: "mission", tier: "local", label_key: "recipes.stage.mission" },
      { kind: "export", tier: "local", label_key: "recipes.stage.export" },
    ],
  },
  {
    id: "cinematic", kind: "production",
    name_key: "recipes.pipeline.cinematic.name", desc_key: "recipes.pipeline.cinematic.desc",
    required_inputs: [{ key: "subject", label_key: "recipes.input.subject" }],
    stages: [{ kind: "pipeline", tier: "cloud", label_key: "recipes.stage.pipeline" }],
  },
];

vi.mock("./recipesApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./recipesApi")>();
  return { ...actual, listRecipes: vi.fn(async () => SAMPLE) };
});
// RecipeLaunch (rendered on select) pulls in the run session; stub it so selecting stays inert.
vi.mock("../session/missionSession", () => ({ missionSession: { launchRecipe: vi.fn() } }));

afterEach(() => { cleanup(); vi.clearAllMocks(); localStorage.clear(); window.location.hash = ""; });

function renderCatalog() {
  return render(<I18nProvider><RecipeCatalog /></I18nProvider>);
}

describe("RecipeCatalog", () => {
  it("lists composed and production recipes with plain-language tier badges", async () => {
    renderCatalog();
    expect(await screen.findByRole("heading", { name: "Recipes" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Full campaign" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Cinematic" })).toBeTruthy();
    // Tiers read in plain language, never a raw stage id or slug.
    expect(screen.getByText("Strategy: local/free")).toBeTruthy();
    expect(screen.getByText("Production: cloud opt-in")).toBeTruthy();
  });

  it("renders French catalog copy (i18n parity)", async () => {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ locale: "fr" }));
    renderCatalog();
    expect(await screen.findByRole("heading", { name: "Recettes" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Campagne complète" })).toBeTruthy();
    expect(screen.getByText("Production: cloud sur accord")).toBeTruthy();
  });

  it("launch reaches the recipe's run surface", async () => {
    renderCatalog();
    const card = (await screen.findByRole("heading", { name: "Full campaign" })).closest("article")!;
    fireEvent.click(within(card).getByRole("button", { name: "Launch" }));
    // RecipeLaunch is now on screen — its subject field is the entry to the run.
    await waitFor(() => expect(screen.getByLabelText("Subject")).toBeTruthy());
  });
});
