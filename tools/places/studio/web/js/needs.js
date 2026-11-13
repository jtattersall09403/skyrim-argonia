// What the stories need of this place (docs/design/place-studio.md, "What the stories need of a place"): the panel,
// the line in the Selected and People panels, the warning before a change to something a need rests on, and the
// "as the player sees it" names over the view. Plain English throughout; the data is GET /api/place/<id>/needs.
import { api } from './api.js';

const NS = 'http://www.w3.org/2000/svg';
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function el(html) { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; }
const MOVED_FAR = 700;           // game units (10 m): a move further than this, or into another cell, moves it out of place
const NAMED_KINDS = new Set(['door', 'container', 'furniture', 'activator', 'clutter', 'plant']);
const NAMES_REACH = 5000;        // named things are labelled within this of where the view looks
const cell = (p) => `${Math.floor(p[0] / 4096)},${Math.floor(p[1] / 4096)}`;

// Which ops touch something a need rests on, and how (pure: tested in test/needs.test.mjs).
export function needChanges(ops, idx) {
  const out = [];
  const hit = (key, change, what, row = null) => {
    for (const u of idx.get(key) || []) if (!out.some((o) => o.u === u && o.change === change)) out.push({ u, change, what, key, row });
  };
  for (const o of ops) {
    if (o.op === 'ref.remove') hit(`ref:${o.id}`, 'removed', 'removed from the place', o.before);
    else if (o.op === 'ref.move' && o.before?.pos && o.after?.pos) {
      const d = Math.hypot(o.after.pos[0] - o.before.pos[0], o.after.pos[1] - o.before.pos[1]);
      if (d > MOVED_FAR || cell(o.after.pos) !== cell(o.before.pos)) hit(`ref:${o.id}`, 'moved', `moved about ${Math.round(d / 70)} metres`);
    } else if (o.op === 'person.remove') hit(`person:${o.person?.id}`, 'removed', 'taken out of the place');
    else if (o.op === 'person.edit' && o.before) {
      const a = o.person?.work || {}, b = o.before.work || {};
      const far = a.pos && b.pos ? Math.hypot(a.pos[0] - b.pos[0], a.pos[1] - b.pos[1]) : 0;
      if (a.space !== b.space || far > MOVED_FAR) hit(`person:${o.person.id}`, 'moved', a.space !== b.space ? 'given a work place in another building' : `given a work place about ${Math.round(far / 70)} metres away`);
      else if ((o.person?.home || null) !== (o.before.home || null)) hit(`person:${o.person.id}`, 'moved', 'given another home');
    } else if (o.op === 'identity.edit' && o.before && o.person?.name !== o.before.name) {
      hit(`person:${o.person?.id}`, 'renamed', `renamed from ${o.before.name} to ${o.person?.name}`);
    }
  }
  return out;
}

