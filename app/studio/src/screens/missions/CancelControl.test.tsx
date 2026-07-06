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

  it("re-enables the control if cancel fails, so the user can retry", async () => {
    const onCancel = vi.fn(async () => { throw new Error("cancel failed"); });
    render(<I18nProvider><CancelControl status="running" onCancel={onCancel} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    fireEvent.click(screen.getByRole("button", { name: "Stop production" }));
    await waitFor(() => expect(onCancel).toHaveBeenCalledTimes(1));
    // Not left locked out: the confirm control is interactive again.
    await waitFor(() => expect((screen.getByRole("button", { name: "Stop production" }) as HTMLButtonElement).disabled).toBe(false));
  });

  it("dismisses the confirmation dialog on Escape", () => {
    render(<I18nProvider><CancelControl status="running" onCancel={vi.fn(async () => true)} /></I18nProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    expect(screen.getByRole("dialog")).toBeTruthy();
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
