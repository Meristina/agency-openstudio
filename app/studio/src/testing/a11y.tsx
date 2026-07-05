import { expect } from "vitest";

export function expectNamedInteractives(root: ParentNode = document) {
  for (const el of Array.from(root.querySelectorAll("button,a,input,select,textarea"))) {
    expect((el as HTMLElement).getAttribute("aria-label") || (el as HTMLElement).textContent || (el as HTMLInputElement).placeholder).toBeTruthy();
  }
}
