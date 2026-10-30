// Pure string rendering shared by the views. A view's render() is state -> HTML, so Node tests run it with no DOM
// and the browser sets it with one innerHTML per push (1.2: views hold no game state; they render what ArgoniaCore
// pushes and send intents back).
import type { IntentMessage } from "../../schema/generated/messages.ts";

const ESC: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export const esc = (s: string): string => s.replace(/[&<>"']/g, (c) => ESC[c]);

// The intent an element sends when activated (click, tap, Enter, the pad's A). bridge.ts reads it back.
export const intentAttr = (m: IntentMessage): string => `data-intent="${esc(JSON.stringify(m))}"`;

// A button that sends an intent. Every actionable control in our views is a <button>, so keyboard focus, Enter and
// Space come from the platform, and nav.ts moves focus between buttons for the pad.
export const intentButton = (m: IntentMessage, cls: string, inner: string, extra = ""): string =>
  `<button type="button" class="${cls}" ${intentAttr(m)}${extra ? " " + extra : ""}>${inner}</button>`;

// Every intent an HTML string carries, decoded; the L1 tests use it to check shapes without a browser.
export function intentsIn(html: string): unknown[] {
  const out: unknown[] = [];
  for (const m of html.matchAll(/data-intent="([^"]*)"/g)) {
    const raw = m[1].replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/&amp;/g, "&");
    out.push(JSON.parse(raw));
  }
  return out;
}

// The text a still would show, tags stripped; the tests look for the strings the state carried.
export const textOf = (html: string): string =>
  html.replace(/<[^>]*>/g, " ").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
