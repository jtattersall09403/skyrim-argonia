// The chart in the browser (1.12 §5, look 1): the render's tile pyramid (tools/chart/pyramid.py) drawn on one canvas
// the size of the sheet, from the level nearest one pixel to one at the zoom, so it stays sharp close in and draws
// only what shows. Two flattened layers: `sketch` everywhere (the coast, rivers, roads and cities over the paper) and
// `full` (the explored land's tint, woods, marsh and tracks) through a soft mask of the land the player has seen.
// Over them the discovered places' markers and the player's, turned to the heading.
// Drag, pinch, the wheel, WASD, +/- and the pad's right stick and triggers move a target view; each frame the view
// glides toward it (geom.ts glide), and when it settles the view is sent as chart.pan, kept between openings.
import type { ChartState, ChartView } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { type CellIndex, type LabelBox, glide, labelAt, levelFor, placeLabels, pan, panIntent, revealDiscs, sketchCities, toPx,
  toward, transform, visibleTiles, ZOOM_MAX, ZOOM_MIN } from "./geom.ts";
import { render } from "./render.ts";

declare global { interface Window { ARGONIA_CHART_INDEX: CellIndex; ARGONIA_CHART_PANE?: boolean } }
// The map pane (pane.html): the same chart docked beside Wind UI's windows, display only, close in round the player.
const PANE = window.ARGONIA_CHART_PANE === true;
if (PANE) document.body.classList.add("pane");
const PANE_ZOOM = 8;   // the pane is short: close in, the land round the player

const root = document.getElementById("view")!;
const ix = window.ARGONIA_CHART_INDEX;
const PYR = ix.pyramid ?? { tile: 512, levels: [1024] };
// The sketch ids the bundle knows: each names the folder of its tiles (made at install, decision 0014).
const SKETCHES: Record<string, string> = { "chart.sketch": "assets/t" };

// Tiles load on first sight and stay; a tile not yet loaded is drawn from the nearest coarser level that is.
const tiles = new Map<string, HTMLImageElement | null>();   // null: loading
function tileImg(dir: string, layer: string, level: number, c: number, r: number): HTMLImageElement | undefined {
  const k = `${dir}/${layer}/${level}/${c}-${r}`;
  const have = tiles.get(k);
  if (have) return have;
  if (have === undefined) {
    tiles.set(k, null);
    const i = new Image();
    i.onload = () => { tiles.set(k, i); drawSoon(); };
    i.onerror = () => window.argonia.errors.push(`chart: cannot load ${k}.png`);
    i.src = `${k}.png`;
  }
  return undefined;
}

let state: ChartState | null = null;
let view: ChartView = { centreX: 0, centreY: 0, zoom: 1 };
let target: ChartView = view;
let mask: HTMLCanvasElement | null = null;   // the seen land, one canvas over the whole chart
let maskFor = "";
let pushKey = "";          // the sketch and revealed cells of the last push: the mask is rebuilt only when they change
let frame = 0, lastT = 0, checked = false, glideFrames = 0, glideMax = 0, glideStart = 0;
const drawSoon = () => { if (!frame) frame = requestAnimationFrame(tick); };
function tick(t: number): void {
  frame = 0;
  const dt = lastT ? Math.min(100, t - lastT) : 16;
  lastT = t;
  const was = view;
  if (!dragging) view = glide(view, target, dt);
  draw();
  // the motion's own measure (1.12 look 1, smooth on every device): frames drawn per glide and the largest step
  const [w0, h0] = sheetSize(), t0 = transform(ix, was, w0, h0), t1 = transform(ix, view, w0, h0);
  const stepPx = Math.max(Math.abs(t1.tx - t0.tx), Math.abs(t1.ty - t0.ty), Math.abs(t1.scale / t0.scale - 1) * w0 / 2);
  if (stepPx > 0.01) { glideFrames++; glideMax = Math.max(glideMax, stepPx); glideStart ||= t; }
  if (view.centreX !== target.centreX || view.centreY !== target.centreY || view.zoom !== target.zoom) drawSoon();
  else {
    lastT = 0;
    if (glideFrames > 1) console.warn(`chart: glide ${glideFrames} frames in ${Math.round(t - glideStart)} ms, largest step ${glideMax.toFixed(1)} px`);
    glideFrames = 0; glideMax = 0; glideStart = 0;
  }
}

