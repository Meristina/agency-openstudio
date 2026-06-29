import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import Timeline from "./Timeline";
import type { MissionEvent } from "../types";

afterEach(cleanup);

describe("<Timeline>", () => {
  it("shows the empty hint when there are no events", () => {
    const { container } = render(<Timeline events={[]} />);
    expect(container.textContent).toContain("No events yet");
  });

  it("renders route, departments, and the inspect verdict from the event stream", () => {
    const events: MissionEvent[] = [
      { phase: "route", status: "done", route: ["solve", "product"] },
      { phase: "dept", dept: "solve", status: "done" },
      { phase: "inspect", iteration: 1, verdict: "PASS" },
      { phase: "done", mission_id: "m1", verdict: "PASS", path: "/p", residual_risk: null },
    ];
    const { container } = render(<Timeline events={events} />);
    const text = container.textContent ?? "";
    expect(text).toContain("Route");
    expect(text).toContain("solve");
    expect(text).toContain("product");
    expect(text).toContain("Departments");
    expect(text).toContain("PASS");
    expect(text).toContain("m1");
  });
});
