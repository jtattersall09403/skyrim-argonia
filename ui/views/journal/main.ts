// The journal in the browser: one innerHTML per journal.state. On the diary (All entries) Q/E, PageUp/PageDown, the
// pad's shoulders and Previous/Next turn: a page whose text runs past the spread continues in further leaves (CSS
// columns of .flow, scrolled a spread at a time); a turn moves a leaf while there is one that way, and only then
// asks ArgoniaCore for the page. On the other ribbons the shoulders step the ribbons. The search field: typing sends
// journal.page with the words (ArgoniaCore filters); the field keeps focus and caret across the redraw; "/" or
// Ctrl+F reach it from anywhere; Escape in the field clears it. Escape elsewhere, the pad's B and touch's B close.
import type { IntentMessage, JournalState } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { render, ribbonStep, searchIntent, turn } from "./render.ts";

const root = document.getElementById("view")!;
let state: JournalState | null = null;
let leaf = 0;
let startAtEnd = false;  // the last turn was back to the previous page

const body = () => root.querySelector<HTMLElement>(".flow");
const field = () => root.querySelector<HTMLInputElement>(".sfield");
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
  if (state.tab !== "all") {
    const m = ribbonStep(state, dir);
    if (m) send(m);
    return m !== null;
  }
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

// Keys typed into the search field are text, not navigation: they stop here before nav.ts reads them, except
// Escape (back: clears, then closes), the arrows up and down (leave the field) and PageUp/PageDown.
window.addEventListener("keydown", (e) => {
  const f = field();
  const inField = f !== null && document.activeElement === f;
  if (!inField) {
    if (f && (e.key === "/" || (e.ctrlKey && e.key.toLowerCase() === "f"))) { e.preventDefault(); e.stopImmediatePropagation(); f.focus(); }
    return;
  }
  if (e.key === "Escape" || e.key === "ArrowUp" || e.key === "ArrowDown" || e.key === "PageUp" || e.key === "PageDown") {
    if (e.key === "Escape" && f.value === "" && !state?.search) return;  // nav.ts: back closes
    if (e.key === "Escape") { e.preventDefault(); e.stopImmediatePropagation(); f.value = ""; if (state) send(searchIntent(state, "")); }
    return;
  }
  e.stopImmediatePropagation();
}, true);
root.addEventListener("input", (e) => {
  const f = e.target as HTMLInputElement;
  if (state && f.classList.contains("sfield")) send(searchIntent(state, f.value));
});

start({
  accepts: ["journal.state"],
  render(m) {
    if (m.type !== "journal.state") return;
    const had = field(), focused = had !== null && document.activeElement === had;
    const caret = had?.selectionStart ?? null;
    state = m.body;
    root.innerHTML = render(state);
    show(startAtEnd ? Number.MAX_SAFE_INTEGER : 0);
    startAtEnd = false;
    const f = field();
    if (focused && f) {
      f.focus({ preventScroll: true });
      const at = Math.min(caret ?? f.value.length, f.value.length);
      f.setSelectionRange(at, at);
    }
  },
  action(a) {
    if (a !== "prev" && a !== "next") return false;
    return step(a === "prev" ? -1 : 1);
  },
  local(el) {
    if (el.dataset.ui === "turn") step(el.dataset.dir === "prev" ? -1 : 1);
  },
  back() { send({ type: "view.close", v: 1, body: { view: "journal" } }); },  // B always closes (1.12 §8)
});
