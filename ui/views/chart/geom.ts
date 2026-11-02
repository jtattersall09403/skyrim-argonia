// The parchment chart's geometry (1.2 §e), pure: cells in the schema's cell units, pixels on the chart's master
// canvas as out/chart/index.json gives them (x east, y south from the canvas's NW corner; cell y grows north).
import type { CellKey, ChartPlayer, ChartView, IntentMessage } from "../../schema/generated/messages.ts";

export type Rect = [number, number, number, number];
export interface CellIndex {
  size: number;                                            // master canvas side in px
  cells: Record<string, Rect>;                             // "x,y" -> [left, top, width, height] in master px
  // label: [x0, y0, x1, y1] of the chart's lettering; a city (lettered by the sketch) also has its name and cell
  places?: Record<string, { city: boolean; label: Rect | null; name?: string; cell?: [number, number] }>;
  pins?: Record<string, string>;                           // a place kind -> its glyph's path (100-unit box)
  pyramid?: { tile: number; levels: number[] };            // the tile pyramid (tools/chart/pyramid.py): level sides
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
  // Beside the place's marker (1.6rem across) when discovered, else beside a small ink dot.
  return { left: px * t.scale + t.tx + minPx * (discovered ? 1.2 : 0.8), top: py * t.scale + t.ty };
}

// Label collisions. Each box is where a label sits on the sheet in screen px; `order` is the caller's priority
// (major cities first). A label keeps its own spot when free; otherwise it tries the offsets round its anchor (above,
// below, and the four diagonals, then two steps out) and takes the first that is on the sheet and clear of every box
// already placed, and of every obstacle (a place's pin, the player's marker: a label never covers them). A label
// with no free spot is dropped (null): at a closer zoom it separates from its neighbour.
export interface LabelBox { id: string; x: number; y: number; w: number; h: number }
export const hits = (a: LabelBox, b: LabelBox, gap = 0): boolean =>
  a.x < b.x + b.w + gap && b.x < a.x + a.w + gap && a.y < b.y + b.h + gap && b.y < a.y + a.h + gap;
export function placeLabels(boxes: LabelBox[], sheetW: number, sheetH: number, gap = 2,
  obstacles: LabelBox[] = []): Map<string, [number, number] | null> {
  const placed: LabelBox[] = [...obstacles], out = new Map<string, [number, number] | null>();
  for (const b of boxes) {
    const offsets: [number, number][] = [[0, 0], [0, -b.h], [0, b.h], [b.w / 2, -b.h], [b.w / 2, b.h], [-b.w / 2, -b.h],
      [-b.w / 2, b.h], [0, -2 * b.h], [0, 2 * b.h]];
    let spot: [number, number] | null = null;
    for (const [dx, dy] of offsets) {
      const c = { ...b, x: b.x + dx, y: b.y + dy };
      if (c.x < 0 || c.y < 0 || c.x + c.w > sheetW || c.y + c.h > sheetH) continue;
      if (placed.some((p) => hits(c, p, gap))) continue;
      placed.push(c); spot = [dx, dy]; break;
    }
    out.set(b.id, spot);
  }
  return out;
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

// The schema allows 0.05..64. Past ZOOM_MAX the largest render's pixels would show (1.12 look 1: "too low resolution
// when you zoom in"): 8 keeps an 8192-px render at about one pixel per screen pixel on a 1080p sheet.
export const ZOOM_MIN = 1, ZOOM_MAX = 8;

// The land the player has seen (1.12 look 1, the owner: the discovered land round the player): every cell stood in
// uncovers a soft disc REVEAL cells in radius about it, as Morrowind's map fills in round where you walk. A cell is
// about 58 m, so the disc is some 230 m across the land each way.
export const REVEAL = 4;
// The discs in master px: [centre x, centre y, radius]; the view fades each from full inside to none at the rim.
export function revealDiscs(ix: CellIndex, revealed: CellKey[], radius = REVEAL): [number, number, number][] {
  const [, , w] = ix.cells["0,0"];
  return revealed.map((c) => { const [x, y] = toPx(ix, c.x + 0.5, c.y + 0.5); return [x, y, (radius + 0.5) * w]; });
}

// The pyramid level to draw at a scale (screen px per master px, times the device ratio): the smallest level whose
// pixels are at least one to a screen pixel, else the largest.
export function levelFor(levels: number[], size: number, scale: number): number {
  for (const s of levels) if (s >= size * scale * 0.95) return s;
  return levels[levels.length - 1];
}
// The tiles of a level that a w x h viewport shows under transform t: [column, row].
export function visibleTiles(level: number, tile: number, size: number, t: { scale: number; tx: number; ty: number },
  w: number, h: number): [number, number][] {
  const k = (tile * size) / level * t.scale, n = level / tile, out: [number, number][] = [];   // a tile's screen side
  const c0 = Math.max(0, Math.floor(-t.tx / k)), c1 = Math.min(n - 1, Math.floor((w - t.tx) / k));
  const r0 = Math.max(0, Math.floor(-t.ty / k)), r1 = Math.min(n - 1, Math.floor((h - t.ty) / k));
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) out.push([c, r]);
  return out;
}

// One frame of the glide toward a target view (1.12 look 1: pan and zoom smooth on every device): the centre moves
// and the zoom scales a share 1 - e^(-dt/TAU) of the way, so a key's step, a trigger's repeat or a stick glides
// rather than jumps. Returns the target once within a hair of it.
export const TAU_MS = 90;
export function glide(v: ChartView, target: ChartView, dtMs: number): ChartView {
  const a = 1 - Math.exp(-Math.max(0, dtMs) / TAU_MS);
  const zoom = Math.exp(Math.log(v.zoom) + (Math.log(target.zoom) - Math.log(v.zoom)) * a);
  const next = { centreX: v.centreX + (target.centreX - v.centreX) * a, centreY: v.centreY + (target.centreY - v.centreY) * a, zoom };
  const near = Math.abs(next.centreX - target.centreX) < 1e-3 && Math.abs(next.centreY - target.centreY) < 1e-3 &&
    Math.abs(next.zoom / target.zoom - 1) < 1e-3;
  return near ? { ...target } : next;
}

// Master px -> screen px for a view of a w x h viewport: zoom 1 fits the whole canvas in the sheet (contain: the
// province top to bottom with nothing cut off, owner play test 1 item 9; paper shows at the sides); a closer zoom
// pans along both sides.
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

// Zooming in goes to the player (the zoom runs from the whole province down to the land round the player, 1.12 §5):
// the new view is centred on the player at `factor` times the zoom. With no player it zooms about the centre.
export function toward(v: ChartView, player: ChartPlayer | undefined, factor: number): ChartView {
  const zoom = Math.round(Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, v.zoom * factor)) * 1000) / 1000;
  return player && factor > 1 ? { centreX: player.x, centreY: player.y, zoom } : { ...v, zoom };
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
