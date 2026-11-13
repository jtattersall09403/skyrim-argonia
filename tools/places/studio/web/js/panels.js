// The sliding panel and the small overlays: what is selected, search, people, land, plants, paths, history,
// saves and finalise, notes for the agent and the first-run guide. Plain English throughout.
import { api } from './api.js';
import { ICON } from './icons.js';
import { thumb } from './thumbs.js';
import { STOP_KINDS, isInnkeeper, patrolOf, setPatrol } from './people.js';
import { clock, parseClock } from './geom.js';
import { whereOf, whereRows } from './where.js';
import { Contents } from './contents.js';
import { identityOf } from './stock.js';
import { groupsOf, touched } from './note_groups.js';
import { FIXTURE_REACH, fixtureOf, lightFacts, lightsOf } from './lights.js';
import { comesWith, hasPrim, halfExtents, primFacts, resized, wallsOf } from './prims.js';

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const KIND_WORD = { building: 'Building', static: 'Fixed piece', clutter: 'Small object', tree: 'Tree', plant: 'Plant', groundcover: 'Ground cover',
  rock: 'Rock', furniture: 'Furniture', door: 'Door', container: 'Chest or container', light: 'Light', activator: 'Thing to use', marker: 'Marker',
  actor: 'Person', water: 'Water', other: 'Other' };
export const plainKind = (k) => KIND_WORD[k] || 'Thing';
const SEAT_WORD = { ground: 'Sits on the ground', above: 'Stands above the ground', water: 'Sits in the water', on: 'Sits on another thing',
  stilts: 'Stands on posts over land or water', clear: 'Raised clear of the ground', free: 'Placed by hand at a fixed height' };
export const PATH_KIND = { path: 'Path', street: 'Street', walkway: 'Walkway' };
// Why the draft cleared a plant (clear.jsonl `why`), in plain words.
const CLEAR_WHY = { building: 'under or beside a building', door: 'in front of a door', street: 'on a street or path', path: 'on a street or path',
  walkway: 'under a walkway', station: 'at a crafting station' };
