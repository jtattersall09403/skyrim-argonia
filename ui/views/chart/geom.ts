// The parchment chart's geometry (1.2 §e), pure: cells in the schema's cell units, pixels on the chart's master
// canvas as out/chart/index.json gives them (x east, y south from the canvas's NW corner; cell y grows north).
import type { CellKey, ChartView, IntentMessage } from "../../schema/generated/messages.ts";

export type Rect = [number, number, number, number];
export interface CellIndex {
  size: number;                                            // master canvas side in px
  cells: Record<string, Rect>;                             // "x,y" -> [left, top, width, height] in master px
  // label: [x0, y0, x1, y1] of the chart's lettering; a city (lettered by the sketch) also has its name and cell
  places?: Record<string, { city: boolean; label: Rect | null; name?: string; cell?: [number, number] }>;
}

// Where the view letters a place in screen px, or null. The chart's own lettering is kept where it reads (at least
// `minPx` tall on screen); where it is smaller, the view letters it at 1rem on a paper plate over the drawn one. A
// place is lettered only where the paper shows it: a city (the sketch) or a discovered place (the revealed layer).
export function labelAt(ix: CellIndex, t: { scale: number; tx: number; ty: number }, id: string, x: number, y: number,
  discovered: boolean, minPx: number): { left: number; top: number; cover?: Rect } | null {
  const rec = ix.places?.[id];
  if (!discovered && !rec?.city) return null;
  const lab = rec?.label ?? null;
  if (lab) {
    if ((lab[3] - lab[1]) * t.scale >= minPx) return null;
    const cover: Rect = [lab[0] * t.scale + t.tx, lab[1] * t.scale + t.ty, (lab[2] - lab[0]) * t.scale, (lab[3] - lab[1]) * t.scale];
    return { left: cover[0], top: cover[1] + cover[3] / 2, cover };
  }
  const [px, py] = toPx(ix, x, y);
  return { left: px * t.scale + t.tx + minPx * 0.6, top: py * t.scale + t.ty };
}

export const key = (c: CellKey): string => `${c.x},${c.y}`;

// The sketch's cities the push did not name: the chart letters them whether or not the player has been there.
export const sketchCities = (ix: CellIndex, named: Set<string>) =>
  Object.entries(ix.places ?? {}).filter(([id, p]) => p.city && p.name && !named.has(id))
    .map(([id, p]) => ({ id, name: p.name!, x: p.cell![0] + 0.5, y: p.cell![1] + 0.5 }));

// Cell units -> master px, read from the index's cell 0,0 (the map is linear: one cell is one rect).
export function toPx(ix: CellIndex, u: number, v: number): [number, number] {
  const [x0, y0, w, h] = ix.cells["0,0"];
  return [x0 + w * u, y0 + h - h * v];
}
export function toUnits(ix: CellIndex, px: number, py: number): [number, number] {
  const [x0, y0, w, h] = ix.cells["0,0"];
  return [(px - x0) / w, (y0 + h - py) / h];
}

// The rects the revealed layer shows through: every revealed cell the index knows. A cell outside the index is
// reported, never drawn.
export function revealRects(ix: CellIndex, revealed: CellKey[]) {
  const rects: [number, number, number, number][] = [], unknown: string[] = [];
  for (const c of revealed) {
    const r = ix.cells[key(c)];
    if (r) rects.push(r); else unknown.push(key(c));
  }
  return { rects, unknown };
}

export const ZOOM_MIN = 1, ZOOM_MAX = 16;     // the schema allows 0.05..64; a chart below 1 or past 16 shows nothing new

// Master px -> screen px for a view of a w x h viewport: zoom 1 fits the whole canvas (contain).
export function transform(ix: CellIndex, v: ChartView, w: number, h: number) {
  const scale = (Math.min(w, h) / ix.size) * v.zoom;
  const [cx, cy] = toPx(ix, v.centreX, v.centreY);
  // The paper always fills the sheet: a centre near the edge stops at the edge; a canvas smaller than the sheet centres.
  const fit = (t: number, side: number) => {
    const span = ix.size * scale;
    return span <= side ? (side - span) / 2 : Math.min(0, Math.max(side - span, t));
  };
  return { scale, tx: fit(w / 2 - cx * scale, w), ty: fit(h / 2 - cy * scale, h) };
}

// A drag of (dx, dy) screen px, or a zoom by a factor about the centre: the new view, clamped to the canvas.
export function pan(ix: CellIndex, v: ChartView, w: number, h: number, dx: number, dy: number, factor = 1): ChartView {
  const t = transform(ix, v, w, h);
  // Start from the centre the sheet shows (after the edge stop), so a drag away from an edge moves at once.
  const cx = (w / 2 - t.tx) / t.scale, cy = (h / 2 - t.ty) / t.scale;
  const zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, v.zoom * factor));
  const px = Math.min(ix.size, Math.max(0, cx - dx / t.scale));
  const py = Math.min(ix.size, Math.max(0, cy - dy / t.scale));
  const [u, vv] = toUnits(ix, px, py);
  const r = (n: number) => Math.round(n * 1000) / 1000;
  return { centreX: r(u), centreY: r(vv), zoom: r(zoom) };
}

export const panIntent = (view: ChartView): IntentMessage => ({ type: "chart.pan", v: 1, body: { view } });
