// The HUD in the browser: hud.state redraws the whole; hud.bars, the frequent update, redraws the bars alone;
// hud.minimap redraws the minimap alone (minimap.ts).
// The view remembers what the last push showed, for the damage trail and the regeneration glint (render.ts
// `remember`); the trail falls to the fill TRAIL_HOLD ms after the last hit, by a CSS transition.
import { start } from "../core/bridge.ts";
import type { Bar, Minimap } from "../../schema/generated/messages.ts";
import { drawMinimap } from "./minimap.ts";
import { type BarMemory, isLow, remember, render, renderBars } from "./render.ts";

const root = document.getElementById("view")!;
const TRAIL_HOLD = 900, REGEN_HOLD = 700;
let last: Partial<Record<Bar["kind"], number>> = {};
let mem: BarMemory = { trail: {}, regen: new Set() };
let fall: number | undefined, still: number | undefined;
let map: Minimap | null = null;   // the last hud.minimap: a hud.state redraws the HUD, and the minimap from this
const minimap = () => {
  const el = root.querySelector<HTMLElement>("[data-minimap]");
  if (el && map) drawMinimap(el, map).then(() => { document.body.dataset.ready = "1"; },
    (e: Error) => window.argonia.errors.push(e.message));
};

function step(bars: Bar[]): void {
  const was = last;
  ({ last, mem } = remember(last, bars, mem));
  const hit = bars.some((b) => b.shown && (last[b.kind] ?? 0) < (was[b.kind] ?? 0));
  if (hit) {
    clearTimeout(fall);
    fall = setTimeout(() => {
      mem = { trail: {}, regen: mem.regen };
      for (const el of root.querySelectorAll<HTMLElement>("[data-trail]")) {
        const f = el.nextElementSibling as HTMLElement | null;
        if (f) el.style.width = f.style.width;
      }
    }, TRAIL_HOLD) as unknown as number;
  }
  if (mem.regen.size) {
    clearTimeout(still);
    still = setTimeout(() => {
      mem = { trail: mem.trail, regen: new Set() };
      for (const el of root.querySelectorAll(".bar.regen")) el.classList.remove("regen");
    }, REGEN_HOLD) as unknown as number;
  }
}

start({
  accepts: ["hud.state", "hud.bars", "hud.minimap"],
  render(m) {
    if (m.type === "hud.state") { step(m.body.bars); root.innerHTML = render(m.body, mem); minimap(); return; }
    if (m.type === "hud.minimap") { map = m.body.map; delete document.body.dataset.ready; minimap(); return; }
    if (m.type === "hud.bars") {
      const el = root.querySelector<HTMLElement>("[data-bars]");
      if (!el) return;                       // before any hud.state there is no HUD to update
      step(m.body.bars);
      el.innerHTML = renderBars(m.body.bars, mem);
      root.querySelector(".hud")?.classList.toggle("low", isLow(m.body.bars));
    }
  },
  back() { /* the HUD takes no input; Escape belongs to the game */ },
});
