// Grass: the game grows it from each land texture's grass list (terrain.json ltex[].grasses: key, edid, model), so
// it is drawn the same way here: a ring of instanced grass round where the camera looks, placed by the land texture
// that dominates each spot (none on a texture with no list, as on a street), and never under water, on a steep
// slope, under a building or on a path the owner drew. Spots are a jittered grid hashed from the position, so the
// same ground always grows the same blades. The ring's range and thinning are the ground-cover rules of objects.js.
import { ObjectLayer, loadModel } from './objects.js';
import { spotsFor, slopeOk, waterOk } from './grass_rules.js';

const STEP = 150;     // one spot per 150 units (about 2 m)
const RING = 3600;    // radius of the ring, about 50 m
const SHOW_BELOW = 9000; // camera distance beyond which no grass is drawn
const hash = (x, y, k) => { let h = (x * 374761393 + y * 668265263 + k * 2147483647) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

const MAX_SPOTS = 2600; // a ring's cap, so a tablet copes
export class GrassLayer extends ObjectLayer {
  // terrain: bundle.js Terrain (or a getter); blocked(x, y): a drawn path; buildings(): [{pos, r}]
  constructor(origin, { terrain, blocked = () => false, buildings = () => [] }) {
    super(origin, new Map());
    this.terrain = terrain; this.blocked = blocked; this.buildings = buildings; this.view = null;
    this.on = true; this.centre = null; this.stale = true; this.good = new Map(); // grass key -> model usable (true) or missing (false)
    this.lastKey = '';
  }
  invalidate() { this.stale = true; this._dirty = true; this.onDirty(); }
  setOn(on) { this.on = on; this.invalidate(); }
  // The land texture that dominates a point: the top alpha layer over half opaque, else the quadrant's base.
  texAt(x, y) {
    const t = this.terrain(); if (!t) return null;
    const cell = t.cellAt(x, y), c = t.cells.get(cell.join(',')); if (!c) return null;
    const lx = (x - cell[0] * t.size) / t.size, ly = (y - cell[1] * t.size) / t.size;
    const qi = (ly >= 0.5 ? 2 : 0) + (lx >= 0.5 ? 1 : 0), q = c.quadrants[qi]; if (!q) return null;
    const col = Math.max(0, Math.min(16, Math.round(((lx - (qi % 2) * 0.5) / 0.5) * 16)));
    const row = Math.max(0, Math.min(16, Math.round(((ly - (qi >> 1) * 0.5) / 0.5) * 16)));
    for (let i = q.layers.length - 1; i >= 0; i--) { const a = q.layers[i].alpha; if (a && a[row * 17 + col] > 0.5) return q.layers[i].tex; }
    return q.base;
  }
  grassesOf(tex) {
    const t = this.terrain(); const list = t?.ltex?.[tex]?.grasses || [];
    const out = [];
    for (const g of list) {
      if (!g.model) continue;
      if (!this.good.has(g.key)) {
        this.good.set(g.key, undefined);
        this.bases.set(g.key, { key: g.key, kind: 'groundcover', model: g.model, bounds: [[-30, -30, 0], [30, 30, 60]] });
        loadModel(g.model, 0, 1, 'groundcover').then((parts) => { this.good.set(g.key, !!parts?.length); this.invalidate(); });
      }
      if (this.good.get(g.key)) out.push(g);
    }
    return out;
  }
  cull(camera) {
    const v = this.view, t = this.terrain();
    if (v && t && this.on && v.rig.dist < SHOW_BELOW) {
      const c = v.rig.target, cx = c.x + this.origin[0], cy = c.y + this.origin[1];
      if (this.stale || !this.centre || Math.hypot(cx - this.centre[0], cy - this.centre[1]) > RING * 0.2) this.regrow(cx, cy, t);
    } else if (this.refs.length) { this.centre = null; this.setRefs([]); }
    return super.cull(camera);
  }
  regrow(cx, cy, t) {
    this.stale = false; this.centre = [cx, cy];
    const blockers = this.buildings(), list = [];
    const x0 = Math.floor((cx - RING) / STEP), x1 = Math.ceil((cx + RING) / STEP), y0 = Math.floor((cy - RING) / STEP), y1 = Math.ceil((cy + RING) / STEP);
    for (let gx = x0; gx <= x1; gx++) for (let gy = y0; gy <= y1; gy++) {
      const cellTex = this.texAt((gx + 0.5) * STEP, (gy + 0.5) * STEP); if (!cellTex) continue;
      const gs0 = this.grassesOf(cellTex); if (!gs0.length) continue;
      const n = spotsFor(gs0[0].density, hash(gx, gy, 9));
      for (let k = 0; k < n && list.length < MAX_SPOTS; k++) {
        const x = (gx + hash(gx, gy, 1 + 10 * k)) * STEP, y = (gy + hash(gx, gy, 2 + 10 * k)) * STEP;
        if (Math.hypot(x - cx, y - cy) > RING) continue;
        const tex = this.texAt(x, y); if (!tex) continue;
        const gs = this.grassesOf(tex); if (!gs.length) continue;
        const g = gs[Math.floor(hash(gx, gy, 3 + 10 * k) * gs.length) % gs.length];
        const z = t.heightAt(x, y); if (z == null) continue;
        const w = t.waterAt(x, y); if (w != null && !waterOk(g, z - w)) continue;
        const slope = t.slopeAt(x, y);
        if (!slopeOk(g, slope) || this.blocked(x, y)) continue;
        if (blockers.some((b) => Math.hypot(b.pos[0] - x, b.pos[1] - y) < b.r)) continue;
        const [h0, h1] = g.height_range ?? [0.8, 1.3], s = h0 + (h1 - h0) * hash(gx, gy, 5 + 10 * k);
        const rot = [0, 0, hash(gx, gy, 4 + 10 * k) * 6.2832];
        if (g.fit_to_slope) {
          const e = 32, gxs = (t.heightAt(x + e, y) - t.heightAt(x - e, y)) / (2 * e), gys = (t.heightAt(x, y + e) - t.heightAt(x, y - e)) / (2 * e);
          rot[0] = -Math.atan(gys); rot[1] = Math.atan(gxs);
        }
        list.push({ ref: { id: `grass.${gx}.${gy}.${k}`, base: g.key, kind: 'groundcover', pos: [x, y, z], rot, scale: s } });
      }
    }
    this.setRefs(list);
  }
}
