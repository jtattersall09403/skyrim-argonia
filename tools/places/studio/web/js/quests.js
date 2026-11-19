// Quest things: what the quest records put at this place (a caged prisoner, a cage door, a quest's guards), drawn as
// their own layer of gold pins, each with when it is in the world and links into the story explorer at its quest and
// stage. A pin is moved like a placed thing (drag it, or Place and tap the ground, and turn it); the move is an edit
// of the save (quest.add / quest.edit / quest.remove), and finalise writes it to the place's quests.jsonl, the one
// spot the quest builder reads (docs/design/place-studio.md, "Quest things"; tools/places/quest_spots.py).
import * as THREE from 'three';
import { api } from './api.js';
import { loadModel } from './objects.js';
import { figureGeometry } from './people.js';
import { spotRow, moveOp, turned, keptRow, drawAs } from './quest_ops.js';

const NS = 'http://www.w3.org/2000/svg';
const GOLD = '#d4a017', GOLD_SEL = '#ffcf33';
const KIND_COLOUR = { person: '#b45ad6', door: GOLD, thing: GOLD, container: GOLD, marker: '#2aa198' };
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch { /* a private window */ } } };
const TURN = Math.PI / 12;   // 15 degrees a press

export class Quests {
  constructor(app) {
    this.app = app; this.data = null; this.sel = null; this.armed = null; this.drag = null; this.markers = new Map();
    this.shown = store.get('studio.quests.shown') !== 'off';
    const pin = new THREE.ConeGeometry(45, 160, 12).rotateX(-Math.PI / 2).translate(0, 0, 80);   // point down on the spot
    this.geo = { pin, head: new THREE.SphereGeometry(55, 14, 10).translate(0, 0, 195), face: new THREE.BoxGeometry(14, 120, 14).translate(0, 60, 12), figure: figureGeometry() };
  }
  get a() { return this.app; }
  // ---------- data ----------
  async load(pid) {
    this.data = null; this.sel = null; this.armed = null;
    try { this.data = await api.quests(pid); } catch { this.data = null; }
    return this.data;
  }
  items() { return this.data?.items || []; }
  item(id) { return this.items().find((i) => i.id === id) || null; }
  // where the item stands now: the model's row (the committed spot with this session's edits over it)
  spot(it) { return this.a.model?.quests.get(it.id) || null; }
  // ---------- drawing ----------
  setShown(on) { this.shown = on; store.set('studio.quests.shown', on ? 'on' : 'off'); this.refresh(); }
  refresh() {
    const a = this.a, v = a.ours?.view; if (!v || !a.model) return;
    const seen = new Set();
    for (const it of this.items()) {
      const s = this.spot(it); if (!s) continue;
      seen.add(it.id);
      let m = this.markers.get(it.id);
      if (!m) {
        const mat = new THREE.MeshLambertMaterial({ color: KIND_COLOUR[it.kind] || GOLD, emissive: '#3a2a00' });
        m = new THREE.Group(); m.userData.quest = it.id; this.markers.set(it.id, m);
        // a thing with a model is drawn as that model (the way the place's own objects are), the pin only where none resolves
        const how = drawAs(it), pin = new THREE.Group();
        if (how === 'person') pin.add(new THREE.Mesh(this.geo.figure, mat));
        else pin.add(new THREE.Mesh(this.geo.pin, mat), new THREE.Mesh(this.geo.head, mat), new THREE.Mesh(this.geo.face, mat));
        m.add(pin); m.userData.pin = pin; m.userData.draw = how;
        if (how === 'model') {
          loadModel(it.model, 0, 0, 'other').then((parts) => {
            if (!parts?.length || parts.placeholder || this.markers.get(it.id) !== m) return;
            const real = new THREE.Group();
            for (const p of parts) real.add(new THREE.Mesh(p.geometry, p.material));
            m.add(real); m.userData.real = real; this.refresh();
          });
        }
      }
      const drafted = !!s.drafted;
      if (m.parent !== v.overlay) v.overlay.add(m);
      const mine = this.sel === it.id, p = this.drag?.id === it.id ? this.drag.pos : s.pos, h = this.drag?.id === it.id ? this.drag.heading : (s.rot?.[2] || 0);
      m.visible = this.shown && (s.space || 'exterior') === a.ours.space;
      m.position.set(p[0] - a.ours.origin[0], p[1] - a.ours.origin[1], p[2] - a.ours.origin[2]);
      m.rotation.set(0, 0, -h);   // a heading turns clockwise seen from above
      m.scale.setScalar(mine ? 1.3 : 1);
      const col = mine ? GOLD_SEL : (KIND_COLOUR[it.kind] || GOLD);
      m.userData.pin.visible = !m.userData.real;   // the real thing drawn: its name label alone marks it
      for (const c of m.userData.pin.children) { c.material.color.set(col); c.material.wireframe = drafted; c.material.transparent = drafted; c.material.opacity = drafted ? 0.6 : 1; }
      m.userData.real?.traverse((o) => { if (o.isMesh) { o.material.transparent = drafted; o.material.opacity = drafted ? 0.55 : 1; } });
      m.userData.at = p;
    }
    for (const [id, m] of this.markers) if (!seen.has(id)) { m.removeFromParent(); this.markers.delete(id); }
    v.redraw(); this.drawLabels();
  }
  layer(view) {
    let s = view.el.querySelector('.quest-layer');
    if (!s) { s = document.createElementNS(NS, 'svg'); s.setAttribute('class', 'sketch quest-layer'); view.el.append(s); }
    return s;
  }
  cameraMoved(view) { if (view === this.a.ours.view && !this._due) { this._due = true; requestAnimationFrame(() => { this._due = false; this.drawLabels(); }); } }
  drawLabels() {
    const a = this.a, v = a.ours.view, svg = this.layer(v); svg.innerHTML = '';
    if (!this.shown || !v.origin) return;
    for (const it of this.items()) {
      const m = this.markers.get(it.id); if (!m?.visible) continue;
      const q = v.toScreen([m.userData.at[0], m.userData.at[1], m.userData.at[2] + 300]);
      if (q.behind || q.x < 0 || q.y < 0 || q.x > v.el.clientWidth || q.y > v.el.clientHeight) continue;
      const t = document.createElementNS(NS, 'text');
      t.setAttribute('class', `who name quest${this.sel === it.id ? ' sel' : ''}`); t.setAttribute('x', q.x); t.setAttribute('y', q.y); t.setAttribute('text-anchor', 'middle');
      t.textContent = `Quest: ${it.name} (${it.code})${this.spot(it)?.drafted ? ' (drafted)' : ''}`; svg.append(t);
    }
  }
  // ---------- picking, dragging, placing ----------
  pick(e) {
    if (!this.shown) return null;
    let best = null, bd = 40;
    for (const [id, m] of this.markers) {
      if (!m.visible) continue;
      const q = e.view.toScreen([m.userData.at[0], m.userData.at[1], m.userData.at[2] + 120]), d = Math.hypot(q.x - e.x, q.y - e.y);
      if (d < bd) { bd = d; best = id; }
    }
    return best;
  }
  groundPoint(e) {
    const g = e.ground(); if (!g) return null;
    const a = this.a, z = a.ours.space === 'exterior' && a.terrain ? (a.terrain.heightAt(g[0], g[1]) ?? g[2]) : g[2];
    return [g[0], g[1], z];
  }
  get tool() {
    const t = this;
    return this._tool || (this._tool = {
      fingerTap: true,
      wantsDrag: (e) => !!t.pick(e),
      tap: (e) => {
        if (t.armed) { const g = t.groundPoint(e); if (g) t.setSpot(t.armed, g); t.armed = null; t.panel(); return; }
        t.select(t.pick(e));
      },
      down: (e) => { const id = t.pick(e); if (!id) return false; const s = t.spot(t.item(id)); t.sel = id; t.drag = { id, pos: [...s.pos], heading: s.rot?.[2] || 0, moved: false }; return true; },
      move: (e) => { if (!t.drag) return; const g = t.groundPoint(e); if (g) { t.drag.pos = g; t.drag.moved = true; t.refresh(); } },
      up: () => { const d = t.drag; t.drag = null; if (d?.moved) t.setSpot(d.id, d.pos, d.heading); else t.select(d?.id || null); },
      cancel: () => { t.drag = null; t.refresh(); },
    });
  }
  select(id) { this.sel = id || null; this.armed = null; this.refresh(); this.a.panels.open('quests'); }
  setSpot(id, pos, heading) {
    const it = this.item(id); if (!it || it.place_person) return;
    const before = this.spot(it), h = heading ?? before?.rot?.[2] ?? 0;
    const space = this.a.ours.space;
    const op = moveOp(before, spotRow(it, space, pos, h)); if (op) this.a.push(op, space);
    this.sel = id; this.refresh();
  }
  turn(id, by) {
    const it = this.item(id), s = it && this.spot(it); if (!s) return;
    const op = moveOp(s, spotRow(it, s.space, s.pos, turned(s.rot?.[2], by))); if (op) this.a.push(op, s.space);
  }
  keep(id) { const it = this.item(id), s = it && this.spot(it); if (s?.drafted) this.a.push({ op: 'quest.edit', quest: keptRow(s), before: JSON.parse(JSON.stringify(s)) }, s.space); }
  clear(id) { const it = this.item(id), s = it && this.spot(it); if (s) this.a.push(moveOp(s, null), s.space); }
  show(id) {
    const it = this.item(id), s = it && this.spot(it); if (!s) return;
    const a = this.a, side = a.ours;
    if ((s.space || 'exterior') !== side.space) a.showSpace(side, s.space || 'exterior');
    const p = s.pos; side.view.rig.pitch = Math.max(side.view.rig.pitch, 0.7); side.view.frame([p[0] - 900, p[1] - 900, p[0] + 900, p[1] + 900, p[2]]);
    this.sel = id; this.refresh();
  }
  // ---------- the panel ----------
  when(it) {
    const link = (url, words) => (url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(words)}</a>` : esc(words));
    const ap = it.appears || {};
    const rows = [`<li><strong>When:</strong> ${esc(ap.words)} ${ap.url ? link(ap.url, ap.stage != null ? `Open stage ${ap.stage} in the story explorer` : 'Open the quest in the story explorer') : ''}</li>`];
    for (const g of it.gone || []) rows.push(`<li><strong>Leaves:</strong> ${esc(g.words)} ${g.url ? link(g.url, g.stage != null ? `Open stage ${g.stage}` : 'Open the quest') : ''}</li>`);
    return rows.join('');
  }
  card(it) {
    const s = this.spot(it), mine = this.sel === it.id, li = el(`<li class="quest-item${mine ? ' sel' : ''}"></li>`);
    const where = it.place_person ? `This person is the place's own ${esc(it.place_person.name || it.place_person.id)}: move them with the People tool.`
      : s ? `Placed${s.space !== 'exterior' ? ` inside (${esc(this.a.spaceName?.(this.a.ours, s.space) || s.space)})` : ''}, facing ${Math.round(((s.rot?.[2] || 0) * 180) / Math.PI)}°.`
        : 'Not placed yet: press Place, then tap the ground where it should stand.';
    const draft = s?.drafted ? `<p class="q-drafted"><strong>Drafted, not yet checked by you:</strong> ${esc(s.why || 'no reason given')}</p>` : '';
    li.innerHTML = `<div class="q-head"><span class="tag">${esc(it.kind_word || it.kind)}</span> <strong>${esc(it.name)}</strong>${it.hostile ? ' <span class="tag">hostile</span>' : ''}${it.lock ? ` <span class="tag">lock: ${esc(it.lock.level)}</span>` : ''}</div>
      ${it.orphan ? '' : `<p class="q-need"><strong>The story asks for:</strong> ${esc(it.need || '(no words given)')}${it.room ? ` <em>(in ${esc(it.room)})</em>` : ''}</p>`}
      ${draft}<ul class="q-when">${this.when(it)}</ul><p class="q-where">${where}</p><div class="row q-buttons"></div>`;
    const btns = li.querySelector('.q-buttons'), b = (label, fn, cls = '') => { const x = el(`<button class="${cls}">${esc(label)}</button>`); x.onclick = (e) => { e.stopPropagation(); fn(); }; btns.append(x); return x; };
    if (!it.place_person) {
      if (s?.drafted) b('Keep this spot', () => this.keep(it.id), 'primary');
      if (s) b('Show', () => this.show(it.id));
      b(this.armed === it.id ? 'Tap the ground…' : s ? 'Move to a tap' : 'Place', () => { this.armed = it.id; this.sel = it.id; this.a.tools.use('quests'); this.panel(); }, 'primary');
      if (s) { b('Turn left', () => this.turn(it.id, -TURN)); b('Turn right', () => this.turn(it.id, TURN)); b('Clear spot', () => this.clear(it.id), 'quiet'); }
    }
    li.onclick = () => { this.sel = it.id; if (s) this.show(it.id); else this.panel(); };
    return li;
  }
  panel() {
    const P = this.a.panels, parts = [];
    parts.push(el(`<p>Things the quests put at this place. They are not part of the place itself: each belongs to a quest, and is in the world only when that quest says. Quest things in the view are drawn as their real model where one is known (a quest's people as standing figures, otherwise a gold pin). Drag a pin to move it, or press <strong>Place</strong> and tap the ground. A move is saved with your other changes and, when you finalise, becomes the one spot the quest is built with.</p>`));
    const tog = el(`<button class="quiet" aria-pressed="${this.shown}">Quest things in the view: ${this.shown ? 'shown' : 'hidden'}</button>`);
    tog.onclick = () => { this.setShown(!this.shown); this.panel(); }; parts.push(tog);
    if (!this.data) parts.push(el('<p class="tag">The quest things could not be read for this place.</p>'));
    else if (!this.items().length) parts.push(el('<p class="tag">No quest puts anything at this place.</p>'));
    const byQuest = new Map();
    for (const it of this.items()) { const k = it.code || it.quest || '?'; if (!byQuest.has(k)) byQuest.set(k, []); byQuest.get(k).push(it); }
    for (const [code, list] of byQuest) {
      const q = list[0];
      parts.push(el(`<h3>${q.quest_url ? `<a href="${esc(q.quest_url)}" target="_blank" rel="noopener">${esc(code)} ${esc(q.title || '')}</a>` : `${esc(code)} ${esc(q.title || '')}`}</h3>`));
      const ol = el('<ul class="quests"></ul>'); for (const it of list) ol.append(this.card(it)); parts.push(ol);
    }
    if (P.name === 'quests') P.show('Quest things', parts);
  }
}
