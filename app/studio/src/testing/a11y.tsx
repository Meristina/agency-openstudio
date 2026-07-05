import { expect } from "vitest";

export function expectNamedInteractives(root: ParentNode = document) {
  for (const el of Array.from(root.querySelectorAll("button,a,input,select,textarea"))) {
    const name =
      (el as HTMLElement).getAttribute("aria-label")?.trim() ||
      (el as HTMLElement).textContent?.trim() ||
      (el as HTMLInputElement).placeholder?.trim();
    expect(name).toBeTruthy();
  }
}
