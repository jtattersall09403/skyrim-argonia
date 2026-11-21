// The Walking mesh view in our place: the built walking mesh drawn as a translucent surface on the ground, decks,
// bridges and stairs (one merged mesh per space: one draw, plus a faint wire), islands cut off from the main mesh in
// warning with their size, door triangles marked, the checks' findings as pins that say what is wrong in one plain
// line when tapped, the owner's walking zones with their notes, a legend, whether the mesh is older than the place,
// and the rebuild of the walking mesh with its progress. The data is walkmesh.js's.
import * as THREE from 'three';
import { api } from './api.js';
import { meshDraw, islandText, pinsFromCheck, staleness, ZONE_COLOURS } from './walkmesh.js';

const NS = 'http://www.w3.org/2000/svg';
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const POLL_MS = 3000;
const STORE = 'studio.walkmesh.v1';
const store = { get: () => { try { return localStorage.getItem(STORE); } catch { return null; } }, set: (v) => { try { localStorage.setItem(STORE, v); } catch { /* private window */ } } };

export class WalkLayer {
  constructor(app) {
    this.app = app; this.on = store.get() === 'on'; this.nav = null; this.meta = null; this.state = null; this.cache = new Map();
    this.group = new THREE.Group(); this.group.renderOrder = 4; this.zones = new THREE.Group(); this.zones.renderOrder = 6;
    this.mat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.42, depthWrite: false, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -8 });
    this.wire = new THREE.MeshBasicMaterial({ color: '#0d3b39', wireframe: true, transparent: true, opacity: 0.16, depthWrite: false });
    this.popup = null; this.legendOpen = null;   // the key opens by itself in a wide view
  }
  // ---------- data ----------
  setNav(d) {
    this.nav = d?.spaces || null; this.meta = d ? { from: d.from || 'build', built_at: d.built_at || null, notes: d.notes || [] } : null;
    for (const c of this.cache.values()) { c.mesh.geometry.dispose(); }
    this.cache.clear(); this.refresh();
  }
  async loadState() {
    const id = this.app.place?.place_id; if (!id) return;
    try { this.state = await api.walkmesh(id); } catch { this.state = null; }
    if (this.app.place?.place_id !== id) return;
    this.pins = null; this.legend(); this.drawLabels(); this.pollIfRunning();
  }
  pinsNow() {
    if (this.pins) return this.pins;
    const a = this.app;
    const ctx = {
      ref: (id) => { for (const [sid, s] of Object.entries(a.model.spaces)) { const r = s.refs.get(id); if (r) return { ...r, space: sid }; } return null; },
      person: (id) => a.model.people.get(id) || null,
      stop: (st) => (Array.isArray(st) ? st : st?.pos ? st.pos : st?.ref ? (ctx.ref(st.ref)?.pos || null) : null),
    };
    this.pins = pinsFromCheck(this.state?.check, ctx); return this.pins;
  }
  // ---------- the toggle ----------
  setShown(on) {
    this.on = on; store.set(on ? 'on' : 'off');
    document.getElementById('walkmesh-btn')?.setAttribute('aria-pressed', String(on));
    if (on && !this.state) this.loadState();
    this.refresh();
  }
  // ---------- drawing ----------
  focus() {
    const pl = this.app.ground?.meta?.place, o = this.app.ours.origin, r = (this.app.ground?.meta?.radius_m || 120) * 70 + 1500;
    return pl ? { x: pl.world_x, y: pl.world_y, r } : o ? { x: o[0], y: o[1], r } : null;
  }
  drawn(space) {
    if (!this.nav?.[space]) return null;
    let c = this.cache.get(space);
    if (!c) {
      const d = meshDraw(this.nav[space], { focus: space === 'exterior' ? this.focus() : null, lift: 10 });
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(d.positions, 3)); g.setAttribute('color', new THREE.BufferAttribute(d.colours, 3));
      g.computeBoundingSphere();
      const mesh = new THREE.Mesh(g, this.mat), wire = new THREE.Mesh(g, this.wire);
      mesh.renderOrder = 4; wire.renderOrder = 5; mesh.frustumCulled = wire.frustumCulled = false;
      c = { data: d, mesh, wire, lift: 10 }; this.cache.set(space, c);
    }
    return c;
  }
  refresh() {
    const a = this.app, v = a.ours?.view; if (!v || !a.model) return;
    const S = a.ours.space, o = a.ours.origin || [0, 0, 0];
    this.group.clear(); this.zones.clear();
    if (this.group.parent !== v.overlay) v.overlay.add(this.group);
    if (this.zones.parent !== v.overlay) v.overlay.add(this.zones);
    this.group.position.set(-o[0], -o[1], -o[2]); this.zones.position.set(-o[0], -o[1], -o[2]);
    const shown = this.on || a.tools?.current === 'walking';
    this.group.visible = this.zones.visible = shown;
    if (shown) {
      const c = this.drawn(S);
      if (c) { this.group.add(c.mesh); if (v.rig.dist < 9000) this.group.add(c.wire); }
      this.drawZones(S);
    }
    this.legend(); this.drawLabels(); v.redraw();
  }
  zoneHeight(p) {
    const a = this.app; if (a.ours.space !== 'exterior') return p[2] ?? 0;
    return p[2] ?? a.terrain?.heightAt(p[0], p[1]) ?? 0;
  }
  drawZones(S) {
    const a = this.app, sel = a.walkTools?.sel;
    for (const r of a.model.walk.values()) {
      if ((r.space || 'exterior') !== S) continue;
      const col = new THREE.Color(ZONE_COLOURS[r.kind] || '#888'), mine = sel === r.id;
      if (r.kind === 'join') {
        const [p, q] = r.points, g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(p[0], p[1], p[2] + 14), new THREE.Vector3(q[0], q[1], q[2] + 14)]);
        const line = new THREE.Line(g, new THREE.LineBasicMaterial({ color: col, depthTest: false, transparent: true, opacity: mine ? 1 : 0.85 }));
        line.renderOrder = 7; this.zones.add(line);
        continue;
      }
      const pts = r.outline, shape = pts.map((q) => new THREE.Vector2(q[0], q[1]));
      const tri = THREE.ShapeUtils.triangulateShape(shape, []);
      const pos = new Float32Array(pts.length * 3);
      pts.forEach((q, i) => { pos[3 * i] = q[0]; pos[3 * i + 1] = q[1]; pos[3 * i + 2] = this.zoneHeight(q) + 10; });
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(tri.flat());
      const fill = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: mine ? 0.38 : 0.24, depthWrite: false, depthTest: false, side: THREE.DoubleSide }));
      fill.renderOrder = 6; this.zones.add(fill);
      const loop = new THREE.LineLoop(g, new THREE.LineBasicMaterial({ color: col, depthTest: false, transparent: true, opacity: mine ? 1 : 0.9 }));
      loop.renderOrder = 7; this.zones.add(loop);
    }
  }
  // labels: the islands' sizes, door marks, the checks' pins and the zones' notes, on the SVG over the view
  layer() {
    const v = this.app.ours.view; let s = v.el.querySelector('.walk-layer');
    if (!s) { s = document.createElementNS(NS, 'svg'); s.setAttribute('class', 'sketch walk-layer'); v.el.append(s); }
    return s;
  }
  cameraMoved(view) {
    if (view !== this.app.ours.view || this._due) return;
    this._due = true; requestAnimationFrame(() => {
      this._due = false; const c = this.cache.get(this.app.ours.space);
      if (c && this.group.visible) { const want = view.rig.dist < 9000; if (want !== (c.wire.parent === this.group)) { if (want) this.group.add(c.wire); else c.wire.removeFromParent(); view.redraw(); } }
      this.drawLabels();
    });
  }
  drawLabels() {
    const a = this.app, v = a.ours?.view; if (!v) return;
    const svg = this.layer(); svg.innerHTML = '';
    const shown = this.on || a.tools?.current === 'walking'; if (!shown || !v.origin) { this.closePop(); return; }
    const S = a.ours.space, W = v.el.clientWidth, H = v.el.clientHeight;
    const vis = (q) => !q.behind && q.x > -20 && q.y > -20 && q.x < W + 20 && q.y < H + 20;
    const add = (tag, attrs, parent = svg) => { const e = document.createElementNS(NS, tag); for (const [k, val] of Object.entries(attrs)) e.setAttribute(k, val); parent.append(e); return e; };
    const zAt = (p) => p[2] ?? (S === 'exterior' ? a.terrain?.heightAt(p[0], p[1]) : 0) ?? 0;
    const c = this.cache.get(S);
    if (c) {
      for (const isl of c.data.islands.slice(0, 60)) {
        const q = v.toScreen([isl.at[0], isl.at[1], isl.at[2] + 40]); if (!vis(q)) continue;
        const g = add('g', { class: 'wm-island', transform: `translate(${q.x},${q.y})` });
        add('circle', { r: 11 }, g); const t = add('text', { y: 4, 'text-anchor': 'middle' }, g); t.textContent = isl.tris > 99 ? '99+' : String(isl.tris);
        const tt = add('title', {}, g); tt.textContent = islandText(isl);
        g.style.pointerEvents = 'auto'; g.addEventListener('pointerdown', (e) => { e.stopPropagation(); e.preventDefault(); this.openPop(q, [islandText(isl)], 'island'); });
      }
      if (v.rig.dist < 6000) for (const d of c.data.doors) {
        const q = v.toScreen([d.at[0], d.at[1], d.at[2] + 20]); if (!vis(q)) continue;
        add('rect', { class: 'wm-door', x: q.x - 5, y: q.y - 5, width: 10, height: 10, rx: 2 });
      }
    }
    for (const p of this.pinsNow()) {
      if (p.space !== S) continue;
      const q = v.toScreen([p.pos[0], p.pos[1], (p.pos[2] ?? zAt(p.pos)) + 30]); if (!vis(q)) continue;
      const g = add('g', { class: 'wm-pin', transform: `translate(${q.x},${q.y})`, role: 'button', 'aria-label': p.lines[0] });
      add('path', { d: 'M0 0 L-9 -16 A10 10 0 1 1 9 -16 Z' }, g);
      const t = add('text', { y: -17, 'text-anchor': 'middle' }, g); t.textContent = p.raw.length > 1 ? String(p.raw.length) : '!';
      g.style.pointerEvents = 'auto'; g.addEventListener('pointerdown', (e) => { e.stopPropagation(); e.preventDefault(); this.openPop(q, p.lines, 'pin', p.raw.length); });
    }
    for (const r of a.model.walk.values()) {
      if ((r.space || 'exterior') !== S || !r.note) continue;
      const pts = r.kind === 'join' ? r.points : r.outline, m = pts.reduce((s, q) => [s[0] + q[0] / pts.length, s[1] + q[1] / pts.length, s[2] + zAt(q) / pts.length], [0, 0, 0]);
      const q = v.toScreen([m[0], m[1], m[2] + 60]); if (!vis(q)) continue;
      const t = add('text', { class: 'wm-note', x: q.x, y: q.y, 'text-anchor': 'middle' }); t.textContent = r.note.length > 40 ? `${r.note.slice(0, 39)}…` : r.note;
    }
  }
  openPop(q, lines, kind, n = 1) {
    this.closePop();
    const v = this.app.ours.view, el = document.createElement('div');
    el.className = `wm-pop ${kind}`; el.setAttribute('role', 'dialog');
    el.innerHTML = `${n > 1 ? `<p class="wm-count">${n} problems here</p>` : ''}${lines.map((l) => `<p>${esc(l)}</p>`).join('')}<button class="quiet small" aria-label="Close">Close</button>`;
    el.style.left = `${Math.min(Math.max(8, q.x - 140), v.el.clientWidth - 296)}px`; el.style.top = `${Math.max(48, q.y + 10)}px`;
    el.querySelector('button').onclick = () => this.closePop();
    v.el.append(el); this.popup = el;
  }
  closePop() { this.popup?.remove(); this.popup = null; }
  // ---------- legend, staleness and rebuild ----------
  legendEl() {
    const v = this.app.ours.view; let el = v.el.querySelector('.wm-legend');
    if (!el) { el = document.createElement('div'); el.className = 'wm-legend'; el.setAttribute('aria-label', 'Walking mesh: what the colours mean'); v.el.append(el); }
    return el;
  }
  legend() {
    const a = this.app, shown = this.on || a.tools?.current === 'walking', el = this.legendEl();
    el.hidden = !shown; if (!shown) return;
    const S = a.ours?.space, c = S ? this.drawn(S) : null, run = this.state?.run;
    const st = staleness({ builtAt: this.meta?.built_at || this.state?.nav?.built_at, filesAt: this.state?.files_at, ops: a.log?.applied?.() || [], from: this.meta?.from });
    const running = run && (run.state === 'starting' || run.state === 'running');
    const sw = (cls, label) => `<li><i class="sw ${cls}"></i>${label}</li>`;
    const n = c?.data.islands.length || 0;
    const vw = a.ours?.view.el.clientWidth || 0, narrow = vw < 640;
    if (this.legendOpen == null) this.legendOpen = vw >= 760;
    const small = narrow && !this.legendOpen;   // a narrow view keeps the place in sight: the card is a line and a button
    el.classList.toggle('small', small);
    const what = c ? (n ? `${n} cut-off piece${n === 1 ? '' : 's'}` : 'all joined') : 'not built yet';
    el.innerHTML = `
      <button class="wm-legend-head" aria-expanded="${this.legendOpen}" aria-label="Walking mesh: what the colours mean"><strong>Walking mesh</strong><span>${what}${small && st.stale ? ', older than the place' : ''} · ${this.legendOpen ? 'hide key' : 'key'}</span></button>
      <div class="wm-legend-body">
        ${st.words && !small ? `<p class="wm-age ${st.stale ? 'stale' : ''}">${esc(st.words)}</p>` : ''}
        ${(this.meta?.notes || []).length && !small ? `<p class="wm-age stale">${(this.meta.notes).map(esc).join('<br>')}</p>` : ''}
        ${running ? `<div class="wm-run"><span>${esc(run.words || 'Rebuilding')}…</span><b><i style="width:${Math.round(100 * (Math.max(0, (run.steps || []).indexOf(run.step)) + 0.5) / Math.max(1, (run.steps || [1]).length))}%"></i></b></div>`
          : `<button class="wm-rebuild ${st.stale ? 'primary' : 'quiet'}">Rebuild the walking mesh</button>`}
        ${run?.state === 'failed' ? `<p class="wm-age stale">The last rebuild did not finish: ${esc(run.error || 'no reason given')}</p>` : ''}
        ${this.err ? `<p class="wm-age stale">${esc(this.err)}</p>` : ''}
        ${small ? '' : c ? (this.legendOpen ? `<ul>
          ${sw('main', 'Where people can walk')}
          ${sw('island', 'Cut off: people cannot reach it from the rest (the number is its size)')}
          ${sw('door', 'A door: people pass through here')}
          ${sw('pin', 'A problem the checks found: tap it')}
          ${sw('block', 'Your "No walking here"')}
          ${sw('walk', 'Your "Walk here" or "Join these"')}
        </ul>` : '') : `<p>${this.nav ? 'This room has no walking mesh.' : 'This place has not been built yet, so there is no walking mesh to show.'}</p>`}
      </div>`;
    el.querySelector('.wm-legend-head').onclick = () => { this.legendOpen = !this.legendOpen; this.legend(); };
    const rb = el.querySelector('.wm-rebuild'); if (rb) rb.onclick = () => this.rebuild();
  }
  async rebuild() {
    const a = this.app, id = a.place?.place_id; if (!id) return;
    this.err = null;
    clearTimeout(a.autoT); if (a.dirtySave) await a.autosave();   // the rebuild reads the autosave: everything on screen
    const r = await api.rebuildWalk(id, 'autosave');
    if (r.error) { this.err = r.error; this.legend(); return; }
    this.state = { ...(this.state || {}), run: { state: 'starting', step: 'copy', steps: ['copy', 'apply', 'build', 'export'], words: 'Starting' } };
    this.legend(); this.pollIfRunning(true);
  }
  pollIfRunning(force = false) {
    const run = this.state?.run, id = this.app.place?.place_id;
    if (!force && !(run && (run.state === 'starting' || run.state === 'running'))) return;
    clearTimeout(this.pollT);
    this.pollT = setTimeout(async () => {
      let st; try { st = await api.walkmesh(id); } catch { this.pollIfRunning(true); return; }
      if (this.app.place?.place_id !== id) return;
      const was = this.state?.run?.state; this.state = st; this.pins = null;
      if (st.run?.state === 'done' && was !== 'done') {
        const d = await api.nav(id).catch(() => null);
        if (d?.spaces) { this.setNav(d); this.app.people.invalidateRoutes(); this.app.people.setNav(d.spaces); }
        this.app.toast('The walking mesh is rebuilt with your changes.', 5000);
      }
      this.legend(); this.drawLabels();
      if (st.run && (st.run.state === 'starting' || st.run.state === 'running')) this.pollIfRunning(true);
    }, POLL_MS);
  }
  // A walking mesh triangle under the pen's ray, nearest the eye: {point: [x, y, z]} or null (the mesh's own surface:
  // a deck, a stair or the ground where the mesh lies).
  hit(ray) {
    const c = this.cache.get(this.app.ours.space); if (!c || !this.group.visible) return null;
    const rc = this._rc || (this._rc = new THREE.Raycaster()); rc.ray.copy(ray); rc.far = Infinity;
    c.mesh.updateMatrixWorld(true);
    const h = rc.intersectObject(c.mesh, false)[0]; if (!h) return null;
    const o = this.app.ours.origin; return { point: [h.point.x + o[0], h.point.y + o[1], h.point.z + o[2] - c.lift] };
  }
  // The walking mesh's height at (x, y) on the level nearest zHint (within `reach`): a deck over the ground is told
  // from the ground under it. null where no triangle of that level lies.
  heightAt(x, y, zHint, reach = 120) {
    const c = this.cache.get(this.app.ours.space); if (!c) return null;
    const o = this.app.ours.origin, rc = this._rd || (this._rd = new THREE.Raycaster());
    rc.ray.origin.set(x - o[0], y - o[1], zHint + reach + c.lift - o[2]); rc.ray.direction.set(0, 0, -1); rc.far = 2 * reach;
    c.mesh.updateMatrixWorld(true);
    let best = null;
    for (const h of rc.intersectObject(c.mesh, false)) { const z = h.point.z + o[2] - c.lift; if (best == null || Math.abs(z - zHint) < Math.abs(best - zHint)) best = z; }
    return best;
  }
}
