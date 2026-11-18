// Ground height, water and slope at a point, worked out on this device from the loaded ground and its land patches:
// the same arithmetic as tools/places/seat.py `Ground.at` (the /seat endpoint's answer), so the studio answers it
// offline. tools/tests/test_places_studio_offline.py proves the two give equal answers on sample points.
// `t` is a bundle.js Terrain (heights with the edit model's patches over them); `defaultWater` the space's
// water.default_height.
const CELL = 4096, STEP = CELL / 32, NO_WATER = -1.0e6, N = 33;

function vertex(t, gx, gy) {
  const cx = Math.floor(gx / 32), col = gx - 32 * cx, cy = Math.floor(gy / 32), row = gy - 32 * cy;
  if (t.has([cx, cy])) return t.h([cx, cy], row, col);
  for (const [dcx, dcy] of [[-1, 0], [0, -1], [-1, -1]]) {
    const c2 = col - 32 * dcx, r2 = row - 32 * dcy;
    if (t.has([cx + dcx, cy + dcy]) && c2 <= 32 && r2 <= 32) return t.h([cx + dcx, cy + dcy], r2, c2);
  }
  return null;
}
export function heightAt(t, x, y) {
  const fx = x / STEP, fy = y / STEP, gx = Math.floor(fx), gy = Math.floor(fy), tx = fx - gx, ty = fy - gy;
  const v = [vertex(t, gx, gy), vertex(t, gx + 1, gy), vertex(t, gx, gy + 1), vertex(t, gx + 1, gy + 1)];
  if (v.some((a) => a == null)) {
    const known = v.filter((a) => a != null);
    return known.length ? known.reduce((s, a) => s + a, 0) / known.length : null;
  }
  if (tx + ty <= 1) return v[0] + (v[1] - v[0]) * tx + (v[2] - v[0]) * ty;
  return v[3] + (v[2] - v[3]) * (1 - tx) + (v[1] - v[3]) * (1 - ty);
}
export function waterAt(t, x, y, defaultWater = null) {
  const c = t.cells.get(`${Math.floor(x / CELL)},${Math.floor(y / CELL)}`);
  const own = c?.water && Math.abs(c.water.height) < 1e30 ? c.water.height : undefined;
  const w = own !== undefined ? own : defaultWater;
  return w == null || w <= NO_WATER ? null : w;
}
export function normalAt(t, x, y, d = STEP) {
  const hx0 = heightAt(t, x - d, y), hx1 = heightAt(t, x + d, y), hy0 = heightAt(t, x, y - d), hy1 = heightAt(t, x, y + d);
  if ([hx0, hx1, hy0, hy1].some((a) => a == null)) return [0, 0, 1];
  const nx = -(hx1 - hx0) / (2 * d), ny = -(hy1 - hy0) / (2 * d), nz = 1, m = Math.sqrt(nx * nx + ny * ny + nz * nz);
  return [nx / m, ny / m, nz / m];
}
export function slopeAt(t, x, y) {
  return (Math.acos(Math.max(-1, Math.min(1, normalAt(t, x, y)[2]))) * 180) / Math.PI;
}
const round = (v, n) => Math.round(v * 10 ** n) / 10 ** n;
// GET /api/place/<id>/seat's answer: {x, y, ground, water, slope, normal, sha}.
export function seatAt(t, x, y, defaultWater = null, sha = null) {
  return { x, y, ground: heightAt(t, x, y), water: waterAt(t, x, y, defaultWater), slope: round(slopeAt(t, x, y), 2),
    normal: normalAt(t, x, y).map((a) => round(a, 4)), sha };
}
export const GRID = N;
