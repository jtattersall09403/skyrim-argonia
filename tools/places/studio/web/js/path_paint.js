// How a drawn path is painted onto the land, by the one rule the world's roads and the place build share
// (tools/newworld/world/roadpaint.py; tools/places/build.py plan_paths): from the path's edge (its half width) the road
// holds the measured ramp (PULL_E/PULL_W: full on the path, 0 by 8.55 m out for a road or a street, at 0.8 scale for a
// path, a dirt track or a boardwalk ashore); its track core (two track materials of the ground's road set, shared by the
// along-road noise roadMix) hands to the verge over 4.5 m. Drawn as three alpha layers over the world's ground, bottom
// first (verge, track B, track A), whose composite is the build's weights. Pure, so node tests it against the build's
// own numbers.
export const M_PER_UNIT = 1 / 70;
export const PULL_E = [-0.45, 0.55, 1.55, 2.55, 4.55, 8.55];
export const PULL_W = [0.97, 0.90, 0.76, 0.56, 0.36, 0.0];
export const CORE_IN = -3.0, CORE_OUT = 1.5, TRACK_MIN = 0.15;
export const SCALE = { major: 1.0, minor: 0.8 };
export const STYLE_CLASS = { road: 'major', street: 'major', path: 'minor', dirt: 'minor', track: 'minor', boardwalk: 'minor' };
// a style of one land texture (the world material's id, the end of its editor id); every other style takes the road set
export const PATH_STYLE_LTEX = { skirt: 'verge', mud: 'swamp_mud', sand: 'sand', stone: 'rock' };
// roadpaint.py ROAD_SETS: [track A, track B, verge]
export const ROAD_SETS = {
  marsh: ['mud_track', 'gravel_track', 'verge'], forest: ['gravel_track', 'mud_track', 'verge'],
  upland: ['earth_track', 'gravel_track', 'clay_verge'], coast: ['sand_track', 'gravel_track', 'clay_verge'],
  clay: ['earth_track', 'mud_track', 'clay_verge'],
};
export const DEFAULT_ROAD = 'forest';
const NOISE_SEED = 9113;

