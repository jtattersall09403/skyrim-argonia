// node test/navroute.test.mjs : the router on a small made-up mesh and, when it has been exported, on Helstrom's.
import assert from 'node:assert';
import fs from 'node:fs';
import { NavMesh } from '../js/navroute.js';

// an L-shaped floor of unit squares (each two triangles), 100 units a square: (0,0)-(3,1) and (2,1)-(3,3)
function squares(cells) {
  const verts = [], tris = [], id = new Map();
  const vid = (x, y) => { const k = `${x},${y}`; if (!id.has(k)) { id.set(k, verts.length / 3); verts.push(x * 100, y * 100, 0); } return id.get(k); };
  for (const [x, y] of cells) { const a = vid(x, y), b = vid(x + 1, y), c = vid(x + 1, y + 1), d = vid(x, y + 1); tris.push(a, b, c, a, c, d); }
  const n = tris.length / 3, nb = new Array(n * 3).fill(-1), edge = new Map();
  for (let t = 0; t < n; t++) for (let k = 0; k < 3; k++) {
    const p = tris[3 * t + k], q = tris[3 * t + (k + 1) % 3], key = p < q ? `${p},${q}` : `${q},${p}`;
    if (edge.has(key)) { const [t2, k2] = edge.get(key); nb[3 * t + k] = t2; nb[3 * t2 + k2] = t; } else edge.set(key, [t, k]);
  }
  return { verts, tris, nb, kind: new Array(n).fill(0) };
}
const L = new NavMesh(squares([[0, 0], [1, 0], [2, 0], [2, 1], [2, 2]]));
const r = L.route([20, 50, 0], [250, 280, 0]);
assert(r, 'a way round the corner');
const len = (pts) => pts.slice(1).reduce((s, p, i) => s + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);
// the shortest way bends once at the inner corner (200, 100), held a little off it
assert(len(r) < Math.hypot(180, 50) + Math.hypot(50, 180) + 40, `too long: ${len(r)}`);
assert(r.some((p) => Math.hypot(p[0] - 200, p[1] - 100) < 60), 'bends at the inner corner');
for (const p of r) assert(L.triAt(p) >= 0, `off the floor at ${p}`);
assert(Math.abs(len(L.route([20, 50, 0], [60, 50, 0])) - 40) < 1e-6, 'straight inside one square');
assert.equal(L.route([20, 50, 0], [30, 60, 0]).length, 2, 'two points inside one triangle');
assert.equal(L.route([20, 50, 0], [2000, 2000, 0]), null, 'off the mesh');
// a straight corridor is walked straight
const C = new NavMesh(squares([[0, 0], [1, 0], [2, 0], [3, 0]]));
const s = C.route([10, 50, 0], [390, 50, 0]);
assert(Math.abs(len(s) - 380) < 1e-6 && s.every((p) => Math.abs(p[1] - 50) < 1e-6), 'straight along a corridor');

const real = new URL('../../../../../out/places/nav/helstrom.json', import.meta.url);
if (fs.existsSync(real)) {
  const d = JSON.parse(fs.readFileSync(real)), t0 = performance.now(), m = new NavMesh(d.spaces.exterior), t1 = performance.now();
  // between the middles of two far triangles of the biggest island
  const seen = new Uint8Array(m.n), stack = [0]; let far = 0; seen[0] = 1;
  while (stack.length) { const i = stack.pop(); if (Math.hypot(m.cx[i] - m.cx[0], m.cy[i] - m.cy[0]) > Math.hypot(m.cx[far] - m.cx[0], m.cy[far] - m.cy[0])) far = i; for (let k = 0; k < 3; k++) { const o = m.nb[3 * i + k]; if (o >= 0 && !seen[o]) { seen[o] = 1; stack.push(o); } } }
  const a = [m.cx[0], m.cy[0], m.cz[0]], b = [m.cx[far], m.cy[far], m.cz[far]], t2 = performance.now(), w = m.route(a, b), t3 = performance.now();
  assert(w && w.length > 2, 'a way across Helstrom');
  let offMesh = 0; for (const p of w) if (m.triAt(p) < 0) offMesh++;
  assert.equal(offMesh, 0, 'every point of the way is on the mesh');
  console.log(`helstrom: ${m.n} triangles made ready in ${Math.round(t1 - t0)} ms; a walk of ${Math.round(len(w) / 70)} m (${Math.round(Math.hypot(a[0] - b[0], a[1] - b[1]) / 70)} m straight) found in ${Math.round(t3 - t2)} ms, ${w.length} points`);
}
console.log('navroute ok');
