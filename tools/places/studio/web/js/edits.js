// The edit list: the contract's ops (docs/design/place-studio.md, Edits), applied to and reverted from the place
// model. Pure JavaScript, no DOM: node runs it against the shared fixtures (test/edits_fixtures). It mirrors
// tools/places/edits.py: apply(model, ops) gives the same place files.
import { describeContent } from './stock.js';
import { newNoteId } from './note_groups.js';

export const GRID = 33;
const TOL = 1e-3;
const clone = (o) => (o === undefined ? undefined : JSON.parse(JSON.stringify(o)));
const r1 = (v) => Math.round(v * 10) / 10;
// A cleared plant's key: base and position to a tenth of a unit (tools/places/edits.py _veg_key).
export const vegKey = (it) => `${it.base}|${it.pos.map(r1).join('|')}`;

export class EditConflict extends Error {}
const conflict = (op, msg) => { throw new EditConflict(`op ${op.n} (${op.op}): ${msg}`); };

// Equal within the save tolerance, as edits.py `same`.
export function same(a, b) {
  if (typeof a === 'boolean' || typeof b === 'boolean') return a === b;
  if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) <= TOL;
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, i) => same(x, b[i]));
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const ka = Object.keys(a).filter((k) => a[k] !== undefined).sort(), kb = Object.keys(b).filter((k) => b[k] !== undefined).sort();
    return ka.length === kb.length && ka.every((k, i) => k === kb[i] && same(a[k], b[k]));
  }
  return a === b;
}

// model: {spaces:{id:{refs:Map, space}}, clear:Map key->{base,pos,by}, land:Map "cx,cy"->Map(row*33+col -> dz),
// landRows:Map "cx,cy"->{why, textures}, paths:Map, people:Map, place, identities, stock}
// identities and stock are the place's people source and stock source as the server sends them (or null): the
// content ops (identity.edit, stock.*) change them as edits.py does.
export function emptyModel() {
  return { spaces: {}, clear: new Map(), land: new Map(), landRows: new Map(), paths: new Map(), people: new Map(), quests: new Map(), walk: new Map(), paint: new Map(), place: {}, identities: null, stock: null };
}

// ---------- content ops: who people are and what things hold (edits.py CONTENT) ----------
export const CONTENT_OPS = ['identity.edit', 'stock.container.set', 'stock.container.remove', 'stock.loose.add', 'stock.loose.remove',
  'stock.loose.edit', 'stock.possessions.set', 'stock.trader.set', 'stock.delivery.set'];
// op family -> [payload key, source, list, the fields that name a row (none: a delivery is found by its whole row)]
const CONTENT = { identity: ['person', 'identities', 'people', ['id']], 'stock.container': ['container', 'stock', 'containers', ['space', 'ref']],
  'stock.loose': ['loose', 'stock', 'loose', ['id']], 'stock.possessions': ['possessions', 'stock', 'possessions', ['person']],
  'stock.trader': ['trader', 'stock', 'traders', ['person']], 'stock.delivery': ['delivery', 'stock', 'deliveries', []] };
const SOURCE_ORDER = { identities: { households: ['id'], people: ['id'] },
  stock: { containers: ['space', 'ref'], loose: ['id'], possessions: ['person'], traders: ['person'], deliveries: ['give_seq', 'by', 'person', 'ref', 'status', 'why'] } };
const family = (kind) => kind.slice(0, kind.lastIndexOf('.'));
const verbOf = (kind) => kind.slice(kind.lastIndexOf('.') + 1);
// Python's sort of (0, number) | (1, text) tuples
function orderBy(fields) {
  const key = (r, f) => (typeof r[f] === 'number' ? [0, r[f]] : [1, r[f] == null ? '' : String(r[f])]);
  return (a, b) => {
    for (const f of fields) {
      const [x, y] = [key(a, f), key(b, f)];
      if (x[0] !== y[0]) return x[0] - y[0];
      if (x[1] < y[1]) return -1; if (x[1] > y[1]) return 1;
    }
    return 0;
  };
}
export function canonicalSource(kind, doc) {
  const out = clone(doc);
  for (const [k, fields] of Object.entries(SOURCE_ORDER[kind])) if (Array.isArray(out[k])) out[k].sort(orderBy(fields));
  return out;
}
function applyContent(m, op) {
  const [field, docKey, table, keys] = CONTENT[family(op.op)], verb = verbOf(op.op);
  const doc = m[docKey];
  if (!doc) conflict(op, `the place has no ${docKey === 'identities' ? 'people' : 'stock'} source`);
  const rows = doc[table] || (doc[table] = []);
  let row, before;
  if (verb === 'remove') { row = null; before = op[field]; } else { row = op[field]; before = verb === 'add' ? null : op.before ?? null; }
  const find = (r) => rows.findIndex((x) => (keys.length ? keys.every((k) => x[k] === r[k]) : same(x, r)));
  const named = row ?? before, what = `${field} ${(keys.length ? keys : ['give_seq']).map((k) => named[k]).join('/')}`;
  if (before == null) {
    if (find(row) >= 0) conflict(op, `${what} already exists`);
    rows.push(clone(row)); return;
  }
  const i = find(before);
  if (i < 0) conflict(op, `${what} does not exist`);
  if (!same(rows[i], before)) conflict(op, `${what} differs from the save's before`);
  if (row == null) rows.splice(i, 1); else rows[i] = clone(row);
}