function interp(x, xs, ys) {
  if (x <= xs[0]) return ys[0];
  for (let i = 1; i < xs.length; i++) if (x <= xs[i]) return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
  return ys[ys.length - 1];
}
// the road's total weight at e metres from its surface edge (+ outward), at a class's scale
export function pull(e, scale = 1) {
  const x = e / scale;
  if (x <= PULL_E[0]) return Math.min(1, Math.max(PULL_W[0], PULL_W[0] + (PULL_E[0] - x) * 0.03 / 1.5));
  return interp(x, PULL_E, PULL_W);
}
export function reachM(scale = 1) { return PULL_E[PULL_E.length - 1] * scale; }
export function coreShare(e, scale = 1) { return Math.max(0, Math.min(1, (CORE_OUT - e / scale) / (CORE_OUT - CORE_IN))); }
export function trackMix(t) { return TRACK_MIN + (1 - 2 * TRACK_MIN) * (0.5 + 0.5 * Math.tanh(1.6 * t)); }
// -> [pull, track A, track B, verge] weights of the vertex
export function roadWeights(e, scale, mix) {
  const p = pull(e, scale), c = coreShare(e, scale), m = trackMix(mix);
  return [p, p * c * m, p * c * (1 - m), p * (1 - c)];
}
// the same as three alpha layers over any ground, bottom first: [verge, track B, track A] opacities
export function layerOpacities(e, scale, mix) {
  const [, a, b, v] = roadWeights(e, scale, mix);
  const oa = a; let left = 1 - oa;
  const ob = left > 1e-9 ? b / left : 0; left *= 1 - ob;
  const ov = left > 1e-9 ? v / left : 0;
  const c = (x) => Math.max(0, Math.min(1, x));
  return [c(ov), c(ob), c(oa)];
}
// texture.py vnoise / road_mix, bit for bit: value noise on a hashed lattice at world sample positions
function hash(i, j, seed) {
  let h = (Math.imul(i, 374761393) + Math.imul(j, 668265263) + Math.imul(seed, 1442695041)) >>> 0;
  h = Math.imul((h ^ (h >>> 13)) >>> 0, 1274126177) >>> 0;
  h = (h ^ (h >>> 16)) >>> 0;
  return Math.fround(h & 0xffff) / 32767.5 - 1;
}
export function vnoise(seed, r, c, s) {
  const fr = r / s, fc = c / s, i = Math.floor(fr), j = Math.floor(fc);
  let u = fr - i, v = fc - j; u = u * u * (3 - 2 * u); v = v * v * (3 - 2 * v);
  const a = hash(i, j, seed), b = hash(i, j + 1, seed), c_ = hash(i + 1, j, seed), d = hash(i + 1, j + 1, seed);
  return ((a + (b - a) * v) * (1 - u) + (c_ + (d - c_) * v) * u) / 0.42;
}
export function roadMix(x, y) {
  const wy = Math.floor(-y / 128 + 0.5), wx = Math.floor(x / 128 + 0.5);
  return 0.7 * vnoise(NOISE_SEED + 777, wy, wx, 60) + 0.3 * vnoise(NOISE_SEED + 778, wy, wx, 130);
}
export function segDist(x, y, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
  const t = l ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l)) : 0;
  return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy);
}
function keyOf(want, ltex) {
  for (const [k, v] of Object.entries(ltex || {})) if ((v?.edid || '').toLowerCase().endsWith(want)) return k;
  return null;
}
// The road set of the ground the place stands on: the set whose first track the world's own land here carries most
// (the world paints its roads with the province's set), else the default.
export function roadSetName(terrain) {
  const count = {};
  for (const c of terrain?.list || []) for (const q of c.quadrants || []) for (const k of [q.base, ...(q.layers || []).map((l) => l.tex)]) {
    const e = (terrain.ltex?.[k]?.edid || '').toLowerCase();
    for (const [name, set] of Object.entries(ROAD_SETS)) if (e.endsWith(set[0]) || e.endsWith(set[2])) count[name] = (count[name] || 0) + 1;
  }
  let best = DEFAULT_ROAD, n = 0;
  for (const [name, set] of Object.entries(ROAD_SETS)) if ((count[name] || 0) > n) { n = count[name]; best = name; }
  return best;
}
// The land textures a path is painted with, [track A, track B, verge] keys: a key the owner picked (all three), a
// one-texture style, else the road set; null when the land lists none of them.
export function pathLtexes(style, ltex, setName = DEFAULT_ROAD) {
  if (style && ltex?.[style]) return [style, style, style];
  const want = PATH_STYLE_LTEX[style] ? Array(3).fill(PATH_STYLE_LTEX[style]) : ROAD_SETS[setName] || ROAD_SETS[DEFAULT_ROAD];
  const keys = want.map((w) => keyOf(w, ltex));
  return keys.includes(null) ? null : keys;
}
// the path's main texture (its first track), for its swatch
export function pathLtex(style, ltex, setName = DEFAULT_ROAD) { return pathLtexes(style, ltex, setName)?.[0] ?? null; }
// A path's three layer opacities at each of one cell's grid x grid points (row-major, row 0 at the south edge):
// [verge, track B, track A], or null when it does not reach the cell. terrain: bundle.js Terrain (size, step, grid,
// h, cells) for the boardwalk rule.
export function cellLayers(p, cell, t) {
  const scale = SCALE[STYLE_CLASS[p.style] || 'minor'], half = (p.width ?? 256) / 2, reach = half + reachM(scale) / M_PER_UNIT;
  const g = t.grid, x0 = cell[0] * t.size, y0 = cell[1] * t.size, segs = [];
  for (let i = 1; i < p.points.length; i++) {
    const a = p.points[i - 1], b = p.points[i];
    if (Math.max(a[0], b[0]) + reach < x0 || Math.min(a[0], b[0]) - reach > x0 + t.size || Math.max(a[1], b[1]) + reach < y0 || Math.min(a[1], b[1]) - reach > y0 + t.size) continue;
    segs.push([a, b]);
  }
  if (!segs.length) return null;
  const out = [new Float32Array(g * g), new Float32Array(g * g), new Float32Array(g * g)]; let any = false;
  const c = t.cells?.get(cell.join(',')), water = p.style === 'boardwalk' && c?.water ? c.water.height : null;
  for (let r = 0; r < g; r++) for (let col = 0; col < g; col++) {
    const x = x0 + col * t.step, y = y0 + r * t.step;
    let d = Infinity; for (const [a, b] of segs) d = Math.min(d, segDist(x, y, a, b));
    const e = (d - half) * M_PER_UNIT;
    if (e > reachM(scale)) continue;
    // a boardwalk's line is walked on its decks: only where it comes ashore is it a path on the ground
    if (water != null && t.h(cell, r, col) < water - 8) continue;
    const o = layerOpacities(e, scale, roadMix(x, y));
    if (o[0] + o[1] + o[2] > 1e-3) { out[0][r * g + col] = o[0]; out[1][r * g + col] = o[1]; out[2][r * g + col] = o[2]; any = true; }
  }
  return any ? out : null;
}