// The seen land: a soft disc about each revealed cell (geom.ts revealDiscs), full inside and fading to nothing at the
// rim (the old chart's long fade), on a canvas of MASK px a side over the whole chart.
const MASK = 1024;
function buildMask(s: ChartState): HTMLCanvasElement {
  const m = document.createElement("canvas"); m.width = m.height = MASK;
  const c = m.getContext("2d")!;
  const k = MASK / ix.size;
  const unknown = s.revealed.filter((r) => !ix.cells[`${r.x},${r.y}`]);
  if (unknown.length) console.warn(`chart: ${unknown.length} revealed cells not in the index`);
  for (const [x, y, rad] of revealDiscs(ix, s.revealed)) {
    const g = c.createRadialGradient(x * k, y * k, 0, x * k, y * k, rad * k);
    g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.55, "rgba(255,255,255,1)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.fillStyle = g;
    c.beginPath(); c.arc(x * k, y * k, rad * k, 0, 2 * Math.PI); c.fill();
  }
  return m;
}

// Whether the seen land covers a point in cell units (the mask is our own canvas, so it reads back in game).
let maskData: Uint8ClampedArray | null = null, maskDataFor = "";
function seenAt(u: number, v: number): boolean {
  if (!mask) return false;
  if (maskDataFor !== maskFor) { try { maskData = mask.getContext("2d")!.getImageData(0, 0, MASK, MASK).data; } catch { maskData = null; } maskDataFor = maskFor; }
  if (!maskData) return true;
  const [x, y] = toPx(ix, u, v), k = MASK / ix.size;
  const i = Math.round(y * k), j = Math.round(x * k);
  return i >= 0 && j >= 0 && i < MASK && j < MASK && maskData[(i * MASK + j) * 4 + 3] > 128;
}

let seen: HTMLCanvasElement | null = null;   // the explored layer through the mask, the sheet's size
function layer(c: CanvasRenderingContext2D, dir: string, name: string, level: number, t: { scale: number; tx: number; ty: number },
  w: number, h: number): void {
  const T = PYR.tile, side = (T * ix.size) / level;   // a tile's side in master px
  for (const [col, row] of visibleTiles(level, T, ix.size, t, w, h)) {
    const x = t.tx + col * side * t.scale, y = t.ty + row * side * t.scale, d = side * t.scale;
    const img = tileImg(dir, name, level, col, row);
    if (img) { c.drawImage(img, x, y, d + 0.5, d + 0.5); continue; }   // half a px over: no seams between tiles
    // not loaded yet: the part of a coarser loaded tile that covers it
    for (const lv of PYR.levels.filter((l) => l < level).reverse()) {
      const f = level / lv, pc = Math.floor(col / f), pr = Math.floor(row / f);
      const up = tileImg(dir, name, lv, pc, pr);
      if (!up) continue;
      const sub = T / f;
      c.drawImage(up, (col - pc * f) * sub, (row - pr * f) * sub, sub, sub, x, y, d + 0.5, d + 0.5);
      break;
    }
  }
}

function draw(): void {
  if (!state) return;
  const canvas = root.querySelector<HTMLCanvasElement>("canvas.layers");
  if (!canvas) return;
  const w = canvas.clientWidth, h = canvas.clientHeight, dpr = window.devicePixelRatio || 1;
  if (canvas.width !== Math.round(w * dpr)) canvas.width = Math.round(w * dpr);
  if (canvas.height !== Math.round(h * dpr)) canvas.height = Math.round(h * dpr);
  if (maskFor !== pushKey) { mask = buildMask(state); maskFor = pushKey; }
  const dir = SKETCHES[state.sketch];
  if (!dir) { window.argonia.errors.push(`chart: unknown sketch '${state.sketch}'`); return; }
  const t = transform(ix, view, w, h);
  const level = levelFor(PYR.levels, ix.size, t.scale * dpr);
  const c = canvas.getContext("2d")!;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.clearRect(0, 0, w, h);   // the margins show the sheet's paper (the theme's .paper mottle)
  c.imageSmoothingEnabled = true; c.imageSmoothingQuality = "high";
  // Unexplored land is blank parchment (1.12 look 1, the owner's ruling: the land revealed round where the player has
  // been): every layer, coast, rivers, roads and cities included, shows only through the seen land's soft mask.
  if (state.revealed.length && mask) {
    seen ??= document.createElement("canvas");
    if (seen.width !== canvas.width || seen.height !== canvas.height) { seen.width = canvas.width; seen.height = canvas.height; }
    const s = seen.getContext("2d")!;
    s.setTransform(dpr, 0, 0, dpr, 0, 0);
    s.globalCompositeOperation = "source-over";
    s.clearRect(0, 0, w, h);
    s.imageSmoothingEnabled = true;
    layer(s, dir, "full", level, t, w, h);
    s.globalCompositeOperation = "destination-in";
    s.drawImage(mask, t.tx, t.ty, ix.size * t.scale, ix.size * t.scale);
    s.globalCompositeOperation = "source-over";
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.drawImage(seen, 0, 0);
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!checked) selfCheck(s, t, dpr, w, h);
  }
  // Where the sheet is wider than the chart, feather the chart's straight edges into the paper (destination-out).
  const x0 = t.tx, x1 = t.tx + ix.size * t.scale, y0 = t.ty, y1 = t.ty + ix.size * t.scale;
  const f = Math.max(24, 3 * parseFloat(getComputedStyle(document.documentElement).fontSize));
  c.globalCompositeOperation = "destination-out";
  const strip = (ax: number, ay: number, bx: number, by: number, rx: number, ry: number, rw: number, rh: number) => {
    const g = c.createLinearGradient(ax, ay, bx, by);
    g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)");
    c.fillStyle = g; c.fillRect(rx, ry, rw, rh);
  };
  if (x0 > 0) strip(x0, 0, x0 + f, 0, x0, Math.max(0, y0), f, Math.min(h, y1) - Math.max(0, y0));
  if (x1 < w) strip(x1, 0, x1 - f, 0, x1 - f, Math.max(0, y0), f, Math.min(h, y1) - Math.max(0, y0));
  if (y0 > 0) strip(0, y0, 0, y0 + f, Math.max(0, x0), y0, Math.min(w, x1) - Math.max(0, x0), f);
  if (y1 < h) strip(0, y1, 0, y1 - f, Math.max(0, x0), y1 - f, Math.min(w, x1) - Math.max(0, x0), f);
  c.globalCompositeOperation = "source-over";
  for (const el of root.querySelectorAll<HTMLElement>(".place, .me")) {
    const [px, py] = toPx(ix, Number(el.dataset.x), Number(el.dataset.y));
    el.style.left = `${px * t.scale + t.tx}px`; el.style.top = `${py * t.scale + t.ty}px`;
    if (el.dataset.heading !== undefined) el.style.transform = `rotate(${Number(el.dataset.heading)}deg)`;
  }
  const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
  // Pass 1: where each label wants to sit, measured with its text. Pass 2: collisions by priority.
  const boxes: (LabelBox & { el: HTMLElement; city: boolean })[] = [];
  for (const el of root.querySelectorAll<HTMLElement>(".label")) {
    const at = labelAt(ix, t, el.dataset.label!, Number(el.dataset.x), Number(el.dataset.y),
      el.dataset.discovered === "true", rem * 0.75);
    el.hidden = at === null || at.left > w || at.left < 0 || at.top > h || at.top < 0 ||   // the sheet clips the rest
      (el.dataset.discovered !== "true" && !seenAt(Number(el.dataset.x), Number(el.dataset.y)));   // fog hides a city's name
    el.style.transform = "";
    if (!at || el.hidden) continue;
    el.style.left = `${at.left}px`; el.style.top = `${at.top}px`;
    el.classList.toggle("over", at.cover !== undefined);
    el.classList.toggle("beside", at.cover === undefined);   // no drawn label: a small ink mark at the place
    if (at.cover) { el.style.minWidth = `${at.cover[2] + 0.4 * rem}px`; el.style.minHeight = `${at.cover[3] + 0.2 * rem}px`; }
    else { el.style.minWidth = ""; el.style.minHeight = ""; }
    const lead = at.cover ? 0.2 * rem : 0.55 * rem;   // the plate's margin, or the ink mark beside a bare label
    const bw = el.offsetWidth + lead, bh = el.offsetHeight;
    boxes.push({ id: el.dataset.label!, x: at.left - lead, y: at.top - bh / 2, w: bw, h: bh, el,
      city: !!ix.places?.[el.dataset.label!]?.city });
  }
  // Major cities first, then the rest; the larger plate (the bigger drawn name) first within each.
  boxes.sort((a, b) => Number(b.city) - Number(a.city) || b.w * b.h - a.w * a.h);
  // The pins and the player's marker stay where they are: the labels move round them.
  const marks: LabelBox[] = [];
  for (const el of root.querySelectorAll<HTMLElement>(".place:not([hidden]), .me")) {
    const r = el.offsetWidth / 2;
    marks.push({ id: "", x: parseFloat(el.style.left) - r, y: parseFloat(el.style.top) - r, w: 2 * r, h: 2 * r });
  }
  const spots = placeLabels(boxes, w, h, 2, marks);
  for (const b of boxes) {
    const spot = spots.get(b.id) ?? null;
    b.el.hidden = spot === null;
    b.el.classList.toggle("moved", !!spot && (spot[0] !== 0 || spot[1] !== 0) && b.el.classList.contains("over"));
    if (b.el.style.minWidth) {
      b.el.style.setProperty("--cw", `calc(${b.el.style.minWidth} + 0.6rem)`);
      b.el.style.setProperty("--ch", `calc(${b.el.style.minHeight} + 0.6rem)`);
    }
    if (spot) b.el.style.setProperty("--dx", `${-spot[0]}px`), b.el.style.setProperty("--dy", `${-spot[1]}px`);
    if (spot) b.el.style.transform = `translate(${spot[0]}px, calc(-50% + ${spot[1]}px))`;
  }
  document.body.dataset.ready = "1";
}

