// Routes on the built place's own walking mesh (the game's navmesh, exported by tools/places/navexport.py): the
// way the game's people find theirs. A search over the mesh's triangles (preferred-path triangles cheaper, water
// dearer), then the shortest line through the triangles it found, held a body's width off each corner. Pure: no
// drawing, no DOM.
const CELL = 512;        // the lookup grid over the triangles
const BODY = 32;         // how far off a corner a walker keeps
const PREFER = 0.6;      // a preferred-path triangle costs this much of a plain one
const WADE = 3;          // a water triangle costs this many plain ones
const REACH = 300;       // a stop this far off the mesh (a chair against a wall, a bed) is walked to from its nearest triangle
const REACH_Z = 220;     // and no more than this above or below it

class Heap {
  constructor() { this.k = []; this.v = []; }
  get size() { return this.k.length; }
  push(key, val) {
    const k = this.k, v = this.v; let i = k.length; k.push(key); v.push(val);
    while (i > 0) { const p = (i - 1) >> 1; if (k[p] <= key) break; k[i] = k[p]; v[i] = v[p]; i = p; }
    k[i] = key; v[i] = val;
  }
  pop() {
    const k = this.k, v = this.v, top = v[0], lk = k.pop(), lv = v.pop(), n = k.length;
    if (n) {
      let i = 0;
      for (;;) {
        let c = 2 * i + 1; if (c >= n) break;
        if (c + 1 < n && k[c + 1] < k[c]) c++;
        if (k[c] >= lk) break;
        k[i] = k[c]; v[i] = v[c]; i = c;
      }
      k[i] = lk; v[i] = lv;
    }
    return top;
  }
}

const cross = (ax, ay, bx, by, cx, cy) => (bx - ax) * (cy - ay) - (cx - ax) * (by - ay);

