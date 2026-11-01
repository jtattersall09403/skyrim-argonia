// The HUD in the browser: hud.state redraws the whole; hud.bars, the frequent update (5 a second), moves the bars;
// hud.minimap redraws the minimap alone (minimap.ts).
// Owner look 1: redrawing the bars at each push made them step and restarted their glint (the flashing). Now the
// bars' elements persist; each push sets the widths under CSS transitions (render.ts `motion`, Skyrim's meter's
// glide and trailing catch-up). A bar's length (its maximum) moves by a CSS transition too.
import { start } from "../core/bridge.ts";
import type { Bar, Minimap } from "../../schema/generated/messages.ts";
import { drawMinimap } from "./minimap.ts";
import { barLength, fillPct, isLow, type Meter, meter, motion, render, renderBars } from "./render.ts";

const root = document.getElementById("view")!;
type Kind = Bar["kind"];
const meters: Partial<Record<Kind, Meter>> = {};
const targets: Partial<Record<Kind, number>> = {};
const lost: Partial<Record<Kind, number>> = {};   // when each bar last fell (s), for the trail's span
const f0 = fillPct;
let map: Minimap | null = null;   // the last hud.minimap: a hud.state redraws the HUD, and the minimap from this
const minimap = () => {
  const el = root.querySelector<HTMLElement>("[data-minimap]");
  if (el && map) drawMinimap(el, map).then(() => { document.body.dataset.ready = "1"; },
    (e: Error) => window.argonia.errors.push(e.message));
};

// Take a push's bars: the rows rebuilt only when the set of shown bars changes (breath or grip coming or going),
// else each part's width set in place under its transition (render.ts `motion`).
function take(bars: Bar[]): void {
  const shown = bars.filter((b) => b.shown);
  const el = root.querySelector<HTMLElement>("[data-bars]");
  if (!el) return;                       // before any hud.state there is no HUD to update
  const have = [...el.querySelectorAll<HTMLElement>("[data-kind]")].map((r) => r.dataset.kind).join();
  if (have !== shown.map((b) => b.kind).join()) el.innerHTML = renderBars(shown, meters);
  for (const b of shown) {
    const t = performance.now() / 1000, was = targets[b.kind];
    if (was !== undefined && f0(b) < was) lost[b.kind] = t;
    const f = fillPct(b), mv = motion(was, f, t - (lost[b.kind] ?? -Infinity));
    targets[b.kind] = f;
    meters[b.kind] = meter(f);
    const bar = el.querySelector<HTMLElement>(`[data-kind="${b.kind}"] .bar`)!;
    const fill = bar.querySelector<HTMLElement>(".fill")!, trail = bar.querySelector<HTMLElement>(".trail")!;
    fill.style.transition = mv.fill; fill.style.width = `${f.toFixed(2)}%`;
    if (mv.trail) { trail.style.transition = mv.trail; trail.style.width = `${f.toFixed(2)}%`; }
    bar.style.width = `${barLength(b).toFixed(2)}rem`;
    bar.setAttribute("aria-valuenow", String(Math.round(b.current)));
    bar.setAttribute("aria-valuemax", String(Math.round(b.max)));
    bar.classList.toggle("low", b.kind === "health" && isLow([b]));
  }
  root.querySelector(".hud")?.classList.toggle("low", isLow(bars));
}

start({
  accepts: ["hud.state", "hud.bars", "hud.minimap"],
  render(m) {
    if (m.type === "hud.state") {
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
