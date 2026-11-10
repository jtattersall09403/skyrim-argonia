// Place Studio: the owner's editor for one of our places beside the source place it was seeded from.
import * as THREE from 'three';
import { api } from './api.js';
import { loadBundle, seatZ } from './bundle.js';
import { EditLog, modelFromFiles, describe, vegKey } from './edits.js';
import { View } from './view.js';
import { TerrainMesh, LandTex } from './terrain_mesh.js';
import { ObjectLayer } from './objects.js';
import { fitPoint, unfitPoint } from './xform.js';
import { Tools } from './tools.js';
import { People } from './people.js';
import { Panels, plainKind } from './panels.js';
import { segDist, clock } from './geom.js';

const VEG = new Set(['tree', 'plant', 'groundcover']);
const $ = (s) => document.querySelector(s);
const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window */ } } };

class Studio {
  constructor() {
    this.penSeen = false; this.selection = new Set(); this.srcSel = []; this.showCleared = false; this.time = 9;
    this.ours = { view: new View($('#view-ours'), { name: 'Our place', app: this }), space: 'exterior', side: 'ours' };
    this.src = { view: new View($('#view-src'), { name: 'Source place', app: this }), space: 'exterior', side: 'src' };
    this.ours.view.side = this.ours; this.src.view.side = this.src;
    this.tools = new Tools(this); this.people = new People(this); this.panels = new Panels(this);
    this.linked = false; this.dirtySave = false; this.revs = {}; this.loop();
    this.wireChrome();
  }
  // ---------- loading ----------
  async start() {
    this.places = await api.places();
    if (!this.places?.length) { this.loading('No place has a draft yet. Run the draft step for a place first.'); return; }
    const sel = $('#place-pick'); sel.innerHTML = '';
    for (const p of this.places) sel.add(new Option(p.title || p.place_id, p.place_id));
    const want = new URLSearchParams(location.search).get('place') || this.places[0].place_id;
    sel.value = want; sel.onchange = () => this.openPlace(sel.value);
    this.heartbeat(); this.statusCheck();
    await this.openPlace(want);
    if (!store.get('studio.intro.v1')) this.panels.intro();
  }
  loading(text) { const l = $('#loading'); if (text === false) { l.hidden = true; return; } l.hidden = false; $('#loading-text').textContent = text; }
  async openPlace(id) {
    const t0 = performance.now();
    this.place = this.places.find((p) => p.place_id === id); this.placeFit = normaliseFit(this.place.fit);
    this.loading(`Loading ${this.place.title || id}: the ground`);
    this.landTex = this.landTex || await new LandTex().init();
    const [ground, draft] = await Promise.all([loadBundle(`ground.${id}`), loadBundle(`draft.${id}`, { extras: true, optional: true })]);
    this.ground = ground; this.draft = draft || emptyDraft(id);
    if (!draft) this.toast('This place has no draft yet: you see our ground with nothing placed on it.', 6000);
    this.bases = new Map([...ground.bases, ...this.draft.bases]); this.npcs = new Map([...ground.npcs, ...this.draft.npcs]);
    this.terrain = ground.spaces.exterior?.terrain;
    const spaces = {}; for (const [sid, s] of Object.entries(this.draft.spaces)) spaces[sid] = s.refs;
    this.model = modelFromFiles({ spaces, ...this.draft.files });
    this.spaceInfo = Object.fromEntries(Object.entries(this.draft.spaces).map(([k, v]) => [k, v.info]));
    if (this.terrain) this.terrain.override = this.model.land;
    this.log = new EditLog(this.model);
    this.log.on((kind, ops) => this.afterEdit(kind, ops));
    this.worldRefs = (ground.spaces.exterior?.refs || []).filter((r) => r.layer !== 'place');
    const origin = ground.meta.anchor ? ground.meta.anchor.map(Math.round) : [0, 0, 0];
    this.ours.origin = origin;
    this.ours.world = new ObjectLayer(origin, this.bases); this.ours.place = new ObjectLayer(origin, this.bases);
    this.loading('Drawing the land');
    this.ours.terrainMesh = this.terrain ? await new TerrainMesh(this.terrain, origin, { paths: () => [...this.model.paths.values()], landTex: this.landTex }).build() : null;
    if (this.ours.terrainMesh) this.ours.terrainMesh.onChange = () => this.ours.view.redraw();
    // sources: the allocated one first, then the similar places
    const srcSel = $('#source-pick'); srcSel.innerHTML = '';
    this.sourceIds = [this.place.source_id, ...(this.place.similar || [])];
    this.sourceIds.forEach((s, i) => srcSel.add(new Option(i === 0 ? `${s} (allocated)` : `${s} (similar)`, s)));
    srcSel.onchange = () => this.openSource(srcSel.value);
    await this.openSource(this.place.source_id);
    this.showSpace(this.ours, 'exterior', true);
    this.loadMs = Math.round(performance.now() - t0);
    this.loading(false);
    await this.panels.resumeAutosave();
    this.tools.use('select');
  }
  async openSource(sid) {
    this.loading(`Loading the source place ${sid}`);
    const bid = `src.${sid}`;
    this.srcBundle = await loadBundle(bid);
    this.fit = sid === this.place.source_id && this.placeFit ? this.placeFit : this.fitFromAnchors();
    this.srcBases = this.srcBundle.bases; this.sourceId = sid;
    const s = this.src, terr = this.srcBundle.spaces.exterior?.terrain;
    s.origin = this.srcBundle.meta.anchor ? this.srcBundle.meta.anchor.map(Math.round) : [0, 0, 0];
    s.terrain = terr; s.layer = new ObjectLayer(s.origin, this.srcBases);
    s.terrainMesh = terr ? await new TerrainMesh(terr, s.origin, { landTex: this.landTex }).build() : null;
    if (s.terrainMesh) s.terrainMesh.onChange = () => s.view.redraw();
    this.pathStyles = this.derivePathStyles();
    this.ours.terrainMesh?.setPathStyles(this.pathStyles); this.ours.terrainMesh?.update(this.ours.view.rig.target); s.terrainMesh?.update(s.view.rig.target);
    this.srcSel = []; this.showSpace(s, 'exterior', true); this.loading(false);
  }
  // The path looks the source place uses: its land textures named like roads, paths, streets or mud.
  derivePathStyles() {
    const out = {}, re = /(path|road|street|cobble|dirt|mud|track|gravel|plank|trail)/i;
    for (const terr of [this.srcBundle.spaces.exterior?.terrain, this.terrain]) {
      if (!terr) continue;
      const used = new Set(); for (const c of terr.list) for (const q of c.quadrants) { used.add(q.base); for (const l of q.layers) used.add(l.tex); }
      for (const key of used) {
        const lt = terr.ltex[key] || {}, words = `${lt.edid || ''} ${lt.diffuse || key || ''}`;
        if (key && re.test(words) && !out[key]) out[key] = { tex: key, label: plainTexName(lt.edid || lt.diffuse || key) };
      }
      Object.assign(this.ltexAll || (this.ltexAll = {}), terr.ltex);
    }
    if (!Object.keys(out).length) out.path = { tex: null, colour: '#7a6446', label: 'Dirt path' };
    for (const p of this.model.paths.values()) if (!out[p.style]) out[p.style] = { tex: this.terrain?.ltex[p.style] ? p.style : null, colour: '#7a6446', label: plainTexName(this.terrain?.ltex[p.style]?.edid || p.style) };
    return out;
  }
  // Without a fit in place.json, the source's anchor lands on ours.
  fitFromAnchors() {
    const a = this.srcBundle.meta.anchor || [0, 0, 0], b = this.ground.meta.anchor || [0, 0, 0];
    return { dx: b[0] - a[0], dy: b[1] - a[1], dz: 0, rot: 0, scale: 1 };
  }
  // ---------- spaces: outside or a room ----------
  showSpace(side, sid, first) {
    side.space = sid; const v = side.view;
    if (side === this.ours) { this.selection.clear(); this.tools.selectionChanged(); }
    const interior = sid !== 'exterior';
    v.terrainData = interior ? null : (side === this.ours ? this.terrain : side.terrain);
    const layers = side === this.ours ? [this.ours.world, this.ours.place] : [side.layer];
    v.setContent({ origin: side.origin, terrain: interior ? null : side.terrainMesh, objects: layers, interior });
    v.overlay.clear();
    this.refreshSide(side);
    const refs = this.refsOf(side);
    if (interior) {
      const bx = boxOf(refs); v.floorZ = bx[5]; bx[4] = bx[5];
      v.rig.pitch = 1.0; v.frame(bx);
    } else if (first || side.returnRig) {
      if (side.returnRig) { Object.assign(v.rig, side.returnRig); v.rig.target = side.returnRig.target.clone(); side.returnRig = null; v.changed(); }
      else {
        const pr = refs.filter((r) => r.layer !== 'world'), core = pr.filter((r) => ['building', 'door', 'furniture', 'container'].includes(r.kind));
        if (pr.length) v.frame(boxOf(core.length ? core : pr, 0.1));
        else if (side === this.ours) {
          const pl = this.ground.meta.place, c = pl ? [pl.world_x, pl.world_y] : side.origin;
          v.frame([c[0] - 6000, c[1] - 6000, c[0] + 6000, c[1] + 6000, this.terrain?.heightAt(c[0], c[1]) ?? 0]);
        } else if (v.terrainData) { const b = v.terrainData.bounds(); v.frame([...b, 0]); }
      }
    }
    if (!interior) side.terrainMesh?.update(v.rig.target);
    this.crumbs(side); this.people.refresh();
  }
  enter(side, door) {
    const to = door.door?.to_space; if (!to) return;
    const has = side === this.ours ? this.model.spaces[to] : this.srcBundle.spaces[to];
    if (!has) { this.toast('That door leads to a room this place does not have.'); return; }
    if (side.space === 'exterior') side.returnRig = { ...side.view.rig, target: side.view.rig.target.clone() };
    side.trail = [...(side.trail || []), { space: side.space, door }];
    this.showSpace(side, to);
  }
  leave(side, idx = 0) {
    const t = side.trail || []; const back = t[idx]; if (!back) return;
    side.trail = t.slice(0, idx); this.showSpace(side, back.space);
  }
  crumbs(side) {
    const nav = side.view.el.querySelector('.crumbs'); nav.innerHTML = '';
    if (side.space === 'exterior') return;
    (side.trail || []).forEach((t, i) => {
      const b = document.createElement('button'); b.textContent = i === 0 ? '← Outside' : this.spaceName(side, t.space);
      b.onclick = () => this.leave(side, i); nav.append(b);
    });
    const here = document.createElement('span'); here.className = 'view-title'; here.textContent = this.spaceName(side, side.space); nav.append(here);
  }
  spaceName(side, sid) {
    if (sid === 'exterior') return 'Outside';
    const info = side === this.ours ? this.spaceInfo[sid] : this.srcBundle.spaces[sid]?.info;
    return info?.name || sid.replace(/([a-z])([A-Z0-9])/g, '$1 $2');
  }
  // ---------- what each view draws ----------
  refsOf(side) {
    if (side === this.ours) {
      const placed = [...(this.model.spaces[side.space]?.refs.values() || [])];
      return side.space === 'exterior' ? [...this.worldRefs, ...placed] : placed;
    }
    return this.srcBundle.spaces[side.space]?.refs || [];
  }
  placeRefsById() { return this.model.spaces[this.ours.space]?.refs || new Map(); }
  // A placed ref as drawn: seated on the land as it is now.
  seated(ref) {
    if (this.ours.space !== 'exterior' || !ref.seat) return ref;
    const z = seatZ(this.terrain, ref, this.placeRefsById());
    return z === ref.pos[2] ? ref : { ...ref, pos: [ref.pos[0], ref.pos[1], z] };
  }
  isCleared(r) { return this.model.clear.has(vegKey(r)); }
  underPath(r) {
    for (const p of this.model.paths.values()) {
      const w = p.width / 2 + 40;
      for (let i = 1; i < p.points.length; i++) if (segDist(r.pos, p.points[i - 1], p.points[i]) < w) return true;
    }
    return false;
  }
  refreshSide(side, { world = true } = {}) {
    if (side === this.ours) {
      if (side.space === 'exterior' && world) {
        const list = [];
        for (const r of this.worldRefs) {
          const veg = VEG.has(r.kind) || r.kind === 'rock' || r.kind === 'clutter';
          const off = veg && (this.isCleared(r) || (VEG.has(r.kind) && this.underPath(r)));
          if (!off) list.push({ ref: r }); else if (this.showCleared) list.push({ ref: r, ghost: true });
        }
        side.world.setRefs(list);
      } else if (side.space !== 'exterior') side.world.setRefs([]);
      side.place.setRefs([...(this.model.spaces[side.space]?.refs.values() || [])].map((r) => ({ ref: this.seated(r) })));
      this.tools.drawSelection();
    } else side.layer.setRefs(this.refsOf(side).map((r) => ({ ref: r })));
    side.view.redraw();
  }
  // ---------- edits ----------
  push(ops, space) { return this.log.push(ops, space ?? this.ours.space); }
  afterEdit(kind, ops) {
    const touched = new Set(ops.map((o) => o.op.split('.')[0]));
    if (touched.has('land')) { this.ours.terrainMesh?.refreshCells(new Set(ops.filter((o) => o.op === 'land.patch').map((o) => o.cell.join(',')))); this.ours.terrainMesh?.tint?.(); }
    if (touched.has('path')) this.ours.terrainMesh?.rebakeAll();
    if (touched.has('veg') || touched.has('path')) this.refreshSide(this.ours);
    else this.refreshSide(this.ours, { world: false });
    if (touched.has('person') || touched.has('ref')) this.people.refresh();
    if (kind !== 'call') this.markUnsaved();
    this.panels.historyChanged(); this.updateUndo();
    if (kind === 'push') this.panels.chip(ops);
    if (kind === 'call') this.markUnsaved();
    // the selection may point at things that undo took away
    for (const id of [...this.selection]) if (!this.placeRefsById().has(id)) this.selection.delete(id);
    this.tools.selectionChanged();
  }
  updateUndo() { $('#undo').disabled = !this.log?.canUndo(); $('#redo').disabled = !this.log?.canRedo(); }
  nameOf(keyOrId) {
    const r = this.placeRefsById().get(keyOrId) || this.findRef(keyOrId);
    const key = r ? r.base : keyOrId, b = this.bases.get(key) || this.srcBases?.get(key);
    return b ? friendly(b, r?.kind) : (keyOrId || 'something');
  }
  findRef(id) { for (const s of Object.values(this.model.spaces)) if (s.refs.has(id)) return s.refs.get(id); return null; }
  describe(op) { return describe(op, (k) => this.nameOf(k)); }
  // ---------- saves ----------
  markUnsaved() {
    this.dirtySave = true; this.saveState('unsaved');
    clearTimeout(this.autoT); this.autoT = setTimeout(() => this.autosave(), 1500);
  }
  saveState(s) {
    const el = $('#save-state'); el.dataset.state = s;
    el.textContent = { saved: 'All changes saved', unsaved: 'Unsaved changes', saving: 'Saving…', failed: 'Not saved: the studio server did not answer. Retrying.',
      conflict: 'Not saved: this place was saved from another tab. Reload to carry on from there.' }[s];
  }
  saveBody(save_id, name, final = false) {
    return { save_id, place_id: this.place.place_id, name, at: new Date().toISOString(), final, rev: this.revs[save_id] || 0,
      base: { draft_key: this.place.stamps?.draft_key || this.draft.meta.stamp?.key || null, ground_sha: this.place.stamps?.ground_sha || this.status?.ground_sha || null },
      ops: this.log.applied() };
  }
  async autosave() {
    this.saveState('saving');
    try {
      const r = await this.putSave('autosave', 'Autosave');
      if (r.conflict) { this.saveState('conflict'); return; }
      this.dirtySave = false; this.saveState('saved');
    }
    catch { this.saveState('failed'); clearTimeout(this.autoT); this.autoT = setTimeout(() => this.autosave(), 5000); }
  }
  // Write a save at the rev this tab last read; the server answers 409 when another tab moved it on.
  async putSave(sid, name, final = false) {
    const r = await api.putSave(this.place.place_id, sid, this.saveBody(sid, name, final));
    if (!r.conflict) this.revs[sid] = r.rev;
    return r;
  }
  async loadSave(save) {
    if (save.save_id) this.revs[save.save_id] = save.rev || 0;
    // back to the draft, then the save's ops in order
    const spaces = {}; for (const [sid, s] of Object.entries(this.draft.spaces)) spaces[sid] = s.refs;
    const m = modelFromFiles({ spaces, ...this.draft.files });
    Object.assign(this.model, m); if (this.terrain) this.terrain.override = this.model.land;
    this.log.model = this.model; const err = this.log.load(save.ops || []);
    if (err) { console.error(err); this.toast(`Opened ${this.log.ops.length} of ${save.ops.length} changes. The next one no longer fits the draft: ${err.message}`, 8000); }
    this.ours.terrainMesh?.refreshCells(this.ours.terrainMesh.cells.keys()); this.ours.terrainMesh?.rebakeAll(); this.ours.terrainMesh?.tint?.();
    this.ours.trail = []; this.showSpace(this.ours, 'exterior');
    this.refreshSide(this.ours); this.panels.historyChanged(); this.updateUndo();
  }
  // ---------- chrome ----------
  wireChrome() {
    $('#undo').onclick = () => this.log?.undo(); $('#redo').onclick = () => this.log?.redo();
    $('#finalise-btn').onclick = () => this.panels.finalise();
    $('#link').onclick = (e) => { this.linked = !this.linked; e.currentTarget.setAttribute('aria-pressed', this.linked); if (this.linked) this.cameraMoved(this.ours.view); };
    $('#swap').onclick = () => { const v = $('#views'); v.dataset.swapped = v.dataset.swapped === 'true' ? 'false' : 'true'; };
    document.querySelectorAll('.view .fs').forEach((b) => { b.onclick = () => { const v = b.closest('.view'); v.classList.toggle('full'); b.setAttribute('aria-pressed', v.classList.contains('full')); }; });
    $('#time').oninput = (e) => this.setTime(Number(e.target.value));
    const orient = () => { $('#views').dataset.layout = innerHeight > innerWidth ? 'stack' : 'side'; };
    addEventListener('resize', orient); orient();
    addEventListener('keydown', (e) => {
      if (e.target.matches('input, textarea, select')) return;
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); e.shiftKey ? this.log.redo() : this.log.undo(); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') { e.preventDefault(); this.log.redo(); }
      this.tools.key?.(e);
    });
    // no page zoom, pull to refresh, double-tap zoom or long-press menus
    for (const ev of ['gesturestart', 'gesturechange', 'dblclick']) document.addEventListener(ev, (e) => e.preventDefault(), { passive: false });
    document.addEventListener('touchmove', (e) => { if (!e.target.closest('#panel-body')) e.preventDefault(); }, { passive: false });
    document.addEventListener('contextmenu', (e) => { if (!e.target.closest('input, textarea')) e.preventDefault(); });
    const mq = matchMedia('(prefers-color-scheme: dark)');
    const theme = () => { const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark' : mq.matches; this.ours.view.setTheme(dark); this.src.view.setTheme(dark); };
    mq.addEventListener('change', theme); theme(); this.applyTheme = theme;
    addEventListener('beforeunload', (e) => { if (this.dirtySave) { this.autosave(); e.preventDefault(); } });
  }
  setTime(t) { this.time = t; $('#time').value = t; $('#time-out').textContent = clock(t); this.people.refresh(); }
  heartbeat() {
    const beat = () => { if (document.visibilityState === 'visible') api.heartbeat(); };
    beat(); this.hbT = setInterval(beat, 60000);
    document.addEventListener('visibilitychange', beat);
  }
  async statusCheck() {
    try { this.status = await api.status(); } catch { return; }
    const s = this.status, fp = $('#fingerprint'), short = (x) => (x || 'unknown').slice(0, 10);
    fp.textContent = `World build ${short(s.ground_sha)}`; fp.dataset.ok = String(!!s.match);
    fp.title = `This view is built from world file ${s.ground_sha}. The play machine has ${s.deployed_sha}.`;
    const w = $('#warn');
    if (!s.match) { w.hidden = false; w.textContent = `The world shown here (build ${short(s.ground_sha)}) is not the one on the play machine (build ${short(s.deployed_sha)}). Heights, water and plants may differ from the game until the two match.`; }
    else w.hidden = true;
  }
  toolFor(view) { return this.tools.forView(view); }
  focusView(view) { this.focused = view; }
  cameraMoved(view) {
    const side = view === this.ours.view ? this.ours : this.src;
    if (side.space === 'exterior') side.terrainMesh?.update(view.rig.target);
    this.tools.cameraMoved(view); this.people.cameraMoved(view);
    if (!this.linked || this.ours.space !== 'exterior' || this.src.space !== 'exterior') return;
    const [a, b] = view === this.ours.view ? [this.ours, this.src] : [this.src, this.ours];
    const ga = [a.view.rig.target.x + a.origin[0], a.view.rig.target.y + a.origin[1], a.view.rig.target.z + a.origin[2]];
    const toOurs = a === this.src, k = this.fit.scale || 1;
    const gb = toOurs ? fitPoint(this.fit, ga) : unfitPoint(this.fit, ga);
    const rb = b.view.rig;
    rb.target.set(gb[0] - b.origin[0], gb[1] - b.origin[1], gb[2] - b.origin[2]);
    rb.yaw = a.view.rig.yaw + (toOurs ? 1 : -1) * (this.fit.rot || 0);
    rb.pitch = a.view.rig.pitch; rb.dist = a.view.rig.dist * (toOurs ? k : 1 / k);
    b.view.changed(true); if (b.space === 'exterior') b.terrainMesh?.update(rb.target); this.tools.cameraMoved(b.view); this.people.cameraMoved(b.view);
  }
  toast(text, ms = 3500) { const t = $('#toast'); t.textContent = text; t.hidden = false; clearTimeout(this.toastT); this.toastT = setTimeout(() => { t.hidden = true; }, ms); }
  loop() {
    const tick = (now) => {
      const a = this.ours.view.render(now), b = this.src.view.render(now);
      if (a || b) this.frames = (this.frames || 0) + 1;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  stats() {
    return { ours: this.ours.view.frameStats(), src: this.src.view.frameStats(), loadMs: this.loadMs,
      drawn: { world: this.ours.world?.drawn, place: this.ours.place?.drawn, src: this.src.layer?.drawn },
      refs: { world: this.worldRefs?.length, place: this.model?.spaces.exterior?.refs.size, src: this.srcBundle?.spaces.exterior?.refs.length } };
  }
}

// [x0, y0, x1, y1, mean z, min z] of some refs.
// With trim, the outer tenth each side is left out, so a few far-flung refs do not set the frame.
function boxOf(refs, trim = 0) {
  if (!refs.length) return [-1000, -1000, 1000, 1000, 0, 0];
  const q = (k) => { const a = refs.map((r) => r.pos[k]).sort((x, y) => x - y), i = Math.floor(trim * (a.length - 1)); return [a[i], a[a.length - 1 - i]]; };
  const [x0, x1] = q(0), [y0, y1] = q(1), zs = refs.map((r) => r.pos[2]);
  return [x0, y0, x1, y1, zs.reduce((s, v) => s + v, 0) / zs.length, Math.min(...zs)];
}
// place.json's fit: one transform, or per cluster (the first is the place's main frame).
function normaliseFit(f) {
  if (!f) return null;
  if (f.pivot && (f.anchor || f.to)) { // the draft's global fit: turn clockwise by rot_deg about pivot, pivot lands on anchor
    const rot = -((f.rot_deg ?? 0) * Math.PI) / 180, c = Math.cos(rot), s = Math.sin(rot), to = f.anchor || f.to;
    return { dx: to[0] - (c * f.pivot[0] - s * f.pivot[1]), dy: to[1] - (s * f.pivot[0] + c * f.pivot[1]), dz: f.dz || 0, rot, scale: 1 };
  }
  const c = Array.isArray(f.clusters) ? f.clusters[0] : Array.isArray(f) ? f[0] : f;
  return c && 'dx' in c ? { dx: c.dx || 0, dy: c.dy || 0, dz: c.dz || 0, rot: c.rot || 0, scale: c.scale || 1 } : null;
}
function emptyDraft(id) {
  return { id: `draft.${id}`, meta: { spaces: ['exterior'], stamp: null }, bases: new Map(), npcs: new Map(),
    spaces: { exterior: { id: 'exterior', info: { space_id: 'exterior', type: 'exterior' }, refs: [] } }, files: {} };
}
function plainTexName(s) {
  const w = String(s).split('/').pop().replace(/\.\w+$/, '').replace(/^\d+/, '').replace(/([a-z])([A-Z0-9])/g, '$1 $2').replace(/[_-]+/g, ' ').trim();
  return w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : 'Path';
}
export function friendly(base, kind) {
  const n = base?.name || base?.edid || base?.key || 'something';
  return n.length > 40 ? n.slice(0, 38) + '…' : n || plainKind(kind);
}
const studio = new Studio();
window.studio = studio; window.THREE = THREE;
studio.start().catch((e) => { console.error(e); studio.loading(`The studio could not load: ${e.message}. Reload the page to try again.`); });
