// A place's units: each a thing a builder would call one structure (a house with its porch, door, steps and lamps; a
// ship with its masts, rigging and gangplank; a tent with its bedrolls), which a tap selects whole and a move carries
// whole. Pure: no three.js, no page; node tests it (test/units.test.mjs).
//
// Membership, one rule:
//   1. a ref's own `unit` names its unit ("" takes it out of every unit); else the draft's `cluster` does;
//   2. a building in no unit starts its own; a unit lying within another's body (its footprint mostly inside the
//      body's pieces, its height within) is part of it, as a ship's sail is of its hull, a doorframe of its house and
//      a tent's bedding cluster of the tent;
//   3. a ref in no unit belongs to the unit of what it is seated `on`; else to the unit whose body piece it stands
//      within (the smallest), in plan and between that piece's floor and roof (a bedroll inside a tent, a lamp on a
//      ship's deck);
// A unit's body is its buildings and its big pieces (200 by 200 units or more), never a marker, an effect or the
// ground's things; a unit with no such piece is all body.
//   4. plants, trees, ground cover, rocks and people belong to the ground, never to a unit but by their own `unit`.
// A unit of one piece one sees (its lights and invisible walls aside) is no unit.

import { patrolOf } from './routines.js';
import { turnRot } from './xform.js';

const rnd = (v, k = 100) => Math.round(v * k) / k;
const clone = (o) => JSON.parse(JSON.stringify(o));
const norm = (a) => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };
const GROUND = new Set(['tree', 'plant', 'groundcover', 'rock', 'actor']);
const BODY_AREA = 40000;          // a piece this big in plan (200 by 200 units) is part of its unit's body
const INSIDE = 0.5;               // a unit lying at least half inside another's body is part of it
const FLOOR = 48, ROOF = 16;      // how far under a body's floor, and over its roof, a thing may stand and be in it

// A ref's box in the world's plan and height: its base's bounds turned by its Z angle (the game's clockwise turn) and
// scaled, at its drawn position. Without bounds, a 64-unit box round its origin.
export function boxOf(r, base, pos = r.pos) {
  const b = base?.bounds || [[-32, -32, 0], [32, 32, 64]], s = r.scale ?? 1, a = r.rot?.[2] || 0, c = Math.cos(a), n = Math.sin(a);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const x of [b[0][0], b[1][0]]) for (const y of [b[0][1], b[1][1]]) {
    const wx = pos[0] + s * (c * x + n * y), wy = pos[1] + s * (-n * x + c * y);
    x0 = Math.min(x0, wx); y0 = Math.min(y0, wy); x1 = Math.max(x1, wx); y1 = Math.max(y1, wy);
  }
  return { x0, y0, x1, y1, z0: pos[2] + s * b[0][2], z1: pos[2] + s * b[1][2] };
}
const area = (b) => Math.max(0, b.x1 - b.x0) * Math.max(0, b.y1 - b.y0);
const union = (bs) => bs.reduce((u, b) => (u ? { x0: Math.min(u.x0, b.x0), y0: Math.min(u.y0, b.y0), x1: Math.max(u.x1, b.x1), y1: Math.max(u.y1, b.y1), z0: Math.min(u.z0, b.z0), z1: Math.max(u.z1, b.z1) } : { ...b }), null);
const overlap = (a, b) => area({ x0: Math.max(a.x0, b.x0), y0: Math.max(a.y0, b.y0), x1: Math.min(a.x1, b.x1), y1: Math.min(a.y1, b.y1) });
const within = (p, b) => p[0] >= b.x0 && p[0] <= b.x1 && p[1] >= b.y0 && p[1] <= b.y1 && p[2] >= b.z0 - FLOOR && p[2] <= b.z1 + ROOF;
const HELPER = /marker|^fx|mist/i;
const onOf = (r) => (r.seat?.mode === 'on' ? (Array.isArray(r.seat.on) ? r.seat.on[0] : r.seat.on) : null);

