// Place Studio: the owner's editor for one of our places beside the source place it was seeded from.
import * as THREE from 'three';
import { api, API_BASE } from './api.js';
import { loadBundle, seatZ } from './bundle.js';
import { EditLog, modelFromFiles, describe, vegKey } from './edits.js';
import { View } from './view.js';
import { TerrainMesh, LandTex } from './terrain_mesh.js';
import { ObjectLayer } from './objects.js';
import { GrassLayer } from './grass.js';
import { fitPoint, unfitPoint } from './xform.js';
import { Tools } from './tools.js';
import { People } from './people.js';
import { Panels, plainKind } from './panels.js';
import { segDist, clock } from './geom.js';
import { Governor } from './governor.js';

const VEG = new Set(['tree', 'plant', 'groundcover']);
// The page tells the server what it is doing and what went wrong (out/places/studio-client.log), so a fault on the
// tablet can be read from the build machine.
const T0 = performance.now();
export function report(stage, extra = {}) {
  try {
    const body = JSON.stringify({ stage, t: Math.round(performance.now() - T0), ...extra });
    if (!navigator.sendBeacon?.(`${API_BASE}/clientlog`, body)) fetch(`${API_BASE}/clientlog`, { method: 'POST', body, credentials: 'same-origin', keepalive: true }).catch(() => {});
  } catch { /* never in the way */ }
}
addEventListener('error', (e) => report('error', { message: String(e.message || e.error || e).slice(0, 500), at: `${(e.filename || '').split('/').pop()}:${e.lineno || 0}` }));
addEventListener('unhandledrejection', (e) => report('rejection', { message: String(e.reason?.stack || e.reason).slice(0, 700) }));
const $ = (s) => document.querySelector(s);
const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window */ } } };

