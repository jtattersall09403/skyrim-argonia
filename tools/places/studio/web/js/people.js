// People: where each stands at the time on the day scrubber, their routine as a path through the place, and
// editing of their placement, stops, times and patrol points. Routines run through doors from street to room.
import * as THREE from 'three';
import { mintId } from './ids.js';
import { clock } from './geom.js';

const COLOURS = ['#2f7fd1', '#c2410c', '#15803d', '#7e22ce', '#b45309', '#0e7490', '#be185d', '#4d7c0f'];
const NS = 'http://www.w3.org/2000/svg';
const clone = (o) => JSON.parse(JSON.stringify(o));
const rnd = (v) => Math.round(v * 100) / 100;
export const STOP_KINDS = { sleep: 'Sleeping', eat: 'Eating', work: 'Working', wander: 'Walking about', sandbox: 'Idling about', patrol: 'On patrol' };
// A patrol is {points: [[x,y] | [x,y,z] | stop...], loop}; an older bare list of points is read the same.
export const patrolOf = (p) => (Array.isArray(p.patrol) ? p.patrol : p.patrol?.points) || [];
export function setPatrol(x, pts) {
  if (!pts.length) { delete x.patrol; return; }
  x.patrol = { points: pts, loop: Array.isArray(x.patrol) ? true : (x.patrol?.loop ?? true) };
}