// {units: Map id -> {id, head, name, members: [ids], body, box}, of: Map ref id -> unit id}
// refs: the space's refs; baseOf(ref) its base; posOf(ref) where it is drawn (seated).
export function unitsOf(refs, baseOf, posOf = (r) => r.pos) {
  const live = refs.filter((r) => !r.removed && r.pos), byId = new Map(live.map((r) => [r.id, r]));
  const box = new Map(live.map((r) => [r.id, boxOf(r, baseOf(r), posOf(r))]));
  const of = new Map(), explicit = new Set();
  for (const r of live) {
    if (typeof r.unit === 'string') { explicit.add(r.id); if (r.unit) of.set(r.id, r.unit); }
    else if (r.cluster && !GROUND.has(r.kind)) of.set(r.id, String(r.cluster));
  }
  for (const r of live) if (!of.has(r.id) && !explicit.has(r.id) && r.kind === 'building' && !onOf(r)) of.set(r.id, `u.${r.id}`);
  const groups = () => { const g = new Map(); for (const [id, u] of of) { if (!g.has(u)) g.set(u, []); g.get(u).push(id); } return g; };
  const helper = (r) => HELPER.test(`${baseOf(r)?.edid || ''} ${baseOf(r)?.model || ''}`);
  // a unit's body: the boxes of its buildings and big pieces (all its pieces when it has none of those)
  const bodyOf = (ids) => {
    const big = ids.filter((id) => { const r = byId.get(id); return !GROUND.has(r.kind) && !helper(r) && (r.kind === 'building' || area(box.get(id)) >= BODY_AREA); });
    return (big.length ? big : ids).map((id) => box.get(id));
  };
  const bodyArea = (bs) => bs.reduce((s, b) => s + area(b), 0);
  const inBody = (full, bs) => Math.min(area(full), bs.reduce((s, b) => s + overlap(full, b), 0)) / (area(full) || 1);
  // rule 2: a unit inside another's body joins it, the smaller into the larger (a ref whose unit is set stays)
  let g = groups();
  const order = [...g.keys()].map((u) => ({ u, body: bodyOf(g.get(u)) })).sort((a, b) => bodyArea(b.body) - bodyArea(a.body));
  for (let i = order.length - 1; i > 0; i--) {
    const A = order[i], full = union(A.body);
    for (let j = 0; j < i; j++) {
      const B = order[j], bz = union(B.body);
      if (!g.has(B.u) || bodyArea(B.body) < 1.5 * bodyArea(A.body)) continue;
      if (inBody(full, B.body) < INSIDE || full.z0 > bz.z1 + ROOF || full.z1 < bz.z0 - FLOOR) continue;
      for (const id of g.get(A.u)) if (!explicit.has(id)) of.set(id, B.u);
      g = groups(); break;
    }
  }
  // rule 3: what has no unit, by its seat, then by where it stands
  const pieces = [...groups()].flatMap(([u, ids]) => bodyOf(ids).map((body) => ({ u, body }))).sort((a, b) => area(a.body) - area(b.body));
  const free = live.filter((r) => !of.has(r.id) && !explicit.has(r.id));
  const bySeat = () => { let moved = true; while (moved) { moved = false; for (const r of free) if (!of.has(r.id)) { const u = of.get(onOf(r)); if (u) { of.set(r.id, u); moved = true; } } } };
  bySeat();
  for (const r of free) {
    if (of.has(r.id) || GROUND.has(r.kind) || onOf(r)) continue;
    const p = posOf(r), hit = pieces.find((b) => within(p, b.body));
    if (hit) of.set(r.id, hit.u);
  }
  bySeat();
  const units = new Map();
  for (const [u, ids] of groups()) {
    // a unit is two or more pieces one sees: a building with only its lights or invisible walls is no unit (they
    // follow it as they follow any piece)
    if (ids.filter((id) => byId.get(id).kind !== 'light' && !byId.get(id).primitive).length < 2) { for (const id of ids) of.delete(id); continue; }
    // its head, which names it: the lowest of its buildings (a hull under its sail), else its biggest piece
    const named = ids.filter((id) => !helper(byId.get(id)) && !GROUND.has(byId.get(id).kind)), pool = named.length ? named : ids;
    const blds = pool.filter((id) => byId.get(id).kind === 'building');
    const head = blds.length ? blds.reduce((h, id) => (box.get(id).z0 < box.get(h).z0 ? id : h), blds[0])
      : pool.reduce((h, id) => (area(box.get(id)) > area(box.get(h)) ? id : h), pool[0]);
    const hb = baseOf(byId.get(head)) || {};
    units.set(u, { id: u, head, name: unitName(hb), members: ids, body: union(bodyOf(ids)), box: union(ids.map((id) => box.get(id))) });
  }
  return { units, of };
}

// A unit's name for the owner: what its head piece is ("Imperial ship", "Stone house"), else "a structure".
export function unitName(base) {
  const n = (base.name || base.edid || '').replace(/^(SOMR|DLC\d\w*?|Morr|Fix_?)/, '').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_\d]+/g, ' ').trim();
  return n ? n[0].toUpperCase() + n.slice(1).toLowerCase() : 'A structure';
}

// Whether a spot [x, y(, z)] stands in a unit: within its whole box in plan.
export function spotIn(unit, p) { const b = unit.box; return !!p && p[0] >= b.x0 && p[0] <= b.x1 && p[1] >= b.y0 && p[1] <= b.y1; }