// Place files ({spaces:{id:{refs:[...], space}} or {id:[refs]}, clear, land, paths, people, place, identities?,
// stock?}) as a model.
export function modelFromFiles(files) {
  const m = emptyModel(); m.place = clone(files.place || {});
  m.identities = files.identities ? clone(files.identities) : null; m.stock = files.stock ? clone(files.stock) : null;
  for (const [sid, sp] of Object.entries(files.spaces || {})) {
    const rows = Array.isArray(sp) ? sp : sp.refs || [];
    m.spaces[sid] = { refs: new Map(rows.map((r) => [r.id, clone(r)])), space: Array.isArray(sp) ? null : clone(sp.space ?? null) };
  }
  for (const c of files.clear || []) m.clear.set(vegKey(c), { ...clone(c), by: c.by || 'draft' });
  for (const p of files.land || []) {
    const k = p.cell.join(','), cm = m.land.get(k) || new Map();
    // a cell's land rows add, as the ground reads them (seat.Ground.apply_patches; edits.py's land.patch)
    for (const [row, col, dz] of p.verts) cm.set(row * GRID + col, (cm.get(row * GRID + col) ?? 0) + dz);
    m.land.set(k, cm); if (!m.landRows.has(k)) m.landRows.set(k, { why: p.why, textures: p.textures });
  }
  for (const p of files.paths || []) m.paths.set(p.id, clone(p));
  for (const p of files.people || []) m.people.set(p.id, clone(p));
  for (const p of files.quests || []) m.quests.set(p.id, clone(p));
  for (const p of files.walk || []) m.walk.set(p.id, clone(p));
  for (const p of files.paint || []) m.paint.set(p.id, clone(p));
  return m;
}

// A copied room's refs as copied from the source, which the place files list only when changed (m.source:
// {space id: [rows]}, set by the caller; edits.py `apply(..., source)`).
const SOURCE_KEYS = ['base', 'pos', 'rot', 'scale'];
function sourceRows(m, sp) {
  const info = m.spaces[sp]?.space, rows = m.source?.[sp];
  if (!info?.copy_of || !rows) return null;
  return new Map(rows.map((r) => [r.id, r]));
}
// The source row of a copied room's ref that has no row of its own, or null.
function implicit(m, sp, rid) {
  const src = sourceRows(m, sp);
  if (!src) return null;
  for (const r of m.spaces[sp].refs.values()) if (r.src === rid && r.id !== rid) return null;
  const r = src.get(rid);
  return r ? clone(r) : null;
}
// True when a copy ref's override row is the source ref unchanged (so the row is dropped).
function matchesSource(m, sp, row) {
  if (!row.src || row.id !== row.src || row.removed) return false;
  const s = sourceRows(m, sp)?.get(row.src);
  return !!s && same(row, s);
}

// The door that leads to row lands where row's arrival went: its landing shifts as the arrival did from `was`
// (edits.py _link_partner), so a move and its inverse give it back exactly.
function linkPartner(m, row, was) {
  const arr = row.door?.arrival; if (!arr || !was) return;
  const delta = arr.map((v, i) => v - was[i]);
  for (const sp of Object.values(m.spaces)) for (const [id, r] of sp.refs) {
    if (r.door?.to_ref !== row.id || r.door.to_pos == null) continue;
    const to = r.door.to_pos.map((v, i) => (i < delta.length ? Math.round((v + delta[i]) * 100) / 100 : v));
    sp.refs.set(id, { ...r, door: { ...r.door, to_pos: to } });
  }
}
// A door moved takes its arrival with it, and its partner's landing: both shift by the door's own move, unless the op
// sets the door itself (edits.py _carry_arrival).
function carryArrival(m, row, was, after) {
  const d = row.door;
  if ('door' in after || !('pos' in after) || was.length < 3 || !d?.arrival) return;
  const delta = row.pos.map((v, i) => v - was[i]);
  if (!delta.some((v) => Math.abs(v) > TOL)) return;
  row.door = { ...d, arrival: d.arrival.map((v, i) => Math.round((v + delta[i]) * 100) / 100) };
  linkPartner(m, row, d.arrival);
}

function space(m, sid) {
  if (!m.spaces[sid]) m.spaces[sid] = { refs: new Map(), space: null };
  return m.spaces[sid];
}

