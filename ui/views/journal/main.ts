// The journal in the browser: one innerHTML per journal.state; Q/E, PageUp/PageDown, the pad's shoulders and the
// Previous and Next buttons turn. A page whose text runs past the spread continues in further leaves (the CSS
// columns of .flow or .index, scrolled a spread at a time): a turn moves a leaf while there is one that way, and only
// then asks ArgoniaCore for the page (journal.page). Coming back to a page starts at its last leaf.
import type { IntentMessage, JournalState } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { render, turn } from "./render.ts";

const root = document.getElementById("view")!;
let state: JournalState | null = null;
let leaf = 0;
let startAtEnd = false;  // the last turn was back to the previous page

const body = () => root.querySelector<HTMLElement>(".flow, .index");
function stride(f: HTMLElement): number {
  return f.clientWidth + (parseFloat(getComputedStyle(f).columnGap) || 0);
}
function leaves(): number {
  const f = body();
  if (!f || f.clientWidth === 0) return 1;
  return Math.max(1, Math.ceil((f.scrollWidth - 1) / stride(f)));
}
function show(i: number): void {
  const f = body();
  leaf = Math.min(Math.max(i, 0), leaves() - 1);
  if (f) f.scrollLeft = leaf * stride(f);
  root.dataset.leaf = String(leaf);
  root.dataset.leaves = String(leaves());
  const folio = root.querySelector<HTMLElement>(".folio");
  if (folio) {  // the page as ArgoniaCore counts it, and the leaf within it when it has more than one
    folio.dataset.page ??= folio.textContent ?? "";
    folio.textContent = leaves() > 1 ? `Pages ${2 * leaf + 1}–${2 * leaf + 2} of ${2 * leaves()}` : folio.dataset.page;
  }
  for (const b of root.querySelectorAll<HTMLButtonElement>(".turn")) {
    const back = b.dataset.dir === "prev";
    const local = back ? leaf > 0 : leaf + 1 < leaves();
    b.classList.toggle("none", !local && b.dataset.intent === undefined);
  }
}

function step(dir: -1 | 1): boolean {
  if (!state) return false;
  if (dir < 0 ? leaf > 0 : leaf + 1 < leaves()) { show(leaf + dir); return true; }
  const m: IntentMessage | null = turn(state, dir);
  if (!m) return false;
  startAtEnd = dir < 0;
  send(m);
  return true;
}

// The leaves depend on the laid-out text: measured again when the window or the font changes.
window.addEventListener("resize", () => show(leaf));
void document.fonts.ready.then(() => show(leaf));

start({
  accepts: ["journal.state"],
  render(m) {
    if (m.type !== "journal.state") return;
    state = m.body;
    root.innerHTML = render(state);
    show(startAtEnd ? Number.MAX_SAFE_INTEGER : 0);
    startAtEnd = false;
  },
  action(a) {
    if (a !== "prev" && a !== "next") return false;
    return step(a === "prev" ? -1 : 1);
  },
  local(el) {
    if (el.dataset.ui === "turn") step(el.dataset.dir === "prev" ? -1 : 1);
  },
  back() { send({ type: "view.close", v: 1, body: { view: "journal" } }); },
});
