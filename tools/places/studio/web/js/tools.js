// The tools: select and the gizmo, adding from the source or a search, land, plants and paths.
import * as THREE from 'three';
import { ICON } from './icons.js';
import { mintId } from './ids.js';
import { fitRot } from './xform.js';
import { seatZ } from './bundle.js';
import { vegKey } from './edits.js';
import { segDist } from './geom.js';
import { lightsOf, localOf, poseFor } from './lights.js';
import { scaledPrim, wallsOf } from './prims.js';

const VEG = new Set(['tree', 'plant', 'groundcover']);
const RAIL = [
  ['select', 'Select'], ['search', 'Add'], ['people', 'People'], ['land', 'Land'], ['plants', 'Plants'], ['paths', 'Paths'],
  null, ['history', 'History'], ['saves', 'Saves'], ['notes', 'Notes'], ['help', 'Help'],
];
const rnd = (v, k = 100) => Math.round(v * k) / k;
const clone = (o) => JSON.parse(JSON.stringify(o));
const NS = 'http://www.w3.org/2000/svg';

function inPoly(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
// A pen stroke as a clean line: drop jitter, then round the corners.
export function smoothLine(pts, tol = 60) {
  if (pts.length < 3) return pts;
  const rdp = (a, b) => {
    let best = -1, bi = -1;
    for (let i = a + 1; i < b; i++) { const d = segDist(pts[i], pts[a], pts[b]); if (d > best) { best = d; bi = i; } }
    return best > tol ? [...rdp(a, bi).slice(0, -1), ...rdp(bi, b)] : [pts[a], pts[b]];
  };
  let out = rdp(0, pts.length - 1);
  for (let k = 0; k < 2; k++) {
    const n = [out[0]];
    for (let i = 0; i < out.length - 1; i++) {
      const [a, b] = [out[i], out[i + 1]];
      n.push([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]], [0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]]);
    }
    n.push(out[out.length - 1]); out = n;
  }
  return out.map(([x, y]) => [rnd(x, 10), rnd(y, 10)]);
}