// An owner's op replayed over a draft an agent changed in answer to him (place.json agent_answers): a move or
// removal of an answered row whose before no longer fits is his edit over the row as it stands (his favour), except
// when the answer names this op's own note: the answer stands and his op is kept as no change (edits.py _rebased).
const rowId = (op) => op.id || ['ref', 'quest', 'walk', 'path', 'person'].map((k) => op[k]?.id).find(Boolean);
// The note an op of the owner's belongs to: its note group, its own note, else 'unnoted' (edits.py _note_of).
const noteOf = (op) => op.note_group || op.note || 'unnoted';
export function answeredNote(m, op) {
  const id = rowId(op);
  const notes = new Set((m.place?.agent_answers || []).filter((a) => (a.rows || []).includes(id)).map((a) => a.answers));
  return notes.size > 0 && notes.has(noteOf(op));
}

const answersOn = (m, id) => new Set((m.place?.agent_answers || []).filter((a) => (a.rows || []).includes(id)).map((a) => a.answers));
const ROW_TABLES = { person: 'people', quest: 'quests', walk: 'walk', path: 'paths' };

// A person's, quest spot's, walk's or path's edit of his on an answered row whose before no longer fits: his row
// over the row as it stands, or no change when the answer names his note (edits.py _rebased_row).
function rebaseRow(m, op, note) {
  const table = op.op.split('.')[0], row = op[table], notes = answersOn(m, row?.id);
  if (!notes.size) return op;
  const cur = m[ROW_TABLES[table]]?.get(row.id);
  if (!cur) return op;
  if (notes.has(note ?? noteOf(op))) return { ...op, before: clone(cur), [table]: clone(cur) };
  return same(cur, op.before) ? op : { ...op, before: clone(cur) };
}

// A unit he moved whole, some of whose members an agent answered: each answered member rebased as its own move
// would be, the spots it carries as rebaseRow (edits.py _rebased_unit).
function rebaseUnit(m, op) {
  const note = noteOf(op), refs = m.spaces[op.space || 'exterior']?.refs;
  const out = { ...op, refs: op.refs.map((u) => {
    const notes = answersOn(m, u.id), r = notes.size ? refs?.get(u.id) : null;
    if (!r || r.removed) return u;
    const mine = notes.has(note);
    if (!mine && Object.entries(u.before).every(([k, v]) => same(r[k] ?? null, v ?? null))) return u;
    const before = Object.fromEntries(Object.keys(u.before).map((k) => [k, clone(r[k] ?? null)]));
    return { ...u, before, after: mine ? clone(before) : u.after };
  }) };
  for (const [key, table] of [['people', 'person'], ['quests', 'quest'], ['walks', 'walk'], ['paths', 'path']])
    if (op[key]) out[key] = op[key].map((u) => { const g = rebaseRow(m, { op: `${table}.edit`, [table]: u[table], before: u.before }, note); return { ...u, [table]: g[table], before: g.before }; });
  return out;
}

export function rebaseOp(m, op) {
  if (op.op === 'unit.move') return rebaseUnit(m, op);
  if (['person.edit', 'quest.edit', 'walk.edit', 'path.edit'].includes(op.op)) return rebaseRow(m, op);
  if (op.op !== 'ref.move' && op.op !== 'ref.remove') return op;
  const notes = answersOn(m, op.id);
  if (!notes.size) return op;
  const r = m.spaces[op.space || 'exterior']?.refs.get(op.id);
  if (!r || r.removed) return op;
  if (op.op === 'ref.remove') return same(r, op.before) ? op : { ...op, before: clone(r) };
  const before = Object.fromEntries(Object.keys(op.before).map((k) => [k, clone(r[k] ?? null)]));
  // the answer, made over his session, stands: his op of the answered note is kept as no change
  if (notes.has(noteOf(op))) return { ...op, before, after: clone(before) };
  if (Object.entries(op.before).every(([k, v]) => same(r[k] ?? null, v ?? null))) return op;
  return { ...op, before };
}

// Apply one op; throws EditConflict when its before does not match, leaving the model as it was.
export function applyOp(m, op) {
  const sp = op.space || 'exterior';
  switch (op.op) {
    case 'ref.add': {
      if (op.space_copy_of && sp === 'exterior') conflict(op, 'space_copy_of names an interior, not the exterior');
      const fresh = !m.spaces[sp], s = space(m, sp);
      const had = s.refs.get(op.ref.id);
      if (had && !had.removed) conflict(op, `ref ${op.ref.id} already exists`);
      if (op.space_copy_of && !fresh && (s.space || s.refs.size > 0)) conflict(op, `space ${sp} already exists; a copied room needs a new space id`);
      s.refs.delete(op.ref.id);   // a copy ref removed by an override row comes back
      if (!matchesSource(m, sp, op.ref)) s.refs.set(op.ref.id, clone(op.ref));
      if (op.space_copy_of) {
        s.space = { space_id: sp, copy_of: op.space_copy_of, name: op.space_name || sp };
        for (const [sid, other] of Object.entries(m.spaces))
          for (const r of other.refs.values()) if (r.door?.to_space === sp) Object.assign(s.space, { door_from: r.id, parent: sid });
      }
      const target = m.spaces[op.ref.door?.to_space]?.space;
      if (target?.copy_of && !target.door_from) Object.assign(target, { door_from: op.ref.id, parent: sp });
      break;
    }
    case 'ref.remove': {
      const s = space(m, sp);
      let r = s.refs.get(op.id);
      if (r?.removed) r = undefined;
      if (!r) {
        const src = implicit(m, sp, op.id);
        if (!src) conflict(op, `ref ${op.id} is not in ${sp}`);
        for (const k of SOURCE_KEYS) if (k in op.before && !same(src[k], op.before[k])) conflict(op, `ref ${op.id} ${k} is ${JSON.stringify(src[k])}, the save expected ${JSON.stringify(op.before[k])}`);
        s.refs.set(op.id, { id: op.id, src: op.id, removed: true });
      } else {
        if (!same(r, op.before)) conflict(op, `ref ${op.id} differs from the save's before`);
        s.refs.delete(op.id);
        if (r.src && s.space?.copy_of && sourceRows(m, sp)?.has(r.src)) s.refs.set(r.id, { id: r.id, src: r.src, removed: true });
      }
      if (op.space_drop && s.refs.size === 0) delete m.spaces[sp];
      break;
    }
    case 'ref.move': {
      const s = space(m, sp);
      let r = s.refs.get(op.id);
      if (r?.removed) conflict(op, `ref ${op.id} is removed from ${sp}`);
      if (!r) {
        r = implicit(m, sp, op.id);
        if (!r) conflict(op, `ref ${op.id} is not in ${sp}`);
      }
      for (const [k, v] of Object.entries(op.before)) if (!same(r[k] ?? null, v ?? null)) conflict(op, `ref ${op.id} ${k} differs from what the save expected`);
      const next = { ...r }, was = [...(r.pos || [])];
      for (const [k, v] of Object.entries(op.after)) next[k] = clone(v);
      if (next.unit === null) delete next.unit;   // null: the unit rule decides again (units.js)
      carryArrival(m, next, was, op.after);
      if (matchesSource(m, sp, next)) s.refs.delete(op.id); else s.refs.set(op.id, next);
      break;
    }
    case 'unit.move': {
      // a unit moved, turned or raised whole: each member as its own ref.move (a door's arrival as the op gives it,
      // turned with the unit, its partner's landing following), then the people's and quest spots it carries
      for (const u of op.refs) {
        if ('door' in u.after) { const r = space(m, sp).refs.get(u.id); if (!r || !same(r.door, u.before.door)) conflict(op, `ref ${u.id} door differs from what the save expected`); }
        // the door as the op gives it (its arrival turned with the unit), not ref.move's plain shift of it
        const before = Object.fromEntries(Object.entries(u.before).filter(([k]) => k !== 'door'));
        applyOp(m, { n: op.n, op: 'ref.move', space: sp, id: u.id, before, after: u.after });
        if ('door' in u.after) linkPartner(m, space(m, sp).refs.get(u.id), u.before.door?.arrival);
      }
      for (const [key, table] of [['people', 'person'], ['quests', 'quest'], ['walks', 'walk'], ['paths', 'path']])
        for (const u of unitCarried(m, op, key)) applyOp(m, { n: op.n, op: `${table}.edit`, [table]: u[table], before: u.before });
      break;
    }
    case 'veg.clear': {
      for (const it of op.items) if (m.clear.has(vegKey(it))) conflict(op, `plant ${it.base} at ${it.pos} is already cleared`);
      for (const it of op.items) m.clear.set(vegKey(it), { ...clone(it), by: it.by || 'owner' });
      break;
    }
    case 'veg.restore': {
      for (const it of op.items) if (!m.clear.has(vegKey(it))) conflict(op, `plant ${it.base} at ${it.pos} is not cleared`);
      for (const it of op.items) m.clear.delete(vegKey(it));
      break;
    }
    case 'land.patch': {
      const k = op.cell.join(','), cm = m.land.get(k) || new Map();
      for (const [row, col, b] of op.verts) if (!same(cm.get(row * GRID + col) ?? 0, b)) conflict(op, `cell ${op.cell} vertex ${row},${col}: the save expected ${b}`);
      for (const [row, col, , a] of op.verts) { if (a === 0) cm.delete(row * GRID + col); else cm.set(row * GRID + col, a); }
      m.land.set(k, cm); if (!m.landRows.has(k)) m.landRows.set(k, { why: op.note || '' });
      break;
    }
    case 'path.add': case 'path.edit': case 'path.remove': case 'person.add': case 'person.edit': case 'person.remove':
    case 'quest.add': case 'quest.edit': case 'quest.remove': case 'walk.add': case 'walk.edit': case 'walk.remove':
    case 'paint.add': case 'paint.remove': {
      const [table, verb] = op.op.split('.'), rows = { path: m.paths, person: m.people, quest: m.quests, walk: m.walk, paint: m.paint }[table], row = op[table];
      const cur = rows.get(row.id);
      if (verb === 'add') { if (cur) conflict(op, `${table} ${row.id} already exists`); rows.set(row.id, clone(row)); break; }
      if (!cur) conflict(op, `${table} ${row.id} does not exist`);
      if (!same(cur, verb === 'edit' ? op.before : op.before || row)) conflict(op, `${table} ${row.id} differs from the save's before`);
      if (verb === 'remove') rows.delete(row.id); else rows.set(row.id, clone(row));
      break;
    }
    case 'identity.edit': case 'stock.container.set': case 'stock.container.remove': case 'stock.loose.add': case 'stock.loose.remove':
    case 'stock.loose.edit': case 'stock.possessions.set': case 'stock.trader.set': case 'stock.delivery.set':
      applyContent(m, op); break;
    default: throw new EditConflict(`op ${op.n}: unknown op '${op.op}'`);
  }
}

// After a save's ops: every door added into one of the place's own spaces is paired (edits.py _check_doors).
export function checkDoors(m, ops) {
  for (const op of ops) {
    const d = op.op === 'ref.add' && op.ref.door;
    if (!d?.to_space || !m.spaces[d.to_space]?.space) continue;
    const back = m.spaces[d.to_space].refs.get(d.to_ref);
    if (back && back.door?.to_space === (op.space || 'exterior') && back.door?.to_ref === op.ref.id) continue;
    if (!back && !ops.some((o) => o.op === 'ref.add' && o.space === d.to_space)) continue;
    conflict(op, `door ${op.ref.id} leads to ${d.to_space}/${d.to_ref}, which does not lead back`);
  }
}

// The op that undoes op (edits.py `inverse`).
export function inverse(op) {
  const inv = clone(op);
  switch (op.op) {
    case 'ref.add': inv.op = 'ref.remove'; inv.id = op.ref.id; inv.before = clone(op.ref); delete inv.ref; if (op.space_copy_of) inv.space_drop = true; break;
    case 'ref.remove': inv.op = 'ref.add'; inv.ref = clone(op.before); delete inv.id; delete inv.before; delete inv.space_drop; break;
    case 'ref.move': inv.before = clone(op.after); inv.after = clone(op.before); break;
    case 'unit.move':
      inv.refs = op.refs.map((u) => ({ ...clone(u), before: clone(u.after), after: clone(u.before) }));
      if (op.people) inv.people = op.people.map((u) => ({ person: clone(u.before), before: clone(u.person) }));
      if (op.quests) inv.quests = op.quests.map((u) => ({ quest: clone(u.before), before: clone(u.quest) }));
      if (op.walks) inv.walks = op.walks.map((u) => ({ walk: clone(u.before), before: clone(u.walk) }));
      if (op.paths) inv.paths = op.paths.map((u) => ({ path: clone(u.before), before: clone(u.path) }));
      break;
    case 'veg.clear': inv.op = 'veg.restore'; break;
    case 'veg.restore': inv.op = 'veg.clear'; break;
    case 'land.patch': inv.verts = op.verts.map(([r, c, b, a]) => [r, c, a, b]); break;
    case 'identity.edit': case 'stock.container.set': case 'stock.container.remove': case 'stock.loose.add': case 'stock.loose.remove':
    case 'stock.loose.edit': case 'stock.possessions.set': case 'stock.trader.set': case 'stock.delivery.set': {
      const field = CONTENT[family(op.op)][0], base = family(op.op), verb = verbOf(op.op);
      if (verb === 'add') inv.op = `${base}.remove`;
      else if (verb === 'remove') { inv.op = base === 'stock.container' ? `${base}.set` : `${base}.add`; delete inv.before; }
      else if (op.op === 'stock.container.set' && op.before == null) { inv.op = 'stock.container.remove'; delete inv.before; }
      else { inv[field] = clone(op.before ?? null); inv.before = clone(op[field]); }
      break;
    }
    default: {
      const [table, verb] = op.op.split('.');
      if (verb === 'add') { inv.op = `${table}.remove`; inv.before = clone(op[table]); }
      else if (verb === 'remove') { inv.op = `${table}.add`; inv[table] = clone(op.before || op[table]); delete inv.before; }
      else { inv.before = clone(op[table]); inv[table] = clone(op.before); }
    }
  }
  return inv;
}
export function revertOp(m, op) { applyOp(m, inverse(op)); }
// What a unit's move carries of `key` (edits.py unit_carried, the same rule; the studio's units.js spotsMoved makes
// it so): its own doors' spurs only, its people's own spots, never a spot another person also stands at, a guard's
// post or a patrol point; an older save's move that carried those replays without them.
const SHARED = 64;
function posSpots(p) {
  const out = [];
  if (p.work && !p.work.ref && Array.isArray(p.work.pos)) out.push([['work'], p.work.pos]);
  (p.routine || []).forEach((st, i) => { const at = st.at || {}; if (!at.ref && Array.isArray(at.pos) && (at.space || 'exterior') === 'exterior') out.push([['routine', i], at.pos]); });
  const pat = Array.isArray(p.patrol) ? p.patrol : p.patrol?.points || [];
  pat.forEach((q, i) => { if (Array.isArray(q)) out.push([['patrol', i], q]); });
  return out;
}
function setSpot(p, w, v) {
  if (w[0] === 'work') p.work.pos = v;
  else if (w[0] === 'routine') p.routine[w[1]].at.pos = v;
  else (Array.isArray(p.patrol) ? p.patrol : p.patrol.points)[w[1]] = v;
}
export function unitCarried(m, op, key) {
  const items = clone(op[key] || []);
  if (key === 'paths') {
    const rows = space(m, op.space || 'exterior').refs;
    const doors = new Set((op.refs || []).filter((u) => u.after?.door || u.before?.door || rows.get(u.id)?.door).map((u) => u.id));
    const out = [];
    for (const it of items) {
      const b = it.before, a = it.path, pts = (b.points || []).map((q) => [...q]), n = pts.length;
      if (n < 2 || (a.points || []).length !== n) continue;
      for (const [end, nxt, link] of [[0, 1, b.from], [n - 1, n - 2, b.to]]) {
        if (!doors.has(link)) continue;
        pts[end] = [...a.points[end]]; if (n > 2) pts[nxt] = [...a.points[nxt]];
      }
      if (!same(pts, b.points)) out.push({ path: { ...a, points: pts }, before: b });
    }
    return out;
  }
  if (key !== 'people') return items;
  const people = [...(m.people?.values?.() || [])], out = [];
  for (const it of items) {
    const b = it.before, a = clone(it.person), guard = String(b.role || '').toLowerCase() === 'guard';
    const sb = posSpots(b), sa = posSpots(a);
    sb.forEach(([w, pb], k) => {
      const pa = sa[k]?.[1]; if (!pa || same(pa, pb)) return;
      const shared = people.some((o) => o.id !== b.id && posSpots(o).some(([, q]) => Math.hypot(q[0] - pb[0], q[1] - pb[1]) <= SHARED));
      if (guard || w[0] === 'patrol' || shared) setSpot(a, w, clone(pb));
    });
    if (!same(a, b)) out.push({ person: a, before: b });
  }
  return out;
}

