import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import TaxonomyBrowser from "./TaxonomyBrowser";

afterEach(cleanup);

const tree = {
  clients: [
    { name: "Acme", missions: 1, projects: [{ name: "Rebrand", missions: 1, campaigns: [{ name: "Spring", missions: 1 }] }] },
  ],
};

describe("TaxonomyBrowser", () => {
  it("renders groups and filters by campaign", () => {
    const onFilter = vi.fn();
    render(
      <TaxonomyBrowser
        taxonomy={tree}
        missions={[{ mission_id: "m1", goal: "launch", verdict: "PASS" }]}
        selectedId={null}
        onFilter={onFilter}
        onOpen={vi.fn()}
        onClear={vi.fn()}
        onAssign={vi.fn()}
      />,
    );
    expect(screen.getByText("Acme")).toBeTruthy();
    fireEvent.click(screen.getAllByText(/Spring/)[0]);
    expect(onFilter).toHaveBeenCalledWith({ client: "Acme", project: "Rebrand", campaign: "Spring" });
  });

  it("renders an empty state", () => {
    render(<TaxonomyBrowser taxonomy={{ clients: [] }} missions={[]} selectedId={null} onFilter={vi.fn()} onOpen={vi.fn()} onClear={vi.fn()} onAssign={vi.fn()} />);
    expect(screen.getByText("No saved missions.")).toBeTruthy();
    expect(screen.getByText("No matching missions.")).toBeTruthy();
  });

  it("assigns the selected mission", () => {
    const onAssign = vi.fn();
    render(<TaxonomyBrowser taxonomy={tree} missions={[{ mission_id: "m1" }]} selectedId="m1" onFilter={vi.fn()} onOpen={vi.fn()} onClear={vi.fn()} onAssign={onAssign} />);
    fireEvent.change(screen.getByLabelText("Assign client"), { target: { value: "Acme" } });
    fireEvent.click(screen.getByRole("button", { name: "Assign" }));
    expect(onAssign).toHaveBeenCalledWith("m1", { client: "Acme", project: undefined, campaign: undefined });
  });
});
