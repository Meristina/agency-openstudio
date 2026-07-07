import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../i18n/I18nProvider";
import RecipeLaunch from "./RecipeLaunch";
import type { Recipe } from "./recipesApi";

const launchRecipe = vi.fn();
const navigate = vi.fn();
vi.mock("../session/missionSession", () => ({ missionSession: { launchRecipe: (...a: unknown[]) => launchRecipe(...a) } }));
vi.mock("../../shell/router", () => ({ navigate: (...a: unknown[]) => navigate(...a) }));

// A recipe with one local stage and one cloud stage — exercises both tier states + the opt-in gate.
const RECIPE: Recipe = {
  id: "full-campaign", kind: "composed",
  name_key: "recipes.full_campaign.name", desc_key: "recipes.full_campaign.desc",
  required_inputs: [{ key: "subject", label_key: "recipes.input.subject" }],
  stages: [
    { kind: "mission", tier: "local", label_key: "recipes.stage.mission" },
    { kind: "pipeline", tier: "cloud", label_key: "recipes.stage.pipeline" },
  ],
};

afterEach(() => { cleanup(); vi.clearAllMocks(); localStorage.clear(); });

function renderLaunch() {
  return render(<I18nProvider><RecipeLaunch recipe={RECIPE} /></I18nProvider>);
}

describe("RecipeLaunch", () => {
  it("shows a local(free)/cloud tier per stage; only a cloud stage is opt-in-able", () => {
    renderLaunch();
    expect(screen.getByText("Strategy: local/free")).toBeTruthy();
    expect(screen.getByText("Production: cloud opt-in")).toBeTruthy();
    const [local, cloud] = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(local.disabled).toBe(true);   // a local stage is never an opt-in
    expect(cloud.disabled).toBe(false);  // the cloud stage requires an explicit opt-in
    expect(cloud.checked).toBe(false);   // default off — a default launch stays local
  });

  it("launches with the subject + chosen opt-ins and hands off to the unified timeline", () => {
    renderLaunch();
    fireEvent.change(screen.getByLabelText("Subject"), { target: { value: "  launch coffee  " } });
    const [, cloud] = screen.getAllByRole("checkbox");
    fireEvent.click(cloud);  // opt the cloud stage in explicitly
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(launchRecipe).toHaveBeenCalledWith("full-campaign", "launch coffee", ["pipeline"]);
    expect(navigate).toHaveBeenCalledWith("#/missions");  // the run is followed on the S3 timeline (reuse)
  });

  it("does not launch on an empty subject", () => {
    renderLaunch();
    fireEvent.change(screen.getByLabelText("Subject"), { target: { value: "   " } });
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(launchRecipe).not.toHaveBeenCalled();
    expect(navigate).not.toHaveBeenCalled();
  });
});
