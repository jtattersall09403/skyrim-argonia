// Our character sheet in the browser: one innerHTML per charsheet.state. LB/RB (prev/next) cycle the Attributes,
// Skills and Perks tabs, which are buttons too; a perk the player can take (click, Enter, the pad's A) sends
// charsheet.perk. Escape, Tab, the pad's B and touch's B close.
import { send, start } from "../core/bridge.ts";
import type { CharsheetState } from "../../schema/generated/messages.ts";
import { close, render, step, type Tab } from "./render.ts";

const root = document.getElementById("view")!;
let state: CharsheetState | undefined;
let tab: Tab = "attributes";

function draw(focus?: string): void {
  if (!state) return;
  const top = root.querySelector<HTMLElement>(".well")?.scrollTop ?? 0;  // a re-push after a perk keeps the list where it was
  root.innerHTML = render(state, tab);
  const w = root.querySelector<HTMLElement>(".well");
  if (w) w.scrollTop = top;
  if (focus) root.querySelector<HTMLElement>(focus)?.focus({ preventScroll: true });
}

start({
  accepts: ["charsheet.state"],
  render(m) {
    if (m.type !== "charsheet.state") return;
    const first = state === undefined;
    state = m.body;
    draw();
    // the first row holds the focus at the opening, so the pad and the arrows start on a marked row
    if (first) root.querySelector<HTMLElement>(".well .name")?.focus({ preventScroll: true });
  },
  action(a) {
    if (a !== "prev" && a !== "next") return false;
    tab = step(tab, a === "next" ? 1 : -1);
    draw(".well .name");
    return true;
  },
  local(el) {
    if (el.dataset.ui !== "tab") return;
    tab = el.dataset.tab as Tab;
    draw(`[data-key="tab:${tab}"]`);
  },
  back() { send(close()); },
});

// The focused row's one-line description fills the line under the lists.
document.addEventListener("focusin", (e) => {
  const el = e.target as HTMLElement;
  const hint = root.querySelector<HTMLElement>(".hint");
  if (hint && el.matches?.(".well .name, .side .name")) hint.textContent = el.dataset.hint ?? "";
});
