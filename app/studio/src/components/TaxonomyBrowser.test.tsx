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

  it("flat campaign buttons filter without leaking extra fields", () => {
    const onFilter = vi.fn();
    render(
      <TaxonomyBrowser taxonomy={tree} missions={[]} selectedId={null} onFilter={onFilter} onOpen={vi.fn()} onClear={vi.fn()} onAssign={vi.fn()} />,
    );
    // The flat "Campaigns" section renders a second Spring button.
    fireEvent.click(screen.getAllByText(/Spring/)[1]);
    expect(onFilter).toHaveBeenCalledWith({ client: "Acme", project: "Rebrand", campaign: "Spring" });
  });

  it("disables Assign until a field is filled and resets per mission", () => {
    const onAssign = vi.fn();
    const { rerender } = render(
      <TaxonomyBrowser taxonomy={tree} missions={[{ mission_id: "m1" }, { mission_id: "m2" }]} selectedId="m1" onFilter={vi.fn()} onOpen={vi.fn()} onClear={vi.fn()} onAssign={onAssign} />,
    );
    const assign = screen.getByRole("button", { name: "Assign" }) as HTMLButtonElement;
    expect(assign.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Assign client"), { target: { value: "Acme" } });
    expect((screen.getByRole("button", { name: "Assign" }) as HTMLButtonElement).disabled).toBe(false);
    // Switching missions remounts the box: the stale value must not survive.
    rerender(
      <TaxonomyBrowser taxonomy={tree} missions={[{ mission_id: "m1" }, { mission_id: "m2" }]} selectedId="m2" onFilter={vi.fn()} onOpen={vi.fn()} onClear={vi.fn()} onAssign={onAssign} />,
    );
    expect((screen.getByLabelText("Assign client") as HTMLInputElement).value).toBe("");
    expect((screen.getByRole("button", { name: "Assign" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
