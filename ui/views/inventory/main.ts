// Our inventory in the browser: one innerHTML per inventory.state. A stack (click, Enter, the pad's A) sends
// inventory.use; the detail panel's Drop sends inventory.drop. LB/RB (prev/next) cycle the category tabs, which are
// buttons too; the focused stack fills the detail panel. Escape, Tab, the pad's B and touch's B close.
import { send, start } from "../core/bridge.ts";
import type { InventoryState } from "../../schema/generated/messages.ts";
import { close, detailText, use, drop, render, step, type Tab, visible } from "./render.ts";

const root = document.getElementById("view")!;
let state: InventoryState | undefined;
let tab: Tab = "all";
let sel: string | undefined;

const well = () => root.querySelector<HTMLElement>(".well");

function draw(focus?: string): void {
  if (!state) return;
  const top = well()?.scrollTop ?? 0;  // a re-push after a use keeps the list where it was
  root.innerHTML = render(state, tab, sel);
  const w = well();
  if (w) w.scrollTop = top;
  if (focus) root.querySelector<HTMLElement>(focus)?.focus({ preventScroll: true });
}

start({
  accepts: ["inventory.state"],
  render(m) {
    if (m.type !== "inventory.state") return;
    const first = state === undefined;
    state = m.body;
    draw();
    // the first stack holds the focus at the opening, so the pad and the arrows start on a marked row
    if (first) root.querySelector<HTMLElement>(".row .name")?.focus({ preventScroll: true });
  },
  action(a) {
    if (a === "drop") {  // the pad's X drops the focused stack, as the detail panel's Drop does
      const id = (document.activeElement as HTMLElement | null)?.closest<HTMLElement>(".row")
        ?.querySelector<HTMLElement>(".name")?.dataset.id ?? sel;
      if (id && state?.items.some((x) => x.id === id)) send(drop(id));
      return true;
    }
    if (a !== "prev" && a !== "next") return false;
    tab = step(tab, a === "next" ? 1 : -1);
    sel = visible(state!, tab)[0]?.id;
    draw();
    root.querySelector<HTMLElement>(".row .name, .tab.on")?.focus({ preventScroll: true });
    return true;
  },
  local(el) {
    if (el.dataset.ui !== "tab" || !state) return;
    tab = el.dataset.tab as Tab;
    sel = visible(state, tab)[0]?.id;
    draw(`[data-key="tab:${tab}"]`);
  },
  back() { send(close()); },
});

// The focused stack fills the detail panel; a focus on the panel's own buttons leaves it as it is.
document.addEventListener("focusin", (e) => {
  const el = e.target as HTMLElement;
  if (!state || !el.matches?.(".row .name")) return;
  sel = el.dataset.id;
  const i = state.items.find((x) => x.id === sel);
  const d = root.querySelector<HTMLElement>(".detail")!;
  d.querySelector(".dtext")!.innerHTML = detailText(i);
  if (!i) return;
  const [u, dr] = d.querySelectorAll<HTMLButtonElement>(".act");
  u.dataset.intent = JSON.stringify(use(i.id)); u.textContent = i.action;
  dr.dataset.intent = JSON.stringify(drop(i.id));
});