// Lengths in metres for the owner (the game's unit is 1/70 of a metre).
const metres = (u) => `${(u / 70).toFixed(Math.abs(u) < 700 ? 1 : 0)} m`;
function seatWords(s) {
  if (!s) return 'Placed at a fixed height';
  const base = SEAT_WORD[s.mode] || s.mode, dz = Math.round(s.dz || 0);
  return dz && s.mode !== 'free' ? `${base}, ${metres(Math.abs(dz))} ${dz > 0 ? 'higher' : 'lower'}` : base;
}
// The crafting station a ref is, from place.json `stations.found` and `added`.
function stationOf(place, id) {
  const st = place?.stations; if (!st) return null;
  for (const [name, ids] of Object.entries(st.found || {})) if ((ids || []).includes(id)) return stationName(name);
  for (const x of st.added || []) if (x.id === id) return `${stationName(x.station)}, added by the draft`;
  return null;
}
const stationName = (k) => k.replace(/-/g, ' ').replace(/^./, (c) => c.toUpperCase());
function seg(name, options, value, onPick) {
  const w = document.createElement('div'); w.className = 'seg'; w.setAttribute('role', 'group'); w.setAttribute('aria-label', name);
  for (const [v, label] of options) {
    const b = document.createElement('button'); b.textContent = label; b.setAttribute('aria-pressed', String(v === value));
    b.onclick = () => { w.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', 'false')); b.setAttribute('aria-pressed', 'true'); onPick(v); };
    w.append(b);
  }
  return w;
}
function el(html) { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; }
function toggle(label, on, fn) {
  const b = el(`<button class="quiet" aria-pressed="${on}">${esc(label)}: ${on ? 'on' : 'off'}</button>`);
  b.onclick = () => { on = !on; b.setAttribute('aria-pressed', on); b.textContent = `${label}: ${on ? 'on' : 'off'}`; fn(on); }; return b;
}
function slider(label, min, max, step, value, fmt, fn) {
  const w = el(`<label class="field">${esc(label)} <strong></strong><input type="range" min="${min}" max="${max}" step="${step}" value="${value}"></label>`);
  const out = w.querySelector('strong'), inp = w.querySelector('input'); out.textContent = fmt(value);
  inp.oninput = () => { out.textContent = fmt(Number(inp.value)); fn(Number(inp.value)); }; return w;
}

export class Panels {
  constructor(app) {
    this.app = app; this.name = null; this.search = { q: '', scope: 'source', kind: '', results: [] }; this.contents = new Contents(this);
    $('#panel-close').onclick = () => this.close();
  }
  get T() { return this.app.tools; }
  show(title, body) {
    $('#panel').hidden = false; $('#panel-title').textContent = title;
    const b = $('#panel-body'); b.innerHTML = ''; b.append(...[].concat(body).filter(Boolean));
    this.app.ours.view.resize(); this.app.src.view.resize();
  }
  close() { $('#panel').hidden = true; this.name = null; this.app.ours.view.resize(); this.app.src.view.resize(); }
  open(name) {
    this.name = name;
    const f = { select: () => this.selectPanel(), search: () => this.searchPanel(), people: () => this.peoplePanel(), land: () => this.landPanel(),
      plants: () => this.plantsPanel(), paths: () => this.pathsPanel(), history: () => this.historyPanel(), saves: () => this.savesPanel(), notes: () => this.notesPanel(), needs: () => this.app.needs.panel() }[name];
    if (f) f();
  }
  // ---------- selection ----------
  selectionInfo(refs, note) {
    if (this.name === 'source' && this.app.tools.placing) return; // keep the source card while adding
    if (this.name === 'select' || this.name === 'source' || (!this.name && refs.length && this.app.tools.current === 'select')) { this.name = 'select'; this.selectPanel(refs, note); }
  }
  selectPanel(refs = this.T.selRefs(), note = '') {
    const a = this.app, T = this.T, parts = [];
    if (!refs.length) {
      parts.push(el(`<p>Tap a thing in our place to select it. Draw round several with the pen to select them all. Tap the same spot again to reach what is behind.</p>`));
      parts.push(el('<p>To copy from the source place, tap a thing on the source side, then tap our place where it should go.</p>'));
    } else if (refs.length === 1) parts.push(this.refCard(refs[0], a.bases, 'ours'));
    else {
      const counts = {}; for (const r of refs) counts[plainKind(r.kind)] = (counts[plainKind(r.kind)] || 0) + 1;
      parts.push(el(`<p><strong>${refs.length} things selected</strong>: ${Object.entries(counts).map(([k, n]) => `${n} × ${esc(k.toLowerCase())}`).join(', ')}.</p>`));
      parts.push(this.whereEl(refs, 'ours'));
    }
    if (note) parts.push(el(`<p class="tag">${esc(note)}</p>`));
    if (refs.length) {
      parts.push(el('<h3>Move a little</h3>'));
      const step = 32, turn = Math.PI / 12, pad = el('<div class="row"></div>');
      const btn = (label, fn) => { const b = el(`<button class="quiet">${label}</button>`); b.onclick = fn; return b; };
      pad.append(btn('North', () => T.nudge(0, step, 0)), btn('South', () => T.nudge(0, -step, 0)), btn('West', () => T.nudge(-step, 0, 0)), btn('East', () => T.nudge(step, 0, 0)),
        btn('Up', () => T.nudge(0, 0, 8)), btn('Down', () => T.nudge(0, 0, -8)), btn('Turn left', () => T.nudge(0, 0, 0, -turn)), btn('Turn right', () => T.nudge(0, 0, 0, turn)),
        btn('Bigger', () => T.nudge(0, 0, 0, 0, 0.05)), btn('Smaller', () => T.nudge(0, 0, 0, 0, -0.05)));
      parts.push(pad);
      const acts = el('<div class="row"></div>');
      acts.append(btn('Sit on the ground', () => T.snapToGround()), btn('Duplicate', () => T.duplicate()));
      const rm = el('<button class="danger">Remove from our place</button>'); rm.onclick = () => T.remove(); acts.append(rm);
      parts.push(acts);
      const nb = el(`<button class="quiet">Leave a note about ${refs.length === 1 ? 'this' : 'these'} for the agent</button>`);
      nb.onclick = () => { this.name = 'notes'; T.markRail('notes'); this.notesPanel(true); };
      parts.push(nb);
    }
    parts.push(el('<h3>How selecting works</h3>'));
    const r = el('<div class="row"></div>');
    r.append(seg('Pen selects with', [['lasso', 'Draw round'], ['box', 'Box']], T.opts.selMode, (v) => { T.opts.selMode = v; }),
      toggle('Tap adds to selection', T.opts.adds, (v) => { T.opts.adds = v; }));
    const r2 = el('<div class="row"></div>');
    r2.append(toggle('Keep on the ground when moving', T.opts.snapGround, (v) => { T.opts.snapGround = v; }), toggle('Turn in 15° steps', T.opts.snapRot, (v) => { T.opts.snapRot = v; }));
    const r3 = el('<div class="row"></div>');
    r3.append(toggle('Lights and invisible walls: always show them', !!T.opts.lights, (v) => { T.opts.lights = v; T.lightsShown(); }));
    parts.push(r, r2, r3);
    this.show(refs.length ? 'Selected' : 'Select', parts);
  }
  refCard(r, bases, side) {
    const a = this.app, base = bases.get(r.base) || a.srcBases?.get(r.base) || {};
    const kind = r.kind || base.kind, w = el('<div></div>');
    const head = el(`<div class="card-head"><img class="thumb" alt="" width="88" height="88"><p><strong>${esc(base.name || base.edid || 'Unnamed')}</strong><br>${esc(plainKind(kind))}</p></div>`);
    head.querySelector('img').src = thumb({ ...base, key: base.key || r.base, kind });
    w.append(head);
    const tags = el('<p></p>');
    if (base.nordic) tags.append(el('<span class="tag nordic">Nordic piece: not for Black Marsh</span>'));
    const enter = r.door?.to_space ? r : null;
    const building = kind === 'building' && side === 'src' ? this.T.doorsOf(r, a.refsOf(a.src)) : [];
    if (enter || building.length) tags.append(el(`<span class="tag enter">${building.length ? `Can be entered: comes with its room inside and ${building.length} door${building.length > 1 ? 's' : ''}` : 'Door into a room'}</span>`));
    if (tags.children.length) w.append(tags);
    const facts = [['Made from', `${base.edid || ''} (${r.base})`]];
    if (side === 'ours') facts.push(['Copied from', r.src ? `${a.sourceId} thing ${r.src}` : 'Added here, not copied']);
    if (side === 'ours') facts.push(['How it sits', seatWords(r.seat)]);
    const station = side === 'ours' && stationOf(a.place, r.id);
    if (station) facts.push(['Crafting station', station]);
    if (side === 'ours' && r.why) facts.push(['Why the draft added it', r.why]);
    if (side === 'ours' && r.align) facts.push(['Lined up with', `the original it replaces (${r.align.of}), turned ${Math.round(r.align.turn_deg)} degrees`]);
    if (side === 'ours' && r.door?.arrival) facts.push(['Coming out', 'you arrive outside this door, on our ground and clear of anything in the way']);
    if (r.owner) facts.push(['Belongs to', r.owner]);
    if (r.door?.to_space) facts.push(['Door leads to', side === 'ours' ? a.spaceName(a.ours, r.door.to_space) : a.spaceName(a.src, r.door.to_space)]);
    const lit = this.lightFacts(r, base, side);
    facts.push(...lit.facts);
    if (hasPrim(r)) {
      const on = r.seat?.on && (side === 'ours' ? a.placeRefsById().get(r.seat.on) : null);
      const ob = on && (a.bases.get(on.base) || {});
      facts.push(...primFacts(r, base, ob ? ob.name || ob.edid || on.base : null));
    }
    if (side === 'ours') { const nl = a.needs?.refLine(r); if (nl) w.append(nl); }
    w.append(this.whereEl([r], side));
    if (lit.swatch) w.append(lit.swatch);
    w.append(el(`<dl class="facts">${facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`));
    if (side === 'ours' && hasPrim(r)) w.append(this.primSize(r));
    const held = side === 'ours' && this.contents.refSection(r, base);
    if (held) w.append(held);
    if (r.door?.to_space) {
      const b = el('<button class="primary">Go inside</button>');
      b.onclick = () => a.enter(side === 'ours' ? a.ours : a.src, r); w.append(b);
    }
    return w;
  }
  // A primitive's size, changed by its full extents in game units (a sphere by its radius), as one ordinary edit.
  primSize(r) {
    const round = /^Sphere$/i.test(r.primitive.type || ''), h = halfExtents(r);
    const names = round ? ['Radius'] : ['Long', 'Wide', 'High'], vals = round ? [h[0]] : h.map((v) => 2 * v);
    const f = el(`<form class="row prim-size" aria-label="Size of the invisible ${round ? 'sphere' : 'box'}">${names.map((n, i) =>
      `<label>${n} <input type="number" min="2" step="1" data-i="${i}" value="${Math.round(vals[i])}" aria-label="${n}, units"></label>`).join('')}
      <button type="submit" class="quiet">Set the size</button></form>`);
    f.onsubmit = (e) => {
      e.preventDefault();
      const size = [...f.querySelectorAll('input')].map((i) => Number(i.value));
      if (size.some((v) => !(v > 0))) return;
      const before = { primitive: JSON.parse(JSON.stringify(r.primitive)) }, after = { primitive: resized(r.primitive, size) };
      if (JSON.stringify(before) !== JSON.stringify(after)) this.app.push([{ op: 'ref.move', id: r.id, before, after }]);
    };
    return f;
  }
  // A light's radius, colour, shadows and the fixture it belongs to; a fixture's lights.
  lightFacts(r, base, side) {
    const a = this.app, facts = [];
    const refs = side === 'ours' ? [...a.placeRefsById().values()] : a.refsOf(a.src);
    const baseOf = (x) => a.bases.get(x.base) || a.srcBases?.get(x.base), pos = (x) => (side === 'ours' ? a.seated(x).pos : x.pos);
    const name = (x) => { const b = baseOf(x) || {}; return b.name || b.edid || x.base; };
    let swatch = null;
    if ((r.kind || base.kind) === 'light') {
      const f = lightFacts(r, base);
      facts.push(['Light', `reaches ${Math.round(f.radius)} units (${(f.radius / 70).toFixed(1)} m)`]);
      if (f.colour) facts.push(['Colour', `red ${f.colour[0]}, green ${f.colour[1]}, blue ${f.colour[2]}`]);
      facts.push(['Shadows', f.shadow ? 'casts shadows' : 'casts no shadows']);
      const fx = fixtureOf(r, refs, baseOf, pos);
      facts.push(['Belongs to', fx ? `${name(fx)}, ${Math.round(Math.hypot(...pos(fx).map((v, i) => v - pos(r)[i])))} units away: moves and goes with it`
        : `no lantern, sconce, candle, torch, fire or window within ${FIXTURE_REACH} units: it stands alone`]);
      if (f.hex) swatch = el(`<p class="light-swatch"><span class="swatch" style="background:${f.hex}"></span> the light's colour</p>`);
    } else if (side === 'ours') {
      const others = refs.filter((x) => x.id !== r.id && !x.removed);
      const said = comesWith(wallsOf([r], others).length, lightsOf([r], others, baseOf, pos).length);
      if (said) facts.push(['Comes with it', said]);
    }
    return { facts, swatch };
  }
  // Where the selection stands in the game (position, cell outside, turn): drawn as a fact list and kept current
  // by refreshWhere as the things move.
  whereHtml(refs, side) {
    const a = this.app, s = side === 'ours' ? a.ours : a.src, exterior = (s?.space || 'exterior') === 'exterior';
    const shown = side === 'ours' ? refs.map((r) => a.seated(r)) : refs;
    return whereRows(whereOf(shown, { exterior })).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('');
  }
  whereEl(refs, side) { const d = el(`<dl class="facts where" data-side="${side}">${this.whereHtml(refs, side)}</dl>`); return d; }
  refreshWhere() {
    const d = document.querySelector('#panel-body dl.where[data-side="ours"]'); if (!d || this.name !== 'select') return;
    const refs = this.T.selRefs(); if (refs.length) d.innerHTML = this.whereHtml(refs, 'ours');
  }
  sourceInfo(refs) {
    const a = this.app;
    if (!refs.length) { if (this.name === 'source') this.open(a.tools.current || 'select'); return; }
    this.name = 'source';
    const parts = [];
    if (refs.length === 1) parts.push(this.refCard(refs[0], a.srcBases, 'src'));
    else parts.push(el(`<p><strong>${refs.length} things chosen in the source place.</strong> They will keep their arrangement.</p>`));
    parts.push(el('<p>Now tap our place where it should go. Each tap adds another. People are added with the People tool.</p>'));
    const stop = el('<button class="quiet">Stop adding</button>'); stop.onclick = () => { a.tools.stopPlacing(); this.open(a.tools.current); };
    parts.push(stop);
    this.show('From the source place', parts);
  }
  placingChanged() { if (this.name === 'search' || this.name === 'source') this.open(this.app.tools.current); }
  // ---------- search ----------
  searchPanel() {
    const s = this.search, a = this.app, parts = [];
    const q = el(`<input class="text" type="search" placeholder="Describe it: a reed hut, a lantern, a fishing net" aria-label="Search for something to add" value="${esc(s.q)}">`);
    let t; q.oninput = () => { s.q = q.value; clearTimeout(t); t = setTimeout(() => this.runSearch(), 300); };
    q.onkeydown = (e) => { if (e.key === 'Enter') this.runSearch(); };
    parts.push(q);
    const r = el('<div class="row"></div>');
    r.append(seg('Search in', [['source', 'This source place'], ['all', 'Everything we have']], s.scope, (v) => { s.scope = v; this.runSearch(); }));
    const kind = el(`<select aria-label="Kind of thing"><option value="">Any kind</option>${['building', 'static', 'clutter', 'furniture', 'container', 'light', 'door', 'tree', 'plant', 'rock'].map((k) => `<option value="${k}">${plainKind(k)}</option>`).join('')}</select>`);
    kind.value = s.kind; kind.onchange = () => { s.kind = kind.value; this.runSearch(); };
    r.append(kind); parts.push(r);
    if (this.T.placing?.from === 'search') {
      parts.push(el(`<p><strong>Tap our place where the ${esc(this.T.placing.base.name || 'thing')} should go.</strong></p>`));
      const c = el('<button class="quiet">Cancel</button>'); c.onclick = () => { this.T.stopPlacing(); this.searchPanel(); }; parts.push(c);
    }
    const grid = el('<div class="grid" role="list"></div>');
    for (const res of s.results) {
      const card = el(`<button class="card" role="listitem" aria-pressed="${this.T.placing?.base?.key === res.key}"><img alt=""><span class="name">${esc(res.name || res.edid)}</span><span class="tag">${esc(plainKind(res.kind))}</span></button>`);
      if (res.nordic) card.append(el('<span class="tag nordic">Nordic</span>'));
      const img = card.querySelector('img'); img.src = res.thumb || thumb(res, (u) => { img.src = u; });
      card.onclick = () => {
        if (!a.bases.has(res.key)) a.bases.set(res.key, res);
        this.T.placing = { from: 'search', base: res }; this.searchPanel();
      };
      grid.append(card);
    }
    if (!s.results.length) grid.append(el(`<p>${s.q ? 'Nothing found. Try other words, or search everything we have.' : 'Type what you are looking for.'}</p>`));
    parts.push(grid);
    this.show('Add something', parts);
  }
  async runSearch() {
    const s = this.search; if (!s.q.trim()) { s.results = []; if (this.name === 'search') this.searchPanel(); return; }
    try {
      const r = await api.search({ q: s.q, scope: s.scope, source_id: this.app.sourceId, kind: s.kind, limit: 48 });
      s.results = r.results || r || [];
    } catch (e) { this.app.toast(`Search did not answer: ${e.message}`); s.results = []; }
    if (this.name === 'search') { this.searchPanel(); const q = $('#panel-body input[type=search]'); q?.focus(); q?.setSelectionRange(q.value.length, q.value.length); }
  }
  // ---------- people ----------
  peoplePanel() {
    const a = this.app, P = a.people, parts = [];
    if (P.armed) {
      const what = { new: 'where the new person should stand', stop: 'where this stop should be', patrol: 'where the patrol point should be', all: 'where this person should stand' }[P.armed.kind];
      parts.push(el(`<p><strong>Tap our place ${what}.</strong>${P.armed.kind === 'patrol' && P.armed.i == null ? ' Keep tapping to add more points.' : ''}</p>`));
      const c = el('<button class="quiet">Done</button>'); c.onclick = () => { P.armed = null; this.peoplePanel(); }; parts.push(c);
    }
    if (P.navOf(a.ours.space)) parts.push(el('<p class="tag">Each line is the way that person walks in the game: it is found on the built place\'s own walking mesh. A thing you have moved since the place was last built is walked to over our ground until you finalise.</p>'));
    const p = P.sel && a.model.people.get(P.sel);
    if (p) {
      const name = el(`<label class="field">Name<input type="text" value="${esc(p.name)}"></label>`);
      name.querySelector('input').onchange = (e) => this.contents.rename(p, e.target.value);
      const role = el(`<label class="field">What they do<input type="text" value="${esc(p.role)}"></label>`);
      role.querySelector('input').onchange = (e) => P.edit(p.id, (x) => { x.role = e.target.value; });
      const nl = a.needs?.personLine(p.id); if (nl) parts.push(nl);
      parts.push(name, role);
      const svc = Array.isArray(p.services) ? p.services.map((v) => v.detail || v.kind || v.give_kind_id).filter(Boolean) : Object.entries(p.services || {}).filter(([, v]) => v).map(([k]) => k);
      if (svc.length) parts.push(el(`<p>Gives: ${esc(svc.join(', '))}</p>`));
      for (const msg of P.problems(p)) parts.push(el(`<p class="tag nordic">${esc(msg)}</p>`));
      if (isInnkeeper(p) && !p.bed) parts.push(el('<p class="note">Keeps no bed and works all day, as Skyrim\'s innkeepers do.</p>'));
      parts.push(this.contents.personSection(p));
      parts.push(el('<h3>Their day</h3>'));
      const list = el('<ol class="history"></ol>');
      P.sorted(p).forEach((s, i) => {
        const sp = P.stopPoint(s), where = sp.space === 'exterior' ? 'outside' : a.spaceName(a.ours, sp.space);
        const li = el(`<li><div class="what"><div class="row" style="margin:0">
          <input type="text" inputmode="numeric" pattern="[0-2]?[0-9]:[0-5][0-9]" placeholder="HH:MM" aria-label="Starts at (24-hour clock)" value="${clock(s.start)}" style="min-height:44px;width:5.5em">
          <label class="field" style="flex:0">for<input type="number" min="0.25" max="24" step="0.25" value="${s.hours}" style="width:5em" aria-label="Hours"></label>
          <select aria-label="Doing">${Object.entries(s.kind in STOP_KINDS ? STOP_KINDS : { ...STOP_KINDS, [s.kind]: s.kind }).map(([k, v]) => `<option value="${k}" ${k === s.kind ? 'selected' : ''}>${v}</option>`).join('')}</select></div>
          <span class="note">${esc(where)}</span></div></li>`);
        const find = (x) => x.routine.find((r) => r.start === s.start && r.kind === s.kind);
        const [tIn, hIn] = li.querySelectorAll('input'), kIn = li.querySelector('select');
        tIn.onchange = () => { const t = parseClock(tIn.value); if (t === null) { tIn.value = clock(s.start); return; } if (Math.abs(t - s.start) < 1e-6) return; P.edit(p.id, (x) => { const r = find(x); if (r) r.start = t; }); this.peoplePanel(); };
        hIn.onchange = () => P.edit(p.id, (x) => { find(x).hours = Number(hIn.value); });
        kIn.onchange = () => { P.edit(p.id, (x) => { find(x).kind = kIn.value; }); this.peoplePanel(); };
        const mv = el('<button class="quiet">Put on map</button>'); mv.onclick = () => P.arm('stop', { id: p.id, i });
        const go = el('<button class="quiet">See it</button>'); go.onclick = () => { a.setTime(s.start + Math.min(1, s.hours / 2)); if (sp.space !== a.ours.space) { const door = P.doorTo('exterior', sp.space); if (sp.space === 'exterior') a.leave(a.ours, 0); else if (door) a.enter(a.ours, door); } };
        const rm = el('<button class="quiet" aria-label="Remove this stop">Remove</button>'); rm.onclick = () => { P.edit(p.id, (x) => { x.routine.splice(x.routine.indexOf(find(x)), 1); }); this.peoplePanel(); };
        const row = el('<div class="row"></div>'); row.append(go, mv, rm); li.querySelector('.what').append(row);
        list.append(li);
      });
      parts.push(list);
      const add = el('<button class="quiet">Add a stop</button>');
      add.onclick = () => { P.edit(p.id, (x) => { const last = P.sorted(x).pop(); x.routine.push({ start: last ? (last.start + last.hours) % 24 : 8, hours: 1, kind: 'wander', at: { space: a.ours.space, pos: last?.at?.pos ? [...last.at.pos] : null, radius: 256 } }); }); P.arm('stop', { id: p.id, i: P.sorted(a.model.people.get(p.id)).length - 1 }); };
      parts.push(add);
      parts.push(el('<h3>Patrol points</h3>'));
      patrolOf(p).forEach((q, i) => {
        const row = el(`<div class="row"><span style="flex:1">Point ${i + 1}</span></div>`);
        const mv = el('<button class="quiet">Move</button>'); mv.onclick = () => P.arm('patrol', { id: p.id, i });
        const rm = el('<button class="quiet">Remove</button>'); rm.onclick = () => { P.edit(p.id, (x) => { const pts = [...patrolOf(x)]; pts.splice(i, 1); setPatrol(x, pts); }); this.peoplePanel(); };
        row.append(mv, rm); parts.push(row);
      });
      const ap = el('<button class="quiet">Add patrol points</button>'); ap.onclick = () => P.arm('patrol', { id: p.id, i: null }); parts.push(ap);
      parts.push(el('<h3>The person</h3>'));
      const r = el('<div class="row"></div>');
      const mv = el('<button class="quiet">Move this person</button>'); mv.onclick = () => P.arm('all', { id: p.id });
      const rm = el('<button class="danger">Remove this person</button>'); rm.onclick = () => { P.remove(p.id); this.peoplePanel(); };
      const back = el('<button class="quiet">Everyone</button>'); back.onclick = () => P.select(null);
      r.append(back, mv, rm); parts.push(r);
      this.show(p.name || 'Person', parts); return;
    }
    parts.push(el('<p>Drag the time of day below and people move to where they will be. Tap a person to see their day.</p>'));
    const list = el('<ol class="history"></ol>');
    for (const q of P.list()) {
      const trade = identityOf(a.model.identities, q.id)?.trade;
      const li = el(`<li><span class="call-dot" style="background:${P.colour(q)}"></span><span class="what">${esc(q.name)}<span class="note">${esc([q.role, trade].filter(Boolean).join(' · '))}</span></span></li>`);
      const b = el('<button class="quiet">Show</button>'); b.onclick = () => P.select(q.id); li.append(b); list.append(li);
    }
    parts.push(list);
    parts.push(el('<h3>Add a person</h3>'), el('<p>Tap a person in the source place, then tap our place. Or start from one of these:</p>'));
    const pick = el(`<select aria-label="Kind of person">${[...a.npcs.values(), ...a.srcBundle.npcs.values()].map((n) => `<option value="${esc(n.key)}">${esc(n.name || n.edid)} (${esc(n.class || '')})</option>`).join('')}</select>`);
    const go = el('<button class="quiet">Place them</button>'); go.onclick = () => P.arm('new', { base: pick.value });
    const r = el('<div class="row"></div>'); r.append(pick, go); parts.push(r);
    this.show('People', parts);
  }
  personFromSource(ref) {
    const a = this.app, npc = a.srcBundle.npcs.get(ref.base);
    this.show('From the source place', [el(`<p><strong>${esc(npc?.name || 'A person')}</strong>${npc?.class ? `, ${esc(npc.class)}` : ''}</p>`), el('<p>Tap our place where they should stand. You can then give them their day.</p>')]);
  }
  // ---------- land ----------
  landPanel() {
    const L = this.T.land, parts = [];
    parts.push(el('<p>Small changes only: each becomes a patch to the land of one cell. Draw with the pen; press harder for more.</p>'));
    parts.push(seg('Land tool', [['raise', 'Raise'], ['lower', 'Lower'], ['level', 'Level'], ['smooth', 'Smooth']], L.kind, (v) => { L.kind = v; this.landPanel(); }));
    if (L.kind === 'level') {
      const r = el(`<div class="row"><span>Level to height ${L.level == null ? '(where you start drawing)' : Math.round(L.level)}</span></div>`);
      const b = el('<button class="quiet">Pick height: tap the land</button>'); b.onclick = () => { L.picking = true; this.app.toast('Tap the land at the height you want.'); };
      r.append(b); parts.push(r);
    }
    parts.push(slider('Brush size', 128, 1024, 64, L.radius, (v) => `${metres(v)}`, (v) => { L.radius = v; }));
    parts.push(slider('Strength', 0.1, 1, 0.05, L.strength, (v) => `${Math.round(v * 100)}%`, (v) => { L.strength = v; }));
    parts.push(el('<p id="land-count" class="tag">Height points changed in this stroke: 0</p>'));
    const tm = this.app.ours.terrainMesh;
    parts.push(toggle('Show changed land', tm?.showChanged ?? true, (v) => { if (tm) { tm.showChanged = v; tm.tint(); this.app.ours.view.redraw(); } }));
    parts.push(el('<h3>Land patches</h3>'));
    const rows = [];
    for (const [k, c] of this.app.model.land) {
      const cell = k.split(',').map(Number); let n = 0;
      for (const dz of c.values()) if (Math.abs(dz) > 0.5) n++;
      if (n) rows.push(`<li><span class="what">Cell ${cell.join(', ')}<span class="note">${n} height point${n > 1 ? 's' : ''} changed</span></span></li>`);
    }
    parts.push(el(`<ol class="history">${rows.join('') || '<li>No land changed yet.</li>'}</ol>`));
    this.show('Land', parts);
  }
  landCount(n, full) { const e = $('#land-count'); if (e) e.textContent = `Height points changed in this stroke: ${n}${full ? ' (the most one stroke may change)' : ''}`; }
  // ---------- plants ----------
  plantsPanel() {
    const V = this.T.veg, a = this.app, parts = [];
    parts.push(el('<p>Clear plants with the brush, or tap one plant. Bring back puts back exactly what the world had there.</p>'));
    parts.push(seg('Plants tool', [['clear', 'Clear'], ['restore', 'Bring back']], V.mode, (v) => { V.mode = v; if (v === 'restore' && !a.showCleared) { a.showCleared = true; a.refreshSide(a.ours); this.plantsPanel(); } }));
    parts.push(slider('Brush size', 128, 2048, 64, V.radius, (v) => metres(v), (v) => { V.radius = v; }));
    parts.push(toggle('Show cleared plants', a.showCleared, (v) => { a.showCleared = v; a.refreshSide(a.ours); }));
    const by = { draft: 0, owner: 0 }; for (const c of a.model.clear.values()) by[c.by === 'draft' ? 'draft' : 'owner']++;
    parts.push(el(`<p>${by.draft} cleared by the draft, ${by.owner} cleared by you. Plants on paths are cleared with the path.</p>`));
    const why = new Map(); for (const c of a.model.clear.values()) if (c.by === 'draft') { const w = CLEAR_WHY[c.why] || (c.why ? c.why : 'no reason given'); why.set(w, (why.get(w) || 0) + 1); }
    if (why.size) parts.push(el(`<ul class="plain">${[...why].sort((x, y) => y[1] - x[1]).map(([w, n]) => `<li>${n} ${esc(w)}</li>`).join('')}</ul>`));
    this.show('Plants', parts);
  }
  // ---------- paths ----------
  pathsPanel() {
    const P = this.T.path, a = this.app, parts = [];
    parts.push(seg('Paths tool', [['draw', 'Draw'], ['edit', 'Change or erase']], P.mode, (v) => { P.mode = v; this.pathsPanel(); a.tools.drawPathHandles(); }));
    const styles = Object.entries(a.pathStyles || {});
    if (!P.style || !a.pathStyles[P.style]) P.style = styles[0]?.[0];
    const sel = P.sel && a.model.paths.get(P.sel);
    const cur = sel || P;
    parts.push(el('<h3>Look</h3>'));
    parts.push(seg('Kind', Object.entries(PATH_KIND), cur.kind, (v) => { if (sel) a.tools.editPath({ kind: v }); else P.kind = v; }));
    parts.push(seg('Width', [[160, 'Narrow'], [256, 'Medium'], [400, 'Wide']], cur.width, (v) => { if (sel) a.tools.editPath({ width: v }); else P.width = v; }));
    parts.push(seg('Ground', styles.map(([k, s]) => [k, s.label]), cur.style, (v) => { if (sel) a.tools.editPath({ style: v }); else P.style = v; }));
    if (P.mode === 'draw') parts.push(el(`<p>Draw the path with the pen. It is smoothed into a clean line, laid with the ground you picked, and plants on it are cleared.${sel ? ' The look above changes the path you drew last.' : ''}</p>`));
    if (sel) {
      parts.push(el('<p>Drag a point to bend the path.</p>'));
      const er = el('<button class="danger">Erase this path</button>'); er.onclick = () => { a.tools.erasePath(); this.pathsPanel(); }; parts.push(er);
    } else if (P.mode !== 'draw') parts.push(el('<p>Tap a path to change or erase it.</p>'));
    parts.push(el('<h3>Paths in this place</h3>'));
    const list = el('<ol class="history"></ol>');
    for (const p of a.model.paths.values()) {
      const len = Math.round(p.points.slice(1).reduce((s, q, i) => s + Math.hypot(q[0] - p.points[i][0], q[1] - p.points[i][1]), 0));
      const li = el(`<li><span class="what">${PATH_KIND[p.kind] || 'Path'}, ${esc(a.pathStyles[p.style]?.label || p.style)}<span class="note">${metres(len)} long, ${metres(p.width)} wide</span></span></li>`);
      const b = el(`<button class="quiet" aria-pressed="${p.id === P.sel}">Choose</button>`); b.onclick = () => { P.sel = p.id; P.mode = 'edit'; this.pathsPanel(); a.tools.drawPathHandles(); };
      li.append(b); list.append(li);
    }
    parts.push(list);
    this.show('Paths and streets', parts);
  }
  // ---------- notes on changes ----------
  notesChanged() { if (this.name === 'notes') this.notesPanel(); }
  // Select the things some changes touched (in the space on show), so the owner sees what a note is about.
  selectTouched(ops) {
    const a = this.app, here = a.placeRefsById();
    const ids = [...new Set(touched(ops).filter((t) => t.kind === 'ref' && t.space === a.ours.space && here.has(t.id)).map((t) => t.id))];
    if (!ids.length) {
      const elsewhere = touched(ops).some((t) => t.space !== a.ours.space);
      a.toast(elsewhere ? 'Those changes are in another room or outside.' : 'Those changes touched the land, plants, paths or people, not things to select.');
      return;
    }
    this.T.use('select'); a.selection = new Set(ids); this.T.selectionChanged();
  }
  // One change's words, for a list.
  changeWords(group, op) { return group.length > 1 && op.stroke ? `${this.app.describe(op)} (${group.length} cells)` : this.app.describe(op); }
  // ---------- history ----------
  historyChanged() { if (this.name === 'history') this.historyPanel(); }
  historyPanel() {
    const a = this.app, L = a.log, parts = [];
    this.chosen = this.chosen || new Set();
    parts.push(el('<p>Every change is a <strong style="color:var(--fault)">fault</strong> (the draft got it wrong) unless you mark it a <strong style="color:var(--taste)">taste</strong> call (you simply prefer it). Tap a change to go back to it.</p>'));
    const bar = el('<div class="row"></div>');
    const mk = (label, fn) => { const b = el(`<button class="quiet">${label}</button>`); b.onclick = fn; bar.append(b); return b; };
    mk('Chosen are taste', () => { L.setCall([...this.chosen], 'taste'); this.chosen.clear(); this.historyPanel(); });
    mk('Chosen are faults', () => { L.setCall([...this.chosen], 'fault'); this.chosen.clear(); this.historyPanel(); });
    mk('From the first chosen on: taste', () => { const n = Math.min(...this.chosen); if (Number.isFinite(n)) L.sinceCall(n, 'taste'); this.chosen.clear(); this.historyPanel(); });
    parts.push(bar);
    // one note for the chosen changes; tapping a change's note chooses its changes and puts its words here to edit
    if (this.chosen.size) {
      const noteRow = el('<div class="row"></div>');
      const words = el(`<input class="text" type="text" enterkeyhint="done" aria-label="One note for the chosen changes" placeholder="One note for the ${this.chosen.size === 1 ? 'chosen change' : `${this.chosen.size} chosen changes`}">`);
      words.value = this.historyNote || ''; words.oninput = () => { this.historyNote = words.value; };
      const keep = () => { const t = words.value.trim(); if (!t) return; L.setNote([...this.chosen], t); this.chosen.clear(); this.historyNote = ''; a.toast('Note kept with the chosen changes.'); this.historyPanel(); };
      words.onkeydown = (e) => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); keep(); } };
      const go = el('<button class="primary">Note the chosen</button>'); go.onclick = keep;
      const off = el('<button class="quiet">Take their note away</button>');
      off.onclick = () => { L.setNote([...this.chosen], ''); this.chosen.clear(); this.historyNote = ''; this.historyPanel(); };
      noteRow.append(words, go, off); parts.push(noteRow);
    }
    const list = el('<ol class="history changes-noted"></ol>');
    const noteOf = new Map(); for (const g of groupsOf(L.ops, L.notes)) for (const o of g.ops) noteOf.set(o.n, g);
    const top = el(`<li class="${L.cursor === 0 ? 'here' : ''}"><span class="what">The draft as the agent made it</span></li>`);
    const b0 = el('<button class="quiet">Go back here</button>'); b0.onclick = () => L.goto(0); top.append(b0); list.append(top);
    let lastStroke = null;
    L.ops.forEach((op, i) => {
      if (op.stroke && op.stroke === lastStroke) return; lastStroke = op.stroke || null;
      const group = op.stroke ? L.ops.filter((o) => o.stroke === op.stroke) : [op];
      const future = i >= L.cursor;
      const li = el(`<li class="${future ? 'future' : ''}"></li>`);
      const chk = el(`<button class="quiet" aria-pressed="${this.chosen.has(op.n)}" aria-label="Choose this change" style="min-width:44px;padding:0">${this.chosen.has(op.n) ? '✓' : ''}</button>`);
      chk.onclick = () => { this.chosen.has(op.n) ? this.chosen.delete(op.n) : this.chosen.add(op.n); this.historyPanel(); };
      const g = noteOf.get(op.n), text = this.changeWords(group, op);
      const about = g && g.changes.length > 1 ? ` (one note for ${g.changes.length} changes)` : '';
      const what = el(`<button class="what" style="text-align:left;justify-content:flex-start;flex-direction:column;align-items:flex-start;display:flex">${esc(text)}${g ? `<span class="note said" data-note="${esc(g.id)}">${esc(g.text)}${esc(about)}</span>` : ''}</button>`);
      what.onclick = (e) => {
        if (g && e.target.closest('.said')) { this.chosen = new Set(g.ops.map((o) => o.n)); this.historyNote = g.text; this.historyPanel(); return; }
        L.goto(group[group.length - 1].n);
      };
      const call = el(`<button class="call" data-call="${op.call}">${op.call === 'taste' ? 'Taste' : 'Fault'}</button>`);
      call.onclick = () => { L.setCall([op.n], op.call === 'taste' ? 'fault' : 'taste'); this.historyPanel(); };
      li.append(chk, what, call); list.append(li);
    });
    parts.push(list);
    const n = L.applied(), taste = n.filter((o) => o.call === 'taste').length;
    parts.push(el(`<p>${n.length} change${n.length === 1 ? '' : 's'}: ${n.length - taste} fault${n.length - taste === 1 ? '' : 's'}, ${taste} taste.</p>`));
    this.show('History', parts);
  }
  // ---------- saves ----------
  // ---------- notes for the agent ----------
  // What the owner wants changed, in words: about the place, or about the things selected. Kept with the place
  // (edits/notes.jsonl), unsent until the owner sends them all as one batch; then an agent makes the changes and its
  // reply shows under each note.
  async notesPanel(aboutSelection = false) {
    const a = this.app, pid = a.place.place_id, parts = [], sel = this.T.selRefs();
    const nameOf = (r) => { const b = a.bases.get(r.base) || {}; return b.name || b.edid || 'Unnamed'; };
    const text = el('<textarea class="text note-text" rows="4" placeholder="What should change? Say it as you would to a person." aria-label="Your note"></textarea>');
    text.value = this.noteDraft || ''; text.oninput = () => { this.noteDraft = text.value; };
    parts.push(el('<p>Write notes for the agent as you go, as many as you like. They are kept with the place, and no agent reads them until you send them.</p>'), text);
    let about = null;
    if (sel.length) {
      const words = sel.length === 1 ? `About the selected thing: ${nameOf(sel[0])}` : `About the ${sel.length} things selected`;
      about = toggle(words, aboutSelection || this.noteAbout !== false, (v) => { this.noteAbout = v; });
      parts.push(about);
    } else parts.push(el('<p class="tag">About the place as a whole. To make a note about particular things, select them first.</p>'));
    const keep = el('<button class="primary">Keep the note</button>');
    keep.onclick = async () => {
      const words = text.value.trim(); if (!words) { a.toast('Write the note first.'); return; }
      const with_ = about && about.getAttribute('aria-pressed') === 'true' ? sel : [];
      const v = a.ours.view.rig.target, o = a.ours.origin;
      keep.disabled = true;
      try {
        await api.note(pid, { text: words, view: { space: a.ours.space, at: [v.x + o[0], v.y + o[1], v.z + o[2]] },
          things: with_.map((r) => ({ id: r.id, space: a.ours.space, base: r.base, name: nameOf(r), kind: r.kind, pos: r.pos, src: r.src })) });
        this.noteDraft = ''; a.toast('Note kept. Send your notes when you are ready.');
      } catch (e) { a.toast(`The note was not kept: ${e.message}. It is still in the box; try again.`, 7000); }
      if (this.name === 'notes') this.notesPanel();
    };
    parts.push(keep);
    let list = [], listErr = null;
    try { list = await api.notes(pid) || []; } catch (e) { listErr = e; }
    const unsent = list.filter((n) => !n.done && n.sent === false);
    // one batch: every unsent note goes at once, after one confirmation that says what will happen
    const sendBox = el('<div class="send-notes"></div>');
    const sendBtn = el(`<button class="primary send-notes-btn">Send notes to the agent (${unsent.length})</button>`);
    sendBtn.disabled = !unsent.length;
    sendBtn.onclick = () => {
      const n = unsent.length, count = n <= 10 ? ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'][n] : String(n);
      const ask = el(`<div class="report confirm-send"><p>An agent will read ${n === 1 ? 'this note' : `these ${count} notes`} and make the changes. You can keep editing.</p></div>`);
      const go = el('<button class="primary">Send them</button>'), no = el('<button class="quiet">Not yet</button>');
      no.onclick = () => { if (this.name === 'notes') this.notesPanel(); };
      go.onclick = async () => {
        go.disabled = true;
        try { await api.sendNotes(pid); a.toast('Sent. An agent is reading your notes now; its replies show here.', 6000); }
        catch (e) { a.toast(`The notes were not sent: ${e.message}. Try again.`, 7000); }
        if (this.name === 'notes') this.notesPanel();
      };
      const row = el('<div class="row"></div>'); row.append(go, no); ask.append(row);
      sendBox.replaceChildren(ask);
    };
    sendBox.append(sendBtn);
    if (!unsent.length && list.length) sendBox.append(el('<p class="tag">Every note has been sent.</p>'));
    // the notes kept with changes (the note bar under the views, or History): each with the changes it is about
    const groups = groupsOf(a.log?.applied() || [], a.log?.notes);
    if (groups.length) {
      parts.push(el('<h3>Notes with your changes</h3>'), el('<p class="tag">These go to the agent with the changes they are about when you finalise.</p>'));
      const gl = el('<ol class="history notes change-notes"></ol>');
      for (const g of [...groups].reverse()) {
        const n = g.changes.length, call = g.ops.every((o) => o.call === 'taste') ? 'taste' : 'fault';
        const lines = g.changes.slice(0, 4).map((c) => esc(this.changeWords(c, c[0]))).join('; ') + (n > 4 ? `; and ${n - 4} more` : '');
        const li = el(`<li><span class="call-dot" data-call="${call}"></span><span class="what">${esc(g.text)}<span class="note">About ${n === 1 ? 'one change' : `${n} changes`} (${call}): ${lines}</span></span></li>`);
        const sel = el('<button class="quiet">Select</button>'); sel.onclick = () => this.selectTouched(g.ops);
        const ed = el('<button class="quiet">Edit</button>');
        ed.onclick = () => {
          const box = el('<input class="text" type="text" enterkeyhint="done" aria-label="The words of this note">'); box.value = g.text;
          const ok = el('<button class="primary">Keep</button>');
          const keep = () => { const t = box.value.trim(); if (t) a.log.setNote(g.ops.map((o) => o.n), t); };
          ok.onclick = keep; box.onkeydown = (e) => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); keep(); } };
          const r = el('<div class="row"></div>'); r.append(box, ok); li.append(r); box.focus();
        };
        const rm = el('<button class="quiet">Remove</button>'); rm.onclick = () => a.log.setNote(g.ops.map((o) => o.n), '');
        const btns = el('<div class="row"></div>'); btns.append(sel, ed, rm); li.append(btns); gl.append(li);
      }
      parts.push(gl);
    }
    parts.push(el('<h3>Your notes</h3>'), sendBox);
    if (listErr) parts.push(el(`<p>The notes could not be listed: ${esc(listErr.message)}</p>`));
    if (!list.length) parts.push(el('<p class="tag">None yet.</p>'));
    const ol = el('<ol class="history notes free-notes"></ol>');
    const redo = () => { if (this.name === 'notes') this.notesPanel(); };
    const change = async (body) => { try { await api.note(pid, body); } catch (e) { a.toast(`Not changed: ${e.message}`); } redo(); };
    for (const n of [...list].reverse()) {
      const st = n.done ? 'done' : n.sent === false ? 'unsent' : 'sent';
      const said = { unsent: 'not sent yet', sent: 'sent: the agent is working on it', done: 'done' }[st];
      const things = n.things?.length ? (n.things.length === 1 ? `About ${n.things[0].name || 'one thing'}` : `About ${n.things.length} things`) : 'About the place';
      const li = el(`<li class="${st === 'done' ? 'future' : ''}" data-state="${st}"><span class="what">${esc(n.text)}<span class="note">${esc(things)} · ${esc(new Date(n.at).toLocaleString())} · <span class="state">${said}</span></span>${n.reply ? `<span class="note reply">Agent: ${esc(n.reply)}</span>` : ''}</span></li>`);
      const btns = el('<div class="row"></div>');
      const ids = (n.things || []).filter((t) => t.space === a.ours.space && a.placeRefsById().has(t.id)).map((t) => t.id);
      if (ids.length) { const b = el('<button class="quiet">Select</button>'); b.onclick = () => { this.T.use('select'); a.selection = new Set(ids); this.T.selectionChanged(); }; btns.append(b); }
      if (st === 'unsent') {
        const ed = el('<button class="quiet">Edit</button>');
        ed.onclick = () => {
          const box = el('<textarea class="text" rows="3" aria-label="The words of this note"></textarea>'); box.value = n.text;
          const ok = el('<button class="primary">Keep</button>'); ok.onclick = () => { const t = box.value.trim(); if (t) change({ id: n.id, text: t }); };
          const r = el('<div class="row"></div>'); r.append(box, ok); li.append(r); box.focus();
        };
        const rm = el('<button class="quiet">Delete</button>'); rm.onclick = () => change({ id: n.id, delete: true });
        btns.append(ed, rm);
      } else {
        const d = el(`<button class="quiet">${n.done ? 'Reopen' : 'Mark done'}</button>`); d.onclick = () => change({ id: n.id, done: !n.done });
        btns.append(d);
      }
      li.append(btns); ol.append(li);
    }
    parts.push(ol);
    // the panel on show was typed into while the list was fetched: its words, and the cursor, carry over
    const typing = document.activeElement?.classList?.contains('note-text');
    text.value = this.noteDraft || '';
    if (this.name === 'notes') { this.show('Notes for the agent', parts); if (typing) text.focus(); }
  }
  async savesPanel() {
    const a = this.app, parts = [];
    const name = el('<input class="text" type="text" placeholder="Name this save, e.g. Market moved" aria-label="Save name">');
    const save = el('<button class="primary">Save a copy</button>');
    save.onclick = async () => {
      const nm = name.value.trim() || `Save ${new Date().toLocaleString()}`, sid = nm.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48) || 'save';
      const r = await a.putSave(sid, nm);
      a.toast(r.conflict ? `"${nm}" was not saved: ${r.error || 'a save of that name already moved on or is final'}. Pick another name.` : `Saved as "${nm}".`); this.savesPanel();
    };
    const r = el('<div class="row"></div>'); r.append(name, save);
    parts.push(el('<p>Your work saves itself as you go. Save a named copy to come back to a version later.</p>'), r, el('<h3>Saves</h3>'));
    let list = [];
    try { list = await api.saves(a.place.place_id) || []; } catch (e) { parts.push(el(`<p>The saves could not be listed: ${esc(e.message)}</p>`)); }
    list = (list.saves || list).sort((x, y) => (y.save_id === 'autosave') - (x.save_id === 'autosave') || String(y.at).localeCompare(String(x.at)));
    const ol = el('<ol class="history"></ol>');
    for (const s of list) {
      const li = el(`<li><span class="what">${esc(s.save_id === 'autosave' ? 'Latest work (saved automatically)' : s.name || s.save_id)}${s.final ? ' (finalised)' : ''}<span class="note">${esc(new Date(s.at).toLocaleString())}</span></span></li>`);
      const b = el('<button class="quiet">Open</button>');
      b.onclick = async () => { const full = await api.save(a.place.place_id, s.save_id); await a.loadSave(full); a.revs.autosave = a.revs.autosave || (list.find((x) => x.save_id === 'autosave')?.rev ?? 0); a.toast(`Opened "${s.name || s.save_id}". ${full.ops?.length || 0} changes.`); a.markUnsaved(); };
      li.append(b); ol.append(li);
    }
    parts.push(ol);
    const fresh = el('<button class="quiet">Start again from the draft</button>');
    fresh.onclick = async () => { await a.loadSave({ ops: [] }); a.markUnsaved(); a.toast('Back to the draft as the agent made it. Your saves are still listed here.'); };
    parts.push(fresh);
    if (this.name === 'saves') this.show('Saves', parts);
  }
  // When the place has saved work, nothing is applied until the owner chooses: the builder's draft, or one save
  // to continue (an autosave is "unsaved work"). An autosave can be discarded here; one made on an older draft
  // says so, and what no longer fits is reported when it opens.
  async startChoice() {
    const a = this.app, pid = a.place.place_id;
    let list = [];
    try { list = (await api.saves(pid)) || []; } catch (e) { if (!/404/.test(e.message)) a.toast(`Your saves could not be listed: ${e.message}`, 8000); return null; }
    const nOps = (x) => (Array.isArray(x.ops) ? x.ops.length : x.ops ?? 0);
    list = (list.saves || list).map((x) => ({ ...x, ops: nOps(x) })).filter((x) => x.ops > 0 && !x.final)
      .sort((x, y) => (y.save_id === 'autosave') - (x.save_id === 'autosave') || String(y.at).localeCompare(String(x.at)));
    if (!list.length) return null;
    const draftKey = a.saveBody('autosave', 'Autosave').base?.draft_key;
    const when = (t) => new Date(t).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
    const edits = (n) => `${n} edit${n === 1 ? '' : 's'}`;
    const o = $('#start'); o.hidden = false;
    o.innerHTML = `<div class="sheet" role="dialog" aria-label="Choose where to start"><h2>${esc(a.place.title || pid)} has saved work</h2>
      <p>Nothing has been changed yet. Choose where to start.</p>
      <div class="row"><button class="quiet fresh">Start from the builder's draft</button></div><ol class="history start-list"></ol></div>`;
    const ol = o.querySelector('.start-list');
    return new Promise((done) => {
      const close = (v) => { o.hidden = true; o.innerHTML = ''; done(v); };
      const auto0 = list.find((x) => x.save_id === 'autosave');
      if (auto0) o.querySelector('.fresh').after(el('<p class="note">Your first edit from the draft replaces the unsaved work. To keep it, continue it and save it under a name first.</p>'));
      o.querySelector('.fresh').onclick = () => { if (auto0) a.revs.autosave = auto0.rev || 0; close('draft'); };
      for (const s of list) {
        const auto = s.save_id === 'autosave';
        const li = el(`<li><span class="what">${esc(auto ? `Unsaved work from ${when(s.at)}, ${edits(s.ops ?? 0)}` : `${s.name || s.save_id}, ${when(s.at)}, ${edits(s.ops ?? 0)}`)}<span class="note"></span></span></li>`);
        const note = li.querySelector('.note');
        const go = el(`<button class="primary">Continue</button>`);
        go.setAttribute('aria-label', `Continue ${auto ? 'the unsaved work' : s.name || s.save_id}`);
        go.onclick = async () => {
          go.disabled = true;
          try {
            const full = await api.save(pid, s.save_id);
            o.hidden = true; await a.loadSave(full);
            if (auto) a.revs.autosave = full.rev || 0;
            else { a.revs.autosave = list.find((x) => x.save_id === 'autosave')?.rev ?? a.revs.autosave ?? 0; a.markUnsaved(); }
            const n = a.log.applied().length, m = full.ops?.length || 0;
            if (n === m) a.toast(`Opened ${auto ? 'your unsaved work' : `"${s.name || s.save_id}"`}: ${edits(m)}.`, 5000);
            close(s.save_id);
          } catch (e) { o.hidden = false; go.disabled = false; note.textContent = `It could not be opened: ${e.message}`; }
        };
        const row = el('<div class="row"></div>'); row.append(go);
        if (auto) {
          const rm = el('<button class="danger">Discard</button>');
          rm.setAttribute('aria-label', 'Discard the unsaved work');
          rm.onclick = async () => {
            if (rm.dataset.sure !== '1') { rm.dataset.sure = '1'; rm.textContent = 'Discard for good'; note.textContent = 'Tap again to throw these edits away. Named saves are kept.'; return; }
            try {
              a.revs.autosave = s.rev || 0;
              const r = await a.putSave('autosave', 'Autosave');
              if (r.conflict) throw new Error('another tab saved it a moment ago');
              li.remove(); if (!ol.children.length) close('draft');
            } catch (e) { note.textContent = `It could not be discarded: ${e.message}`; }
          };
          row.append(rm);
        }
        const key = s.base?.draft_key;
        if (key && draftKey && key !== draftKey) {
          note.textContent = 'Made on an older draft. Edits that still fit the current draft are kept; the first one that no longer fits, and every edit after it, is shown and not applied.';
          li.classList.add('older');
        }
        li.querySelector('.what').append(row); ol.append(li);
      }
      // the list rows say nothing of an older draft until each save is read: read the bases quietly
      for (const s of list) if (!s.base) api.save(pid, s.save_id).then((f) => {
        const li = [...ol.children][list.indexOf(s)]; const k = f?.base?.draft_key;
        if (li && k && draftKey && k !== draftKey && !li.classList.contains('older')) { li.classList.add('older'); li.querySelector('.note').textContent = 'Made on an older draft. Edits that still fit the current draft are kept; the first one that no longer fits, and every edit after it, is shown and not applied.'; }
      }).catch(() => {});
    });
  }
  // ---------- finalise ----------
  finalise() {
    const a = this.app, ops = a.log.applied(), taste = ops.filter((o) => o.call === 'taste').length;
    const parts = [el(`<div class="report">
      <p>This saves your ${ops.length} change${ops.length === 1 ? '' : 's'} as final and then, without you:</p>
      <ol><li>writes them into ${esc(a.place.title || a.place.place_id)}'s files, so every later build uses your version, not the agent's draft;</li>
      <li>builds the place again, with its paths and walking routes (navmesh), and runs every check;</li>
      <li>has an agent read your ${ops.length - taste} fault${ops.length - taste === 1 ? '' : 's'} and improve the place-building recipe, so the next place is right first time. Your ${taste} taste call${taste === 1 ? '' : 's'} are kept as preferences for this place only;</li>
      <li>shows you a report here.</li></ol>
      <p>Nothing goes to the play machine. You can keep editing afterwards.</p></div>`)];
    const go = el('<button class="primary">Save and finalise</button>'), no = el('<button class="quiet">Not yet</button>');
    no.onclick = () => this.close();
    go.onclick = async () => {
      go.disabled = true;
      const sid = `final-${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15).toLowerCase()}`;
      try {
        const w = await a.putSave(sid, 'Final', true); if (w.conflict) throw new Error(w.error);
        const r = await api.finalise(a.place.place_id, sid); this.watchRun(r.run_id);
      } catch (e) { go.disabled = false; a.toast(`Finalise did not start: ${e.message}`); }
    };
    const r = el('<div class="row"></div>'); r.append(go, no); parts.push(r);
    this.name = 'finalise'; this.show('Save and finalise', parts);
  }
  async watchRun(rid) {
    const a = this.app, STEPS = [['record', 'Writing your changes into the place files'], ['build', 'Building the place and its walking routes, then checking it'], ['learn', 'Improving the place-building recipe'], ['report', 'Writing the report']];
    const poll = async () => {
      let r; try { r = await api.run(a.place.place_id, rid); } catch (e) { r = { state: 'running', log_tail: `waiting for the server: ${e.message}` }; }
      const done = r.state === 'done' || r.state === 'failed', idx = STEPS.findIndex(([k]) => k === r.step);
      const parts = [el(`<ol class="steps">${STEPS.map(([k, label], i) => `<li data-s="${done && r.state === 'done' ? 'done' : r.state === 'failed' && i === idx ? 'failed' : i < idx ? 'done' : i === idx ? 'doing' : ''}">${esc(label)}</li>`).join('')}</ol>`)];
      const tail = r.log || r.log_tail || '';
      if (tail) parts.push(el(`<pre class="log">${esc(tail)}</pre>`));
      if (r.report) parts.push(this.report(r.report));
      if (r.state === 'failed') parts.push(el('<p class="tag nordic">The run stopped. The step marked red failed; the log above says why. Your changes are saved.</p>'));
      // once the edits are written into the place they are the place: drop the unsaved copy and offer the fresh view
      const recorded = idx > 0 || (done && r.state === 'done');
      if (recorded && !this.droppedFor) { this.droppedFor = rid; a.dropAutosave(); }
      if (done && recorded) { const b = el('<button class="primary">Open the finalised place</button>'); b.onclick = () => location.reload(); parts.push(b); }
      if (this.name === 'finalise' || this.name === 'run') { this.name = 'run'; this.show(done ? (r.state === 'done' ? 'Finalised' : 'Finalise stopped') : 'Finalising', parts); }
      if (!done) this.runT = setTimeout(poll, 1500);
    };
    this.name = 'run'; poll();
  }
  // The run's report (markdown): headings, lists, paragraphs and code, nothing else needed.
  report(md) {
    if (md && typeof md === 'object') md = ['## What was built', ...(md.built || []).map((x) => `- ${x}`), '## Checks that failed', ...((md.failed_checks || []).length ? md.failed_checks.map((x) => `- ${x}`) : ['- None']), '## What the recipe now says differently', md.recipe_changes || 'No change.'].join('\n');
    const inline = (t) => esc(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    const out = []; let list = null, code = null;
    for (const line of String(md || '').split('\n')) {
      if (line.startsWith('```')) { if (code) { out.push(`<pre class="log">${esc(code.join('\n'))}</pre>`); code = null; } else code = []; continue; }
      if (code) { code.push(line); continue; }
      const li = line.match(/^\s*[-*] (.*)/);
      if (li) { if (!list) { list = []; } list.push(`<li>${inline(li[1])}</li>`); continue; }
      if (list) { out.push(`<ul>${list.join('')}</ul>`); list = null; }
      const h = line.match(/^(#{1,4}) (.*)/);
      if (h) out.push(`<h3>${inline(h[2])}</h3>`); else if (line.trim()) out.push(`<p>${inline(line)}</p>`);
    }
    if (list) out.push(`<ul>${list.join('')}</ul>`);
    if (code) out.push(`<pre class="log">${esc(code.join('\n'))}</pre>`);
    return el(`<div class="report">${out.join('') || '<p>The report is empty.</p>'}</div>`);
  }
  // ---------- settings: detail, remembered on this device ----------
  settings() {
    const o = $('#settings'), G = this.app.governor; o.hidden = false;
    const opt = (v, t, d) => `<label class="detail-opt"><input type="radio" name="detail" value="${v}"${G.mode === v ? ' checked' : ''}><span><strong>${t}</strong> ${d}</span></label>`;
    o.innerHTML = `<div class="sheet" role="dialog" aria-label="Settings"><h2>Detail</h2>
      <p>How much the views draw. Less detail keeps the views smooth on a slower tablet.</p>
      ${opt('auto', 'Automatic', 'adjusts by itself to stay smooth.')}${opt('high', 'High', 'everything, as far as it goes.')}
      ${opt('medium', 'Medium', 'plants nearer, the other view drawn less often.')}${opt('low', 'Low', 'the least, for a slow tablet.')}
      <label class="detail-opt"><input type="checkbox" name="grass"${this.app.grassOn() ? ' checked' : ''}><span><strong>Grass</strong> grown from the ground's textures near where you look.</span></label>
      <p class="detail-now"></p>${this.weatherChoice()}<button class="primary">Done</button></div>`;
    o.querySelector('select[name=weather]')?.addEventListener('change', (e) => this.app.setWeather(e.target.value));
    o.querySelector('input[name=grass]').onchange = (e) => this.app.setGrass(e.target.checked);
    o.querySelectorAll('input[name=detail]').forEach((i) => { i.onchange = () => { G.setMode(i.value); this.detailShown(); }; });
    o.querySelector('button').onclick = () => { o.hidden = true; };
    this.detailShown();
  }
  // The night views are lit by one of the climate's weathers: the likeliest unless another is chosen.
  weatherChoice() {
    const sky = this.app.ground?.spaces.exterior?.info?.sky, ws = sky?.weathers || [];
    if (!ws.length) return '<h2>Night</h2><p>This place\'s ground has no weather from the game yet, so the night views show a plain night.</p>';
    const pick = this.app.weatherKey(), top = [...ws].sort((a, b) => (b.chance || 0) - (a.chance || 0))[0];
    const words = (w) => esc(`${(w.edid || w.key).replace(/^(Skyrim|ANW_)/, '').replace(/([a-z])([A-Z])/g, '$1 $2')} (${w.chance ?? '?'}% of nights)`);
    return `<h2>Night</h2><p>Outside, the night views are lit as the game lights this world on a night of one of its weathers.</p>
      <label class="field">Weather<select name="weather">${ws.map((w) => `<option value="${esc(w.key)}"${(pick ? w.key === pick : w === top) ? ' selected' : ''}>${words(w)}</option>`).join('')}</select></label>`;
  }
  detailShown() {
    const p = document.querySelector('#settings .detail-now'), G = this.app.governor; if (!p || !G) return;
    const words = ['lowest', 'low', 'reduced', 'medium', 'high', 'highest'];
    p.textContent = `Drawing at ${words[G.level]} detail${G.avg ? `, about ${Math.round(1000 / Math.max(G.avg, 1))} frames a second while moving` : ''}.`;
  }
  // ---------- first run ----------
  intro() {
    const o = $('#intro'); o.hidden = false;
    o.innerHTML = `<div class="sheet" role="dialog" aria-label="How to use the studio"><h2>Place Studio</h2><ul>
      <li>${ICON.move}<span><strong>Look around with your fingers.</strong> One finger turns the view, two fingers drag, pinch and twist.</span></li>
      <li>${ICON.select}<span><strong>Work with the pen.</strong> Tap to select, draw round things to select several, draw paths and land. Your palm and fingers never change anything while the pen is in use.</span></li>
      <li>${ICON.search}<span><strong>Copy from the source.</strong> Tap something in the source place on the right, then tap our place where it should go.</span></li>
      <li>${ICON.history}<span><strong>Every change is a fault</strong> unless you mark it a taste call in the bar under the views. Say what was wrong in that bar too: one note for all the changes since your last note. Undo and redo are at the top.</span></li>
      <li>${ICON.history}<span><strong>Day and night.</strong> The sun and moon in each view's bar switch between the studio's daylight and the game's night: outside, the sky, ambient light, moonlight and fog of this world's weather at night; inside, the room's own lighting, which the game keeps the same at any hour. Every light lights what is round it with its own colour and reach, so you can see whether a place is lit enough. It is close to the game, not the same: there are no shadows, no ENB or Community Shaders effects, windows do not glow, and the game's eye adjusting to the dark is not copied. With the People tool on, the time of day sets both views.</span></li></ul>
      <button class="primary">Start</button></div>`;
    o.querySelector('button').onclick = () => { o.hidden = true; try { localStorage.setItem('studio.intro.v1', '1'); } catch { /* fine */ } };
  }
}