// The ops with each unit.move written as the plain ops it is made of (edits.py `expand`): a ref.move per member, a
// person.edit and quest.edit per spot, each keeping the unit op's n, call, note and stroke.
export function expand(ops) {
  const out = [];
  for (const op of ops) {
    if (op.op !== 'unit.move') { out.push(op); continue; }
    const keep = Object.fromEntries(['n', 'at', 'call', 'note_group', 'note', 'stroke', 'space', 'state'].filter((k) => k in op).map((k) => [k, op[k]]));
    for (const u of op.refs || []) out.push({ ...keep, op: 'ref.move', id: u.id, before: u.before, after: u.after, unit: op.unit });
    for (const u of op.people || []) out.push({ ...keep, op: 'person.edit', person: u.person, before: u.before });
    for (const u of op.quests || []) out.push({ ...keep, op: 'quest.edit', quest: u.quest, before: u.before });
    for (const u of op.walks || []) out.push({ ...keep, op: 'walk.edit', walk: u.walk, before: u.before });
    for (const u of op.paths || []) out.push({ ...keep, op: 'path.edit', path: u.path, before: u.before });
  }
  return out;
}

const sortKeys = (o) => (Array.isArray(o) ? o.map(sortKeys) : o && typeof o === 'object'
  ? Object.fromEntries(Object.keys(o).sort().filter((k) => o[k] !== undefined).map((k) => [k, sortKeys(o[k])])) : o);
