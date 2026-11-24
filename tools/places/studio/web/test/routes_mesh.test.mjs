// Routes judged from the meshes' real triangles (routes.js meshFootprint): a person's way between two stops crosses
// no triangle of a house or a tent standing between them, and takes the path where one leads round.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Walk } from '../js/routes.js';

// a house: four walls 300 high round a 500 x 500 floor (its record's bounds wrongly small, as a reused base's can be)
function house() {
  const P = [], q = (a, b, c, d) => P.push(...a, ...b, ...c, ...a, ...c, ...d), h = 300, r = 250;
  const C = [[-r, -r], [r, -r], [r, r], [-r, r]];
  for (let k = 0; k < 4; k++) { const [x0, y0] = C[k], [x1, y1] = C[(k + 1) % 4]; q([x0, y0, 0], [x1, y1, 0], [x1, y1, h], [x0, y0, h]); }
  q([-r, -r, 2], [r, -r, 2], [r, r, 2], [-r, r, 2]);   // the floor: at the feet, never in the way
  return P;
}
// a tent: a ridge 260 high along Y, its two sloped sides to the ground 220 either side
function tent() {
  const P = [], q = (a, b, c, d) => P.push(...a, ...b, ...c, ...a, ...c, ...d), L = 300;
  q([-220, -L, 0], [-220, L, 0], [0, L, 260], [0, -L, 260]);
  q([220, -L, 0], [220, L, 0], [0, L, 260], [0, -L, 260]);
  return P;
}
const bases = new Map([['house', { model: 'x/house.nif', bounds: [[-50, -50, 0], [50, 50, 300]] }], ['tent', { model: 'x/tent.nif', bounds: [[-220, -300, 0], [220, 300, 260]] }]]);
const meshes = { house: [{ pos: house(), index: null }], tent: [{ pos: tent(), index: null }] };
const refs = [{ id: 'h', kind: 'building', base: 'house', pos: [0, 0, 0], rot: [0, 0, 0.3], scale: 1 },
  { id: 't', kind: 'static', base: 'tent', pos: [0, 1400, 0], rot: [0, 0, 0], scale: 1 }];

// the plan outline of each, turned as placed: a point well inside it is on its footprint triangles
const insideHouse = (p) => { const c = Math.cos(-0.3), s = Math.sin(-0.3), x = c * p[0] - s * p[1], y = s * p[0] + c * p[1]; return Math.abs(x) < 240 && Math.abs(y) < 240; };
const insideTent = (p) => Math.abs(p[0]) < 210 && Math.abs(p[1] - 1400) < 290;
function samples(r, step = 16) {
  const out = [];
  for (let i = 1; i < r.length; i++) { const [a, b] = [r[i - 1], r[i]], n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / step)); for (let k = 0; k <= n; k++) out.push([a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]); }
  return out;
}

test('a route crosses no house or tent footprint, from their triangles', () => {
  const w = new Walk({ bases, refs, meshOf: (r) => meshes[r.base] });
  for (const [a, b] of [[[0, -1200], [0, 2800]], [[-900, 700], [900, 700]], [[0, -1200], [0, 1400 + 600]]]) {
    const r = w.route(a, b);
    const bad = samples(r).filter((p) => insideHouse(p) || insideTent(p));
    assert.equal(bad.length, 0, `through ${bad.length} points: ${JSON.stringify(bad.slice(0, 3))}`);
  }
  // by its record's small box alone, the house would be walked through: the triangles are what keeps it out
  const boxOnly = new Walk({ bases, refs: [refs[0]] }).route([0, -1200], [0, 1200]);
  assert.ok(samples(boxOnly).some(insideHouse), 'the box alone lets the way through the house');
});

test('a route follows a path round the house where one leads there', () => {
  const path = { points: [[0, -1200], [-700, -600], [-700, 600], [0, 1200]], width: 200 };
  const w = new Walk({ bases, refs: [refs[0]], paths: [path], meshOf: (r) => meshes[r.base] });
  const r = w.route([0, -1200], [0, 1200]), pts = samples(r);
  const near = (p) => path.points.slice(1).some((b, i) => {
    const a = path.points[i], dx = b[0] - a[0], dy = b[1] - a[1], u = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)));
    return Math.hypot(a[0] + u * dx - p[0], a[1] + u * dy - p[1]) < 200;
  });
  const on = pts.filter(near).length / pts.length;
  assert.ok(on > 0.7, `on the path for ${Math.round(on * 100)}% of the way`);
  assert.equal(pts.filter(insideHouse).length, 0);
});