export class NavMesh {
  // {verts: [x, y, z, ...], tris: [a, b, c, ...], nb: [across edge 0-1, 1-2, 2-0, ...], kind: [0 | 1 preferred | 2 water, ...]}
  constructor({ verts, tris, nb, kind }) {
    this.v = Float64Array.from(verts); this.t = Int32Array.from(tris); this.nb = Int32Array.from(nb); this.kind = Uint8Array.from(kind);
    const n = this.n = this.kind.length; this.cx = new Float64Array(n); this.cy = new Float64Array(n); this.cz = new Float64Array(n);
    this.grid = new Map();
    for (let i = 0; i < n; i++) {
      const a = this.t[3 * i] * 3, b = this.t[3 * i + 1] * 3, c = this.t[3 * i + 2] * 3, v = this.v;
      this.cx[i] = (v[a] + v[b] + v[c]) / 3; this.cy[i] = (v[a + 1] + v[b + 1] + v[c + 1]) / 3; this.cz[i] = (v[a + 2] + v[b + 2] + v[c + 2]) / 3;
      const x0 = Math.floor(Math.min(v[a], v[b], v[c]) / CELL), x1 = Math.floor(Math.max(v[a], v[b], v[c]) / CELL);
      const y0 = Math.floor(Math.min(v[a + 1], v[b + 1], v[c + 1]) / CELL), y1 = Math.floor(Math.max(v[a + 1], v[b + 1], v[c + 1]) / CELL);
      for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) { const k = x * 100003 + y, g = this.grid.get(k); if (g) g.push(i); else this.grid.set(k, [i]); }
    }
    // the search's working arrays, reused: a stamp says which entries belong to the search in hand
    this.g = new Float64Array(n); this.from = new Int32Array(n); this.stamp = new Uint32Array(n); this.round = 0;
  }
  // The nearest point of triangle i to (x, y) on the plan and the triangle's own height there, left in qx, qy, qz;
  // returns how far off it is (0 when the point is over the triangle).
  near(i, x, y) {
    const v = this.v, t = this.t, a = t[3 * i] * 3, b = t[3 * i + 1] * 3, c = t[3 * i + 2] * 3;
    const area = cross(v[a], v[a + 1], v[b], v[b + 1], v[c], v[c + 1]);
    const d1 = cross(v[a], v[a + 1], v[b], v[b + 1], x, y), d2 = cross(v[b], v[b + 1], v[c], v[c + 1], x, y), d3 = cross(v[c], v[c + 1], v[a], v[a + 1], x, y);
    let qx = x, qy = y, d = 0;
    // a triangle with no area on the plan (a sliver) holds nothing: only its edges are near
    if (area === 0 || ((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0))) {
      d = Infinity;
      for (let k = 0; k < 3; k++) {
        const p = t[3 * i + k] * 3, q = t[3 * i + (k + 1) % 3] * 3, dx = v[q] - v[p], dy = v[q + 1] - v[p + 1];
        const u = Math.max(0, Math.min(1, ((x - v[p]) * dx + (y - v[p + 1]) * dy) / (dx * dx + dy * dy || 1e-9)));
        const ex = v[p] + dx * u, ey = v[p + 1] + dy * u, e = Math.hypot(x - ex, y - ey);
        if (e < d) { d = e; qx = ex; qy = ey; }
      }
    }
    this.qx = qx; this.qy = qy;
    if (Math.abs(area) < 1e-9) this.qz = this.cz[i];
    else {
      const wb = cross(v[a], v[a + 1], qx, qy, v[c], v[c + 1]) / area, wc = cross(v[a], v[a + 1], v[b], v[b + 1], qx, qy) / area;
      this.qz = v[a + 2] + wb * (v[b + 2] - v[a + 2]) + wc * (v[c + 2] - v[a + 2]);
    }
    return d;
  }
  // Where a point stands on the mesh: {tri, x, y, z, d}: the triangle under it nearest its height (d 0), else the
  // nearest within reach and the point of it nearest (d: how far off); null for none. Heights are the triangle's
  // own at that point, so a long slope is not mistaken for the deck over its foot.
  snap(p) {
    const gx = Math.floor(p[0] / CELL), gy = Math.floor(p[1] / CELL); let best = null, bd = Infinity;
    for (let x = gx - 1; x <= gx + 1; x++) for (let y = gy - 1; y <= gy + 1; y++) {
      for (const i of this.grid.get(x * 100003 + y) || []) {
        const d = this.near(i, p[0], p[1]); if (d > REACH) continue;
        const dz = Math.abs(this.qz - (p[2] ?? this.qz)); if (dz > REACH_Z + (d ? 0 : 200)) continue;
        const score = d + dz * 0.25; if (score < bd) { bd = score; best = { tri: i, x: this.qx, y: this.qy, z: this.qz, d }; }
      }
    }
    return best;
  }
  // the triangle a point stands on (snap); -1 for none
  triAt(p) { const s = this.snap(p); return s ? s.tri : -1; }
  // The walked way from a to b ([x, y, z]) as [[x, y, z], ...]; null when either end is off the mesh or no way
  // joins them. Every point lies on the mesh, but for an end that stands off it (a chair against a wall, a bed):
  // that end is the stop itself, and the point next to it is where the mesh comes nearest.
  route(a, b) {
    const sa = this.snap(a), sb = this.snap(b); if (!sa || !sb) return null;
    const A = [a[0], a[1], a[2] ?? sa.z], B = [b[0], b[1], b[2] ?? sb.z];
    const A1 = sa.d > 1 ? [sa.x, sa.y, sa.z] : A, B1 = sb.d > 1 ? [sb.x, sb.y, sb.z] : B, s = sa.tri, e = sb.tri;
    let way = [A1, B1];
    if (s !== e) {
      const round = ++this.round, g = this.g, from = this.from, stamp = this.stamp, heap = new Heap();
      const cost = (i) => (this.kind[i] === 1 ? PREFER : this.kind[i] === 2 ? WADE : 1);
      // searched from the far end, so the chain of "from" reads start to end
      g[e] = 0; from[e] = -1; stamp[e] = round; heap.push(0, e);
      let found = false;
      while (heap.size) {
        const cur = heap.pop();
        if (cur === s) { found = true; break; }
        for (let k = 0; k < 3; k++) {
          const o = this.nb[3 * cur + k]; if (o < 0) continue;
          const c = g[cur] + Math.hypot(this.cx[o] - this.cx[cur], this.cy[o] - this.cy[cur], this.cz[o] - this.cz[cur]) * (cost(o) + cost(cur)) / 2;
          if (stamp[o] !== round || c < g[o]) { g[o] = c; from[o] = cur; stamp[o] = round; heap.push(c + Math.hypot(this.cx[o] - A1[0], this.cy[o] - A1[1]) * PREFER, o); }
        }
      }
      if (!found) return null;
      const chain = []; for (let i = s; i !== -1; i = from[i]) chain.push(i);
      way = this.pull(A1, B1, chain); if (!way) return null;
    }
    if (A1 !== A) way.unshift(A);
    if (B1 !== B) way.push(B);
    return way;
  }
  // which edge of triangle i leads to triangle j; -1 for none
  edgeTo(i, j) { for (let k = 0; k < 3; k++) if (this.nb[3 * i + k] === j) return k; return -1; }
  // The gateway from triangle i into triangle j as [left, right] points ([x, y, z]) seen walking through it; null
  // when neither names the other. Read from i's edge (the walker leaves i's third corner behind, which settles
  // which end is on the left whichever way i winds), else from j's when only j names i. Where the two lie in
  // different cells' meshes and their edges only partly overlap, the gateway is the stretch they share.
  portal(i, j) {
    const v = this.v, t = this.t, ki = this.edgeTo(i, j), kj = this.edgeTo(j, i);
    const pt = (o) => [v[o], v[o + 1], v[o + 2]];
    const side = (m, k) => {   // [left, right] corners of edge k of triangle m, walking out of m
      const p = t[3 * m + k] * 3, q = t[3 * m + (k + 1) % 3] * 3, o = t[3 * m + (k + 2) % 3] * 3;
      return cross(v[p], v[p + 1], v[q], v[q + 1], v[o], v[o + 1]) > 0 ? [q, p] : [p, q];
    };
    if (ki < 0 && kj < 0) return null;
    if (ki < 0) { const [l, r] = side(j, kj); return [pt(r), pt(l)]; }
    const [l, r] = side(i, ki), L = pt(l), R = pt(r);
    if (kj < 0) return [L, R];
    const [jl, jr] = side(j, kj);
    if ((jl === l && jr === r) || (jl === r && jr === l)) return [L, R];   // one mesh: the same two corners
    const dx = R[0] - L[0], dy = R[1] - L[1], len2 = dx * dx + dy * dy || 1e-9;
    const along = (o) => ((v[o] - L[0]) * dx + (v[o + 1] - L[1]) * dy) / len2, u1 = along(jl), u2 = along(jr);
    const lo = Math.max(0, Math.min(u1, u2)), hi = Math.min(1, Math.max(u1, u2));
    if (hi <= lo) return [L, R];
    const at = (u) => [L[0] + dx * u, L[1] + dy * u, L[2] + (R[2] - L[2]) * u];
    return [at(lo), at(hi)];
  }
  // The shortest line from A to B ([x, y, z], on the chain's first and last triangles) through a chain of
  // triangles (the funnel), each gateway narrowed by a body's width at both ends; the line takes its height from
  // every gateway it crosses, so it lies on the mesh over a rise or a deck.
  pull(A, B, chain) {
    const gates = [];
    for (let i = 0; i + 1 < chain.length; i++) {
      const p = this.portal(chain[i], chain[i + 1]); if (!p) return null;
      const [L, R] = p;
      const w = Math.hypot(R[0] - L[0], R[1] - L[1]), m = Math.min(BODY, w * 0.45) / (w || 1);
      gates.push([[L[0] + (R[0] - L[0]) * m, L[1] + (R[1] - L[1]) * m, L[2] + (R[2] - L[2]) * m], [R[0] + (L[0] - R[0]) * m, R[1] + (L[1] - R[1]) * m, R[2] + (L[2] - R[2]) * m]]);
    }
    gates.push([B, B]);
    // two funnel points are one when they stand at the same spot, whichever gateway each came from
    const eq = (p, q) => p === q || (Math.abs(p[0] - q[0]) < 1e-6 && Math.abs(p[1] - q[1]) < 1e-6);
    const corners = [{ p: A, at: -1 }];
    let apex = A, left = A, right = A, ai = -1, li = -1, ri = -1;
    for (let i = 0; i < gates.length; i++) {
      const [L, R] = gates[i];
      if (cross(apex[0], apex[1], right[0], right[1], R[0], R[1]) >= 0) {
        if (eq(apex, right) || cross(apex[0], apex[1], left[0], left[1], R[0], R[1]) < 0) { right = R; ri = i; }
        else { corners.push({ p: left, at: li }); apex = left; ai = li; left = right = apex; li = ri = ai; i = ai; continue; }
      }
      if (cross(apex[0], apex[1], left[0], left[1], L[0], L[1]) <= 0) {
        if (eq(apex, left) || cross(apex[0], apex[1], right[0], right[1], L[0], L[1]) > 0) { left = L; li = i; }
        else { corners.push({ p: right, at: ri }); apex = right; ai = ri; left = right = apex; li = ri = ai; i = ai; continue; }
      }
    }
    corners.push({ p: B, at: gates.length - 1 });
    // between two corners the line crosses the gateways in between: a point at each, at the gateway's height there
    const out = [A];
    for (let c = 1; c < corners.length; c++) {
      const P = corners[c - 1].p, Q = corners[c].p;
      for (let i = corners[c - 1].at + 1; i < corners[c].at; i++) {
        const [L, R] = gates[i], dx = R[0] - L[0], dy = R[1] - L[1], den = (Q[0] - P[0]) * dy - (Q[1] - P[1]) * dx;
        if (Math.abs(den) < 1e-9) continue;
        const u = Math.max(0, Math.min(1, ((Q[0] - P[0]) * (L[1] - P[1]) - (Q[1] - P[1]) * (L[0] - P[0])) / -den));
        const last = out[out.length - 1], x = L[0] + dx * u, y = L[1] + dy * u;
        if (Math.hypot(x - last[0], y - last[1]) > 24) out.push([x, y, L[2] + (R[2] - L[2]) * u]);
      }
      out.push(Q);
    }
    return out;
  }
}