export class Needs {
  constructor(app) { this.app = app; this.data = null; this.idx = new Map(); this.names = false; }
  get a() { return this.app; }
  async load(pid) {
    this.data = null; this.idx = new Map();
    try { this.data = await api.needs(pid); } catch { this.data = null; }
    this.index();
  }
  // key ('ref:<id>' | 'person:<id>') -> [{kind: 'need', n} | {kind: 'use', person, use}]
  index() {
    const add = (k, v) => { if (!this.idx.has(k)) this.idx.set(k, []); this.idx.get(k).push(v); };
    for (const n of this.data?.needs || []) {
      const r = n.rests || {};
      if (r.ref) add(`ref:${r.ref}`, { kind: 'need', n });
      if (r.space && r.space !== 'exterior') {
        const door = this.a.spaceInfo?.[r.space]?.door_from;
        if (door) add(`ref:${door}`, { kind: 'need', n });
      }
      if (r.person) add(`person:${r.person}`, { kind: 'need', n });
      for (const s of n.signs || []) if (s.person && s.person !== r.person) add(`person:${s.person}`, { kind: 'tells', n });
    }
    for (const [pid, p] of Object.entries(this.data?.people || {})) for (const use of p.uses) add(`person:${pid}`, { kind: 'use', pid, person: p, use });
  }
  sentence(u) {
    if (u.kind === 'use') return `${u.use.for} (${u.use.line}; ${u.use.quests})`;
    if (u.kind === 'tells') return `this person is how a player learns of ${u.n.thing}: ${u.n.does} (${u.n.line})`;
    return `${u.n.does} (${u.n.line}; ${u.n.quests})`;
  }
  // ---------- the panel ----------
  panel() {
    const P = this.a.panels, parts = [], d = this.data;
    parts.push(el('<p>Each row is something a story needs a player to find in this place, in plain words. <strong>Met</strong> means it is here and a player who has been told nothing would know it for what it is: by its look, by the name the game shows, by what stands by it, or because someone tells them. The stories are first drafts; they change to fit the place, never the place to fit them.</p>'));
    if (!d?.needs?.length) { parts.push(el('<p class="tag">No story needs anything of this place yet.</p>')); P.show('What the story needs of this place', parts); return; }
    for (const met of [false, true]) {
      const rows = d.needs.filter((n) => n.met === met);
      parts.push(el(`<h3>${met ? 'Met' : 'Not met'} (${rows.length})</h3>`));
      if (!rows.length) { parts.push(el(`<p class="tag">${met ? 'Nothing yet.' : 'Every need is met.'}</p>`)); continue; }
      const ol = el('<ol class="needs"></ol>');
      for (const n of rows) ol.append(this.row(n));
      parts.push(ol);
    }
    const used = Object.entries(d.people || {}).filter(([, p]) => p.uses.length);
    if (used.length) {
      parts.push(el(`<h3>People the stories use (${used.length})</h3>`));
      const ol = el('<ol class="needs people-uses"></ol>');
      for (const [pid, p] of used) {
        const li = el(`<li><span class="what"><strong>${esc(p.who)}</strong>${p.uses.map((u) => `<span class="note">${esc(u.for)} Needed by ${esc(u.line)}: ${esc(u.quests)}. The story needs this person ${esc(u.keep)}.${u.changed?.length ? ` <em>Changed by you: ${esc(u.changed.map((c) => c.what).join('; '))}</em>` : ''}</span>`).join('')}</span></li>`);
        const b = el('<button class="quiet">Show</button>'); b.onclick = () => this.showPerson(pid); li.append(b);
        ol.append(li);
      }
      parts.push(ol);
    }
    P.show('What the story needs of this place', parts);
  }
  row(n) {
    const li = el(`<li data-met="${n.met}"><span class="what"><strong>${esc(n.thing)}</strong>
      <span class="note">Needed by ${esc(n.line)}: ${esc(n.quests)}${n.first_draft ? ' (a first draft of the story)' : ''}.</span>
      <span class="need-line"><b>What the player does there</b> ${esc(n.does)}</span>
      <span class="need-line"><b>How a player would know it</b> ${esc(n.know)}</span>
      <span class="need-line"><b>${n.met ? 'What meets it' : 'What is there now'}</b> ${esc(n.why.replace(/^(Not met|Met)\.\s*/, ''))}</span>
      ${n.fit ? `<span class="need-line"><b>What the story could use instead</b> ${esc(n.fit)}</span>` : ''}
      ${n.narrow ? `<span class="need-line"><b>Could a small change close the gap</b> ${esc(n.narrow)}</span>` : ''}
      ${n.sight ? `<span class="need-line"><b>A fresh reader, shown only what a player sees</b> ${n.sight.result === 'recognised' ? 'knew it' : 'did not know it'}${n.sight.said ? `: "${esc(n.sight.said)}"` : ''}</span>` : ''}
      ${(n.changed || []).map((c) => `<span class="need-line changed"><b>Changed by you</b> ${esc(c.what)} (${esc(new Date(c.at).toLocaleDateString())}). The story will be changed to fit.</span>`).join('')}
      </span></li>`);
    const btns = el('<div class="row"></div>');
    if (n.rests && (n.rests.ref || n.rests.person || (n.rests.space && n.rests.space !== 'exterior'))) {
      const b = el(`<button class="${n.met ? 'primary' : 'quiet'}">${n.met ? 'Show it' : 'Show what could serve'}</button>`);
      b.onclick = () => this.showNeed(n); btns.append(b);
    }
    if (!n.met) {
      const b = el('<button class="quiet">Leave a note for the agent about this</button>');
      b.onclick = () => {
        const P = this.a.panels;
        P.noteDraft = `About what the story needs, "${n.thing}": `;
        P.noteAbout = false; P.name = 'notes'; this.a.tools.markRail('notes'); P.notesPanel();
      };
      btns.append(b);
    }
    li.append(btns);
    return li;
  }
  // ---------- show a need's thing or person in the view ----------
  toTop() { const b = document.getElementById('panel-body'); if (b) b.scrollTop = 0; }
  outside() { const a = this.a; if (a.ours.space !== 'exterior') a.leave(a.ours, 0); }
  showNeed(n) {
    const r = n.rests || {};
    if (r.person) return this.showPerson(r.person);
    const id = r.ref || this.a.spaceInfo?.[r.space]?.door_from;
    if (id) this.showRef(id);
  }
  showRef(id) {
    const a = this.a; this.outside();
    const r = a.model.spaces.exterior?.refs.get(id); if (!r) { a.toast('That thing is no longer in the place.'); return; }
    a.tools.use('select'); a.selection = new Set([id]); a.tools.selectionChanged(); this.toTop();
    const p = r.pos; a.ours.view.rig.pitch = Math.max(a.ours.view.rig.pitch, 0.7); a.ours.view.frame([p[0] - 900, p[1] - 900, p[0] + 900, p[1] + 900, p[2]]);
  }
  showPerson(pid) {
    const a = this.a, p = a.model.people.get(pid); if (!p) { a.toast('That person is no longer in the place.'); return; }
    this.outside(); a.tools.use('people'); a.people.select(pid); this.toTop();
    const w = p.work || {};
    let at = w.space === 'exterior' && w.pos ? w.pos : null;
    if (!at && w.space) { const d = a.model.spaces.exterior?.refs.get(a.spaceInfo?.[w.space]?.door_from); at = d?.pos; }
    if (!at) { const m = a.people.markers.get(pid); at = m?.userData.at; }
    if (at) { const z = at[2] ?? a.terrain?.heightAt(at[0], at[1]) ?? 0; a.ours.view.frame([at[0] - 900, at[1] - 900, at[0] + 900, at[1] + 900, z]); }
  }
  // ---------- the line in the Selected and People panels ----------
  lineFor(key, who) {
    const us = this.idx.get(key) || [];
    if (!us.length && !who) return null;
    const box = el('<div class="need-card"></div>');
    if (who) box.append(el(`<p><strong>Who this is to a player</strong><br>${esc(who)}</p>`));
    for (const u of us) box.append(el(`<p class="need-says"><strong>A quest needs this:</strong> ${esc(this.sentence(u))}</p>`));
    return box;
  }
  refLine(r) { return this.lineFor(`ref:${r.id}`); }
  personLine(pid) { return this.lineFor(`person:${pid}`, this.data?.people?.[pid]?.who); }
  // ---------- the warning ----------
  afterPush(ops) {
    if (!this.data || !ops?.length) return;
    const hits = needChanges(ops, this.idx);
    if (hits.length) this.warn(hits);
  }
  warn(hits) {
    const a = this.a, o = document.getElementById('needwarn');
    const items = hits.map((h) => {
      const what = h.u.kind === 'use' ? h.u.person.name : h.u.n.thing, why = h.u.kind === 'use' ? h.u.use.for : h.u.n.does;
      const by = h.u.kind === 'use' ? `${h.u.use.line}: ${h.u.use.quests}` : `${h.u.n.line}: ${h.u.n.quests}`;
      return `<li><strong>${esc(what)}</strong> (just ${esc(h.what)}). ${esc(why)} Needed by ${esc(by)}.</li>`;
    }).join('');
    o.innerHTML = `<div class="sheet" role="alertdialog" aria-labelledby="needwarn-h"><h2 id="needwarn-h">A quest needs this</h2>
      <ul class="plain">${items}</ul>
      <p>If you change it, that quest will be changed to fit. Carry on?</p>
      <div class="row"><button class="primary" data-go>Carry on</button><button class="quiet" data-undo>Undo this change</button></div></div>`;
    o.hidden = false;
    o.querySelector('[data-go]').focus();
    o.querySelector('[data-go]').onclick = async () => {
      o.hidden = true;
      const save = 'autosave';   // the change is in the unsaved edits until a named save
      for (const h of hits) {
        const body = h.u.kind === 'use' ? { person: h.u.pid } : { need: h.u.n.seq };
        try { await api.needChanged(a.place.place_id, { ...body, change: h.change, what: `${this.subject(h.key, h.row)}: ${h.what}`, save }); } catch (e) { a.toast(`Your change stands, but the note for the story was not kept: ${e.message}`, 7000); return; }
      }
      a.toast('Your change stands. The story will be changed to fit it.', 5000);
      await this.load(a.place.place_id);
      if (a.panels.name === 'needs') this.panel();
    };
    o.querySelector('[data-undo]').onclick = () => { o.hidden = true; a.log.undo(); };
  }
  // what in the place a change touched, in words: a person's name, or a thing's name and kind
  subject(key, row = null) {
    const [kind, id] = key.split(/:(.*)/s), a = this.a;
    if (kind === 'person') return a.model.people.get(id)?.name || this.data?.people?.[id]?.name || 'a person';
    let r = row?.base ? row : null;
    if (!r) for (const s of Object.values(a.model.spaces)) r = s.refs.get(id) || r;
    const b = r ? a.bases.get(r.base) || {} : {};
    const leads = r?.door?.to_space ? a.spaceInfo?.[r.door.to_space]?.name : null;
    return leads ? `the door into "${leads}"` : (b.name ? `the ${b.name.toLowerCase()}` : 'a thing');
  }
  // ---------- as the player sees it: the names the game shows ----------
  setNames(on) {
    this.names = on;
    const b = document.getElementById('player-names'); if (b) b.setAttribute('aria-pressed', String(on));
    this.drawNames();
  }
  layer() {
    const v = this.a.ours.view; let s = v.el.querySelector('.names-layer');
    if (!s) { s = document.createElementNS(NS, 'svg'); s.setAttribute('class', 'sketch names-layer'); v.el.append(s); }
    return s;
  }
  cameraMoved(view) { if (this.names && view === this.a.ours.view && !this._due) { this._due = true; requestAnimationFrame(() => { this._due = false; this.drawNames(); }); } }
  drawNames() {
    const a = this.a, v = a.ours.view, svg = this.layer(); svg.innerHTML = '';
    const banner = v.el.querySelector('.names-banner'); if (banner) banner.remove();
    if (!this.names || !a.model) return;
    const S = a.ours.space, refs = [...(a.model.spaces[S]?.refs.values() || [])];
    const t = v.rig.target, o = a.ours.origin, labels = [];
    const near = (p) => Math.hypot(p[0] - o[0] - t.x, p[1] - o[1] - t.y) < Math.max(NAMES_REACH, v.rig.dist * 1.2);
    for (const r of refs) {
      const base = a.bases.get(r.base) || {};
      let text = null, cls = 'thing';
      if (r.map_marker?.Name) { text = `Map: ${r.map_marker.Name}`; cls = 'marker'; }
      else if (r.door?.to_space && r.door.to_space !== 'exterior') { text = `Door: ${a.spaceInfo?.[r.door.to_space]?.name || '(shows no name)'}`; cls = 'door'; }
      else if (r.door?.to_space === 'exterior' && S !== 'exterior') { text = 'Door: Outside'; cls = 'door'; }
      else if (base.name && NAMED_KINDS.has(r.kind || base.kind) && near(r.pos)) text = base.name;
      if (!text) continue;
      if (cls !== 'marker' && !near(r.pos)) continue;
      const q = v.toScreen([r.pos[0], r.pos[1], r.pos[2] + (cls === 'thing' ? 60 : 260)]);
      if (q.behind || q.x < 0 || q.y < 0 || q.x > v.el.clientWidth || q.y > v.el.clientHeight) continue;
      labels.push({ q, text, cls });
    }
    for (const L of labels.slice(0, 160)) {
      const e = document.createElementNS(NS, 'text'); e.setAttribute('class', `game-name ${L.cls}`); e.setAttribute('x', L.q.x); e.setAttribute('y', L.q.y);
      e.setAttribute('text-anchor', 'middle'); e.textContent = L.text; svg.append(e);
    }
    const room = S === 'exterior' ? null : (a.spaceInfo?.[S]?.name || null);
    const b = el(`<div class="names-banner" role="status">As the player sees it: the names the game shows${S === 'exterior' ? '' : `. This room: ${room ? `"${esc(room)}"` : 'shows no name'}`}. People's names are shown as they always are.</div>`);
    v.el.append(b);
  }
}
