// The Walking tools: say what the walking mesh should do, never pull its triangles (the build makes the mesh; these
// rows of walk.jsonl tell it what to change, so an edit holds over every rebuild). "No walking here" and "Walk here"
// are outlines drawn with the pen on the ground, a deck or a stair (Walk here also as a line with a width); "Join
// these" is two taps on the walking mesh. Each is one op (walk.add / walk.edit / walk.remove): undo, redo, History,
// saved like every other change. Change: tap a zone to choose it, drag its handle to move it, give it a note, delete it.
import { mintId } from './ids.js';
import { smoothLine } from './tools.js';
import { segDist } from './geom.js';
import { ZONE_COLOURS } from './walkmesh.js';

const rnd = (v, k = 10) => Math.round(v * k) / k;
const clone = (o) => JSON.parse(JSON.stringify(o));
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const NS = 'http://www.w3.org/2000/svg';
export const WALK_WORDS = { block: 'No walking here', walk: 'Walk here', join: 'Join these' };
const SAMPLE_PX = 18;       // a pen sample is taken every this many pixels

function inPoly(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

// A line with a width as an outline: each side offset by half the width, joined at the ends.
export function lineOutline(pts, width) {
  if (pts.length < 2) return [];
  const h = width / 2, left = [], right = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    left.push([pts[i][0] - dy * h, pts[i][1] + dx * h, pts[i][2]]); right.push([pts[i][0] + dy * h, pts[i][1] - dx * h, pts[i][2]]);
  }
  return [...left, ...right.reverse()];
}

// The surface heights of a stroke's points: each simplified point takes the height of the pen's stroke where it passes
// nearest (the samples as a line, the height along each stretch between two samples).
export function liftOutline(pts2, samples) {
  return pts2.map(([x, y]) => {
    let best = samples[0]?.[2] ?? 0, bd = Infinity;
    for (let i = 0; i < samples.length; i++) {
      const a = samples[i], b = samples[Math.min(i + 1, samples.length - 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
      const t = L2 > 1e-9 ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L2)) : 0;
      const d = (a[0] + t * dx - x) ** 2 + (a[1] + t * dy - y) ** 2;
      if (d < bd) { bd = d; best = a[2] + t * (b[2] - a[2]); }
    }
    return [rnd(x), rnd(y), rnd(best)];
  });
}

