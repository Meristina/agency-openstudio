import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "../../i18n/I18nProvider";
import CancelControl from "./CancelControl";

afterEach(cleanup);

describe("CancelControl", () => {
  it("requires confirmation and does not double fire", async () => {
    const onCancel = vi.fn(async () => true);
    render(<I18nProvider><CancelControl status="running" onCancel={onCancel} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    expect(onCancel).not.toHaveBeenCalled();
    const confirm = screen.getByRole("button", { name: "Stop production" });
    fireEvent.click(confirm);
    fireEvent.click(confirm);
    await waitFor(() => expect(onCancel).toHaveBeenCalledTimes(1));
  });

  it("is absent after settlement", () => {
    render(<I18nProvider><CancelControl status="done" onCancel={vi.fn()} /></I18nProvider>);
    expect(screen.queryByRole("button", { name: "Stop" })).toBeNull();
  });
});