export class People {
  constructor(app) {
    this.app = app; this.active = false; this.sel = null; this.armed = null; this.markers = new Map(); this._bySrc = new Map(); this._first = new Map();
    // a simple standing figure turned from a profile: legs, body, shoulders, neck, head
    const prof = [[0, 0], [22, 0], [20, 70], [26, 95], [30, 130], [12, 142], [9, 148], [17, 158], [16, 172], [9, 182], [0, 184]];
    this.geo = new THREE.LatheGeometry(prof.map(([x, y]) => new THREE.Vector2(x, y)), 10).rotateX(Math.PI / 2);
  }
  setActive(on) { this.active = on; if (!on) { this.armed = null; } this.refresh(); }
  list() { return [...(this.app.model?.people.values() || [])]; }
  colour(p) { let h = 0; for (const ch of String(p.id)) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return COLOURS[h % COLOURS.length]; }
  // ---------- where a stop is, seen from a space ----------
  // a stop's ref is our id or a source key of that space
  refPos(space, id) {
    const refs = this.app.model.spaces[space]?.refs; if (!refs) return null;
    return (refs.get(id) || this.bySrc(space, refs).get(id))?.pos || null;
  }
  // each space's refs by the source ref they came from, and its first furniture: worked out once per change of the
  // place (refresh clears them), not once per stop per person per camera move
  bySrc(space, refs) {
    let m = this._bySrc.get(space);
    if (!m) { m = new Map(); for (const r of refs.values()) if (r.src && !m.has(r.src)) m.set(r.src, r); this._bySrc.set(space, m); }
    return m;
  }
  // a stop with neither ref nor pos stands at its space's first furniture
  firstFurniture(space) {
    if (this._first.has(space)) return this._first.get(space);
    let furn = null, other = null;
    for (const r of this.app.model.spaces[space]?.refs.values() || []) { if (r.kind === 'furniture') { furn = r; break; } if (!other && r.kind !== 'door') other = r; }
    const p = (furn || (space !== 'exterior' && other) || null)?.pos || null; this._first.set(space, p); return p;
  }
  ground(p) {
    if (!p) return null;
    if (p.length >= 3) return p;
    const h = this.app.terrain?.heightAt(p[0], p[1]); return [p[0], p[1], h ?? 0];
  }
  stopPoint(stop) {
    const at = stop.at || {}, space = at.space || 'exterior';
    let p = at.pos || (at.ref && this.refPos(space, at.ref)) || (!at.ref && !at.pos && this.firstFurniture(space));
    p = p && (p.length >= 3 ? p : this.ground(p));
    return { space, p: p ? this.app.seatedPoint?.(p) || p : null };
  }
  // patrol points as [x,y,z] outside (a stop point inside another space is left out of the drawn route)
  patrolPts(p) {
    return patrolOf(p).map((q) => (Array.isArray(q) ? this.ground(q) : this.stopPoint({ at: q }).p)).filter(Boolean);
  }
  doorTo(fromSpace, toSpace) {
    for (const r of this.app.model.spaces[fromSpace]?.refs.values() || []) if (r.door?.to_space === toSpace) return r;
    return null;
  }
  // A stop as seen from space S: its own point, or the door that leads towards it.
  seenFrom(S, stop) {
    const sp = this.stopPoint(stop);
    if (sp.space === S) return { p: sp.p, inside: false };
    const d = this.doorTo(S, sp.space);
    if (d) return { p: d.pos, inside: true };
    if (S !== 'exterior') { const out = this.doorTo(S, 'exterior'); if (out) return { p: out.pos, inside: true }; }
    return null;
  }
  sorted(p) { return [...(p.routine || [])].sort((a, b) => a.start - b.start); }
  active_(p, t) {
    const st = this.sorted(p); if (!st.length) return null;
    for (let i = 0; i < st.length; i++) {
      const s = st[i], rel = ((t - s.start) % 24 + 24) % 24;
      if (rel < s.hours) return { i, s, rel, prev: st[(i - 1 + st.length) % st.length], st };
    }
    // between stops: still at the last one begun
    let best = st[st.length - 1];
    for (const s of st) if (s.start <= t) best = s;
    const i = st.indexOf(best); return { i, s: best, rel: best.hours, prev: st[(i - 1 + st.length) % st.length], st };
  }
  // Where a person is at time t in space S, or null when elsewhere.
  where(p, t, S) {
    const a = this.active_(p, t); if (!a) return null;
    const here = this.seenFrom(S, a.s); if (!here?.p) return null;
    let pos = here.p;
    const pat = this.patrolPts(p);
    if (pat.length && ['patrol', 'work'].includes(a.s.kind) && this.stopPoint(a.s).space === S && S === 'exterior') {
      const n = pat.length, f = (a.rel * 2) % n, i = Math.floor(f), u = f - i;
      const A = pat[i], B = pat[(i + 1) % n]; pos = [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u];
    } else if (a.rel < 0.5) { // walking from the last stop for the first half hour
      const from = this.seenFrom(S, a.prev);
      if (from?.p) { const u = a.rel / 0.5; pos = [0, 1, 2].map((k) => from.p[k] + (here.p[k] - from.p[k]) * u); }
    }
    return { pos, inside: here.inside, stop: a.s };
  }
  // ---------- drawing ----------
  layer(view) {
    let s = view.el.querySelector('.people-layer');
    if (!s) { s = document.createElementNS(NS, 'svg'); s.setAttribute('class', 'sketch people-layer'); view.el.append(s); }
    return s;
  }
  refresh() {
    const a = this.app; if (!a.model) return;
    this._bySrc.clear(); this._first.clear();
    const v = a.ours.view, S = a.ours.space, seen = new Set();
    for (const p of this.list()) {
      seen.add(p.id);
      let m = this.markers.get(p.id);
      if (!m) { m = new THREE.Mesh(this.geo, new THREE.MeshLambertMaterial({ color: this.colour(p) })); m.userData.person = p.id; this.markers.set(p.id, m); }
      m.material.color.set(this.colour(p));
      const w = this.where(p, a.time, S);
      if (m.parent !== v.overlay) v.overlay.add(m);
      m.visible = !!w;
      if (w) {
        const z = S === 'exterior' && a.terrain ? (a.terrain.heightAt(w.pos[0], w.pos[1]) ?? w.pos[2]) : w.pos[2];
        m.position.set(w.pos[0] - a.ours.origin[0], w.pos[1] - a.ours.origin[1], z - a.ours.origin[2]);
        m.material.transparent = w.inside; m.material.opacity = w.inside ? 0.4 : 1;
        m.scale.setScalar(this.sel === p.id ? 1.35 : 1); m.userData.at = [w.pos[0], w.pos[1], z]; m.userData.inside = w.inside;
      }
    }
    for (const [id, m] of this.markers) if (!seen.has(id)) { m.removeFromParent(); this.markers.delete(id); }
    v.redraw(); this.drawRoutes();
  }
  // labels and routes follow the camera once per animation frame
  cameraMoved(view) { if (view === this.app.ours.view && !this._routesDue) { this._routesDue = true; requestAnimationFrame(() => { this._routesDue = false; this.drawRoutes(); }); } }
  drawRoutes() {
    const a = this.app, v = a.ours.view, svg = this.layer(v); svg.innerHTML = '';
    const S = a.ours.space, scr = (p) => { const z = S === 'exterior' && a.terrain ? (a.terrain.heightAt(p[0], p[1]) ?? p[2]) : p[2]; return v.toScreen([p[0], p[1], z + 10]); };
    const add = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const [k, val] of Object.entries(attrs)) e.setAttribute(k, val); if (text) e.textContent = text; svg.append(e); return e; };
    // short name labels: everyone near the camera, and the selected person wherever they are
    const cam = v.camera.position, o = a.ours.origin, near = Math.max(1800, Math.min(4000, v.rig.dist * 1.2));
    for (const p of v.origin ? this.list() : []) {
      const m = this.markers.get(p.id), mine = this.sel === p.id;
      if (!m?.visible) continue;
      const d = Math.hypot(m.userData.at[0] - o[0] - cam.x, m.userData.at[1] - o[1] - cam.y, m.userData.at[2] - o[2] - cam.z);
      if (!mine && d > near) continue;
      const q = v.toScreen([m.userData.at[0], m.userData.at[1], m.userData.at[2] + 200]);
      if (q.behind || q.x < 0 || q.y < 0 || q.x > v.el.clientWidth || q.y > v.el.clientHeight) continue;
      const nm = p.name || 'Person', short = nm.length > 16 ? `${nm.slice(0, 15)}…` : nm;
      add('text', { class: mine ? 'who name sel' : 'who name', x: q.x, y: q.y, 'text-anchor': 'middle' }, short);
    }
    if (!this.active) return;
    for (const p of this.list()) {
      const c = this.colour(p), mine = this.sel === p.id;
      if (this.sel && !mine) continue;
      const pts = this.sorted(p).map((s) => ({ s, w: this.seenFrom(S, s) })).filter((x) => x.w?.p);
      if (pts.length > 1) add('polyline', { class: 'route', stroke: c, 'stroke-opacity': mine ? 0.95 : 0.5, points: [...pts, pts[0]].map((x) => { const q = scr(x.w.p); return `${q.x},${q.y}`; }).join(' ') });
      const pat = this.patrolPts(p);
      if (pat.length && S === 'exterior') add('polygon', { class: 'route', stroke: c, 'stroke-dasharray': '8 6', points: pat.map((q) => { const s = scr(q); return `${s.x},${s.y}`; }).join(' ') });
      if (mine) {
        for (const x of pts) {
          const q = scr(x.w.p); add('circle', { class: 'stop', cx: q.x, cy: q.y, r: 9, fill: c, 'fill-opacity': x.w.inside ? 0.45 : 1 });
          add('text', { class: 'who', x: q.x + 12, y: q.y - 8 }, `${clock(x.s.start)} ${STOP_KINDS[x.s.kind] || x.s.kind}${x.w.inside ? ' (inside)' : ''}`);
        }
        pat.forEach((q, i) => { if (S !== 'exterior') return; const s = scr(q); add('rect', { class: 'stop', x: s.x - 7, y: s.y - 7, width: 14, height: 14, fill: c }); add('text', { class: 'who', x: s.x + 10, y: s.y + 4 }, `Patrol ${i + 1}`); });
      }
    }
  }
  // ---------- picking and editing ----------
  pick(e) {
    let best = null, bd = 36;
    for (const [id, m] of this.markers) {
      if (!m.visible) continue;
      const q = e.view.toScreen([m.userData.at[0], m.userData.at[1], m.userData.at[2] + 80]), d = Math.hypot(q.x - e.x, q.y - e.y);
      if (d < bd) { bd = d; best = id; }
    }
    return best;
  }
  get tool() {
    const t = this;
    return this._tool || (this._tool = {
      wantsDrag: () => false,
      tap: (e) => {
        if (t.armed) { t.placeArmed(e); return; }
        const id = t.pick(e);
        if (!id) {
          const door = t.app.ours.place.pick(e.ray, { kinds: new Set(['door']) })[0];
          if (door?.ref.door?.to_space) { t.app.enter(t.app.ours, t.app.findRef(door.ref.id) || door.ref); return; }
        }
        t.select(id);
      },
    });
  }
  get srcTool() {
    const t = this, a = this.app;
    return this._srcTool || (this._srcTool = {
      wantsDrag: () => false,
      tap: (e) => {
        const h = a.src.layer.pick(e.ray, { kinds: new Set(['actor']) })[0];
        if (!h) { a.tools.srcSelect.tap(e); return; }
        t.armed = { kind: 'new', from: h.ref }; a.panels.personFromSource(h.ref);
      },
    });
  }
  select(id) { this.sel = id; this.armed = null; this.refresh(); this.app.panels.open('people'); }
  arm(kind, extra = {}) { this.armed = { kind, ...extra }; this.app.panels.open('people'); }
  placeArmed(e) {
    const a = this.app, g = e.ground(); if (!g) return;
    const S = a.ours.space, at = { space: S, pos: [rnd(g[0]), rnd(g[1]), rnd(g[2])], radius: 256 }, arm = this.armed;
    if (arm.kind === 'new') {
      const base = arm.from ? arm.from.base : arm.base, npc = a.npcs.get(base) || a.srcBundle.npcs.get(base);
      const person = { id: mintId(a.place.place_id), name: npc?.name || 'New person', base_from: base, role: 'resident', home: S, bed: null,
        work: null, services: [], faction_ranks: [], routine: [{ start: 0, hours: 24, kind: 'wander', at }] };
      a.push({ op: 'person.add', person }); this.armed = null; this.select(person.id); return;
    }
    const p = a.model.people.get(arm.id); if (!p) return;
    const before = clone(p), after = clone(p);
    if (arm.kind === 'stop') { const s = this.sorted(after)[arm.i]; const idx = after.routine.findIndex((r) => r.start === s.start && r.kind === s.kind); after.routine[idx].at = { ...after.routine[idx].at, ...at, ref: undefined }; delete after.routine[idx].at.ref; }
    if (arm.kind === 'patrol') { const pts = [...patrolOf(after)], q = S === 'exterior' ? at.pos : at; if (arm.i == null) pts.push(q); else pts[arm.i] = q; setPatrol(after, pts); }
    if (arm.kind === 'all') { // move the person: every outdoor stop shifts with them
      const first = this.sorted(p).map((s) => this.stopPoint(s)).find((x) => x.space === S && x.p);
      if (first) { const dx = g[0] - first.p[0], dy = g[1] - first.p[1]; for (const r of after.routine) if ((r.at?.space || 'exterior') === S && r.at.pos) r.at.pos = [rnd(r.at.pos[0] + dx), rnd(r.at.pos[1] + dy), r.at.pos[2]]; for (const q of patrolOf(after)) { const v = Array.isArray(q) ? q : q.pos; if (v && (Array.isArray(q) || (q.space || 'exterior') === S)) { v[0] = rnd(v[0] + dx); v[1] = rnd(v[1] + dy); } } }
    }
    this.armed = arm.kind === 'patrol' && arm.i == null ? arm : null;
    a.push({ op: 'person.edit', person: after, before }); this.refresh(); a.panels.open('people');
  }
  edit(id, fn) {
    const a = this.app, p = a.model.people.get(id); if (!p) return;
    const before = clone(p), after = clone(p); fn(after);
    if (JSON.stringify(before) !== JSON.stringify(after)) a.push({ op: 'person.edit', person: after, before });
  }
  remove(id) {
    const a = this.app, p = a.model.people.get(id); if (!p) return;
    a.push({ op: 'person.remove', person: clone(p), before: clone(p) }); this.sel = null; this.refresh();
  }
  // Problems a routine has: a stop in a room no door reaches, or with no place at all.
  problems(p) {
    const out = [];
    for (const s of p.routine || []) {
      const sp = this.stopPoint(s);
      if (!sp.p) out.push(`${clock(s.start)}: this stop has no spot.`);
      else if (sp.space !== 'exterior' && !this.doorTo('exterior', sp.space)) out.push(`${clock(s.start)}: no door leads from outside into ${sp.space}.`);
    }
    // an innkeeper keeps no bed and works the whole day, as Skyrim's do
    if (!isInnkeeper(p) && !(p.routine || []).some((s) => s.kind === 'sleep' || s.kind === 'bed')) out.push('This person has no time in bed.');
    return out;
  }
}

export const isInnkeeper = (p) => /innkeeper/i.test(p.role || '');
