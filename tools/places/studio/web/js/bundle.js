// A bundle loaded from /api/bundle/<id>/: bases, actor bases, spaces with refs and (exteriors) terrain.
import { getJSON, getJsonl, API_BASE } from './api.js';
import { normaliseCell } from './terrain_cells.js';

let worker = null, seq = 0; const waiting = new Map();
function terrainOffThread(path) {
  if (!worker) {
    worker = new Worker(new URL('./terrain_worker.js', import.meta.url), { type: 'module' });
    worker.onmessage = ({ data }) => { const w = waiting.get(data.id); waiting.delete(data.id); w(data); };
  }
  const id = ++seq, abs = (p) => new URL(API_BASE + p, location.href).href;
  return new Promise((res) => { waiting.set(id, res); worker.postMessage({ id, jsonUrl: abs(path + 'terrain.json'), f32Url: abs(path + 'terrain.f32') }); });
}

export async function loadBundle(id, { extras = false, optional = false, terrain = true, onProgress = () => {} } = {}) {
  const at = `/bundle/${id}/`;
  const meta = await getJSON(at + 'bundle.json', { optional });
  if (!meta) return null;
  onProgress('bases');
  const [bases, npcs] = await Promise.all([getJsonl(at + 'bases.jsonl'), getJsonl(at + 'npcs.jsonl', { optional: true })]);
  const b = { id, meta, bases: new Map(bases.map((x) => [x.key, x])), npcs: new Map(npcs.map((x) => [x.key, x])), spaces: {} };
  for (const sid of meta.spaces || ['exterior']) {
    onProgress(`space ${sid}`);
    const p = `${at}spaces/${encodeURIComponent(sid)}/`;
    const [space, refs] = await Promise.all([getJSON(p + 'space.json', { optional: true }), getJsonl(p + 'refs.jsonl', { optional: true })]);
    const s = { id: sid, info: space || { space_id: sid, type: sid === 'exterior' ? 'exterior' : 'interior' }, refs };
    if (s.info.type === 'exterior' && terrain) {
      const t = await terrainOffThread(p);
      if (t.error) throw new Error(`terrain of ${id}: ${t.error}`);
      if (!t.none) s.terrain = new Terrain(t.json, new Float32Array(t.f32), t.list);
    }
    b.spaces[sid] = s;
  }
  if (extras) {
    const [people, paths, clear, land] = await Promise.all(['people', 'paths', 'clear', 'land']
      .map((f) => getJsonl(`${at}${f}.jsonl`, { optional: true })));
    b.files = { people, paths, clear, land };
  }
  return b;
}

