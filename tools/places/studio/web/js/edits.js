// The edit list: the contract's ops (docs/design/place-studio.md, Edits), applied to and reverted from the place
// model. Pure JavaScript, no DOM: node runs it against the shared fixtures (test/edits_fixtures). It mirrors
// tools/places/edits.py: apply(model, ops) gives the same place files.

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
// landRows:Map "cx,cy"->{why, textures}, paths:Map, people:Map, place}
export function emptyModel() {
  return { spaces: {}, clear: new Map(), land: new Map(), landRows: new Map(), paths: new Map(), people: new Map(), place: {} };
}

// Place files ({spaces:{id:{refs:[...], space}} or {id:[refs]}, clear, land, paths, people, place}) as a model.
export function modelFromFiles(files) {
  const m = emptyModel(); m.place = clone(files.place || {});
  for (const [sid, sp] of Object.entries(files.spaces || {})) {
    const rows = Array.isArray(sp) ? sp : sp.refs || [];
    m.spaces[sid] = { refs: new Map(rows.map((r) => [r.id, clone(r)])), space: Array.isArray(sp) ? null : clone(sp.space ?? null) };
  }
  for (const c of files.clear || []) m.clear.set(vegKey(c), { ...clone(c), by: c.by || 'draft' });
  for (const p of files.land || []) {
    const k = p.cell.join(','), cm = m.land.get(k) || new Map();
    for (const [row, col, dz] of p.verts) cm.set(row * GRID + col, dz);
    m.land.set(k, cm); m.landRows.set(k, { why: p.why, textures: p.textures });
  }
  for (const p of files.paths || []) m.paths.set(p.id, clone(p));
  for (const p of files.people || []) m.people.set(p.id, clone(p));
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

function space(m, sid) {
  if (!m.spaces[sid]) m.spaces[sid] = { refs: new Map(), space: null };
  return m.spaces[sid];
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
      for (const [k, v] of Object.entries(op.before)) if (!same(r[k], v)) conflict(op, `ref ${op.id} ${k} differs from what the save expected`);
      const next = { ...r };
      for (const [k, v] of Object.entries(op.after)) next[k] = clone(v);
      if (matchesSource(m, sp, next)) s.refs.delete(op.id); else s.refs.set(op.id, next);
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
    case 'path.add': case 'path.edit': case 'path.remove': case 'person.add': case 'person.edit': case 'person.remove': {
      const [table, verb] = op.op.split('.'), rows = table === 'path' ? m.paths : m.people, row = op[table];
      const cur = rows.get(row.id);
      if (verb === 'add') { if (cur) conflict(op, `${table} ${row.id} already exists`); rows.set(row.id, clone(row)); break; }
      if (!cur) conflict(op, `${table} ${row.id} does not exist`);
      if (!same(cur, verb === 'edit' ? op.before : op.before || row)) conflict(op, `${table} ${row.id} differs from the save's before`);
      if (verb === 'remove') rows.delete(row.id); else rows.set(row.id, clone(row));
      break;
    }
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
    case 'veg.clear': inv.op = 'veg.restore'; break;
    case 'veg.restore': inv.op = 'veg.clear'; break;
    case 'land.patch': inv.verts = op.verts.map(([r, c, b, a]) => [r, c, a, b]); break;
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
  return sortKeys({ place: m.place, spaces, clear, land, paths: [...m.paths.values()].sort(byId), people: [...m.people.values()].sort(byId) });
}

// The session's history: ops, a cursor (ops before it are applied), calls (fault|taste) and notes.
export class EditLog {
  constructor(model) { this.model = model; this.ops = []; this.cursor = 0; this.listeners = []; this.n = 0; }
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
  applied() { return this.ops.slice(0, this.cursor); }
  // A save's ops onto the model in order; stops at the first that no longer fits and says which.
  load(ops) {
    this.ops = []; this.cursor = 0; this.n = 0; let err = null;
    for (const op of ops) {
      try { applyOp(this.model, op); } catch (e) { err = e; break; }
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
    case 'veg.clear': return `Cleared ${op.items.length} plant${op.items.length === 1 ? '' : 's'}`;
    case 'veg.restore': return `Brought back ${op.items.length} plant${op.items.length === 1 ? '' : 's'}`;
    case 'land.patch': return `${{ raise: 'Raised', lower: 'Lowered', level: 'Levelled', smooth: 'Smoothed' }[op.tool?.kind] || 'Changed'} land (${op.verts.length} points)`;
    case 'path.add': return `Drew a ${op.path.style || ''} path`.replace('  ', ' ');
    case 'path.edit': return 'Changed a path';
    case 'path.remove': return 'Erased a path';
    case 'person.add': return `Added ${op.person.name || 'a person'}`;
    case 'person.edit': return `Changed ${op.person.name || 'a person'}`;
    case 'person.remove': return `Removed ${op.person.name || 'a person'}`;
    default: return op.op;
  }
}