// A rigid move of a unit about its centre c ([x, y]): turned by `turn` (the game's Z angle, clockwise from above),
// then shifted by d ([dx, dy, dz]). Returns a function from a point to the moved point.
export function rigid(c, turn, d) {
  const k = Math.cos(turn), s = Math.sin(turn);
  return (p) => {
    const ox = p[0] - c[0], oy = p[1] - c[1];
    const q = [c[0] + k * ox + s * oy + d[0], c[1] - s * ox + k * oy + d[1]];
    return p.length >= 3 ? [...q, p[2] + (d[2] || 0)] : q;
  };
}

// What a unit's move carries (tools/places/edits.py unit_carried, the same rule): its people's own spots and drawn
// ways standing in it, its quest spots and walking zones, its own doors' spurs. It leaves a spot another person also
// stands at (a shared wander spot, within SHARED), a guard's post and every patrol point, and a path that only passes
// or starts near it. A bed, a station or anything a stop names by its ref goes with its ref, needing no change.
const SHARED = 64;
const posSpots = (p) => {
  const out = [];
  if (p.work && !p.work.ref && Array.isArray(p.work.pos)) out.push(p.work.pos);
  for (const st of p.routine || []) if (st.at && !st.at.ref && Array.isArray(st.at.pos) && (st.at.space || 'exterior') === 'exterior') out.push(st.at.pos);
  for (const q of patrolOf(p)) if (Array.isArray(q)) out.push(q);
  return out;
};
export function spotsMoved(model, S, u, moved, turn, refsById) {
  const people = [], quests = [];
  const all = [...model.people.values()];
  const shared = (p, pos) => all.some((o) => o.id !== p.id && posSpots(o).some((q) => Math.hypot(q[0] - pos[0], q[1] - pos[1]) <= SHARED));
  for (const p of model.people.values()) {
    const after = clone(p); let hit = false;
    const guard = String(p.role || '').toLowerCase() === 'guard';
    const at = (o) => {
      if (!o || o.ref || (o.space || 'exterior') !== S || !Array.isArray(o.pos) || !spotIn(u, o.pos)) return;
      if (guard || (S === 'exterior' && shared(p, o.pos))) return;
      o.pos = moved(o.pos); hit = true;
    };
    at(after.work); for (const st of after.routine || []) at(st.at);
    // a way drawn into a stop bends with the unit where it passes over or ends at it: each of its points standing in the unit moves with it
    if (S === 'exterior') for (const st of after.routine || []) (st.route || []).forEach((q, i) => { if (spotIn(u, q)) { st.route[i] = moved(q); hit = true; } });
    if (hit) people.push({ person: after, before: clone(p) });
  }
  for (const q of model.quests.values()) {
    if ((q.space || 'exterior') !== S || !Array.isArray(q.pos) || !spotIn(u, q.pos)) continue;
    const after = { ...clone(q), pos: moved(q.pos) };
    if (q.rot) after.rot = turnRot(q.rot, turn).map((v) => rnd(norm(v), 10000));
    quests.push({ quest: after, before: clone(q) });
  }
  // the owner's walking zones lying wholly in it (a "walk here" at its steps): their outline moves with it
  const walks = [];
  for (const w of model.walk.values()) {
    const k = w.kind === 'join' ? 'points' : 'outline', pts = w[k];
    if ((w.space || 'exterior') !== S || !Array.isArray(pts) || !pts.length || !pts.every((q) => spotIn(u, q))) continue;
    walks.push({ walk: { ...clone(w), [k]: pts.map(moved) }, before: clone(w) });
  }
  // a street that ends at one of its doors: its last point moves with it and the one before it half as far, so the
  // street bends to the door rather than dragging its whole length
  const paths = [], doors = new Set(u.members.filter((id) => refsById.get(id)?.door));
  for (const w of model.paths.values()) {
    if (S !== 'exterior' || !Array.isArray(w.points) || w.points.length < 2) continue;
    const pts = w.points.map((q) => [...q]), n = pts.length; let hit = false;
    const end = (i, j, linked) => {
      if (!linked && !spotIn(u, pts[i])) return;
      const m = moved(pts[i]), dx = m[0] - pts[i][0], dy = m[1] - pts[i][1];
      pts[i] = [rnd(m[0]), rnd(m[1]), ...pts[i].slice(2)];
      if (n > 2 && !spotIn(u, pts[j])) pts[j] = [rnd(pts[j][0] + dx / 2), rnd(pts[j][1] + dy / 2), ...pts[j].slice(2)];
      hit = true;
    };
    if (doors.has(w.from)) end(0, 1, true);
    if (doors.has(w.to)) end(n - 1, n - 2, true);   // only its own doors' spurs: a path passing or starting near it stays
    if (hit) paths.push({ path: { ...clone(w), points: pts }, before: clone(w) });
  }
  return { ...(people.length ? { people } : {}), ...(quests.length ? { quests } : {}), ...(walks.length ? { walks } : {}), ...(paths.length ? { paths } : {}) };
}
