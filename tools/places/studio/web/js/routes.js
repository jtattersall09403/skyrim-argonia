// Walking routes outside, as people would take them: round buildings, never through open water (decks and
// bridges are walked), and along the paths and streets wherever one leads the right way. A search over a grid of
// 128-unit cells (the land's own grid), the result eased into a line one would walk. Pure: no drawing, no DOM.
const STEP = 128;
const WALKWAY = /dock|boardwalk|bridge|walkway|steps|stair|road|plank|pier|jetty/i;
const STREET = 0.45;   // a step on a path costs this much of a step beside it
const BY_WALL = 1.6;   // a step right beside a wall: people keep to the middle of a gap
const END_FREE = 3;    // cells round each end that are never shut (a stop at a wall, on a ship's deck, at a door)
const MAX_CELLS = 300000; // enough for a walk the length of a town (a search that gave up drew a straight line)
const key = (i, j) => (i + 32768) * 65536 + (j + 32768);

// A small binary heap of [cost, cell key].
class Heap {
  constructor() { this.a = []; }
  get size() { return this.a.length; }
  push(v) {
    const a = this.a; a.push(v); let i = a.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; [a[p], a[i]] = [a[i], a[p]]; i = p; }
  }
  pop() {
    const a = this.a, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last; let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < a.length && a[l][0] < a[m][0]) m = l;
        if (r < a.length && a[r][0] < a[m][0]) m = r;
        if (m === i) break; [a[m], a[i]] = [a[i], a[m]]; i = m;
      }
    }
    return top;
  }
}

// The cells whose middle lies in a ref's footprint (its base's bounds, scaled and turned; the game's yaw is clockwise).
function footprintCells(ref, bounds, shrink, each) {
  const sc = ref.scale ?? 1, rz = ref.rot?.[2] || 0, c = Math.cos(rz), s = Math.sin(rz);
  const x0 = bounds[0][0] * sc + shrink, x1 = bounds[1][0] * sc - shrink, y0 = bounds[0][1] * sc + shrink, y1 = bounds[1][1] * sc - shrink;
  if (x1 <= x0 || y1 <= y0) return;
  const rad = Math.hypot(Math.max(-x0, x1), Math.max(-y0, y1));
  const i0 = Math.round((ref.pos[0] - rad) / STEP), i1 = Math.round((ref.pos[0] + rad) / STEP);
  const j0 = Math.round((ref.pos[1] - rad) / STEP), j1 = Math.round((ref.pos[1] + rad) / STEP);
  for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
    const dx = i * STEP - ref.pos[0], dy = j * STEP - ref.pos[1], lx = c * dx - s * dy, ly = s * dx + c * dy;
    if (lx >= x0 && lx <= x1 && ly >= y0 && ly <= y1) each(i, j);
  }
}

