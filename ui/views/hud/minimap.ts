// The HUD's minimap (1.12 §5): the parchment chart round the player, drawn from the chart's own layers and index
// (the chart view's assets) and the hud.minimap push: the revealed cells in reach, the discovered places in reach
// and the player. Owner look 1: a small square, north always up; only the player's arrow turns, to the camera's
// heading (the push's heading is the camera's yaw). No quest or other markers, ever. Pure geometry here (tested); the drawing below it.
import type { ChartPlace, ChartPlayer, Minimap } from "../../schema/generated/messages.ts";
import { type CellIndex, revealRects, toPx } from "../chart/geom.ts";
import { PIN } from "../chart/render.ts";

export const REACH = 5;   // cells from the player to the square's edge (skse/core chart::kMinimapReach)

// The square's transform: master px -> minimap px, centred on the player, north up (never turned).
export function discTransform(ix: CellIndex, me: ChartPlayer, side: number, reach = REACH) {
  const cell = ix.cells["0,0"][2];
  const scale = side / (2 * reach * cell);
  const [px, py] = toPx(ix, me.x, me.y);
  return { scale, px, py, rot: 0, cx: side / 2, cy: side / 2 };
}

// The arrow's turn toward a new heading by the shorter way round, so 359 -> 1 turns 2 degrees, not back 358.
export function turnTo(shown: number, heading: number): number {
  return shown + ((((heading - shown) % 360) + 540) % 360) - 180;
}

// Where a place sits on the square (minimap px), or null outside it.
export function onDisc(ix: CellIndex, me: ChartPlayer, side: number, p: Pick<ChartPlace, "x" | "y">, reach = REACH) {
  const t = discTransform(ix, me, side, reach);
  const [qx, qy] = toPx(ix, p.x, p.y);
  const dx = (qx - t.px) * t.scale, dy = (qy - t.py) * t.scale;
  const c = Math.cos(t.rot), s = Math.sin(t.rot);
  const x = t.cx + dx * c - dy * s, y = t.cy + dx * s + dy * c;
  return x >= 0 && x <= side && y >= 0 && y <= side ? [x, y] as [number, number] : null;
}

type Layers = { base: HTMLImageElement; revealed: HTMLImageElement; ink: HTMLImageElement };
let layers: Promise<Layers> | null = null;
const load = (src: string) => new Promise<HTMLImageElement>((ok, bad) => {
  const i = new Image(); i.onload = () => ok(i); i.onerror = () => bad(new Error(`minimap: cannot load ${src}`)); i.src = src;
});
function layersOnce(): Promise<Layers> {
  layers ??= Promise.all(["base", "revealed", "ink"].map((n) => load(`../chart/assets/${n}-2048.png`)))
    .then(([base, revealed, ink]) => ({ base, revealed, ink }));
  return layers;
}

let shown = 0;   // the arrow's drawn angle, unwrapped, so its transition always takes the shorter way

// Draws the minimap into its element (rendered by render.ts) from the last push; resolves once drawn.
export async function drawMinimap(el: HTMLElement, m: Minimap): Promise<void> {
  const ix = (window as unknown as { ARGONIA_CHART_INDEX?: CellIndex }).ARGONIA_CHART_INDEX;
  el.hidden = !m.player || !ix;
  if (!m.player || !ix) return;
  const me = m.player;
  const arrow = el.querySelector<HTMLElement>(".mm-me");
  if (arrow) {   // a CSS transition carries the arrow between the pushes (0.2 s apart) so it turns smoothly
    shown = turnTo(shown, me.heading);
    arrow.style.transform = `rotate(${shown}deg)`;
    // a new element (a hud.state redraw) takes its angle at once, then turns smoothly from there
    if (!arrow.classList.contains("turning")) setTimeout(() => arrow.classList.add("turning"), 30);
  }
  el.dataset.heading = String(me.heading);
  const L = await layersOnce();
  const canvas = el.querySelector<HTMLCanvasElement>("canvas")!;
  const dpr = window.devicePixelRatio || 1, side = canvas.clientWidth;
  canvas.width = canvas.height = Math.round(side * dpr);
  const c = canvas.getContext("2d")!;
  const t = discTransform(ix, me, side);
  const onto = (g: CanvasRenderingContext2D) => {
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.translate(t.cx, t.cy); g.rotate(t.rot); g.scale(t.scale, t.scale); g.translate(-t.px, -t.py);
    g.imageSmoothingEnabled = true; g.imageSmoothingQuality = "high";
  };
  c.save();
  c.clearRect(0, 0, canvas.width, canvas.height);
  onto(c);
  c.drawImage(L.base, 0, 0, ix.size, ix.size);
  // The revealed layer through the cells in reach, with a soft edge, then the sketch's ink over all.
  const r = document.createElement("canvas"); r.width = r.height = canvas.width;
  const g = r.getContext("2d")!;
  onto(g);
  if ("filter" in g) g.filter = `blur(${Math.max(1, Math.round(ix.cells["0,0"][2] * t.scale * dpr * 0.25))}px)`;
  g.fillStyle = "#fff";
  for (const [x, y, w, h] of revealRects(ix, m.revealed).rects) g.fillRect(x, y, w, h);
  if ("filter" in g) g.filter = "none";
  g.globalCompositeOperation = "source-in";
  g.drawImage(L.revealed, 0, 0, ix.size, ix.size);
  c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(r, 0, 0);
  onto(c);
  c.drawImage(L.ink, 0, 0, ix.size, ix.size);
  // The discovered places, upright: their glyphs at a fixed size on paper halos.
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  const rem = parseFloat(getComputedStyle(document.documentElement).fontSize), k = (1.1 * rem) / 100;
  for (const p of m.places) {
    const at = onDisc(ix, me, side, p);
    const d = ix.pins?.[PIN[p.kind] ?? "pin-landmark"];
    if (!at || !d) continue;
    c.save(); c.translate(at[0] - 50 * k, at[1] - 50 * k); c.scale(k, k);
    c.shadowColor = "#f1e8cf"; c.shadowBlur = 6 * dpr; c.fillStyle = "#2b2e1c";
    c.fill(new Path2D(d), "evenodd");
    c.restore();
  }
  el.dataset.places = String(m.places.length);
  c.restore();
  el.dataset.drawn = "1";
}
