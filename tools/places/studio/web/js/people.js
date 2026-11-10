// People: where each stands at the time on the day scrubber, their routine as a path through the place, and
// editing of their placement, stops, times and patrol points. Routines run through doors from street to room.
import * as THREE from 'three';
import { mintId } from './ids.js';
import { clock } from './geom.js';

const COLOURS = ['#2f7fd1', '#c2410c', '#15803d', '#7e22ce', '#b45309', '#0e7490', '#be185d', '#4d7c0f'];
const NS = 'http://www.w3.org/2000/svg';
const clone = (o) => JSON.parse(JSON.stringify(o));
const rnd = (v) => Math.round(v * 100) / 100;
export const STOP_KINDS = { home: 'At home', bed: 'Sleeping', work: 'Working', meal: 'Eating', patrol: 'On patrol', wander: 'Walking about', pray: 'Praying', shop: 'Shopping' };

export class People {
  constructor(app) {
    this.app = app; this.active = false; this.sel = null; this.armed = null; this.markers = new Map();
    this.geo = new THREE.CapsuleGeometry(26, 110, 4, 8).rotateX(Math.PI / 2).translate(0, 0, 81);
  }
  setActive(on) { this.active = on; if (!on) { this.armed = null; } this.refresh(); }
  list() { return [...(this.app.model?.people.values() || [])]; }
  colour(p) { const i = this.list().indexOf(p); return COLOURS[(i < 0 ? 0 : i) % COLOURS.length]; }
  // ---------- where a stop is, seen from a space ----------
  refPos(space, id) { return this.app.model.spaces[space]?.refs.get(id)?.pos || null; }
  stopPoint(stop) {
    const at = stop.at || {}; const p = at.pos || (at.ref && this.refPos(at.space || 'exterior', at.ref));
    return { space: at.space || 'exterior', p: p ? this.app.seatedPoint?.(p) || p : null };
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
    if (p.patrol?.length && ['patrol', 'work'].includes(a.s.kind) && this.stopPoint(a.s).space === S && S === 'exterior') {
      const n = p.patrol.length, f = (a.rel * 2) % n, i = Math.floor(f), u = f - i;
      const A = p.patrol[i], B = p.patrol[(i + 1) % n]; pos = [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u];
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
  cameraMoved(view) { if (view === this.app.ours.view) this.drawRoutes(); }
  drawRoutes() {
    const a = this.app, v = a.ours.view, svg = this.layer(v); svg.innerHTML = '';
    if (!this.active) return;
    const S = a.ours.space, scr = (p) => { const z = S === 'exterior' && a.terrain ? (a.terrain.heightAt(p[0], p[1]) ?? p[2]) : p[2]; return v.toScreen([p[0], p[1], z + 10]); };
    const add = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const [k, val] of Object.entries(attrs)) e.setAttribute(k, val); if (text) e.textContent = text; svg.append(e); return e; };
    for (const p of this.list()) {
      const c = this.colour(p), mine = this.sel === p.id;
      if (this.sel && !mine) continue;
      const pts = this.sorted(p).map((s) => ({ s, w: this.seenFrom(S, s) })).filter((x) => x.w?.p);
      if (pts.length > 1) add('polyline', { class: 'route', stroke: c, 'stroke-opacity': mine ? 0.95 : 0.5, points: [...pts, pts[0]].map((x) => { const q = scr(x.w.p); return `${q.x},${q.y}`; }).join(' ') });
      if (p.patrol?.length && S === 'exterior') add('polygon', { class: 'route', stroke: c, 'stroke-dasharray': '8 6', points: p.patrol.map((q) => { const s = scr(q); return `${s.x},${s.y}`; }).join(' ') });
      if (mine) {
        for (const x of pts) {
          const q = scr(x.w.p); add('circle', { class: 'stop', cx: q.x, cy: q.y, r: 9, fill: c, 'fill-opacity': x.w.inside ? 0.45 : 1 });
          add('text', { class: 'who', x: q.x + 12, y: q.y - 8 }, `${clock(x.s.start)} ${STOP_KINDS[x.s.kind] || x.s.kind}${x.w.inside ? ' (inside)' : ''}`);
        }
        (p.patrol || []).forEach((q, i) => { if (S !== 'exterior') return; const s = scr(q); add('rect', { class: 'stop', x: s.x - 7, y: s.y - 7, width: 14, height: 14, fill: c }); add('text', { class: 'who', x: s.x + 10, y: s.y + 4 }, `Patrol ${i + 1}`); });
      }
      const m = this.markers.get(p.id);
      if (m?.visible) { const q = v.toScreen(m.userData.at); add('text', { class: 'who', x: q.x + 14, y: q.y - 30 }, p.name || 'Person'); }
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
      const person = { id: mintId(a.place.place_id), name: npc?.name || 'New person', base_from: base, role: 'resident', home: { space: S }, bed: null,
        work: null, services: {}, faction_ranks: [], routine: [{ start: 0, hours: 24, kind: 'wander', at }] };
      a.push({ op: 'person.add', person }); this.armed = null; this.select(person.id); return;
    }
    const p = a.model.people.get(arm.id); if (!p) return;
    const before = clone(p), after = clone(p);
    if (arm.kind === 'stop') { const s = this.sorted(after)[arm.i]; const idx = after.routine.findIndex((r) => r.start === s.start && r.kind === s.kind); after.routine[idx].at = { ...after.routine[idx].at, ...at, ref: undefined }; delete after.routine[idx].at.ref; }
    if (arm.kind === 'patrol') { after.patrol = after.patrol || []; if (arm.i == null) after.patrol.push(at.pos); else after.patrol[arm.i] = at.pos; }
    if (arm.kind === 'all') { // move the person: every outdoor stop shifts with them
      const first = this.sorted(p).map((s) => this.stopPoint(s)).find((x) => x.space === S && x.p);
      if (first) { const dx = g[0] - first.p[0], dy = g[1] - first.p[1]; for (const r of after.routine) if ((r.at?.space || 'exterior') === S && r.at.pos) r.at.pos = [rnd(r.at.pos[0] + dx), rnd(r.at.pos[1] + dy), r.at.pos[2]]; for (const q of after.patrol || []) { q[0] = rnd(q[0] + dx); q[1] = rnd(q[1] + dy); } }
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
    if (!isInnkeeper(p) && !(p.routine || []).some((s) => s.kind === 'bed')) out.push('This person has no time in bed.');
    return out;
  }
}

export const isInnkeeper = (p) => /innkeeper/i.test(p.role || '');