export class WalkTools {
  constructor(app) {
    this.app = app; this.mode = 'block'; this.shape = 'outline'; this.width = 256; this.gap = 256; this.sel = null; this.joinA = null;
  }
  get layer() { return this.app.walkLayer; }
  // The surface under the pen: whichever the pen's ray meets first of the walking mesh (a deck, a stair, the ground
  // where the mesh lies) and a placed piece's walkable face (a deck or stair the mesh has missed), else the ground.
  surface(e) {
    const mesh = this.layer.hit(e.ray)?.point, piece = this.pieceHit(e.view, e.ray), o = e.ray.origin, v = e.view.origin;
    const d = (p) => (p ? Math.hypot(p[0] - v[0] - o.x, p[1] - v[1] - o.y, p[2] - v[2] - o.z) : Infinity);
    const best = d(piece) + 8 < d(mesh) ? piece : mesh;
    if (best) return best.map((c) => rnd(c));
    const g = e.ground(); return g ? g.map((c) => rnd(c)) : null;
  }
  // The nearest walkable face (facing up within 53 degrees) of a walkway piece's real mesh along a ray, as the sticks'
  // walk reads a deck under the feet: each model's box is only the first reject.
  pieceHit(view, ray) {
    const T = globalThis.THREE || this._T; if (!T || !view.objects) return null;
    const rc = this._rc || (this._rc = new T.Raycaster()); rc.ray.copy(ray); rc.far = 20000;
    const tmp = this._mesh || (this._mesh = new T.Mesh()), inv = new T.Matrix4(), lr = new T.Ray(), box = new T.Box3(), n = new T.Vector3();
    let best = null;
    for (const layer of view.objects) {
      if (layer.isGrass || !layer.groups || !layer.root.visible) continue;
      for (const grp of layer.groups.values()) {
        if (!grp.fullParts || grp.ghost || grp.fx || grp.bulb || grp.prim || grp.unseen) continue;
        box.min.set(...grp.bmin); box.max.set(grp.bmin[0] + grp.bsize[0], grp.bmin[1] + grp.bsize[1], grp.bmin[2] + grp.bsize[2]);
        for (let i = 0; i < grp.refs.length; i++) {
          if (grp.refs[i].walk == null) continue;   // a walkway piece (deck, bridge, steps): never a roof
          const m = grp.matrices[i]; inv.copy(m).invert(); lr.copy(rc.ray).applyMatrix4(inv); if (!lr.intersectsBox(box)) continue;
          tmp.matrixWorld.copy(m);
          for (const part of grp.fullParts) {
            tmp.geometry = part.geometry; tmp.material = part.material;
            for (const h of rc.intersectObject(tmp, false)) {
              if (!h.face) continue;
              n.copy(h.face.normal).transformDirection(m); if (Math.abs(n.z) < 0.6) continue;
              if (!best || h.distance < best.distance) best = h;
              break;
            }
          }
        }
      }
    }
    return best ? [best.point.x + view.origin[0], best.point.y + view.origin[1], best.point.z + view.origin[2]] : null;
  }
  // Each outline point on the surface under it, at the level the pen was on there (the stroke's height where it
  // passes nearest): the walking mesh's own height at that level, else a placed piece's walkable face at that
  // level, else the stroke's height.
  settle(pts) {
    const a = this.app, v = a.ours.view;
    return pts.map(([x, y, hint]) => {
      let z = this.layer.heightAt(x, y, hint, 64);
      if (z == null && a.sticks?.groundAt) { const g = a.sticks.groundAt(v, x, y, hint - 40); if (g != null && Math.abs(g - hint) <= 64) z = g; }
      if (z == null) z = hint;
      return [x, y, rnd(z)];
    });
  }
  get tool() {
    const t = this, a = this.app;
    return this._tool || (this._tool = {
      wantsDrag: () => t.mode === 'block' || t.mode === 'walk',
      tap: (e) => t.tap(e),
      down: (e) => {
        if (!(t.mode === 'block' || t.mode === 'walk')) return false;
        const s = t.surface(e, null); if (!s) return false;
        t.stroke = { samples: [s], scr: [[e.x, e.y]], el: a.tools.svg(e.view, 'polyline', { class: `stroke wm-stroke ${t.mode}` }) };
        t.stroke.el.style.stroke = ZONE_COLOURS[t.mode];
      },
      move: (e) => {
        const s = t.stroke; if (!s) return;
        const last = s.scr[s.scr.length - 1]; if (Math.hypot(e.x - last[0], e.y - last[1]) < SAMPLE_PX) return;
        const p = t.surface(e, s.samples[s.samples.length - 1][2]); if (!p) return;
        s.samples.push(p); s.scr.push([e.x, e.y]); s.el.setAttribute('points', s.scr.map((q) => q.join(',')).join(' '));
      },
      up: (e) => { if (t.stroke && e) { const p = t.surface(e, t.stroke.samples[t.stroke.samples.length - 1][2]); if (p) t.stroke.samples.push(p); } t.strokeEnd(); },
      cancel: () => { t.stroke?.el.remove(); t.stroke = null; },
    });
  }
  strokeEnd() {
    const s = this.stroke; this.stroke = null; if (!s) return; s.el.remove();
    const a = this.app, line = this.mode === 'walk' && this.shape === 'line';
    const simple = smoothLine(s.samples.map((p) => [p[0], p[1]]), line ? 40 : 30);
    let outline;
    if (line) {
      if (simple.length < 2) { a.toast('Draw a line along where people should walk.'); return; }
      outline = this.settle(lineOutline(liftOutline(simple, s.samples), this.width).map((p) => [rnd(p[0]), rnd(p[1]), p[2]]));
    } else {
      outline = this.settle(liftOutline(simple, s.samples));
      if (outline.length > 2 && Math.hypot(outline[0][0] - outline.at(-1)[0], outline[0][1] - outline.at(-1)[1]) < 1) outline.pop();
    }
    let area = 0; for (let i = 0; i < outline.length; i++) { const p = outline[i], q = outline[(i + 1) % outline.length]; area += p[0] * q[1] - q[0] * p[1]; }
    if (outline.length < 3 || Math.abs(area) / 2 < 64 * 64) { a.toast('Draw round the spot: the outline was too small to hold anyone.'); return; }
    const row = { id: mintId(a.place.place_id), kind: this.mode, space: a.ours.space, outline, by: 'owner' };
    if (line) { row.line = liftOutline(simple, s.samples); row.width = this.width; }
    a.push({ op: 'walk.add', walk: row }); this.sel = row.id; this.after();
  }
  tap(e) {
    const a = this.app;
    if (this.mode === 'join') {
      const hit = this.layer.hit(e.ray);
      if (!hit) { a.toast('Tap the walking mesh: the edge or piece that should connect.'); return; }
      if (!this.joinA) { this.joinA = hit.point.map((v) => rnd(v)); this.after(); return; }
      const row = { id: mintId(a.place.place_id), kind: 'join', space: a.ours.space, points: [this.joinA, hit.point.map((v) => rnd(v))], gap: this.gap, by: 'owner' };
      this.joinA = null; a.push({ op: 'walk.add', walk: row }); this.sel = row.id; this.after(); return;
    }
    // choose a zone (in any mode: a tap is never a stroke)
    const g = e.ground(); const at = this.layer.hit(e.ray)?.point || g; if (!at) return;
    this.sel = this.pick(at)?.id || null;
    if (this.sel && this.mode !== 'edit') this.mode = 'edit';
    this.after();
  }
  pick(at) {
    let best = null, bd = Infinity;
    for (const r of this.app.model.walk.values()) {
      if ((r.space || 'exterior') !== this.app.ours.space) continue;
      if (r.kind === 'join') { const d = segDist(at, r.points[0], r.points[1]); if (d < 120 && d < bd) { bd = d; best = r; } continue; }
      if (inPoly(at, r.outline)) { best = r; bd = 0; }
    }
    return best;
  }
  selected() { return this.sel ? this.app.model.walk.get(this.sel) || null : null; }
  edit(change) {
    const r = this.selected(); if (!r) return;
    const after = { ...clone(r), ...change }; for (const k of Object.keys(after)) if (after[k] === undefined || after[k] === '') delete after[k];
    this.app.push({ op: 'walk.edit', walk: after, before: clone(r) }); this.after();
  }
  remove() {
    const r = this.selected(); if (!r) return;
    this.app.push({ op: 'walk.remove', walk: clone(r), before: clone(r) }); this.sel = null; this.after();
  }
  moveBy(dx, dy) {
    const r = this.selected(); if (!r) return;
    const shift = (pts) => pts.map((p) => [rnd(p[0] + dx), rnd(p[1] + dy), p[2]]);
    this.edit(r.kind === 'join' ? { points: shift(r.points) } : { outline: shift(r.outline), ...(r.line ? { line: shift(r.line) } : {}) });
  }
  after() { this.layer.refresh(); this.handles(); if (this.app.panels.name === 'walking') this.panel(); }
  // the chosen zone's handle: drag it to move the zone
  handles() {
    const a = this.app, v = a.ours.view, T = a.tools; T.clearSketch(v);
    if (T.current !== 'walking') return;
    if (this.joinA) { const q = v.toScreen(this.joinA); T.svg(v, 'circle', { cx: q.x, cy: q.y, r: 10, class: 'wm-joina' }); }
    const r = this.selected(); if (!r || (r.space || 'exterior') !== a.ours.space) return;
    const pts = r.kind === 'join' ? r.points : r.outline, m = pts.reduce((s, p) => [s[0] + p[0] / pts.length, s[1] + p[1] / pts.length, s[2] + p[2] / pts.length], [0, 0, 0]);
    const q = v.toScreen(m), c = T.svg(v, 'circle', { cx: q.x, cy: q.y, r: 20, class: 'brush wm-handle', 'aria-label': 'Drag to move' });
    c.style.pointerEvents = 'auto'; c.style.touchAction = 'none';
    c.addEventListener('pointerdown', (ev) => { ev.stopPropagation(); c.setPointerCapture(ev.pointerId); this.drag = { from: v.info(ev).ground() }; });
    c.addEventListener('pointermove', (ev) => {
      if (!this.drag?.from) return; const rect = v.canvas.getBoundingClientRect();
      c.setAttribute('cx', ev.clientX - rect.left); c.setAttribute('cy', ev.clientY - rect.top);
    });
    c.addEventListener('pointerup', (ev) => {
      const d = this.drag; this.drag = null; if (!d?.from) return;
      const to = v.info(ev).ground(); if (!to) return; const dx = to[0] - d.from[0], dy = to[1] - d.from[1];
      if (Math.hypot(dx, dy) > 4) this.moveBy(dx, dy); else this.handles();
    });
  }
  cameraMoved(view) { if (view === this.app.ours.view && this.app.tools.current === 'walking' && !this.drag) this.handles(); }
  // ---------- the panel ----------
  panel() {
    const a = this.app, P = a.panels, el = (h) => { const t = document.createElement('template'); t.innerHTML = h.trim(); return t.content.firstElementChild; };
    const seg = (name, opts, val, pick) => {
      const w = el(`<div class="seg" role="group" aria-label="${esc(name)}"></div>`);
      for (const [v, label] of opts) { const b = el(`<button aria-pressed="${v === val}">${esc(label)}</button>`); b.onclick = () => pick(v); w.append(b); }
      return w;
    };
    const parts = [];
    parts.push(seg('Walking tool', [['block', 'No walking here'], ['walk', 'Walk here'], ['join', 'Join these'], ['edit', 'Change']], this.mode,
      (v) => { this.mode = v; this.joinA = null; if (v !== 'edit') this.sel = null; this.after(); }));
    const say = {
      block: 'Draw round a spot with the pen where people should not walk: through a house, off a ledge. The next build cuts the walking mesh there.',
      walk: this.shape === 'line' ? 'Draw a line along where people should walk. It gets the width below, on the ground, deck or stair under the pen, and the next build makes walking mesh there joined to what is round it.'
        : 'Draw round a spot where people should be able to walk: a gap at a stair\'s foot, a missing link between two decks. The next build makes walking mesh there on the ground, deck or stair under the pen, joined to what is round it.',
      join: this.joinA ? 'Now tap the other edge or piece it should join.' : 'Tap two edges or pieces of the walking mesh that should connect. The next build bridges them if they are close enough and within a step in height, and says why not if they are not.',
      edit: 'Tap a zone to choose it. Drag its round handle to move it, give it a note, or delete it.',
    }[this.mode];
    parts.push(el(`<p>${esc(say)}</p>`));
    if (this.mode === 'walk') {
      parts.push(seg('Shape', [['outline', 'Outline'], ['line', 'Line']], this.shape, (v) => { this.shape = v; this.panel(); }));
      if (this.shape === 'line') parts.push(seg('Width', [[128, 'Narrow'], [256, 'Medium'], [400, 'Wide']], this.width, (v) => { this.width = v; this.panel(); }));
    }
    if (this.mode === 'join') parts.push(seg('How far apart they may be', [[128, 'Close (2 m)'], [256, 'Near (4 m)'], [512, 'Far (7 m)']], this.gap, (v) => { this.gap = v; this.panel(); }));
    if (!a.walkLayer.nav) parts.push(el('<p class="tag">This place has not been built yet, so there is no walking mesh to see. Zones you draw are used by the first build.</p>'));
    const r = this.selected();
    if (r) {
      parts.push(el(`<h3>${esc(WALK_WORDS[r.kind])}</h3>`));
      if (r.kind === 'join') parts.push(el(`<p>Joins two points ${Math.round(Math.hypot(r.points[1][0] - r.points[0][0], r.points[1][1] - r.points[0][1]) / 70 * 10) / 10} m apart; bridged when no more than ${Math.round((r.gap || 256) / 70)} m apart and within a step in height.</p>`));
      const f = el(`<label class="field">Note for this zone<textarea rows="2" placeholder="The guards should not cut through the hatchery">${esc(r.note || '')}</textarea></label>`);
      const save = el('<button class="quiet">Keep this zone\'s note</button>'); save.onclick = () => this.edit({ note: f.querySelector('textarea').value.trim() || undefined });
      parts.push(f, save);
      const row = el('<div class="row"></div>');
      const nud = (label, dx, dy) => { const b = el(`<button class="quiet">${label}</button>`); b.onclick = () => this.moveBy(dx, dy); return b; };
      row.append(nud('North', 0, 64), nud('South', 0, -64), nud('West', -64, 0), nud('East', 64, 0));
      parts.push(row);
      const del = el('<button class="danger">Delete this zone</button>'); del.onclick = () => this.remove(); parts.push(del);
    }
    parts.push(el('<h3>Walking zones in this place</h3>'));
    const list = el('<ol class="history"></ol>');
    const rows = [...a.model.walk.values()];
    if (!rows.length) list.append(el('<li><span class="what">None yet.</span></li>'));
    for (const z of rows) {
      const where = (z.space || 'exterior') === 'exterior' ? 'outside' : `in ${a.spaceName?.(a.ours, z.space) || z.space}`;
      const li = el(`<li><span class="what"><i class="sw ${z.kind === 'block' ? 'block' : 'walk'}"></i>${esc(WALK_WORDS[z.kind])}, ${esc(where)}${z.note ? `<span class="note">${esc(z.note)}</span>` : ''}</span></li>`);
      const b = el(`<button class="quiet" aria-pressed="${z.id === this.sel}">Choose</button>`);
      b.onclick = () => { this.sel = z.id; this.mode = 'edit'; if ((z.space || 'exterior') === a.ours.space) this.lookAt(z); this.after(); };
      li.append(b); list.append(li);
    }
    parts.push(list);
    P.show('Walking', parts);
  }
  lookAt(z) {
    const v = this.app.ours.view, pts = z.kind === 'join' ? z.points : z.outline;
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    v.frame([Math.min(...xs) - 600, Math.min(...ys) - 600, Math.max(...xs) + 600, Math.max(...ys) + 600, pts[0][2]]);
  }
  key(e) { if ((e.key === 'Delete' || e.key === 'Backspace') && this.sel) { this.remove(); return true; } if (e.key === 'Escape') { this.joinA = null; this.sel = null; this.after(); return true; } return false; }
}