class Studio {
  constructor() {
    this._seat = new WeakMap(); this._vk = new WeakMap(); this.penSeen = false; this.selection = new Set(); this.srcSel = []; this.showCleared = false; this.time = 9;
    this.ours = { view: new View($('#view-ours'), { name: 'Our place', app: this }), space: 'exterior', side: 'ours' };
    this.src = { view: new View($('#view-src'), { name: 'Source place', app: this }), space: 'exterior', side: 'src' };
    this.ours.view.side = this.ours; this.src.view.side = this.src;
    this.tools = new Tools(this); this.people = new People(this); this.panels = new Panels(this);
    this.linked = false; this.dirtySave = false; this.revs = {}; this.loop();
    this.wireChrome();
  }
  // ---------- loading ----------
  async start() {
    window.__studioBooted = true;
    report('boot', { gl: glInfo(), w: innerWidth, h: innerHeight, dpr: devicePixelRatio, mem: navigator.deviceMemory });
    this.places = await api.places();
    if (!this.places?.length) { this.loading('No place has a draft yet. Run the draft step for a place first.'); return; }
    const sel = $('#place-pick'); sel.innerHTML = '';
    for (const p of this.places) sel.add(new Option(p.title || p.place_id, p.place_id));
    const want = new URLSearchParams(location.search).get('place') || this.places[0].place_id;
    sel.value = want; sel.onchange = () => this.openPlaceSafe(sel.value);
    this.heartbeat(); this.statusCheck();
    // the guide shows while the place loads, and can be put away at once
    if (!store.get('studio.intro.v1')) this.panels.intro();
    await this.openPlaceSafe(want);
  }
  // Opening a place never hangs: a failed or malformed fetch shows a plain message and a Retry button; a place whose
  // draft changed under the tab (its key moved while loading) is read again once, from the places list.
  async openPlaceSafe(id, again = true) {
    try { await this.openPlace(id, again); }
    catch (e) {
      if (e?.draftMoved && again) {
        try { this.places = await api.places(); } catch { /* the retry below reports it */ }
        return this.openPlaceSafe(id, false);
      }
      console.error(e); report('load-failed', { message: String(e?.stack || e).slice(0, 700) });
      this.loadFailed(e?.message || String(e), () => this.openPlaceSafe(id));
    }
  }
  loadFailed(message, retry) {
    const l = $('#loading'); l.hidden = false;
    $('#loading-text').textContent = `The place could not be loaded (${message}). Nothing has been lost.`;
    l.querySelector('.spinner')?.setAttribute('hidden', '');
    let b = l.querySelector('button.retry');
    if (!b) { b = document.createElement('button'); b.className = 'retry primary'; b.textContent = 'Retry'; l.append(b); }
    b.hidden = false; b.onclick = () => { b.hidden = true; l.querySelector('.spinner')?.removeAttribute('hidden'); retry(); };
  }
  // A calm line under the views while the rest of the place streams in; gone when it is all there.
  progress(what, n, of) {
    const el = $('#progress'); if (!el) return;
    el.hidden = n >= of; el.querySelector('span').textContent = `${what}: ${Math.round((100 * n) / of)}%`;
    el.querySelector('i').style.width = `${(100 * n) / of}%`;
  }
  loading(text) {
    report('loading', { text: text === false ? 'done' : text });
    // a step that takes far longer than it should offers a way out instead of a spinner for ever
    clearTimeout(this.slowT);
    if (text !== false) this.slowT = setTimeout(() => { report('slow', { text }); this.loadFailed(`"${text}" is taking far longer than it should`, () => location.reload()); }, 120000);
    const l = $('#loading'); l.querySelector('button.retry')?.setAttribute('hidden', ''); l.querySelector('.spinner')?.removeAttribute('hidden');
    if (text === false) { l.hidden = true; return; } l.hidden = false; $('#loading-text').textContent = text;
  }
  async openPlace(id, checkKey = true) {
    this.place = this.places.find((p) => p.place_id === id); this.placeFit = normaliseFit(this.place.fit);
    this.loading(`Loading ${this.place.title || id}: the ground`);
    this.landTex = this.landTex || await new LandTex().init();
    const [ground, draft] = await Promise.all([loadBundle(`ground.${id}`), loadBundle(`draft.${id}`, { extras: true, optional: true, terrain: false })]);
    const moved = draft?.meta?.stamp?.key && this.place.stamps?.draft?.key && draft.meta.stamp.key !== this.place.stamps.draft.key;
    if (moved && checkKey) throw Object.assign(new Error('the draft changed while loading'), { draftMoved: true });
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
    this.worldRefs = (ground.spaces.exterior?.refs || []).filter((r) => r.layer !== 'place'); this._wbk = null;
    const origin = ground.meta.anchor ? ground.meta.anchor.map(Math.round) : [0, 0, 0];
    this.ours.origin = origin;
    this.ours.world = new ObjectLayer(origin, this.bases); this.ours.place = new ObjectLayer(origin, this.bases);
    this.ours.grass = this.makeGrass(this.ours, origin, () => this.terrain, () => [...this.worldRefs, ...(this.model.spaces.exterior?.refs.values() || [])]);
    this.ours.grass.view = this.ours.view;
    this.loading('Drawing the land');
    const focus = focusOf([...(this.model.spaces.exterior?.refs.values() || [])], origin, this.ground.meta.place);
    this.ours.terrainMesh = this.terrain ? await new TerrainMesh(this.terrain, origin, { paths: () => [...this.model.paths.values()], landTex: this.landTex })
      .build({ focus, onProgress: (n, of) => this.progress('Drawing the land', n, of) }) : null;
    if (this.ours.terrainMesh) this.ours.terrainMesh.onChange = () => this.ours.view.redraw();
    // sources: the allocated one first, then the similar places
    const srcSel = $('#source-pick'); srcSel.innerHTML = '';
    this.sourceIds = [this.place.source_id, ...(this.place.similar || [])];
    this.sourceIds.forEach((s, i) => srcSel.add(new Option(i === 0 ? `${s} (allocated)` : `${s} (similar)`, s)));
    srcSel.onchange = () => this.openSource(srcSel.value);
    await this.openSource(this.place.source_id);
    this.showSpace(this.ours, 'exterior', true);
    // link every shader the scene uses now, behind the loading screen, so no link stalls a later touch
    this.loading('Preparing the views');
    for (const v of [this.ours.view, this.src.view]) {
      v.updateCamera(); for (const o of v.objects || []) o.cull(v.camera);
      // hidden meshes (stand-ins, empty instances) are shown for the link: compile skips what is not visible
      const hid = []; v.scene.traverse((o) => { if (!o.visible) { hid.push(o); o.visible = true; } });
      try { await v.renderer.compileAsync(v.scene, v.camera); } catch { v.renderer.compile(v.scene, v.camera); }
      for (const o of hid) o.visible = false;
      v.draw(); await new Promise((r) => requestAnimationFrame(r));
    }
    this.ready = true; this.loading(false);
    this.choosing = this.panels.startChoice().finally(() => { this.choosing = null; });
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
    s.grass = this.makeGrass(s, s.origin, () => s.terrain, () => this.srcBundle.spaces.exterior?.refs || []); s.grass.view = s.view;
    s.terrainMesh = terr ? await new TerrainMesh(terr, s.origin, { landTex: this.landTex })
      .build({ focus: focusOf(this.srcBundle.spaces.exterior?.refs || [], s.origin) }) : null;
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
    for (const p of this.model.paths.values()) {
      if (out[p.style]) continue;
      const word = STYLE_WORD[p.style];
      out[p.style] = { tex: this.terrain?.ltex[p.style] ? p.style : null, colour: word?.colour || '#7a6446', label: word?.label || plainTexName(this.terrain?.ltex[p.style]?.edid || p.style) };
    }
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
    if (!interior && side.grass) layers.push(side.grass);
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
        const pr = refs.filter((r) => r.layer !== 'world');
        // the whole town in each view, at a pitch that reads as a place; taps fly closer
        if (pr.length) {
          const b = townBox(pr, side === this.ours ? this.ground.meta.radius_m : 0), z = side.terrain?.heightAt?.((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) ?? (side === this.ours ? this.terrain?.heightAt((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) : null) ?? boxOf(pr)[4];
          v.rig.pitch = 0.9; v.frame([...b.slice(0, 4), z]);
        }
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
  // The answer is kept with the pose, seat rule and nearby land it came from, so a redraw only re-seats what moved
  // or stands on land that changed (a thing seated on another thing is always worked out afresh).
  seated(ref) {
    if (this.ours.space !== 'exterior' || !ref.seat) return ref;
    const s = ref.seat, t = this.terrain, on = s.mode === 'on';
    let c = on ? null : this._seat.get(ref);
    const ver = t && !on ? t.verNear(ref.pos[0], ref.pos[1]) : 0;
    if (c && c.x === ref.pos[0] && c.y === ref.pos[1] && c.z === ref.pos[2] && c.rz === (ref.rot?.[2] || 0) && c.seat === s && c.dz === s.dz && c.ver === ver) return c.out;
    const z = seatZ(t, ref, this.placeRefsById());
    const out = z === ref.pos[2] ? ref : { ...ref, pos: [ref.pos[0], ref.pos[1], z] };
    if (!on) this._seat.set(ref, { x: ref.pos[0], y: ref.pos[1], z: ref.pos[2], rz: ref.rot?.[2] || 0, seat: s, dz: s.dz, ver, out });
    return out;
  }
  vegKeyOf(r) { let k = this._vk.get(r); if (!k) this._vk.set(r, (k = vegKey(r))); return k; }
  worldByKey(k) {
    if (!this._wbk) { this._wbk = new Map(); for (const r of this.worldRefs) if (VEG.has(r.kind) || r.kind === 'rock' || r.kind === 'clutter') this._wbk.set(this.vegKeyOf(r), r); }
    return this._wbk.get(k);
  }
  isCleared(r) { return this.model.clear.has(this.vegKeyOf(r)); }
  underPath(r) {
    for (const p of this.model.paths.values()) {
      const w = p.width / 2 + 40, bb = pathBox(p);
      if (r.pos[0] < bb[0] - w || r.pos[0] > bb[2] + w || r.pos[1] < bb[1] - w || r.pos[1] > bb[3] + w) continue;
      for (let i = 1; i < p.points.length; i++) if (segDist(r.pos, p.points[i - 1], p.points[i]) < w) return true;
    }
    return false;
  }
  // Grass for one view: footprints are the buildings' bounds, paths the ones the owner drew (ours).
  makeGrass(side, origin, terrain, refs) {
    const g = new GrassLayer(origin, {
      terrain, blocked: (x, y) => side === this.ours && this.underPath({ pos: [x, y] }),
      buildings: () => refs().filter((r) => r.kind === 'building').map((r) => {
        const b = (this.bases.get(r.base) || this.srcBases?.get(r.base))?.bounds;
        const s = b ? Math.hypot(b[1][0] - b[0][0], b[1][1] - b[0][1]) / 2 : 200;
        return { pos: r.pos, r: s * (r.scale ?? 1) * 0.8 };
      }),
    });
    g.on = this.grassOn(); return g;
  }
  grassOn() { return store.get('studio.grass.v1') !== 'off'; }
  setGrass(on) {
    store.set('studio.grass.v1', on ? 'on' : 'off');
    for (const s of [this.ours, this.src]) s.grass?.setOn(on);
  }
  // world: the world's plants too (after clearing, restoring or a path); grass: regrow it (not during a drag's preview)
  refreshSide(side, { world = true, grass = true } = {}) {
    if (grass) side.grass?.invalidate();
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
    if (touched.has('land') || touched.has('path')) { this.ours.grass?.invalidate(); }
    if (touched.has('land')) { const keys = new Set(ops.filter((o) => o.op === 'land.patch').map((o) => o.cell.join(','))); this.ours.terrainMesh?.refreshCells(keys); this.ours.terrainMesh?.tintCells(keys); }
    if (touched.has('path')) this.ours.terrainMesh?.rebakeAll(pathsBox(ops));
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
      base: { draft_key: this.place.stamps?.draft?.key || this.draft.meta.stamp?.key || null, ground_sha: this.place.stamps?.ground_sha || this.status?.ground_sha || null },
      ops: this.log.applied() };
  }
  // After a finalise has recorded the edits they are part of the place: the unsaved copy of them is emptied, so the
  // next visit starts on the finalised place and is not offered the same edits again.
  async dropAutosave() {
    clearTimeout(this.autoT); this.finalised = true;
    try { const r = await api.putSave(this.place.place_id, 'autosave', { ...this.saveBody('autosave', 'Autosave'), ops: [] }); if (!r.conflict) this.revs.autosave = r.rev; this.dirtySave = false; }
    catch { /* the start sheet's Discard does the same */ }
  }
  async autosave() {
    if (this.finalised) return;
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
    this.terrain?.bump(null); this.ours.terrainMesh?.refreshCells(this.ours.terrainMesh.cells.keys()); this.ours.terrainMesh?.rebakeAll(); this.ours.terrainMesh?.tint?.();
    this.ours.trail = []; this.showSpace(this.ours, 'exterior');
    this.refreshSide(this.ours); this.panels.historyChanged(); this.updateUndo();
  }
  // ---------- chrome ----------
  wireChrome() {
    $('#undo').onclick = () => this.log?.undo(); $('#redo').onclick = () => this.log?.redo();
    $('#finalise-btn').onclick = () => this.panels.finalise();
    $('#settings-btn').onclick = () => this.panels.settings();
    $('#link').onclick = (e) => { this.linked = !this.linked; e.currentTarget.setAttribute('aria-pressed', this.linked); if (this.linked) this.cameraMoved(this.ours.view); };
    // the source place can be put away to make room, and asked back; remembered on this device
    const srcShown = (on) => {
      $('#views').dataset.src = on ? 'shown' : 'hidden'; $('#show-src').hidden = on; store.set('studio.src.v1', on ? 'shown' : 'hidden');
      $('#view-src').classList.remove('full'); if (!on && this.focused === this.src.view) this.focused = this.ours.view;
      for (const v of [this.ours.view, this.src.view]) { v.resize(); v.redraw(); }
    };
    $('#hide-src').onclick = () => srcShown(false); $('#show-src').onclick = () => srcShown(true);
    if (store.get('studio.src.v1') === 'hidden') srcShown(false);
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
    this.governor = new Governor([this.ours.view, this.src.view], { onChange: () => this.panels?.detailShown?.() });
    let n = 0;
    const tick = (now) => {
      // the view in use draws every frame it changes; the other, while the first moves, every srcEvery-th frame
      const main = this.focused === this.src.view ? this.src.view : this.ours.view, other = main === this.ours.view ? this.src.view : this.ours.view;
      const t0 = performance.now(), a = main.render(now);
      const b = (!a || ++n % this.governor.srcEvery() === 0) ? other.render(now) : false;
      this.governor.frame(now, a || b, performance.now() - t0);
      if (a || b) this.frames = (this.frames || 0) + 1;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  stats() {
    return { detail: this.governor.state(), drawn: { world: this.ours.world?.drawn, place: this.ours.place?.drawn, src: this.src.layer?.drawn },
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
// The town's extent [x0, y0, x1, y1]: the buildings and doors (all the place's refs when it has none), the outer
// 3% each side left out, never wider than the place's radius (metres, 70 units each) either side of its middle.
function townBox(refs, radiusM) {
  const core = refs.filter((r) => ['building', 'door'].includes(r.kind)), use = core.length >= 3 ? core : refs;
  let [x0, y0, x1, y1] = boxOf(use, 0.03);
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, cap = radiusM ? radiusM * 70 : Infinity;
  const hx = Math.min((x1 - x0) / 2, cap), hy = Math.min((y1 - y0) / 2, cap);
  const pad = 300; // the buildings' own size, past their middles
  return [cx - hx * 1.15 - pad, cy - hy * 1.15 - pad, cx + hx * 1.15 + pad, cy + hy * 1.15 + pad];
}
// The draft's style words for paths (paths.jsonl `style` when it is not a land texture key).
const STYLE_WORD = { boardwalk: { colour: '#8b6b47', label: 'Wooden boards' }, dirt: { colour: '#7a6446', label: 'Dirt' },
  mud: { colour: '#5f4d38', label: 'Mud' }, gravel: { colour: '#8d8678', label: 'Gravel' }, stone: { colour: '#80796d', label: 'Stone' } };
// The ground a set of path ops touches (each path as it was and as it is), for redrawing only those cells.
function pathsBox(ops) {
  const b = [Infinity, Infinity, -Infinity, -Infinity];
  for (const o of ops) for (const p of [o.path, o.before]) {
    if (!p?.points) continue; const w = (p.width || 256) * 0.7;
    for (const [x, y] of p.points) { b[0] = Math.min(b[0], x - w); b[1] = Math.min(b[1], y - w); b[2] = Math.max(b[2], x + w); b[3] = Math.max(b[3], y + w); }
  }
  return b[0] === Infinity ? null : b;
}
const PATH_BOX = new WeakMap();
const pathBox = (p) => { let b = PATH_BOX.get(p); if (!b) PATH_BOX.set(p, (b = boxOfPoints(p.points))); return b; };
function boxOfPoints(pts) {
  const b = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [x, y] of pts) { b[0] = Math.min(b[0], x); b[1] = Math.min(b[1], y); b[2] = Math.max(b[2], x); b[3] = Math.max(b[3], y); }
  return b;
}
// Where the land is drawn first: the middle (median) of the place's own buildings and doors, in view coordinates.
function focusOf(refs, origin, pl) {
  const core = refs.filter((r) => r.layer !== 'world' && ['building', 'door', 'furniture'].includes(r.kind));
  const use = core.length ? core : refs.filter((r) => r.layer !== 'world');
  if (!use.length) return pl ? [pl.world_x - origin[0], pl.world_y - origin[1]] : [0, 0];
  const med = (a) => a.sort((x, y) => x - y)[a.length >> 1];
  return [med(use.map((r) => r.pos[0])) - origin[0], med(use.map((r) => r.pos[1])) - origin[1]];
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
function glInfo() {
  try {
    const r = studio.ours.view.renderer, gl = r.getContext(), dbg = gl.getExtension('WEBGL_debug_renderer_info');
    return { gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), webgl2: r.capabilities.isWebGL2, maxTex: r.capabilities.maxTextureSize,
      parallel: !!r.extensions.has('KHR_parallel_shader_compile') };
  } catch (e) { return { error: String(e) }; }
}
function emptyDraft(id) {
  return { id: `draft.${id}`, meta: { spaces: ['exterior'], stamp: null }, bases: new Map(), npcs: new Map(),
    spaces: { exterior: { id: 'exterior', info: { space_id: 'exterior', type: 'exterior' }, refs: [] } }, files: {} };
}
function plainTexName(s) {
  // land texture keys read like 'LDirt02Duplicate002': drop the L prefix, copy markers and numbers
  const w = String(s).split('/').pop().replace(/\.\w+$/, '').replace(/^L(?=[A-Z])/, '').replace(/^L(?=(dirt|grass|mud|gravel|road|stone|sand|moss|swamp|marsh|rock|forest|field))/, '').replace(/_?duplicate\d*/ig, '').replace(/\d+/g, ' ').replace(/([a-z])([A-Z0-9])/g, '$1 $2').replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim();
  return w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : 'Path';
}
export function friendly(base, kind) {
  const n = base?.name || base?.edid || base?.key || 'something';
  return n.length > 40 ? n.slice(0, 38) + '…' : n || plainKind(kind);
}
const studio = new Studio();
window.studio = studio; window.THREE = THREE;
const boot = () => studio.start().catch((e) => { console.error(e); studio.loadFailed(e.message, boot); });
boot();