// Heights of an exterior on the game's grid: cells of 33x33 points, 128 units apart.
export class Terrain {
  constructor(json, f32, list = null) {
    this.json = json; this.f32 = f32; this.size = json.cell_size || 4096; this.grid = json.grid || 33;
    this.step = this.size / (this.grid - 1); this.ltex = json.ltex || {};
    const n = this.grid * this.grid;
    this.list = list || json.cells.map((c) => normaliseCell(c, n));
    this.cells = new Map(this.list.map((c) => [c.cell.join(','), c]));
    this.override = null; // Map "cx,cy" -> Map(idx -> dz): the edit model's land patches
  }
  cellAt(x, y) { return [Math.floor(x / this.size), Math.floor(y / this.size)]; }
  base(cell, row, col) {
    const c = this.cells.get(cell.join(','));
    return c ? this.f32[c.heights + row * this.grid + col] : 0;
  }
  // The height at a grid point, edits included.
  h(cell, row, col) {
    const o = this.override?.get(cell.join(','))?.get(row * this.grid + col);
    return this.base(cell, row, col) + (o || 0);
  }
  has(cell) { return this.cells.has(cell.join(',')); }
  // A world point's grid point(s): edges shared between cells are written on both sides.
  pointsAt(x, y, radius) {
    const out = [], g = this.grid, st = this.step;
    const x0 = Math.ceil((x - radius) / st), x1 = Math.floor((x + radius) / st);
    const y0 = Math.ceil((y - radius) / st), y1 = Math.floor((y + radius) / st);
    for (let gy = y0; gy <= y1; gy++) for (let gx = x0; gx <= x1; gx++) {
      const px = gx * st, py = gy * st, d = Math.hypot(px - x, py - y);
      if (d > radius) continue;
      const per = g - 1;
      const cxs = [Math.floor(gx / per)], cys = [Math.floor(gy / per)];
      if (gx % per === 0) cxs.push(gx / per - 1);
      if (gy % per === 0) cys.push(gy / per - 1);
      const shared = [];
      for (const cx of cxs) for (const cy of cys) {
        const cell = [cx, cy];
        if (this.has(cell)) shared.push({ cell, row: gy - cy * per, col: gx - cx * per });
      }
      if (shared.length) out.push({ x: px, y: py, d, shared });
    }
    return out;
  }
  // Height at any point on the land's own triangles (each quad split along its south-east to north-west diagonal),
  // as tools/places/seat.py `Ground.height`.
  heightAt(x, y) {
    const cell = this.cellAt(x, y);
    if (!this.has(cell)) return null;
    const lx = (x - cell[0] * this.size) / this.step, ly = (y - cell[1] * this.size) / this.step;
    const c = Math.min(this.grid - 2, Math.floor(lx)), r = Math.min(this.grid - 2, Math.floor(ly));
    const fx = lx - c, fy = ly - r;
    const h00 = this.h(cell, r, c), h10 = this.h(cell, r, c + 1), h01 = this.h(cell, r + 1, c), h11 = this.h(cell, r + 1, c + 1);
    return fx + fy <= 1 ? h00 + (h10 - h00) * fx + (h01 - h00) * fy : h11 + (h01 - h11) * (1 - fx) + (h10 - h11) * (1 - fy);
  }
  waterAt(x, y) { const c = this.cells.get(this.cellAt(x, y).join(',')); return c?.water ? c.water.height : null; }
  slopeAt(x, y) {
    const e = 32, hx = this.heightAt(x + e, y) - this.heightAt(x - e, y), hy = this.heightAt(x, y + e) - this.heightAt(x, y - e);
    return Math.atan(Math.hypot(hx, hy) / (2 * e));
  }
  bounds() {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const c of this.list) {
      x0 = Math.min(x0, c.cell[0]); y0 = Math.min(y0, c.cell[1]); x1 = Math.max(x1, c.cell[0]); y1 = Math.max(y1, c.cell[1]);
    }
    return [x0 * this.size, y0 * this.size, (x1 + 1) * this.size, (y1 + 1) * this.size];
  }
}

// Where a ref sits for its seat rule, from the loaded ground and its patches: tools/places/seat.py `seat_z`.
// foot is [x0, y0, x1, y1] in the ref's own frame (or the older [hx, hy], centred), sampled 5 x 5.
function footPoints(x, y, rz, foot, n = 5) {
  if (!foot) return [[x, y]];
  const [x0, y0, x1, y1] = foot.length === 2 ? [-foot[0], -foot[1], foot[0], foot[1]] : foot;
  const c = Math.cos(rz), s = Math.sin(rz), pts = [];
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const u = x0 + ((x1 - x0) * i) / (n - 1), v = y0 + ((y1 - y0) * j) / (n - 1); // Skyrim's yaw turns clockwise seen from above
    pts.push([x + u * c + v * s, y - u * s + v * c]);
  }
  return pts;
}
function footGround(t, x, y, rz, foot, stilts, high = false) {
  let out = null;
  for (const [px, py] of footPoints(x, y, rz, foot)) {
    let h = t.heightAt(px, py); if (h == null) continue;
    if (stilts) { const w = t.waterAt(px, py); if (w != null) h = Math.max(h, w); }
    out = out == null ? h : high ? Math.max(out, h) : Math.min(out, h);
  }
  return out;
}
export function seatZ(terrain, ref, refsById) {
  const s = ref.seat, mode = s?.mode || 'free';
  if (mode === 'free' || !terrain) return ref.pos[2];
  const [x, y] = ref.pos, rz = ref.rot?.[2] || 0;
  let base = null;
  if (mode === 'ground') base = footGround(terrain, x, y, rz, s.foot, false);
  else if (mode === 'stilts') base = footGround(terrain, x, y, rz, s.foot, true);
  else if (mode === 'clear') base = footGround(terrain, x, y, rz, s.foot, false, true);
  else if (mode === 'above') base = terrain.heightAt(x, y);
  else if (mode === 'water') base = terrain.waterAt(x, y) ?? terrain.heightAt(x, y);
  else if (mode === 'on') { const sup = refsById?.get(s.on); if (!sup) return ref.pos[2]; base = sup.pos[2]; }
  if (base == null) return ref.pos[2];
  return Math.round((base + (s.dz || 0)) * 1000) / 1000;
}