export class Walk {
  // terrain: {heightAt(x, y), waterAt(x, y)} or null (an even floor); refs: the place's outdoor refs;
  // bases: Map(key -> {model, bounds}); paths: [{points, width}]
  constructor({ terrain = null, refs = [], bases = new Map(), paths = [] } = {}) {
    this.t = terrain; this.wall = new Set(); this.wallOf = new Map(); this.deck = new Set(); this.street = new Set(); this.byWall = new Set(); this.wetMemo = new Map();
    let n = 0;
    for (const r of refs) {
      if (r.kind !== 'building') continue;
      const id = ++n;
      const b = bases.get(r.base), bd = b?.bounds;
      if (!bd || bd[1].some((v, k) => v - bd[0][k] > 20000)) continue;
      const deck = r.walk != null || WALKWAY.test(b.model || '');
      footprintCells(r, bd, deck ? -32 : 48, (i, j) => {
        const k = key(i, j);
        if (deck) this.deck.add(k); else { this.wall.add(k); const w = this.wallOf.get(k); if (w) w.push(id); else this.wallOf.set(k, [id]); }
      });
    }
    for (const k of this.deck) this.wall.delete(k);   // one walks a deck even where a house stands on it
    for (const k of this.wall) {
      const i = Math.floor(k / 65536) - 32768, j = (k % 65536) - 32768;
      for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) { const n = key(i + di, j + dj); if (!this.wall.has(n)) this.byWall.add(n); }
    }
    for (const p of paths) {
      const hw = Math.max(STEP * 0.75, (p.width || 256) / 2);
      for (let s = 1; s < p.points.length; s++) {
        const a = p.points[s - 1], b = p.points[s], n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / (STEP / 2)));
        for (let q = 0; q <= n; q++) {
          const x = a[0] + ((b[0] - a[0]) * q) / n, y = a[1] + ((b[1] - a[1]) * q) / n;
          for (let i = Math.round((x - hw) / STEP); i <= Math.round((x + hw) / STEP); i++) for (let j = Math.round((y - hw) / STEP); j <= Math.round((y + hw) / STEP); j++) {
            if (Math.hypot(i * STEP - x, j * STEP - y) <= hw) this.street.add(key(i, j));
          }
        }
      }
    }
  }
  wet(i, j) {
    if (!this.t) return false;
    const k = key(i, j); let w = this.wetMemo.get(k);
    if (w === undefined) {
      const h = this.t.heightAt(i * STEP, j * STEP), wl = this.t.waterAt(i * STEP, j * STEP);
      w = h != null && wl != null && h < wl - 8; this.wetMemo.set(k, w);
    }
    return w;
  }
  // own: the buildings a leg's ends stand in (a hatch on a ship's deck): the leg walks those, and no other
  shut(i, j, own = null) {
    const k = key(i, j);
    if (this.wall.has(k) && !(own && this.wallOf.get(k).every((id) => own.has(id)))) return true;
    return !this.deck.has(k) && !this.wall.has(k) && this.wet(i, j);
  }
  cost(i, j) { const k = key(i, j); return (this.street.has(k) ? STREET : 1) * (this.byWall.has(k) ? BY_WALL : 1); }
  // The way from a to b ([x, y, ...]) as [[x, y], ...]; the straight line when there is no way round.
  // A stop boxed in by its neighbours' outlines (records' boxes are coarser than the walls) gets more room at the ends.
  route(a, b) {
    for (const free of [END_FREE, END_FREE * 3]) { const r = this.search(a, b, free); if (r) return r; }
    return [[a[0], a[1]], [b[0], b[1]]];
  }
  search(a, b, endFree) {
    const si = Math.round(a[0] / STEP), sj = Math.round(a[1] / STEP), gi = Math.round(b[0] / STEP), gj = Math.round(b[1] / STEP);
    if (si === gi && sj === gj) return [[a[0], a[1]], [b[0], b[1]]];
    const pad = 48, i0 = Math.min(si, gi) - pad, i1 = Math.max(si, gi) + pad, j0 = Math.min(sj, gj) - pad, j1 = Math.max(sj, gj) + pad;
    const start = key(si, sj), goal = key(gi, gj), cost = new Map([[start, 0]]), prev = new Map(), heap = new Heap();
    const own = new Set([...(this.wallOf.get(start) || []), ...(this.wallOf.get(goal) || [])]);
    heap.push([0, start]);
    let found = false;
    while (heap.size) {
      const [, cur] = heap.pop();
      if (cur === goal) { found = true; break; }
      if (cost.size > MAX_CELLS) break;
      const ci = Math.floor(cur / 65536) - 32768, cj = (cur % 65536) - 32768, cc = cost.get(cur);
      for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) {
        if (!di && !dj) continue;
        const ni = ci + di, nj = cj + dj;
        if (ni < i0 || ni > i1 || nj < j0 || nj > j1) continue;
        const nearEnd = Math.max(Math.abs(ni - si), Math.abs(nj - sj)) <= endFree || Math.max(Math.abs(ni - gi), Math.abs(nj - gj)) <= endFree;
        if (!nearEnd && this.shut(ni, nj, own)) continue;
        // no cutting a corner between two shut cells
        if (di && dj && !nearEnd && (this.shut(ci + di, cj, own) || this.shut(ci, cj + dj, own))) continue;
        const nk = key(ni, nj), c = cc + Math.hypot(di, dj) * this.cost(ni, nj);
        if (c < (cost.get(nk) ?? Infinity)) { cost.set(nk, c); prev.set(nk, cur); heap.push([c + Math.hypot(ni - gi, nj - gj) * STREET, nk]); }
      }
    }
    if (!found) return null;
    const cells = []; for (let k = goal; k !== start; k = prev.get(k)) cells.push(k);
    cells.reverse();
    const pts = [[a[0], a[1]], ...cells.slice(0, -1).map((k) => [(Math.floor(k / 65536) - 32768) * STEP, ((k % 65536) - 32768) * STEP]), [b[0], b[1]]];
    return thin(ease(pts, (x, y) => this.shut(Math.round(x / STEP), Math.round(y / STEP), own)), 10);
  }
}

// The grid's stair steps eased into a line one would walk: each point drawn to the mean of its neighbours two either
// side, the ends held; a point stays where it was when easing would carry it into something shut.
export function ease(pts, shut, spacing = 64, passes = 5) {
  if (pts.length < 3) return pts;
  let out = [pts[0]];
  for (let s = 1; s < pts.length; s++) {
    const a = pts[s - 1], b = pts[s], n = Math.max(1, Math.floor(Math.hypot(b[0] - a[0], b[1] - a[1]) / spacing));
    for (let k = 1; k <= n; k++) out.push([a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]);
  }
  for (let p = 0; p < passes; p++) {
    const nxt = [out[0]];
    for (let i = 1; i < out.length - 1; i++) {
      let x = 0, y = 0, n = 0;
      for (let k = Math.max(0, i - 2); k <= Math.min(out.length - 1, i + 2); k++) { x += out[k][0]; y += out[k][1]; n++; }
      nxt.push(shut(x / n, y / n) ? out[i] : [x / n, y / n]);
    }
    nxt.push(out[out.length - 1]); out = nxt;
  }
  return out;
}

// Fewer points, the same line within tol units.
export function thin(pts, tol) {
  if (pts.length < 3) return pts;
  const a = pts[0], b = pts[pts.length - 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1e-9;
  let best = -1, k = 0;
  for (let i = 1; i < pts.length - 1; i++) {
    const d = Math.abs((b[0] - a[0]) * (a[1] - pts[i][1]) - (a[0] - pts[i][0]) * (b[1] - a[1])) / L;
    if (d > best) { best = d; k = i; }
  }
  return best <= tol ? [a, b] : [...thin(pts.slice(0, k + 1), tol).slice(0, -1), ...thin(pts.slice(k), tol)];
}

// The point a fraction u (0 to 1) of the way along a line, by length.
export function along(pts, u) {
  if (pts.length < 2) return pts[0];
  let total = 0; const len = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); len.push(d); total += d; }
  let want = Math.max(0, Math.min(1, u)) * total;
  for (let i = 0; i < len.length; i++) {
    if (want <= len[i] || i === len.length - 1) { const f = len[i] ? want / len[i] : 0; return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f]; }
    want -= len[i];
  }
  return pts[pts.length - 1];
}
