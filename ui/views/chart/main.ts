// The chart in the browser: the three layers out/chart renders (base, revealed, ink; 2.W4 §c) stacked on a canvas,
// the revealed layer masked to the cells chart.state lists, with a soft edge (the old chart's long fade).
// Drag, pinch, the wheel, WASD, +/- and the pad's right stick and triggers move a local view while the gesture
// lasts; when it settles the view is sent as chart.pan, and ArgoniaCore keeps it between openings.
import type { ChartState, ChartView } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { type CellIndex, pan, panIntent, revealRects, toPx, transform } from "./geom.ts";
import { render } from "./render.ts";

declare global { interface Window { ARGONIA_CHART_INDEX: CellIndex } }

const root = document.getElementById("view")!;
const ix = window.ARGONIA_CHART_INDEX;
// The sketch ids the bundle knows: each names the folder of its three layers (made at install, decision 0014).
const SKETCHES: Record<string, string> = { "chart.sketch": "assets" };

const load = (src: string) => new Promise<HTMLImageElement>((ok, bad) => {
  const i = new Image(); i.onload = () => ok(i); i.onerror = () => bad(new Error(`chart: cannot load ${src}`)); i.src = src;
});
const layers = new Map<string, Promise<{ base: HTMLImageElement; revealed: HTMLImageElement; ink: HTMLImageElement }>>();
function layersFor(id: string) {
  if (!layers.has(id)) {
    const dir = SKETCHES[id];
    if (!dir) throw new Error(`chart: unknown sketch '${id}'`);
    layers.set(id, Promise.all(["base", "revealed", "ink"].map((n) => load(`${dir}/${n}-2048.png`)))
      .then(([base, revealed, ink]) => ({ base, revealed, ink })));
  }
  return layers.get(id)!;
}

let state: ChartState | null = null;
let view: ChartView = { centreX: 0, centreY: 0, zoom: 1 };
let masked: HTMLCanvasElement | null = null;
let maskedFor = "";
let imgs: { base: HTMLImageElement; revealed: HTMLImageElement; ink: HTMLImageElement } | null = null;

// The revealed layer through the cells: one mask pixel per cell, smoothed up in two steps (a soft edge about a
// cell wide), then the layer drawn "source-in".
function mask(revealed: HTMLImageElement, s: ChartState): HTMLCanvasElement {
  const n = Math.round(ix.size / ix.cells["0,0"][2]);
  const small = document.createElement("canvas"); small.width = small.height = n;
  const c = small.getContext("2d")!;
  c.fillStyle = "#fff";
  const { rects, unknown } = revealRects(ix, s.revealed);
  if (unknown.length) window.argonia.errors.push(`chart: ${unknown.length} revealed cells not in the index`);
  const k = n / ix.size;
  for (const [x, y, w, h] of rects) c.fillRect(x * k, y * k, w * k, h * k);
  let src: HTMLCanvasElement = small;
  for (const side of [n * 4, revealed.width]) {
    const up = document.createElement("canvas"); up.width = up.height = side;
    const u = up.getContext("2d")!; u.imageSmoothingEnabled = true; u.imageSmoothingQuality = "high";
    u.drawImage(src, 0, 0, side, side); src = up;
  }
  const u = src.getContext("2d")!;
  u.globalCompositeOperation = "source-in";
  u.drawImage(revealed, 0, 0);
  return src;
}