// The model as place files in edits.py's canonical order, for comparing with the shared fixtures.
export function modelToFiles(m) {
  const byId = (a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  const spaces = {};
  for (const [sid, s] of Object.entries(m.spaces)) spaces[sid] = { refs: [...s.refs.values()].sort(byId), space: s.space ?? null };
  const land = [];
  for (const [k, cm] of m.land) {
    if (!cm.size && !m.landRows.get(k)?.textures) continue;
    const verts = [...cm.entries()].map(([idx, dz]) => [Math.floor(idx / GRID), idx % GRID, dz]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const row = { cell: k.split(',').map(Number), verts, ...(m.landRows.get(k) || {}) };
    if (row.textures === undefined) delete row.textures;
    land.push(row);
  }
  land.sort((a, b) => a.cell[0] - b.cell[0] || a.cell[1] - b.cell[1]);
  const vk = (c) => [c.base, ...c.pos.map(r1)];
  const clear = [...m.clear.values()].sort((a, b) => { const x = vk(a), y = vk(b); for (let i = 0; i < x.length; i++) { if (x[i] < y[i]) return -1; if (x[i] > y[i]) return 1; } return 0; });
  const out = { place: m.place, spaces, clear, land, paths: [...m.paths.values()].sort(byId), people: [...m.people.values()].sort(byId) };
  if (m.quests.size) out.quests = [...m.quests.values()].sort(byId);   // kept only when it has rows, as edits.py
  if (m.walk.size) out.walk = [...m.walk.values()].sort(byId);
  if (m.paint.size) out.paint = [...m.paint.values()].sort(byId);
  if (m.identities) out.identities = canonicalSource('identities', m.identities);
  if (m.stock) out.stock = canonicalSource('stock', m.stock);
  return sortKeys(out);
}

// The session's history: ops, a cursor (ops before it are applied), calls (fault|taste) and notes. A note is
// {id, text, at} in this.notes; each op it covers carries its id in `note_group` (note_groups.js).
export class EditLog {
  constructor(model) { this.model = model; this.ops = []; this.cursor = 0; this.listeners = []; this.n = 0; this.notes = new Map(); }
  on(fn) { this.listeners.push(fn); }
  emit(kind, ops) { for (const fn of this.listeners) fn(kind, ops); }
  // Add one op or a group (one stroke); applies them and drops the redo tail.
  push(opOrOps, space = 'exterior') {
    const list = Array.isArray(opOrOps) ? opOrOps : [opOrOps];
    if (!list.length) return [];
    this.ops.length = this.cursor;
    const stroke = list.length > 1 ? `s${Date.now().toString(36)}${this.n}` : undefined;
    for (const op of list) {
      op.n = ++this.n; op.at = op.at || new Date().toISOString(); op.space = op.space || space;
      op.call = op.call || 'fault';
      if (this.state && !op.state) op.state = this.state;   // made while a quest state other than the start is shown
      if (stroke && !op.stroke) op.stroke = stroke;
      applyOp(this.model, op); this.ops.push(op);
    }
    this.cursor = this.ops.length;
    this.emit('push', list); return list;
  }
  canUndo() { return this.cursor > 0; }
  canRedo() { return this.cursor < this.ops.length; }
  undo() {
    if (!this.canUndo()) return [];
    const last = this.ops[this.cursor - 1], out = [];
    do { const op = this.ops[--this.cursor]; revertOp(this.model, op); out.push(op); }
    while (last.stroke && this.cursor > 0 && this.ops[this.cursor - 1].stroke === last.stroke);
    this.emit('undo', out); return out;
  }
  redo() {
    if (!this.canRedo()) return [];
    const first = this.ops[this.cursor], out = [];
    do { const op = this.ops[this.cursor++]; applyOp(this.model, op); out.push(op); }
    while (first.stroke && this.cursor < this.ops.length && this.ops[this.cursor].stroke === first.stroke);
    this.emit('redo', out); return out;
  }
  // Move the cursor straight to just after op number n (0: before everything).
  goto(n) {
    const idx = n === 0 ? 0 : this.ops.findIndex((o) => o.n === n) + 1;
    while (this.cursor > idx) this.undo();
    while (this.cursor < idx) this.redo();
  }
  setCall(ns, call, note) {
    const set = new Set(ns);
    const hit = this.ops.filter((o) => set.has(o.n) || (o.stroke && this.ops.some((p) => set.has(p.n) && p.stroke === o.stroke)));
    for (const o of hit) { o.call = call; if (note !== undefined) { if (note) o.note = note; else delete o.note; } }
    this.emit('call', hit); return hit;
  }
  sinceCall(n, call) { return this.setCall(this.ops.filter((o) => o.n >= n).map((o) => o.n), call); }
  // The ops of changes ns, whole strokes.
  strokesOf(ns) {
    const set = new Set(ns), strokes = new Set(this.ops.filter((o) => set.has(o.n) && o.stroke).map((o) => o.stroke));
    return this.ops.filter((o) => set.has(o.n) || (o.stroke && strokes.has(o.stroke)));
  }
  // One note for changes ns (and call, when given, for all of them). When ns are exactly one note's changes its
  // words change; otherwise they leave any note they had and share a new one. Empty words take their note away.
  setNote(ns, text, call) {
    const hit = this.strokesOf(ns); if (!hit.length) return [];
    text = String(text ?? '').trim();
    if (call) for (const o of hit) o.call = call;
    const ids = new Set(hit.map((o) => o.note_group || ''));
    const one = ids.size === 1 && !ids.has('') ? [...ids][0] : null;
    if (text && one && this.ops.filter((o) => o.note_group === one).length === hit.length && this.notes.has(one)) {
      this.notes.get(one).text = text;
    } else {
      const id = text ? newNoteId(this.notes) : null;
      if (id) this.notes.set(id, { id, text, at: new Date().toISOString() });
      for (const o of hit) { delete o.note; if (id) o.note_group = id; else delete o.note_group; }
      const used = new Set(this.ops.map((o) => o.note_group).filter(Boolean));
      for (const k of [...this.notes.keys()]) if (!used.has(k)) this.notes.delete(k);
    }
    this.emit('note', hit); return hit;
  }
  // The notes the applied ops carry, for a save: each once.
  notesFor(ops = this.applied()) {
    const used = new Set(ops.map((o) => o.note_group).filter(Boolean));
    return [...this.notes.values()].filter((n) => used.has(n.id)).map((n) => ({ ...n }));
  }
  applied() { return this.ops.slice(0, this.cursor); }
  // A save's ops onto the model in order (and its notes); stops at the first that no longer fits and says which.
  load(ops, notes = []) {
    this.notes = new Map((notes || []).filter((x) => x?.id).map((x) => [x.id, { id: x.id, text: String(x.text ?? ''), at: x.at }]));
    this.ops = []; this.cursor = 0; this.n = 0; let err = null;
    const undone = new Set((this.model.place?.agent_answers || []).flatMap((a) => (a.undoes || []).flatMap((g) => (a.rows || []).map((id) => `${id} ${g}`))));
    for (const raw of ops) {
      // a change of his a later request of his asked the agent to undo is kept as no change (edits.py _undone)
      if (undone.has(`${rowId(raw)} ${raw.note_group || raw.note}`)) continue;
      const op = rebaseOp(this.model, raw);
      // an op of a note the agent answered on its row, which no longer fits: the answer already made the row what
      // the op makes it, so it is kept as no change (edits.py apply)
      // (kept in his history as his: undoing it undoes what it did, which the answer had already made)
      try { applyOp(this.model, op); } catch (e) { if (!answeredNote(this.model, raw)) { err = e; break; } this.ops.push(raw); this.n = Math.max(this.n, raw.n || 0); continue; }
      this.ops.push(op); this.n = Math.max(this.n, op.n || 0);
    }
    this.cursor = this.ops.length; this.emit('load', this.ops); return err;
  }
}

// Plain-English line for an op, for the history list.
export function describe(op, nameOf = (k) => k) {
  switch (op.op) {
    case 'ref.add': return `Added ${nameOf(op.ref.base)}`;
    case 'ref.remove': return `Removed ${nameOf(op.before?.base)}`;
    case 'ref.move': return `Moved ${nameOf(op.base || op.id)}`;
    case 'unit.move': return `Moved the whole of ${op.name || 'a unit'} (${op.refs.length} pieces${(op.people?.length || 0) + (op.quests?.length || 0) ? `, with ${(op.people?.length || 0) + (op.quests?.length || 0)} spots` : ''}${op.paths?.length ? `; the end of ${op.paths.length === 1 ? 'a street' : `${op.paths.length} streets`} moved with it` : ''})`;
    case 'veg.clear': return `Cleared ${op.items.length} plant${op.items.length === 1 ? '' : 's'}`;
    case 'veg.restore': return `Brought back ${op.items.length} plant${op.items.length === 1 ? '' : 's'}`;
    case 'land.patch': return `${{ raise: 'Raised', lower: 'Lowered', level: 'Levelled', smooth: 'Smoothed' }[op.tool?.kind] || 'Changed'} land (${op.verts.length} points)`;
    case 'path.add': return `Drew a ${op.path.style || ''} path`.replace('  ', ' ');
    case 'path.edit': return 'Changed a path';
    case 'path.remove': return 'Erased a path';
    case 'person.add': return `Added ${op.person.name || 'a person'}`;
    case 'person.edit': return `Changed ${op.person.name || 'a person'}`;
    case 'person.remove': return `Removed ${op.person.name || 'a person'}`;
    case 'quest.add': return `Placed quest thing ${op.quest.name || op.quest.ref}`;
    case 'quest.edit': return `Moved quest thing ${op.quest.name || op.quest.ref}`;
    case 'quest.remove': return `Cleared the spot of quest thing ${op.quest.name || op.quest.ref}`;
    case 'walk.add': return { block: 'Marked "No walking here"', walk: 'Marked "Walk here"', join: 'Asked to join two walking areas' }[op.walk.kind] || 'Added a walking zone';
    case 'walk.edit': return op.walk.note !== op.before?.note ? 'Gave a walking zone a note' : 'Moved a walking zone';
    case 'walk.remove': return 'Deleted a walking zone';
    case 'paint.add': return op.paint.erase ? 'Erased ground paint' : `Painted the ground with ${nameOf(op.paint.texture)}`;
    case 'paint.remove': return 'Took a ground paint stroke away';
    default: return CONTENT_OPS.includes(op.op) ? describeContent(op, nameOf) : op.op;
  }
}
