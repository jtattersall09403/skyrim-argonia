// A place's ground paint (paint.jsonl), read into weights on the land's vertex lattice: the rule of
// tools/places/paint.py, line for line. Rows apply in id order; painting a texture at cover a multiplies every weight
// under it by (1 - a) and adds a to its own; erasing multiplies everything (and the total) by (1 - a), so the world's
// paint shows again. Pure; node tests it against numbers the Python rule wrote (test/paint_rule.json).
import { vnoise } from './path_paint.js';

export const STEP = 128;
export const BRUSHES = ['soft', 'hard', 'scatter'];
export const PMIN = 0.35, OP_MIN = 0.5, SCATTER_SCALE = 1.6, SCATTER_CUT = [0.3, 0.75];

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const smooth = (s) => { s = clamp(s); return s * s * (3 - 2 * s); };
export function falloff(t, soft) { return soft <= 1e-6 ? (t <= 1 ? 1 : 0) : smooth((1 - t) / soft); }
export function scatter(gx, gy, seed) {
  const n = clamp(0.5 + 0.25 * vnoise(seed | 0, gy, gx, SCATTER_SCALE));
  return clamp((n - SCATTER_CUT[0]) / (SCATTER_CUT[1] - SCATTER_CUT[0]));
}
function seg(x, y, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
  const t = L ? clamp(((x - a[0]) * dx + (y - a[1]) * dy) / L) : 0;
  return [Math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy)), t];
}
export function bounds(row) {
  const pts = row.points || row.polygon, pad = row.size ?? 256;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of pts) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); }
  return [x0 - pad, y0 - pad, x1 + pad, y1 + pad];
}
// one row's cover (0..1) at a world point
export function cover(row, x, y) {
  const size = row.size ?? 256, soft = row.softness ?? (row.brush === 'hard' ? 0 : 0.6), strength = row.strength ?? 1;
  let v = 0, p = 1;
  if (row.polygon) {
    const poly = row.polygon; let inside = false, d = Infinity;
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / ((b[1] - a[1]) || 1e-12) + a[0]) inside = !inside;
      d = Math.min(d, seg(x, y, a, b)[0]);
    }
    const feather = size * soft;
    v = feather <= 1e-6 ? (inside ? 1 : 0) : (inside ? smooth(d / feather) : 0);
  } else {
    const pts = row.points.map((q) => [q[0], q[1], clamp(q.length > 2 ? q[2] : 1)]);
    const segs = pts.length > 1 ? pts.slice(1).map((b, i) => [pts[i], b]) : [[pts[0], pts[0]]];
    p = 0;
    for (const [a, b] of segs) {
      const [d, t] = seg(x, y, a, b), pr = a[2] + (b[2] - a[2]) * t, r = size * (PMIN + (1 - PMIN) * pr);
      const f = falloff(d / Math.max(r, 1e-6), soft);
      if (f > v) { v = f; p = pr; }
    }
  }
  if (row.brush === 'scatter') v *= scatter(Math.round(x / STEP), Math.round(y / STEP), row.seed ?? 0);
  return clamp(v * strength * (OP_MIN + (1 - OP_MIN) * p));
}
export function ordered(rows) { return [...rows].sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)); }
// The paint of one cell on a grid x grid lattice (row 0 at the south): {total: Float32Array, w: Map key -> Float32Array}
// or null when no row reaches it.
export function cellPaint(rows, cell, size = 4096, grid = 33) {
  const step = size / (grid - 1), x0 = cell[0] * size, y0 = cell[1] * size, n = grid * grid;
  const total = new Float32Array(n), w = new Map(); let any = false;
  for (const r of ordered(rows)) {
    const b = bounds(r);
    if (b[2] < x0 || b[0] > x0 + size || b[3] < y0 || b[1] > y0 + size) continue;
    const a = new Float32Array(n); let hit = false;
    for (let i = 0; i < grid; i++) for (let j = 0; j < grid; j++) { const v = cover(r, x0 + j * step, y0 + i * step); if (v > 1e-4) { a[i * grid + j] = v; hit = true; } }
    if (!hit) continue;
    any = true;
    for (const arr of w.values()) for (let k = 0; k < n; k++) arr[k] *= 1 - a[k];
    if (r.erase) for (let k = 0; k < n; k++) total[k] *= 1 - a[k];
    else {
      const arr = w.get(r.texture) || new Float32Array(n); w.set(r.texture, arr);
      for (let k = 0; k < n; k++) { arr[k] += a[k]; total[k] = total[k] * (1 - a[k]) + a[k]; }
    }
  }
  if (!any) return null;
  for (const [k, arr] of [...w]) if (!arr.some((v) => v > 1e-4)) w.delete(k);
  return { total, w };
}
export function nextId(rows) {
  let n = 0; for (const r of rows) { const t = String(r.id || '').split('.').pop(); if (/^\d+$/.test(t)) n = Math.max(n, +t); }
  return `paint.${String(n + 1).padStart(4, '0')}`;
}