function draw(): void {
  if (!state || !imgs) return;
  const canvas = root.querySelector<HTMLCanvasElement>("canvas.layers");
  if (!canvas) return;
  const w = canvas.clientWidth, h = canvas.clientHeight, dpr = window.devicePixelRatio || 1;
  if (canvas.width !== Math.round(w * dpr)) canvas.width = Math.round(w * dpr);
  if (canvas.height !== Math.round(h * dpr)) canvas.height = Math.round(h * dpr);
  const key = `${state.sketch}|${JSON.stringify(state.revealed)}`;
  if (maskedFor !== key) { masked = mask(imgs.revealed, state); maskedFor = key; }
  const t = transform(ix, view, w, h);
  const c = canvas.getContext("2d")!;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.fillStyle = "#ddd0aa"; c.fillRect(0, 0, w, h);
  c.imageSmoothingEnabled = true; c.imageSmoothingQuality = "high";
  c.setTransform(dpr * t.scale, 0, 0, dpr * t.scale, dpr * t.tx, dpr * t.ty);
  c.drawImage(imgs.base, 0, 0, ix.size, ix.size);
  c.drawImage(masked!, 0, 0, ix.size, ix.size);
  c.drawImage(imgs.ink, 0, 0, ix.size, ix.size);
  for (const el of root.querySelectorAll<HTMLElement>(".place")) {
    const [px, py] = toPx(ix, Number(el.dataset.x), Number(el.dataset.y));
    el.style.left = `${px * t.scale + t.tx}px`; el.style.top = `${py * t.scale + t.ty}px`;
  }
  document.body.dataset.ready = "1";
}

let settle = 0;
function moved(next: ChartView, now = false): void {
  view = next; draw();
  clearTimeout(settle);
  const go = () => send(panIntent(view));
  if (now) go(); else settle = window.setTimeout(go, 300);
}
const sheetSize = () => {
  const c = root.querySelector<HTMLCanvasElement>("canvas.layers")!;
  return [c.clientWidth, c.clientHeight] as const;
};
const step = (dx: number, dy: number, f = 1) => { const [w, h] = sheetSize(); moved(pan(ix, view, w, h, dx, dy, f)); };

// Touch and mouse: one pointer drags, two pinch.
const pts = new Map<number, { x: number; y: number }>();
let pinch0 = 0;
root.addEventListener("pointerdown", (e) => {
  if (!(e.target as HTMLElement).closest("canvas")) return;
  (e.target as HTMLElement).setPointerCapture(e.pointerId);
  pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch0 = Math.hypot(a.x - b.x, a.y - b.y); }
});
root.addEventListener("pointermove", (e) => {
  const p = pts.get(e.pointerId); if (!p) return;
  const [w, h] = sheetSize();
  if (pts.size === 1) { view = pan(ix, view, w, h, e.clientX - p.x, e.clientY - p.y); }
  pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (pts.size === 2) {
    const [a, b] = [...pts.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y);
    if (pinch0 > 0) view = pan(ix, view, w, h, 0, 0, d / pinch0);
    pinch0 = d;
  }
  draw();
});
const up = (e: PointerEvent) => { if (pts.delete(e.pointerId) && pts.size === 0) moved(view, true); };
root.addEventListener("pointerup", up);
root.addEventListener("pointercancel", up);
root.addEventListener("wheel", (e) => { e.preventDefault(); step(0, 0, e.deltaY < 0 ? 1.25 : 0.8); }, { passive: false });
window.addEventListener("resize", draw);

start({
  accepts: ["chart.state"],
  render(m) {
    if (m.type !== "chart.state") return;
    state = m.body; view = m.body.view;
    root.innerHTML = render(state);
    delete document.body.dataset.ready;
    layersFor(state.sketch).then((l) => { imgs = l; draw(); }, (e: Error) => window.argonia.errors.push(e.message));
    if (imgs) draw();
  },
  action(a) {
    const PAN = 0.12 * Math.min(...sheetSize());
    switch (a) {
      case "zoomIn": step(0, 0, 1.5); return true;
      case "zoomOut": step(0, 0, 1 / 1.5); return true;
      case "panUp": step(0, PAN); return true;
      case "panDown": step(0, -PAN); return true;
      case "panLeft": step(PAN, 0); return true;
      case "panRight": step(-PAN, 0); return true;
      default: return false;
    }
  },
  back() { send({ type: "view.close", v: 1, body: { view: "chart" } }); },
  local(el) { if (el.dataset.ui === "zoom-in") step(0, 0, 1.5); if (el.dataset.ui === "zoom-out") step(0, 0, 1 / 1.5); },
});