// The reveal's own proof in game (1.12 look 1: 1.12's journey read the native log, never the pixels). The tiles are
// file images, which may taint the sheet for reading back, so the proof reads canvases of our own making: the mask
// must be opaque at the player and clear far from every revealed cell, and the web view must honour the
// "destination-in" the explored layer is cut with (a solid square cut by the mask's left half keeps only that half).
// The verdict goes to the console, which ArgoniaCore logs ("views: chart console: chart: reveal ...").
function selfCheck(_s: CanvasRenderingContext2D, _t: { scale: number; tx: number; ty: number }, dpr: number, _w: number, _h: number): void {
  const p = state?.player;
  if (!p || !mask) return;
  checked = true;
  const k = MASK / ix.size;
  const alpha = (cv: HTMLCanvasElement, x: number, y: number) => {
    try { return cv.getContext("2d")!.getImageData(Math.round(x), Math.round(y), 1, 1).data[3]; } catch { return -1; }
  };
  const [mx, my] = toPx(ix, p.x, p.y);
  const here = alpha(mask, mx * k, my * k);
  const far = alpha(mask, mx * k < MASK / 2 ? MASK - 1 : 0, my * k < MASK / 2 ? MASK - 1 : 0);
  const probe = document.createElement("canvas"); probe.width = 8; probe.height = 4;
  const half = document.createElement("canvas"); half.width = 8; half.height = 4;
  half.getContext("2d")!.fillRect(0, 0, 4, 4);
  const q = probe.getContext("2d")!;
  q.fillStyle = "#c00"; q.fillRect(0, 0, 8, 4);
  q.globalCompositeOperation = "destination-in"; q.drawImage(half, 0, 0); q.globalCompositeOperation = "source-over";
  const cut = alpha(probe, 1, 1) === 255 && alpha(probe, 6, 1) === 0;
  const verdict = here > 200 && far === 0 && cut ? "ok" : "FAIL";
  console.warn(`chart: reveal ${verdict} (mask ${here} at the player, ${far} far; destination-in ${cut ? "honoured" : "NOT honoured"}; ` +
    `${state!.revealed.length} cells, level ${levelFor(PYR.levels, ix.size, _t.scale * dpr)})`);
}

