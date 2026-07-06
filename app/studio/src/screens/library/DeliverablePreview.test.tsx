import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../i18n/I18nProvider";
import DeliverablePreview from "./DeliverablePreview";

afterEach(cleanup);

describe("DeliverablePreview", () => {
  it("renders sources, decisions, media, and closes without navigation", () => {
    const onClose = vi.fn();
    render(
      <I18nProvider>
        <DeliverablePreview
          onClose={onClose}
          preview={{ headline: "Sponsor deck", outcome: "successful", keySources: ["https://example.com", "javascript:bad"], keyDecisions: ["Use current offer"], media: [{ type: "image", status: "ok", url: "/media/a.png", prompt: "hero" }] }}
        />
      </I18nProvider>,
    );
    expect(screen.getByText("Sponsor deck")).toBeTruthy();
    expect(screen.getByRole("link", { name: "https://example.com" }).getAttribute("rel")).toBe("noopener noreferrer");
    expect(screen.getByText("javascript:bad")).toBeTruthy();
    expect(screen.getByAltText("hero")).toBeTruthy();
    screen.getByRole("button", { name: "Close preview" }).click();
    expect(onClose).toHaveBeenCalled();
  });

  it("omits broken media placeholders when there is no media", () => {
    render(<I18nProvider><DeliverablePreview onClose={() => {}} preview={{ headline: "Research", outcome: "successful", keySources: [], keyDecisions: [], media: [] }} /></I18nProvider>);
    expect(screen.queryByText("Generated assets")).toBeFalsy();
  });
});
