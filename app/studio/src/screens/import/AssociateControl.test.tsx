import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../i18n/I18nProvider";
import { getAssociation } from "./associationStore";
import AssociateControl from "./AssociateControl";

afterEach(() => {
  cleanup();
  localStorage.clear();
});

describe("AssociateControl", () => {
  it("files and unassigns material using taxonomy choices", () => {
    const onAssociated = vi.fn();
    render(
      <I18nProvider>
        <AssociateControl
          item={{ id: "d1", kind: "document", name: "Brief", importedAt: 1, association: null }}
          taxonomy={{ clients: [{ name: "Acme", missions: 0, projects: [{ name: "Expo", missions: 0, campaigns: [] }] }] }}
          onAssociated={onAssociated}
        />
      </I18nProvider>,
    );
    fireEvent.change(screen.getByLabelText("Client"), { target: { value: "Acme" } });
    fireEvent.change(screen.getByLabelText("Project"), { target: { value: "Expo" } });
    fireEvent.click(screen.getByRole("button", { name: "File" }));
    expect(getAssociation("d1")).toEqual({ client: "Acme", project: "Expo" });
    fireEvent.click(screen.getByRole("button", { name: "Return to unassigned" }));
    expect(getAssociation("d1")).toBeNull();
    expect(onAssociated).toHaveBeenCalledTimes(2);
  });
});