// A move sets the target; the frame loop glides to it. The view is sent once it has settled.
let settle = 0, dragging = false;
function aim(next: ChartView, now = false): void {
  target = next; drawSoon();
  clearTimeout(settle);
  if (PANE) return;   // the pane never moves the chart's remembered view
  const go = () => send(panIntent(target));
  if (now) go(); else settle = window.setTimeout(go, 300);
}
const sheetSize = () => {
  const c = root.querySelector<HTMLCanvasElement>("canvas.layers")!;
  return [c.clientWidth, c.clientHeight] as const;
};
const step = (dx: number, dy: number, f = 1) => { const [w, h] = sheetSize(); aim(pan(ix, target, w, h, dx, dy, f)); };
// The zoom buttons, keys and triggers: in goes toward the player, out about the centre, down to the whole province.
const zoom = (f: number) => aim(toward(target, state?.player, f));

// Touch and mouse: one pointer drags (the chart follows the hand at once), two pinch.
const pts = new Map<number, { x: number; y: number }>();
let pinch0 = 0;
root.addEventListener("pointerdown", (e) => {
  if (!(e.target as HTMLElement).closest("canvas")) return;
  (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
  dragging = true; target = view;
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
  target = view;
  drawSoon();
});
const up = (e: PointerEvent) => { if (pts.delete(e.pointerId) && pts.size === 0) { dragging = false; aim(view, true); } };
root.addEventListener("pointerup", up);
root.addEventListener("pointercancel", up);
root.addEventListener("wheel", (e) => { e.preventDefault(); step(0, 0, e.deltaY < 0 ? 1.25 : 0.8); }, { passive: false });
window.addEventListener("resize", drawSoon);

const clampZoom = (v: ChartView): ChartView => ({ ...v, zoom: Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, v.zoom)) });

start({
  accepts: ["chart.state"],
  render(m) {
    if (m.type !== "chart.state") return;
    state = m.body;
    view = target = clampZoom(PANE && m.body.player ? { centreX: m.body.player.x, centreY: m.body.player.y, zoom: PANE_ZOOM } : m.body.view);
    const key = `${state.sketch}|${JSON.stringify(state.revealed)}`;
    if (key !== pushKey) { pushKey = key; checked = false; }
    root.innerHTML = render(state, sketchCities(ix, new Set(state.places.map((p) => p.id))), ix.pins);
    delete document.body.dataset.ready;
    // the whole province's smallest level first, so the first frame is never empty
    for (let r = 0; r < PYR.levels[0] / PYR.tile; r++) for (let c = 0; c < PYR.levels[0] / PYR.tile; c++)
      for (const l of ["sketch", "full"]) tileImg(SKETCHES[state.sketch] ?? "", l, PYR.levels[0], c, r);
    drawSoon();
  },
  action(a) {
    const PAN = 0.18 * Math.min(...sheetSize());
    if (!PANE && a !== "accept") console.warn(`chart: input ${a}`);
    switch (a) {
      // the d-pad pans too: in game PrismaUI passes the pad's buttons but not its right stick
      case "up": step(0, PAN); return true;
      case "down": step(0, -PAN); return true;
      case "left": step(PAN, 0); return true;
      case "right": step(-PAN, 0); return true;
      case "zoomIn": zoom(1.5); return true;
      case "zoomOut": zoom(1 / 1.5); return true;
      case "panUp": step(0, PAN); return true;
      case "panDown": step(0, -PAN); return true;
      case "panLeft": step(PAN, 0); return true;
      case "panRight": step(-PAN, 0); return true;
      default: return false;
    }
  },
  back() { if (!PANE) send({ type: "view.close", v: 1, body: { view: "chart" } }); },
  local(el) { if (el.dataset.ui === "zoom-in") zoom(1.5); if (el.dataset.ui === "zoom-out") zoom(1 / 1.5); },
});
