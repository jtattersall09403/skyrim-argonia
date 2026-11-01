// The HUD in the browser: hud.state redraws the whole; hud.bars, the frequent update (5 a second), moves the bars;
// hud.minimap redraws the minimap alone (minimap.ts).
// Owner look 1: redrawing the bars at each push made them step and restarted their glint (the flashing). Now the
// bars' elements persist; each push only sets a target, and one animation frame loop eases every fill and trail
// toward it (render.ts `tick`, Skyrim's meter's motion). A bar's length (its maximum) moves by a CSS transition.
import { start } from "../core/bridge.ts";
import type { Bar, Minimap } from "../../schema/generated/messages.ts";
import { drawMinimap } from "./minimap.ts";
import { barLength, fillPct, isLow, type Meter, meter, render, renderBars, tick } from "./render.ts";

const root = document.getElementById("view")!;
type Kind = Bar["kind"];
const meters: Partial<Record<Kind, Meter>> = {};
const targets: Partial<Record<Kind, number>> = {};
let map: Minimap | null = null;   // the last hud.minimap: a hud.state redraws the HUD, and the minimap from this
const minimap = () => {
  const el = root.querySelector<HTMLElement>("[data-minimap]");
  if (el && map) drawMinimap(el, map).then(() => { document.body.dataset.ready = "1"; },
    (e: Error) => window.argonia.errors.push(e.message));
};

// Take a push's bars: new targets; a bar newly shown starts at its value; the rows rebuilt only when the set of
// shown bars changes (breath or grip coming or going), else updated in place.
function take(bars: Bar[]): void {
  const shown = bars.filter((b) => b.shown);
  for (const k of Object.keys(meters) as Kind[]) if (!shown.some((b) => b.kind === k)) { delete meters[k]; delete targets[k]; }
  for (const b of shown) { targets[b.kind] = fillPct(b); meters[b.kind] ??= meter(fillPct(b)); }
  const el = root.querySelector<HTMLElement>("[data-bars]");
  if (!el) return;                       // before any hud.state there is no HUD to update
  const have = [...el.querySelectorAll<HTMLElement>("[data-kind]")].map((r) => r.dataset.kind).join();
  if (have !== shown.map((b) => b.kind).join()) el.innerHTML = renderBars(shown, meters);
  else for (const b of shown) {
    const bar = el.querySelector<HTMLElement>(`[data-kind="${b.kind}"] .bar`)!;
    bar.style.width = `${barLength(b).toFixed(2)}rem`;
    bar.setAttribute("aria-valuenow", String(Math.round(b.current)));
    bar.setAttribute("aria-valuemax", String(Math.round(b.max)));
    bar.classList.toggle("low", b.kind === "health" && isLow([b]));
  }
  root.querySelector(".hud")?.classList.toggle("low", isLow(bars));
  run();
}

// A 16 ms timer, not requestAnimationFrame: the first in-game run (hud-look 20261101T132445) showed the bars never
// moving, the unfocused overlay view not being given animation frames.
let last = 0, raf = 0;
function frame(): void {
  const now = performance.now();
  const dt = Math.min(0.1, last ? (now - last) / 1000 : 0.016);
  last = now;
  let moving = false;
  for (const k of Object.keys(meters) as Kind[]) {
    const m = (meters[k] = tick(meters[k]!, targets[k]!, dt));
    if (m.fill !== m.target || m.trail !== m.fill) moving = true;
    const row = root.querySelector<HTMLElement>(`[data-kind="${k}"]`);
    if (!row) continue;
    (row.querySelector(".fill") as HTMLElement).style.width = `${m.fill.toFixed(2)}%`;
    (row.querySelector(".trail") as HTMLElement).style.width = `${m.trail.toFixed(2)}%`;
  }
  raf = moving ? (setTimeout(frame, 16) as unknown as number) : 0;
  if (!moving) last = 0;
}
const run = () => { if (!raf) raf = setTimeout(frame, 16) as unknown as number; };

start({
  accepts: ["hud.state", "hud.bars", "hud.minimap"],
  render(m) {
    if (m.type === "hud.state") {
      for (const b of m.body.bars) if (b.shown) { targets[b.kind] = fillPct(b); meters[b.kind] ??= meter(fillPct(b)); }
      root.innerHTML = render(m.body, meters);
      take(m.body.bars);
      minimap();
      return;
    }
    if (m.type === "hud.minimap") { map = m.body.map; delete document.body.dataset.ready; minimap(); return; }
    if (m.type === "hud.bars") take(m.body.bars);
  },
  back() { /* the HUD takes no input; Escape belongs to the game */ },
});
