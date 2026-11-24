// Things that hang on a wall (a sconce, a torch holder, a shelf, a sign, a banner) put on the wall face under the pen,
// and a light source added with its light. Pure: no three.js, no page (test/wallsnap.test.mjs).
//
// A wall thing is told by its record (its editor id or model names a sconce, holder, shelf, sign, banner, plaque,
// tapestry or trophy) and its mesh: Bethesda builds every such model with its back on the model's origin, so its
// bounds run from about the origin out along one horizontal axis. That axis is the way it faces out of the wall, and
// the Creation Kit's own placements of these bases stand with the origin on the wall face, turned so that axis is the
// face's normal. The face is found on the wall's real triangles (rayTriangles), never its box.
import { localOf, poseFor, lightsOf, isFixture } from './lights.js';
import { applyRot } from './xform.js';

const WALL_NAME = /sconce|torchholder|torch_?holder|wallmount|wall_?shelf|shelf|sign|banner|plaque|tapestry|trophy|wallhang|wall_?torch|walllantern|lanternhook/i;
const BACK = 0.25;      // the back of the bounds lies within this share of the depth from the origin
const VERTICAL = 0.5;   // a face whose normal leans more than this out of level is a floor or roof, not a wall

// {out: [x, y] in the model's frame, back: the bounds' back along it} for a base that hangs on a wall, else null.
export function wallMount(base) {
  const b = base?.bounds; if (!b) return null;
  const named = WALL_NAME.test(`${base.edid || ''} ${base.model || ''} ${base.name || ''}`);
  let best = null;
  for (const k of [0, 1]) {
    const lo = b[0][k], hi = b[1][k], depth = hi - lo; if (depth <= 0) continue;
    for (const s of [1, -1]) {
      const back = s > 0 ? lo : -hi, far = s > 0 ? hi : -lo;   // along the out axis: the back's and the far side's reach
      if (Math.abs(back) > BACK * depth || far <= 0) continue;
      const thin = depth / Math.max(1, b[1][1 - k] - b[0][1 - k]);
      const score = far / depth - Math.abs(back) / depth + (thin < 1 ? 0.1 : 0);
      if (!best || score > best.score) best = { out: k === 0 ? [s, 0] : [0, s], back, score };
    }
  }
  if (!best) return null;
  return named ? { out: best.out, back: best.back } : null;
}

// The nearest triangle a ray meets: {t, point, normal} (normal towards the ray's origin), or null. pos: flat
// [x, y, z, ...]; index: flat triangle corners, or null for unindexed.
export function rayTriangles(o, d, pos, index = null) {
  let best = null;
  const n = index ? index.length / 3 : pos.length / 9;
  const v = (i) => [pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]];
  for (let f = 0; f < n; f++) {
    const a = v(index ? index[f * 3] : f * 3), b = v(index ? index[f * 3 + 1] : f * 3 + 1), c = v(index ? index[f * 3 + 2] : f * 3 + 2);
    const e1 = sub(b, a), e2 = sub(c, a), p = cross(d, e2), det = dot(e1, p);
    if (Math.abs(det) < 1e-12) continue;
    const inv = 1 / det, s = sub(o, a), u = dot(s, p) * inv; if (u < 0 || u > 1) continue;
    const q = cross(s, e1), w = dot(d, q) * inv; if (w < 0 || u + w > 1) continue;
    const t = dot(e2, q) * inv; if (t <= 1e-6 || (best && t >= best.t)) continue;
    let nrm = norm(cross(e1, e2)); if (dot(nrm, d) > 0) nrm = nrm.map((x) => -x);
    best = { t, point: [o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t], normal: nrm };
  }
  return best;
}

// The pose of a wall thing on a face at `point` with world normal `normal`: its origin on the face, its out axis along
// the face's level normal (the game's Z turn, clockwise from above). Null when the face is not a wall.
export function onWall(mount, point, normal) {
  if (!mount || Math.abs(normal[2]) > VERTICAL) return null;
  const h = Math.hypot(normal[0], normal[1]); if (h < 1e-9) return null;
  const want = Math.atan2(normal[1] / h, normal[0] / h), have = Math.atan2(mount.out[1], mount.out[0]);
  let z = have - want; z = Math.atan2(Math.sin(z), Math.cos(z));
  return { pos: [...point], rot: [0, 0, Math.round(z * 10000) / 10000] };
}

// The light a light source added to the place comes with: a light ref (no id) or null. `table` is the measured pairing
// (tools/places/light_pairs.json, served at /api/light_pairs): for each base Skyrim, its DLCs and our source mods
// place with a light beside it, that light and its offset in the base's own frame. A base the table does not hold
// takes the light a placed one of the same base has in the place (the lights stage's binding: the nearest fixture
// within reach), else none. `refs` are the place's refs; `baseOf(ref)` its base.
export function lightFor(fix, base, refs, baseOf, table = {}) {
  if (fix.kind === 'light') return null;
  const t = table?.[fix.base];
  if (t) {
    const s = fix.scale ?? 1, o = applyRot(fix.rot || [0, 0, 0], t.offset.map((v) => v * s));
    return { base: t.light, kind: 'light', pos: fix.pos.map((v, i) => Math.round((v + o[i]) * 100) / 100), rot: [0, 0, 0], scale: 1, layer: 'place', flags: [] };
  }
  if (!isFixture(fix, base)) return null;
  for (const f of refs.filter((r) => r.base === fix.base && r !== fix && !r.removed)) {
    const pair = lightsOf([f], refs, baseOf)[0];
    if (!pair) continue;
    const [light] = pair, local = localOf(light, f);
    const [pos, rot] = poseFor(local, fix, light);
    const out = JSON.parse(JSON.stringify(light));
    delete out.id; delete out.src; delete out.cluster; delete out.unit;
    return { ...out, pos: pos.map((v) => Math.round(v * 100) / 100), rot, layer: 'place' };
  }
  return null;
}

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => { const l = Math.hypot(...a) || 1; return a.map((x) => x / l); };