export class Tools {
  constructor(app) {
    this.app = app; this.current = null; this.placing = null; this.opts = { snapGround: true, snapRot: true, selMode: 'lasso', adds: false };
    this.land = { kind: 'raise', radius: 384, strength: 0.5, level: null, picking: false };
    this.veg = { mode: 'clear', radius: 512 };
    this.path = { mode: 'draw', width: 256, style: null, kind: 'path', sel: null };
    this.outline = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: '#1fb5a8', depthTest: false, transparent: true }));
    this.outline.renderOrder = 10; this.srcOutline = this.outline.clone(); this.srcOutline.material = new THREE.LineBasicMaterial({ color: '#f0a030', depthTest: false, transparent: true });
    this.buildRail(); this.buildGizmo();
  }
  buildRail() {
    const rail = document.getElementById('rail'); rail.innerHTML = '';
    for (const it of RAIL) {
      if (!it) { const s = document.createElement('div'); s.className = 'sep'; rail.append(s); continue; }
      const b = document.createElement('button'); b.dataset.tool = it[0]; b.setAttribute('aria-pressed', 'false');
      b.innerHTML = `${ICON[it[0]]}<span>${it[1]}</span>`; b.onclick = () => this.use(it[0]); rail.append(b);
    }
  }
  use(name) {
    const a = this.app;
    if (name === 'help') { a.panels.intro(); return; }
    if (['history', 'saves', 'notes'].includes(name)) { a.panels.open(name); this.markRail(name); return; }
    this.current = name; this.markRail(name); this.clearSketch(a.ours.view); this.clearSketch(a.src.view);
    document.getElementById('timebar').hidden = name !== 'people'; a.timeLight?.();
    a.people.setActive(name === 'people');
    if (name !== 'search' && this.placing?.from === 'search') this.stopPlacing();
    if (name === 'select' && !a.selection.size) a.panels.close(); else a.panels.open(name);
    this.markRail(name); // the select panel opens when something is selected
    this.lightsShown();
    for (const v of [a.ours.view, a.src.view]) v.resize();
  }
  // The helpers (lights as bulbs with their rings, primitives as their boxes) are drawn and picked while selecting or
  // adding, or always with the Lights toggle.
  lightsOn() { return !!this.opts.lights || ['select', 'search'].includes(this.current); }
  lightsShown() {
    const a = this.app, on = this.lightsOn();
    for (const l of [a.ours.place, a.ours.world, a.src.layer]) l?.setShowLights(on);
    for (const v of [a.ours.view, a.src.view]) v?.redraw?.();
  }
  markRail(name) { document.querySelectorAll('#rail button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.tool === name))); }
  forView(view) {
    const a = this.app;
    if (view === a.src.view) return a.people.active ? a.people.srcTool : this.srcSelect;
    if (this.placing) return this.placeTool;
    return { select: this.selectTool, search: this.selectTool, land: this.landTool, plants: this.vegTool, paths: this.pathTool, people: a.people.tool }[this.current] || this.selectTool;
  }
  // Previews under the pen are drawn once per animation frame, however many pen events arrive in it.
  soon(name, fn) {
    this._soon = this._soon || new Map(); const had = this._soon.has(name); this._soon.set(name, fn);
    if (!had) requestAnimationFrame(() => { const f = this._soon.get(name); this._soon.delete(name); f(); });
  }
  key(e) {
    if (e.key === 'Delete' || e.key === 'Backspace') this.remove();
    if (e.key === 'Escape') { this.stopPlacing(); this.app.selection.clear(); this.selectionChanged(); }
  }
  // ---------- sketch overlay (lasso, brush ring, path stroke) ----------
  sketch(view) { return view.el.querySelector('.sketch'); }
  clearSketch(view) { const s = this.sketch(view); while (s.firstChild) s.firstChild.remove(); }
  svg(view, tag, attrs) { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); this.sketch(view).append(e); return e; }
  brushRing(view, g, radius) {
    let ring = this.sketch(view).querySelector('.brush');
    if (!g) { ring?.remove(); return; }
    if (!ring) ring = this.svg(view, 'polygon', { class: 'brush' });
    const pts = [];
    for (let i = 0; i < 40; i++) {
      const a = (i / 40) * Math.PI * 2, x = g[0] + Math.cos(a) * radius, y = g[1] + Math.sin(a) * radius;
      const z = (view.terrainData?.heightAt(x, y) ?? g[2]) + 4, s = view.toScreen([x, y, z]); pts.push(`${s.x},${s.y}`);
    }
    ring.setAttribute('points', pts.join(' '));
  }
  // ---------- select (ours) ----------
  get selectTool() {
    const t = this, a = this.app;
    return this._sel || (this._sel = {
      fingerTap: true,
      wantsDrag: (e) => e.pointerType === 'pen' || e.pointerType === 'mouse',
      tap: (e) => t.tapPick(e, a.ours, a.selection),
      down: (e) => { t.lasso = { pts: [[e.x, e.y]], el: t.svg(e.view, t.opts.selMode === 'box' ? 'rect' : 'polygon', { class: 'lasso' }) }; },
      move: (e) => t.lassoMove(e),
      up: (e) => t.lassoEnd(e, a.ours),
      cancel: (e) => { t.lasso?.el.remove(); t.lasso = null; t.clearSketch(e.view); },
    });
  }
  lassoMove(e) {
    const l = this.lasso; if (!l) return; l.pts.push([e.x, e.y]);
    if (this.opts.selMode === 'box') {
      const [x0, y0] = l.pts[0]; Object.entries({ x: Math.min(x0, e.x), y: Math.min(y0, e.y), width: Math.abs(e.x - x0), height: Math.abs(e.y - y0) }).forEach(([k, v]) => l.el.setAttribute(k, v));
    } else l.el.setAttribute('points', l.pts.map((p) => p.join(',')).join(' '));
  }
  lassoEnd(e, side) {
    const l = this.lasso; this.lasso = null; if (!l) return; l.el.remove();
    if (l.pts.length < 4) { this.tapPick(e, side, side === this.app.ours ? this.app.selection : null); return; }
    let poly = l.pts;
    if (this.opts.selMode === 'box') { const [x0, y0] = l.pts[0], [x1, y1] = l.pts[l.pts.length - 1]; poly = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]; }
    const refs = side === this.app.ours ? [...(this.app.model.spaces[side.space]?.refs.values() || [])].map((r) => this.app.seated(r)) : this.app.refsOf(side);
    const hit = refs.filter((r) => { const s = side.view.toScreen(r.pos); return !s.behind && inPoly([s.x, s.y], poly); });
    if (side === this.app.ours) {
      if (!this.opts.adds) this.app.selection.clear();
      for (const r of hit) this.app.selection.add(r.id);
      this.selectionChanged();
    } else { this.app.srcSel = hit; this.srcChanged(); }
  }
  // Tap: what is under the pen, best first; tapping the same spot again steps to the next thing there.
  tapPick(e, side, selSet) {
    const layers = side === this.app.ours ? [side.place] : [side.layer];
    const hits = layers.flatMap((l) => l.pick(e.ray));
    const same = this.lastTap && this.lastTap.side === side && Math.hypot(this.lastTap.x - e.x, this.lastTap.y - e.y) < 14 && performance.now() - this.lastTap.t < 4000;
    let idx = 0;
    if (same && hits.length > 1) idx = (this.lastTap.idx + 1) % hits.length;
    this.lastTap = { side, x: e.x, y: e.y, idx, t: performance.now(), n: hits.length };
    const h = hits[idx];
    if (side === this.app.ours) {
      if (h && !same && this.app.selection.size === 1 && this.app.selection.has(h.ref.id) && h.ref.door?.to_space) { this.app.enter(side, this.app.findRef(h.ref.id) || h.ref); return; }
      if (!this.opts.adds) selSet.clear();
      if (h) { selSet.has(h.ref.id) && this.opts.adds ? selSet.delete(h.ref.id) : selSet.add(h.ref.id); }
      this.cycleNote = hits.length > 1 ? `${idx + 1} of ${hits.length} things here. Tap again for the next.` : '';
      this.selectionChanged();
    } else {
      if (h && !same && this.app.srcSel.length === 1 && this.app.srcSel[0].id === h.ref.id && h.ref.door?.to_space) { this.app.enter(side, h.ref); return; }
      this.app.srcSel = h ? [h.ref] : [];
      this.cycleNote = hits.length > 1 ? `${idx + 1} of ${hits.length} things here. Tap again for the next.` : '';
      this.srcChanged();
    }
  }
  get srcSelect() {
    const t = this, a = this.app;
    return this._srcSel || (this._srcSel = {
      fingerTap: true,
      wantsDrag: (e) => e.pointerType === 'pen' || e.pointerType === 'mouse',
      tap: (e) => t.tapPick(e, a.src, null),
      down: (e) => { t.lasso = { pts: [[e.x, e.y]], el: t.svg(e.view, t.opts.selMode === 'box' ? 'rect' : 'polygon', { class: 'lasso' }) }; },
      move: (e) => t.lassoMove(e), up: (e) => t.lassoEnd(e, a.src),
      cancel: () => { t.lasso?.el.remove(); t.lasso = null; },
    });
  }
  srcChanged() {
    const a = this.app; this.drawOutline(a.src, a.srcSel, this.srcOutline);
    if (a.srcSel.length) {
      this.placing = { from: 'source', refs: a.srcSel, space: a.src.space };
      a.panels.sourceInfo(a.srcSel);
    } else { if (this.placing?.from === 'source') this.placing = null; a.panels.sourceInfo([]); }
    this.placeGizmo();  // no handles while placing: a tap there places
  }
  stopPlacing() { this.placing = null; this.app.srcSel = []; this.drawOutline(this.app.src, [], this.srcOutline); this.app.panels.placingChanged?.(); this.placeGizmo(); }
  // ---------- selection outline and gizmo ----------
  selectionChanged() {
    const a = this.app; if (!a.model) return;
    this.drawSelection(); a.panels.selectionInfo([...a.selection].map((id) => a.placeRefsById().get(id)).filter(Boolean), this.cycleNote);
  }
  drawSelection() {
    const a = this.app; if (!a.model) return;
    const sel = this.selRefs();
    this.drawOutline(a.ours, sel.map((r) => a.seated(r)), this.outline);
    // a selected light, and the lights of a selected fixture, show their radius rings
    a.ours.place?.setRingIds([...sel.filter((r) => r.kind === 'light'), ...this.followers(sel).filter((f) => !f.wall).map((f) => f.ref)].map((r) => r.id));
    this.placeGizmo(); a.panels?.refreshWhere?.();
  }
  drawOutline(side, refs, line) {
    const layer = side === this.app.ours ? side.place : side.layer;
    if (!layer) return;
    const E = [[0, 1], [0, 2], [1, 3], [2, 3], [4, 5], [4, 6], [5, 7], [6, 7], [0, 4], [1, 5], [2, 6], [3, 7]], pos = [];
    for (const r of refs) { const c = layer.worldBox(r); for (const [i, j] of E) pos.push(c[i].x, c[i].y, c[i].z, c[j].x, c[j].y, c[j].z); }
    line.geometry.dispose(); line.geometry = new THREE.BufferGeometry(); line.geometry.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    if (line.parent !== side.view.overlay) side.view.overlay.add(line);
    side.view.redraw();
  }
  buildGizmo() {
    const g = document.querySelector('#view-ours .gizmo');
    g.innerHTML = `<div class="ring"></div><div class="h move" data-h="move" role="button" aria-label="Drag to move">${ICON.move}</div>
      <div class="h" data-h="lift" role="button" aria-label="Drag up or down to lift">${ICON.lift}</div>
      <div class="h" data-h="rotate" role="button" aria-label="Drag round to turn">${ICON.rotate}</div>
      <div class="h" data-h="scale" role="button" aria-label="Drag to resize">${ICON.scale}</div>`;
    this.gizmo = g;
    g.querySelectorAll('.h').forEach((h) => {
      h.addEventListener('pointerdown', (e) => { e.stopPropagation(); if (e.pointerType === 'touch' && this.app.penSeen) return; h.setPointerCapture(e.pointerId); this.gizmoDown(h.dataset.h, e); });
      h.addEventListener('pointermove', (e) => this.gizmoMove(e));
      h.addEventListener('pointerup', (e) => this.gizmoUp(e));
      h.addEventListener('pointercancel', () => this.gizmoCancel());
    });
  }
  selRefs() { const m = this.app.placeRefsById(); return [...this.app.selection].map((id) => m.get(id)).filter(Boolean); }
  // ---------- lights travel with their fixtures, invisible walls with their pieces ----------
  baseOf(r) { return this.app.bases.get(r.base) || this.app.srcBases?.get(r.base); }
  // The lights that belong to the fixtures among refs, and the invisible walls seated on the pieces among them (not
  // themselves selected), each with where it sits in its owner's frame: they follow every move, turn and resize of
  // it, in the same undo step; a wall also grows or shrinks with its piece.
  followers(refs) {
    const a = this.app, ids = new Set(refs.map((r) => r.id)), pos = (r) => a.seated(r).pos;
    const others = [...a.placeRefsById().values()].filter((r) => !ids.has(r.id) && !r.removed);
    const pose = (r) => clone({ pos: r.pos, rot: r.rot, scale: r.scale ?? 1, seat: r.seat });
    const lights = lightsOf(refs, others, (r) => this.baseOf(r), pos).map(([ref, fix]) => ({ ref, fix, local: localOf(ref, fix, pos), before: pose(ref) }));
    const walls = wallsOf(refs, others).map(([ref, fix]) => ({ ref, fix, wall: true, s0: fix.scale ?? 1, local: localOf(ref, fix, pos),
      before: { ...pose(ref), primitive: clone(ref.primitive) } }));
    return [...lights, ...walls];
  }
  // Each follower placed for its owner's pose now (its height through its own seat, so the build seats it there).
  carry(fol) {
    const a = this.app, ext = a.ours.space === 'exterior';
    for (const f of fol) {
      const [p, rot] = poseFor(f.local, f.fix, f.ref, (r) => a.seated(r).pos), r = f.ref;
      r.pos = [rnd(p[0]), rnd(p[1]), r.pos[2]]; r.rot = [rot[0], rot[1], rnd(norm(rot[2]), 10000)];
      if (ext && r.seat && r.seat.mode !== 'free') {
        r.seat = { ...r.seat }; const cur = seatZ(a.terrain, r, a.placeRefsById());
        r.seat.dz = rnd((r.seat.dz || 0) + p[2] - cur); r.pos[2] = rnd(p[2]);
      } else r.pos[2] = rnd(p[2]);
      if (f.wall) { const k = (f.fix.scale ?? 1) / f.s0; r.primitive = k === 1 ? clone(f.before.primitive) : scaledPrim(f.before.primitive, k); }
    }
  }
  followerOps(fol) {
    const ops = [];
    for (const f of fol) {
      const after = clone({ pos: f.ref.pos, rot: f.ref.rot, scale: f.ref.scale ?? 1, seat: f.ref.seat, ...(f.wall ? { primitive: f.ref.primitive } : {}) });
      Object.assign(f.ref, clone(f.before));
      if (JSON.stringify(after) !== JSON.stringify(f.before)) ops.push({ op: 'ref.move', id: f.ref.id, before: f.before, after });
    }
    return ops;
  }
  centre(refs) { const n = refs.length || 1; return [0, 1, 2].map((i) => refs.reduce((s, r) => s + this.app.seated(r).pos[i], 0) / n); }
  placeGizmo() {
    const g = this.gizmo, refs = this.selRefs(), v = this.app.ours.view;
    const show = refs.length && ['select', 'search'].includes(this.current) && !this.placing;
    g.hidden = !show; if (!show) return;
    const c = this.centre(refs), s = v.toScreen(c);
    if (s.behind) { g.hidden = true; return; }
    const R = 78;
    g.style.left = `${s.x}px`; g.style.top = `${s.y}px`;
    const set = (h, x, y) => { const el = g.querySelector(`[data-h="${h}"]`); el.style.left = `${x}px`; el.style.top = `${y}px`; };
    set('move', 0, 0); set('lift', 0, -R); set('rotate', R, 0); set('scale', R * 0.72, R * 0.72);
    const ring = g.querySelector('.ring'); Object.assign(ring.style, { left: `${-R}px`, top: `${-R}px`, width: `${2 * R}px`, height: `${2 * R}px` });
  }
  gizmoDown(kind, e) {
    const refs = this.selRefs(); if (!refs.length || this.placing) return;
    const v = this.app.ours.view, info = v.info(e);
    this.drag = { kind, refs, before: new Map(refs.map((r) => [r.id, clone({ pos: r.pos, rot: r.rot, scale: r.scale ?? 1, seat: r.seat })])),
      x0: e.clientX, y0: e.clientY, g0: info.ground(), c: this.centre(refs), fol: this.followers(refs) };
    const sc = v.toScreen(this.drag.c), rect = v.canvas.getBoundingClientRect();
    this.drag.sx = sc.x + rect.left; this.drag.sy = sc.y + rect.top; this.drag.a0 = Math.atan2(e.clientY - this.drag.sy, e.clientX - this.drag.sx);
  }
  gizmoMove(e) {
    const d = this.drag; if (!d) return;
    const v = this.app.ours.view, a = this.app;
    for (const r of d.refs) { const b = d.before.get(r.id); r.pos = [...b.pos]; r.rot = [...(b.rot || [0, 0, 0])]; r.scale = b.scale; r.seat = b.seat ? { ...b.seat } : b.seat; }
    if (d.kind === 'move') {
      const g = v.info(e).ground(); if (!g || !d.g0) return;
      const dx = g[0] - d.g0[0], dy = g[1] - d.g0[1];
      for (const r of d.refs) { r.pos[0] = rnd(r.pos[0] + dx); r.pos[1] = rnd(r.pos[1] + dy); this.reseat(r); }
    } else if (d.kind === 'lift') {
      const dz = rnd(-(e.clientY - d.y0) * v.rig.dist * 0.0012);
      for (const r of d.refs) { if (r.seat && r.seat.mode !== 'free' && r.seat.mode !== 'on') r.seat = { ...r.seat, dz: rnd((r.seat.dz || 0) + dz) }; else r.pos[2] = rnd(r.pos[2] + dz); }
    } else if (d.kind === 'rotate') {
      let ang = Math.atan2(e.clientY - d.sy, e.clientX - d.sx) - d.a0;
      if (this.opts.snapRot) ang = Math.round(ang / (Math.PI / 12)) * (Math.PI / 12);
      // screen clockwise is a clockwise turn seen from above, which is the game's positive Z angle
      const c = Math.cos(-ang), s = Math.sin(-ang);
      for (const r of d.refs) {
        const ox = r.pos[0] - d.c[0], oy = r.pos[1] - d.c[1];
        if (d.refs.length > 1) { r.pos[0] = rnd(d.c[0] + c * ox - s * oy); r.pos[1] = rnd(d.c[1] + s * ox + c * oy); this.reseat(r); }
        r.rot = [r.rot[0], r.rot[1], rnd(norm(r.rot[2] + ang), 10000)];
      }
    } else if (d.kind === 'scale') {
      const f = Math.max(0.1, Math.min(10, Math.exp(((e.clientX - d.x0) - (e.clientY - d.y0)) * 0.004)));
      for (const r of d.refs) r.scale = rnd((d.before.get(r.id).scale || 1) * f, 1000);
    }
    this.carry(d.fol);
    this.soon('drag', () => a.refreshSide(a.ours, { world: false, grass: false }));
  }
  reseat(r) {
    if (this.app.ours.space !== 'exterior') return;
    if (this.opts.snapGround) { if (!r.seat || r.seat.mode === 'free') r.seat = { mode: 'ground', dz: 0 }; r.pos[2] = rnd(seatZ(this.app.terrain, r, this.app.placeRefsById())); }
  }
  gizmoUp(e) {
    const d = this.drag; if (!d) return;
    // a tap on a handle with no movement changes nothing (it never re-seats things where they stand)
    if (e && Math.hypot(e.clientX - d.x0, e.clientY - d.y0) < 3) { this.gizmoCancel(); return; }
    this.drag = null;
    const ops = [];
    for (const r of d.refs) {
      const after = clone({ pos: r.pos, rot: r.rot, scale: r.scale ?? 1, seat: r.seat }), before = d.before.get(r.id);
      if (r.seat && r.seat.mode !== 'free' && this.app.ours.space === 'exterior') after.pos[2] = rnd(seatZ(this.app.terrain, r, this.app.placeRefsById()));
      Object.assign(r, clone(before));
      if (JSON.stringify(after) !== JSON.stringify(before)) ops.push({ op: 'ref.move', id: r.id, before, after });
    }
    // the fixtures' lights and the pieces' walls follow their final poses, in the same undo step
    for (const r of d.refs) { const k = ops.find((o) => o.id === r.id); if (k) Object.assign(r, clone(k.after)); }
    this.carry(d.fol); ops.push(...this.followerOps(d.fol));
    for (const r of d.refs) Object.assign(r, clone(d.before.get(r.id)));
    this.app.push(ops);
  }
  gizmoCancel() {
    const d = this.drag; this.drag = null; if (!d) return;
    for (const r of d.refs) Object.assign(r, clone(d.before.get(r.id)));
    for (const f of d.fol || []) Object.assign(f.ref, clone(f.before));
    this.app.refreshSide(this.app.ours, { world: false });
  }
  // Ops that move refs, and the lights and invisible walls that follow them with them (one undo step).
  withFollowers(refs, ops) {
    const fol = this.followers(refs); if (!fol.length) return ops;
    const before = new Map(refs.map((r) => [r.id, clone({ pos: r.pos, rot: r.rot, scale: r.scale ?? 1, seat: r.seat })]));
    for (const o of ops) { const r = refs.find((x) => x.id === o.id); if (r) Object.assign(r, clone(o.after)); }
    this.carry(fol); const extra = this.followerOps(fol);
    for (const r of refs) Object.assign(r, before.get(r.id));
    return [...ops, ...extra];
  }
  cameraMoved(view) {
    if (view === this.app.ours.view) this.placeGizmo();
    this.clearSketch(view);
  }
  // Nudge by a step in the game's directions, or turn by the snap step.
  nudge(dx, dy, dz, drot = 0, dscale = 0) {
    const ops = [];
    for (const r of this.selRefs()) {
      const before = clone({ pos: r.pos, rot: r.rot, scale: r.scale ?? 1, seat: r.seat }), after = clone(before);
      after.pos[0] = rnd(after.pos[0] + dx); after.pos[1] = rnd(after.pos[1] + dy);
      if (dz) { if (after.seat && after.seat.mode !== 'free' && after.seat.mode !== 'on') after.seat.dz = rnd((after.seat.dz || 0) + dz); else after.pos[2] = rnd(after.pos[2] + dz); }
      after.rot = [after.rot?.[0] || 0, after.rot?.[1] || 0, rnd(norm((after.rot?.[2] || 0) + drot), 10000)];
      if (dscale) after.scale = rnd(Math.max(0.1, after.scale * (1 + dscale)), 1000);
      if (after.seat && after.seat.mode !== 'free' && this.app.ours.space === 'exterior') after.pos[2] = rnd(seatZ(this.app.terrain, { ...r, ...after }, this.app.placeRefsById()));
      ops.push({ op: 'ref.move', id: r.id, before, after });
    }
    this.app.push(this.withFollowers(this.selRefs(), ops));
  }
  snapToGround() {
    const ops = [];
    for (const r of this.selRefs()) {
      const before = clone({ pos: r.pos, rot: r.rot, scale: r.scale ?? 1, seat: r.seat }), after = clone(before);
      after.seat = { mode: 'ground', dz: 0 }; after.pos[2] = rnd(seatZ(this.app.terrain, { ...r, seat: after.seat }, null));
      ops.push({ op: 'ref.move', id: r.id, before, after });
    }
    this.app.push(this.withFollowers(this.selRefs(), ops));
  }
  duplicate() {
    const a = this.app, ops = [], ids = [], sel = this.selRefs();
    const refs = [...sel, ...this.followers(sel).map((f) => f.ref)];  // a fixture's copy comes with its light, a piece's with its walls
    const fresh = new Map(refs.map((r) => [r.id, mintId(a.place.place_id)]));
    for (const r of refs) {
      const n = clone(r); n.id = fresh.get(r.id); n.pos[0] = rnd(n.pos[0] + 150); n.pos[1] = rnd(n.pos[1] + 150);
      if (n.seat?.mode === 'on' && fresh.has(n.seat.on)) n.seat.on = fresh.get(n.seat.on);  // seated on the copy
      if (n.door) delete n.door; // a copied door does not lead anywhere until it is paired
      ops.push({ op: 'ref.add', ref: n }); if (sel.includes(r)) ids.push(n.id);
    }
    a.push(ops); a.selection = new Set(ids); this.selectionChanged();
  }
  remove() {
    const a = this.app, sel = this.selRefs(); if (!sel.length) return;
    const refs = [...sel, ...this.followers(sel).map((f) => f.ref)];  // a fixture goes with its light, a piece with its walls
    a.push(refs.map((r) => ({ op: 'ref.remove', id: r.id, before: clone(r) })));
    a.selection.clear(); this.selectionChanged();
  }
  // ---------- adding: a source group or a searched base, where the pen taps ----------
  get placeTool() {
    const t = this;
    return this._place || (this._place = { wantsDrag: () => false, tap: (e) => t.placeAt(e), hover: () => {} });
  }
  placeAt(e) {
    const a = this.app, g = e.ground(); if (!g) { a.toast('Tap on the ground to put it there.'); return; }
    const p = this.placing; let ops;
    if (p.from === 'search') ops = [{ op: 'ref.add', ref: this.newRef(p.base, g) }];
    else ops = this.copyGroup(p.refs, p.space, g);
    a.push(ops);
    const added = ops.filter((o) => (o.space || a.ours.space) === a.ours.space).map((o) => o.ref.id);
    a.selection = new Set(added); this.selectionChanged();
    if (p.from === 'search') { this.placing = null; this.current = 'search'; a.panels.placingChanged(); this.selectionChanged(); }
  }
  newRef(base, g) {
    const a = this.app, ext = a.ours.space === 'exterior';
    const r = { id: mintId(a.place.place_id), base: base.key, kind: base.kind || 'static', pos: [rnd(g[0]), rnd(g[1]), rnd(g[2])], rot: [0, 0, 0], scale: 1,
      layer: 'place', flags: [], seat: ext ? { mode: 'ground', dz: 0 } : { mode: 'free' } };
    return r;
  }
  // Doors on or in a source building, found by standing inside its footprint.
  doorsOf(building, srcRefs) {
    const b = this.app.srcBases.get(building.base)?.bounds; if (!b) return [];
    return srcRefs.filter((d) => d.kind === 'door' && d.door?.to_space && d !== building && (() => {
      // the door in the building's own frame (the game's Z angle turns clockwise)
      const dx = d.pos[0] - building.pos[0], dy = d.pos[1] - building.pos[1], c = Math.cos(building.rot[2]), s = Math.sin(building.rot[2]);
      const lx = c * dx - s * dy, ly = s * dx + c * dy, sc = building.scale || 1, m = 200;
      return lx > b[0][0] * sc - m && lx < b[1][0] * sc + m && ly > b[0][1] * sc - m && ly < b[1][1] * sc + m;
    })());
  }
  copyGroup(srcRefs, srcSpace, g) {
    const a = this.app, fit = a.fit, toExt = a.ours.space === 'exterior', fromExt = srcSpace === 'exterior';
    const allSrc = a.srcBundle.spaces[srcSpace]?.refs || [];
    let group = [...srcRefs];
    if (fromExt) for (const r of srcRefs) if (r.kind === 'building') for (const d of this.doorsOf(r, allSrc)) if (!group.includes(d)) group.push(d);
    const n = group.length, cx = group.reduce((s, r) => s + r.pos[0], 0) / n, cy = group.reduce((s, r) => s + r.pos[1], 0) / n;
    const minZ = Math.min(...group.map((r) => r.pos[2]));
    const rot = toExt && fromExt ? fit.rot || 0 : 0, c = Math.cos(rot), s = Math.sin(rot), k = fit.scale || 1;
    const st = a.src.terrain;
    const place = (sp) => { const ox = (sp[0] - cx) * k, oy = (sp[1] - cy) * k; return [rnd(g[0] + c * ox - s * oy), rnd(g[1] + s * ox + c * oy)]; };
    const ops = [], idMap = new Map();
    for (const r of group) idMap.set(r.id, mintId(a.place.place_id));
    const interiors = new Map();
    for (const r of group) {
      const nr = clone(r); nr.id = idMap.get(r.id); nr.src = r.id; nr.layer = 'place';
      const [x, y] = place(r.pos);
      nr.rot = rot ? fitRot(fit, r.rot || [0, 0, 0]) : [...(r.rot || [0, 0, 0])];
      if (toExt) {
        const sg = fromExt && st ? st.heightAt(r.pos[0], r.pos[1]) : null;
        const dz = sg != null ? rnd(r.pos[2] - sg) : rnd(r.pos[2] - minZ);
        nr.seat = { mode: Math.abs(dz) < 2 ? 'ground' : 'above', dz: Math.abs(dz) < 2 ? 0 : dz };
        nr.pos = [x, y, 0]; nr.pos[2] = rnd(seatZ(a.terrain, nr, null));
      } else { nr.seat = { mode: 'free' }; nr.pos = [x, y, rnd(g[2] + (r.pos[2] - minZ))]; }
      delete nr.owner; // owners are ours to set
      if (r.door?.to_space) {
        const to = r.door.to_space;
        if (!interiors.has(to)) interiors.set(to, this.copyInterior(to, r, nr));
        const it = interiors.get(to);
        nr.door = { ...r.door, to_space: it.space, to_ref: it.idMap.get(r.door.to_ref) || r.door.to_ref };
        it.outside.set(r.door.to_ref, nr);
      }
      ops.push({ op: 'ref.add', ref: nr });
    }
    for (const it of interiors.values()) {
      for (const op of it.ops) {
        const back = it.outside.get(op.srcId); delete op.srcId;
        if (back && op.ref.door) {
          // the way out lands where the source's own way out lands, carried across with the building (else at its door)
          const sp = op.ref.door.to_pos; let to = [...back.pos], tr = [...back.rot];
          if (sp && fromExt) { const [ax, ay] = place(sp); to = [ax, ay, toExt ? rnd(a.terrain?.heightAt(ax, ay) ?? back.pos[2]) : back.pos[2]]; tr = rot ? fitRot(fit, op.ref.door.to_rot || [0, 0, 0]) : [...(op.ref.door.to_rot || [0, 0, 0])]; }
          op.ref.door = { ...op.ref.door, to_space: a.ours.space, to_ref: back.id, to_pos: to, to_rot: tr };
        }
        ops.push(op);
      }
    }
    if (interiors.size) a.toast(`Added with ${interiors.size === 1 ? 'its room inside' : `its ${interiors.size} rooms inside`} and the doors between them.`);
    return ops;
  }
  copyInterior(srcSpace, srcDoor) {
    const a = this.app, refs = a.srcBundle.spaces[srcSpace]?.refs || [];
    let sid = srcSpace, i = 2; while (a.model.spaces[sid]) sid = `${srcSpace}_${i++}`;
    const idMap = new Map(refs.map((r) => [r.id, mintId(a.place.place_id)]));
    const info = a.srcBundle.spaces[srcSpace]?.info || {};
    const ops = refs.map((r, j) => {
      const nr = clone(r); nr.id = idMap.get(r.id); nr.src = r.id; nr.layer = 'place'; nr.seat = { mode: 'free' };
      const op = { op: 'ref.add', space: sid, ref: nr, srcId: r.id };
      if (j === 0) { op.space_copy_of = `${a.sourceId}/${srcSpace}`; op.space_name = info.name || srcSpace; }
      return op;
    });
    a.spaceInfo[sid] = { space_id: sid, type: 'interior', name: info.name || srcSpace, copy_of: `${a.sourceId}/${srcSpace}` };
    void srcDoor;
    return { space: sid, idMap, ops, outside: new Map() };
  }
  // ---------- land ----------
  get landTool() {
    const t = this, a = this.app, L = this.land;
    return this._land || (this._land = {
      wantsDrag: () => true,
      hover: (e) => t.brushRing(e.view, e.ground(), L.radius),
      tap: (e) => { if (L.picking) { const g = e.ground(); if (g) { L.level = rnd(g[2]); L.picking = false; a.panels.open('land'); } return; } t._land.down(e); t._land.up(e); },
      down: (e) => {
        if (a.ours.space !== 'exterior') { a.toast('Land can be changed outside only.'); return false; }
        const g = e.ground(); if (!g) return false;
        t.stroke = { before: new Map(), level: L.kind === 'level' ? (L.level ?? rnd(g[2])) : null };
        t.landDab(e, g);
      },
      move: (e) => { const g = e.ground(); t.brushRing(e.view, g, L.radius); if (g && t.stroke) t.landDab(e, g); },
      up: () => t.landEnd(),
      cancel: () => t.landEnd(true),
    });
  }
  landDab(e, g) {
    const a = this.app, T = a.terrain, L = this.land, st = this.stroke, MAX = 1500;
    const pts = T.pointsAt(g[0], g[1], L.radius), amt = L.strength * (0.4 + e.pressure) * 24;
    const changedCells = new Set();
    for (const p of pts) {
      const fall = 0.5 + 0.5 * Math.cos(Math.PI * Math.min(1, p.d / L.radius));
      const k0 = p.shared[0], cur = T.h(k0.cell, k0.row, k0.col);
      let nz = cur;
      if (L.kind === 'raise') nz = cur + amt * fall;
      else if (L.kind === 'lower') nz = cur - amt * fall;
      else if (L.kind === 'level') nz = cur + (st.level - cur) * Math.min(1, 0.25 * fall * (0.5 + e.pressure) * L.strength * 2);
      else if (L.kind === 'smooth') {
        const nb = T.pointsAt(p.x, p.y, T.step * 1.5).map((q) => T.h(q.shared[0].cell, q.shared[0].row, q.shared[0].col));
        const avg = nb.reduce((s, v) => s + v, 0) / nb.length; nz = cur + (avg - cur) * 0.5 * fall * L.strength;
      }
      for (const s of p.shared) {
        const key = `${s.cell.join(',')}|${s.row}|${s.col}`;
        const ck = s.cell.join(','), cm = T.override.get(ck) || new Map(), idx = s.row * T.grid + s.col;
        if (!st.before.has(key)) { if (st.before.size >= MAX) continue; st.before.set(key, { ...s, dz: cm.get(idx) || 0 }); }
        cm.set(idx, rnd(nz - T.base(s.cell, s.row, s.col))); T.override.set(ck, cm); changedCells.add(ck);
      }
    }
    a.ours.terrainMesh.refreshCells(changedCells); a.ours.terrainMesh.tintCells(changedCells);
    this.soon('land', () => { a.refreshSide(a.ours, { world: false, grass: false }); a.panels.landCount?.(st.before.size, st.before.size >= MAX); });
  }
  landEnd(cancel) {
    const a = this.app, T = a.terrain, st = this.stroke; this.stroke = null; if (!st) return;
    const byCell = new Map();
    for (const b of st.before.values()) {
      const ck = b.cell.join(','), cm = T.override.get(ck), idx = b.row * T.grid + b.col, after = cm.get(idx) || 0;
      if (b.dz) cm.set(idx, b.dz); else cm.delete(idx); // put back; the op applies it
      if (cancel || Math.abs(after - b.dz) < 0.01) continue;
      if (!byCell.has(ck)) byCell.set(ck, { cell: b.cell, verts: [] });
      byCell.get(ck).verts.push([b.row, b.col, b.dz, Math.abs(after) < 0.01 ? 0 : after]);
    }
    const L = this.land, tool = { kind: L.kind, radius: L.radius, strength: L.strength };
    if (L.kind === 'level') tool.height = st.level;
    const ops = [...byCell.values()].map((c) => ({ op: 'land.patch', cell: c.cell, verts: c.verts, tool }));
    const touched = new Set([...st.before.values()].map((b) => b.cell.join(',')));
    if (ops.length) { a.ours.terrainMesh.refreshCells(touched); a.push(ops, 'exterior'); } else { a.ours.terrainMesh.refreshCells(touched); a.ours.terrainMesh.tintCells(touched); a.refreshSide(a.ours, { world: false }); }
  }
  // ---------- plants ----------
  get vegTool() {
    const t = this, a = this.app, V = this.veg;
    return this._veg || (this._veg = {
      wantsDrag: (e) => e.pointerType !== 'touch' || !a.penSeen,
      hover: (e) => t.brushRing(e.view, e.ground(), V.radius),
      tap: (e) => t.vegTap(e),
      down: (e) => { if (a.ours.space !== 'exterior') return false; t.vstroke = new Map(); t.vegDab(e); },
      move: (e) => { t.brushRing(e.view, e.ground(), V.radius); if (t.vstroke) t.vegDab(e); },
      up: () => t.vegEnd(), cancel: () => { t.vstroke = null; t.brushRing(a.ours.view, null); a.refreshSide(a.ours); },
    });
  }
  vegTap(e) {
    const a = this.app, restore = this.veg.mode === 'restore';
    const hits = a.ours.world.pick(e.ray, { kinds: VEG, includeGhosts: true }).filter((h) => h.ghost === restore || (!restore && !h.ghost));
    const h = hits.find((x) => (restore ? a.isCleared(x.ref) : !a.isCleared(x.ref)));
    if (!h) { a.toast(restore ? 'Turn on "Show cleared plants" and tap a ghost to bring it back.' : 'No plant there.'); return; }
    // a restore carries the whole cleared row (by, why, ref) so its undo puts it back exactly
    const item = restore ? { ...a.model.clear.get(a.vegKeyOf(h.ref)) } : { base: h.ref.base, pos: h.ref.pos };
    a.push({ op: restore ? 'veg.restore' : 'veg.clear', items: [item] }, 'exterior');
  }
  vegDab(e) {
    const a = this.app, g = e.ground(); if (!g) return;
    const restore = this.veg.mode === 'restore', R2 = this.veg.radius ** 2;
    for (const r of a.worldRefs) {
      if (!VEG.has(r.kind)) continue;
      const d2 = (r.pos[0] - g[0]) ** 2 + (r.pos[1] - g[1]) ** 2; if (d2 > R2) continue;
      const k = a.vegKeyOf(r); if (this.vstroke.has(k)) continue;
      if (restore ? a.isCleared(r) : !a.isCleared(r)) { this.vstroke.set(k, restore ? { ...a.model.clear.get(k) } : { base: r.base, pos: r.pos }); this.vfresh = true; }
    }
    if (!this.vfresh) return;
    // preview: hide (or show) what the brush has touched so far
    this.soon('veg', () => {
      if (!this.vstroke) return; this.vfresh = false;
      const W = a.ours.world, list = [];
      for (const x of W.refs) {
        const hit = this.vstroke.has(a.vegKeyOf(x.ref));
        if (!restore) { if (!hit) list.push(x); } else list.push(hit && x.ghost ? { ref: x.ref } : x);
      }
      // restoring with the cleared plants not shown: they come back into view as the brush passes
      if (restore) for (const k of this.vstroke.keys()) { const r = a.worldByKey(k); if (r && !W.byId.has(r.id)) list.push({ ref: r }); }
      W.setRefs(list);
    });
  }
  vegEnd() {
    const a = this.app, items = [...(this.vstroke?.values() || [])]; this.vstroke = null;
    if (items.length) a.push({ op: this.veg.mode === 'restore' ? 'veg.restore' : 'veg.clear', items }, 'exterior');
    else a.refreshSide(a.ours);
  }
  // ---------- paths ----------
  get pathTool() {
    const t = this, a = this.app, P = this.path;
    return this._path || (this._path = {
      wantsDrag: () => P.mode === 'draw',
      tap: (e) => t.pathTap(e),
      down: (e) => { if (a.ours.space !== 'exterior') return false; const g = e.ground(); if (!g) return false; t.pstroke = { pts: [g], el: t.svg(e.view, 'polyline', { class: 'stroke' }), scr: [[e.x, e.y]] }; },
      move: (e) => { const s = t.pstroke; if (!s) return; const g = e.ground(); if (!g) return; s.pts.push(g); s.scr.push([e.x, e.y]); s.el.setAttribute('points', s.scr.map((p) => p.join(',')).join(' ')); },
      up: () => t.pathEnd(),
      cancel: () => { t.pstroke?.el.remove(); t.pstroke = null; },
    });
  }
  pathEnd() {
    const s = this.pstroke; this.pstroke = null; if (!s) return; s.el.remove();
    const pts = smoothLine(s.pts.map((p) => [p[0], p[1]]), Math.max(40, this.path.width / 4));
    if (pts.length < 2 || Math.hypot(pts[0][0] - pts[pts.length - 1][0], pts[0][1] - pts[pts.length - 1][1]) < 100) return;
    const a = this.app, P = this.path, style = P.style || Object.keys(a.pathStyles)[0];
    const path = { id: mintId(a.place.place_id), kind: P.kind, points: pts, width: P.width, style };
    a.push({ op: 'path.add', path }, 'exterior'); P.sel = path.id; this.drawPathHandles(); a.panels.open('paths');
  }
  pathTap(e) {
    const a = this.app, g = e.ground(); if (!g) return;
    let best = null, bd = Infinity;
    for (const p of a.model.paths.values()) for (let i = 1; i < p.points.length; i++) { const d = segDist(g, p.points[i - 1], p.points[i]) - p.width / 2; if (d < bd) { bd = d; best = p; } }
    this.path.sel = best && bd < 200 ? best.id : null; this.drawPathHandles(); a.panels.open('paths');
  }
  drawPathHandles() {
    const a = this.app, v = a.ours.view; this.clearSketch(v);
    const p = a.model.paths.get(this.path.sel); if (!p || this.current !== 'paths') return;
    const sk = this.sketch(v);
    p.points.forEach((pt, i) => {
      if (p.points.length > 12 && i % Math.ceil(p.points.length / 12) && i !== p.points.length - 1) return;
      const z = a.terrain.heightAt(pt[0], pt[1]) ?? 0, s = v.toScreen([pt[0], pt[1], z]);
      const c = this.svg(v, 'circle', { cx: s.x, cy: s.y, r: 18, class: 'brush' }); c.style.pointerEvents = 'auto'; c.style.touchAction = 'none';
      c.addEventListener('pointerdown', (ev) => { ev.stopPropagation(); c.setPointerCapture(ev.pointerId); this.pdrag = { i, before: clone(p) }; });
      c.addEventListener('pointermove', (ev) => { if (!this.pdrag) return; const g = v.info(ev).ground(); if (!g) return; p.points[i] = [rnd(g[0], 10), rnd(g[1], 10)]; c.setAttribute('cx', ev.clientX - v.canvas.getBoundingClientRect().left); c.setAttribute('cy', ev.clientY - v.canvas.getBoundingClientRect().top); this.soon('path', () => { const w = p.width, xs = [...p.points, ...this.pdrag?.before.points || []]; a.ours.terrainMesh.rebakeAll([Math.min(...xs.map((q) => q[0])) - w, Math.min(...xs.map((q) => q[1])) - w, Math.max(...xs.map((q) => q[0])) + w, Math.max(...xs.map((q) => q[1])) + w]); v.redraw(); }); });
      c.addEventListener('pointerup', () => { const d = this.pdrag; this.pdrag = null; if (!d) return; const after = clone(p); Object.assign(p, d.before); a.push({ op: 'path.edit', path: after, before: d.before }, 'exterior'); this.drawPathHandles(); });
    });
    void sk;
  }
  editPath(change) {
    const a = this.app, p = a.model.paths.get(this.path.sel); if (!p) return;
    const before = clone(p), after = { ...clone(p), ...change };
    a.push({ op: 'path.edit', path: after, before }, 'exterior'); this.drawPathHandles();
  }
  erasePath() {
    const a = this.app, p = a.model.paths.get(this.path.sel); if (!p) return;
    a.push({ op: 'path.remove', path: clone(p), before: clone(p) }, 'exterior'); this.path.sel = null; this.clearSketch(a.ours.view);
  }
}
function norm(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }
