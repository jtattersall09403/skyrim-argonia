// What a thing holds and who a person is, in the Selected and People panels (docs/design/place-studio.md, Stock):
// a container's, a person's and a trader's things, each with its reason; a thing laid out; a person's identity.
// Every change is a content op pushed to the edit log like any other edit. Nothing here prompts the owner: it is
// there when they look. Item search runs on demand (a few results at a time), never on every frame.
// Each control reads its holder's row as it stands when the owner acts (`get`), so a late event from a panel drawn
// before another edit never carries a stale `before`.
import { api } from './api.js';
import { allowedItem, bandLabel, backstoryOf, containerKind, containerOf, householdOf, identityOf, looseAt, newContainer,
  newPossessions, opFor, OWNER_WHY, possessionsOf, tierLabel, traderOf, withBackstory, withCount, withGold, withItem,
  withLock, withoutItem } from './stock.js';

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function el(html) { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; }
const facts = (rows) => el(`<dl class="facts">${rows.filter(([, v]) => v != null && v !== '').map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`);
const json = (o) => JSON.stringify(o ?? null);
const KIND = { weapon: 'Weapon', armour: 'Armour', jewellery: 'Jewellery', gem: 'Gem', 'soul-gem': 'Soul gem', potion: 'Potion', poison: 'Poison',
  scroll: 'Scroll', key: 'Key', ammunition: 'Arrows or bolts', 'spell-tome': 'Spell tome', 'skill-book': 'Skill book', clothing: 'Clothes', book: 'Book',
  food: 'Food', ingredient: 'Ingredient', 'ingot-or-ore': 'Ore or ingot', hide: 'Hide', 'animal-part': 'Animal part', tool: 'Tool', clutter: 'Odds and ends', light: 'Light' };

export class Contents {
  constructor(panels) { this.panels = panels; this.finds = new Map(); }   // each adder's search, by its holder
  get app() { return this.panels.app; }
  get data() { return this.app.stockData; }
  get scale() { return this.data?.scale || {}; }
  get ceiling() { return this.data?.facts?.ceiling_tier || null; }
  get stock() { return this.app.model.stock; }
  item(id) { return this.app.stockItems?.get(id) || { id, name: id }; }
  itemName(id) { const f = this.item(id); return f.name || f.edid || id; }
  personName(id) { return identityOf(this.app.model.identities, id)?.name || this.app.model.people.get(id)?.name || id; }
  // One change to a holder: its row now, the row after (null takes a laid-out thing away); nothing when unchanged.
  edit(holder, get, make) {
    const cur = get() ?? null;
    if (!cur && holder !== 'possessions') return;
    const after = make(cur);
    if (after === undefined || json(after) === json(cur)) return;
    this.app.push(opFor(holder, cur, after));
  }

  // ---------- the Selected panel: a container, or things laid out on or as the selected ref ----------
  refSection(r, base) {
    const a = this.app, space = a.ours.space;
    if (!this.data || !this.stock) return null;
    const row = containerOf(this.stock, space, r.id), loose = looseAt(this.stock, space, r.id);
    const isContainer = row || r.kind === 'container' || base?.type === 'CONT' || base?.kind === 'container';
    if (!isContainer && !loose.length) return null;
    const w = el('<section class="contents"></section>');
    if (isContainer) w.append(...this.containerParts(r, base, space));
    for (const lo of loose) w.append(...this.looseParts(lo, r));
    return w;
  }
  ownerWords(row) {
    if (row.owner_person) return this.personName(row.owner_person);
    if (row.owner_household) {
      const ids = this.app.model.identities, hh = householdOf(ids, row.owner_household);
      const head = (ids?.people || []).find((p) => p.household?.id === row.owner_household && p.household?.role === 'head');
      return hh?.name || (head ? `${head.name}'s household` : row.owner_household);
    }
    return row.owner_faction || 'Nobody: anyone may take from it';
  }
  containerParts(r, base, space) {
    const get = () => containerOf(this.stock, space, r.id), row = get();
    const parts = [el('<h3>What it holds</h3>')];
    if (!row) {
      const k = containerKind(base, this.scale);
      parts.push(el(k.always
        ? `<p class="tag">Not stocked yet. A ${esc(k.kind.replace(/-/g, ' '))} always matters, so the build keeps only its set dressing until it has a stock list.</p>`
        : '<p class="tag">Set dressing: it keeps what the source put in it.</p>'));
      const b = el('<button class="quiet">Stock this container</button>');
      b.onclick = () => { if (!get()) this.app.push(opFor('container', null, newContainer(r.id, space, k.kind, null))); };
      parts.push(b);
      return parts;
    }
    parts.push(el('<p class="tag">Stocked: every thing in it is chosen, with its reason.</p>'));
    const sec = (this.scale.security || []).find((s) => s.id === row.security);
    parts.push(facts([['Kind', row.kind.replace(/-/g, ' ')], ['Belongs to', this.ownerWords(row)], ['Lock', row.lock || 'No lock'],
      ['Kept', sec ? `${sec.id} ${sec.label}: ${sec.means}` : row.security], ['Best thing in it', tierLabel(this.scale, row.tier)],
      ['Gold', `${row.gold || 0}`], ['Why it holds this', row.why]]));
    parts.push(this.itemList('container', get));
    const ctl = el('<div class="row"></div>');
    const lock = el(`<label class="field">Lock<select aria-label="Lock">${['', ...(this.scale.lock_levels || [])].map((l) => `<option value="${esc(l)}" ${l === (row.lock || '') ? 'selected' : ''}>${esc(l || 'No lock')}</option>`).join('')}</select></label>`);
    lock.querySelector('select').onchange = (e) => this.edit('container', get, (cur) => withLock(cur, e.target.value || null));
    const gold = el(`<label class="field">Gold<input type="number" min="0" step="1" inputmode="numeric" value="${row.gold || 0}" aria-label="Gold in it"></label>`);
    gold.querySelector('input').onchange = (e) => this.edit('container', get, (cur) => withGold(cur, e.target.value));
    ctl.append(lock, gold);
    parts.push(ctl, this.adder('container', get, (cur, id, why) => withItem(cur, id, 1, why), `container:${space}/${r.id}`));
    const off = el('<button class="quiet">Take its stock list away</button>');
    off.onclick = () => { const cur = get(); if (cur) this.app.push({ op: 'stock.container.remove', container: cur }); };
    parts.push(off);
    return parts;
  }
  looseParts(lo, r) {
    const get = () => (this.stock?.loose || []).find((x) => x.id === lo.id), name = this.itemName(lo.item);
    const f = this.item(lo.item), ok = allowedItem(f, this.ceiling, this.scale);
    const parts = [el(`<h3>${lo.id === r.id ? 'This thing' : 'Laid out on it'}</h3>`)];
    const list = el(`<ol class="history stocklist"><li><span class="what">${lo.count} × ${esc(name)}<span class="note">${esc(this.itemNote(f))}</span><span class="note why">Why: ${esc(lo.why)}</span>${lo.owner_person || lo.owner_faction ? `<span class="note">Belongs to ${esc(lo.owner_person ? this.personName(lo.owner_person) : lo.owner_faction)}</span>` : ''}${ok.ok ? '' : `<span class="tag nordic">${esc(ok.why)}</span>`}</span></li></ol>`);
    const row = el('<div class="row"></div>');
    const btn = (t, label, make, dis) => { const b = el(`<button class="quiet" aria-label="${esc(label)}">${t}</button>`); b.disabled = !!dis; b.onclick = () => this.edit('loose', get, make); row.append(b); };
    btn('−', `One fewer ${name}`, (cur) => (cur.count > 1 ? { ...cur, count: cur.count - 1 } : undefined), lo.count <= 1);
    btn('+', `One more ${name}`, (cur) => ({ ...cur, count: cur.count + 1 }));
    btn('Take it away', `Take away ${name}`, () => null);
    list.querySelector('li').append(row);
    parts.push(list);
    return parts;
  }

  // ---------- a holder's things ----------
  itemNote(f) {
    const v = f.value != null ? `${f.value} gold` : 'value not measured yet';
    return [KIND[f.kind] || 'Thing', v, tierLabel(this.scale, f.tier)].join(' · ');
  }
  itemList(holder, get, { worn = false } = {}) {
    const ol = el('<ol class="history stocklist"></ol>'), row = get();
    if (!row?.items?.length) ol.append(el('<li><span class="what">Nothing yet.</span></li>'));
    for (const it of row?.items || []) {
      const f = this.item(it.item), name = this.itemName(it.item), ok = allowedItem(f, this.ceiling, this.scale);
      const li = el(`<li><span class="what">${it.count} × ${esc(name)}${worn && it.worn ? ' (worn)' : ''}<span class="note">${esc(this.itemNote(f))}</span><span class="note why">Why: ${esc(it.why)}</span>${ok.ok ? '' : `<span class="tag nordic">${esc(ok.why)}</span>`}</span></li>`);
      const r = el('<div class="row"></div>');
      const count = (cur) => cur?.items.find((i) => i.item === it.item)?.count;
      const btn = (t, label, make, dis) => { const b = el(`<button class="quiet" aria-label="${esc(label)}">${t}</button>`); b.disabled = !!dis; b.onclick = () => this.edit(holder, get, make); r.append(b); };
      btn('−', `One fewer ${name}`, (cur) => (count(cur) > 1 ? withCount(cur, it.item, count(cur) - 1) : undefined), it.count <= 1);
      btn('+', `One more ${name}`, (cur) => (count(cur) ? withCount(cur, it.item, count(cur) + 1) : undefined));
      btn('Remove', `Remove ${name}`, (cur) => (count(cur) ? withoutItem(cur, it.item) : undefined));
      li.append(r); ol.append(li);
    }
    return ol;
  }
  // Find a thing to add: the place's own item search, results capped; a thing this place may not hold is listed
  // with its reason and refused when tapped.
  adder(holder, get, make, key) {
    if (!this.finds.has(key)) this.finds.set(key, { key, q: '', why: '', results: [] });
    const F = this.finds.get(key), w = el('<div class="adder"></div>');
    const q = el(`<input class="text" type="search" placeholder="Find a thing: sword, ring, potion" aria-label="Find a thing to add" value="${esc(F.q)}">`);
    const why = el(`<input class="text" type="text" placeholder="Why it is here (optional)" aria-label="Why it is here" value="${esc(F.why)}">`);
    const list = el('<ol class="history stocklist results" aria-label="Things found"></ol>');
    const draw = () => {
      list.innerHTML = '';
      if (F.q.trim() && !F.results.length) list.append(el(`<li><span class="what">${F.busy ? 'Looking…' : 'Nothing found by that name.'}</span></li>`));
      for (const res of F.results) {
        const li = el(`<li class="${res.allowed ? '' : 'refused'}"><span class="what">${esc(res.name || res.edid)}<span class="note">${esc(this.itemNote(res))}</span>${res.allowed ? '' : `<span class="tag nordic">${esc(res.why)}</span>`}</span></li>`);
        const b = el(`<button class="quiet" aria-label="Add ${esc(res.name || res.edid)}">Add</button>`);
        b.onclick = () => {
          if (!res.allowed) { this.app.toast(res.why, 6000); return; }
          this.app.stockItems.set(res.id, res);
          const reason = why.value.trim() || OWNER_WHY;
          F.q = ''; F.results = []; F.why = '';
          this.edit(holder, get, (cur) => make(cur, res.id, reason));
        };
        li.append(b); list.append(li);
      }
    };
    let t;
    q.oninput = () => { F.q = q.value; clearTimeout(t); t = setTimeout(() => this.runFind(F, draw), 300); };
    q.onkeydown = (e) => { if (e.key === 'Enter') { clearTimeout(t); this.runFind(F, draw); } };
    why.oninput = () => { F.why = why.value; };
    draw();
    w.append(el('<h3>Add a thing</h3>'), q, why, list);
    return w;
  }
  async runFind(F, draw) {
    if (!F.q.trim()) { F.results = []; draw(); return; }
    const asked = F.q; F.busy = true; draw();
    try { const r = await api.items(this.app.place.place_id, { q: asked, limit: 12 }); if (F.q === asked) F.results = r?.results || []; }
    catch (e) { this.app.toast(`The item search did not answer: ${e.message}`); }
    F.busy = false; draw();
  }

  // ---------- the People panel: who a person is, what they carry, what they sell ----------
  personSection(p) {
    const a = this.app, ids = a.model.identities;
    const getId = () => identityOf(a.model.identities, p.id), idn = getId(), w = el('<section class="contents"></section>');
    if (!this.data || !idn) {
      if (this.data) w.append(el('<p class="tag">This person has no row in the place\'s people list yet.</p>'));
      return w;
    }
    const hh = householdOf(ids, idn.household?.id);
    const home = hh ? (hh.name || a.spaceName(a.ours, hh.home_space)) : null;
    const race = (this.data.lookups?.race || []).find((x) => x.id === idn.race)?.name || idn.race;
    const band = (this.scale.person_wealth_bands || []).find((b) => b.id === idn.wealth);
    w.append(el('<h3>Who they are</h3>'), facts([['Household', home ? `${home}, as ${String(idn.household?.role || '').replace(/-/g, ' ')}` : 'None'],
      ['Race', race], ['Wealth', band ? `${bandLabel(this.scale, idn.wealth)}: ${band.about}` : idn.wealth], ['Status', idn.status !== 'alive' ? idn.status : null]]));
    const set = (fn) => this.edit('identity', getId, (cur) => { const x = JSON.parse(JSON.stringify(cur)); fn(x); return x; });
    const trade = el(`<label class="field">Trade<input type="text" value="${esc(idn.trade)}" aria-label="Trade"></label>`);
    trade.querySelector('input').onchange = (e) => set((x) => { x.trade = e.target.value.trim(); });
    const wealth = el(`<label class="field">Wealth<select aria-label="Wealth">${(this.scale.person_wealth_bands || []).map((b) => `<option value="${b.id}" ${b.id === idn.wealth ? 'selected' : ''}>${esc(bandLabel(this.scale, b.id))}</option>`).join('')}</select></label>`);
    wealth.querySelector('select').onchange = (e) => set((x) => { x.wealth = e.target.value; });
    const story = el(`<label class="field">Backstory<textarea class="text note-text" rows="4" aria-label="Backstory">${esc(backstoryOf(idn))}</textarea></label>`);
    story.querySelector('textarea').onchange = (e) => this.edit('identity', getId, (cur) => withBackstory(cur, e.target.value.trim()));
    w.append(trade, wealth, story);
    const getPos = () => possessionsOf(this.stock, p.id), pos = getPos();
    w.append(el('<h3>What they carry</h3>'));
    if (pos?.why) w.append(el(`<p class="note">${esc(pos.why)}</p>`));
    w.append(this.itemList('possessions', getPos, { worn: true }));
    w.append(this.adder('possessions', getPos, (cur, id, why) => withItem(cur || newPossessions(p.id), id, 1, why), `possessions:${p.id}`));
    const getTr = () => traderOf(this.stock, p.id), tr = getTr();
    if (tr) {
      w.append(el('<h3>What they sell</h3>'), facts([['Gold to trade with', `${tr.gold}`], ['Why', tr.why]]));
      const g = el(`<label class="field">Trader's gold<input type="number" min="0" step="1" inputmode="numeric" value="${tr.gold}" aria-label="Trader's gold"></label>`);
      g.querySelector('input').onchange = (e) => this.edit('trader', getTr, (cur) => withGold(cur, e.target.value));
      w.append(g, this.itemList('trader', getTr), this.adder('trader', getTr, (cur, id, why) => withItem(cur, id, 1, why), `trader:${p.id}`));
    }
    return w;
  }
  // A new name is the people list's (the identity) and the placed person's alike, in one change.
  rename(p, name) {
    const cur = this.app.model.people.get(p.id) || p;
    name = name.trim(); if (!name || name === cur.name) return;
    const idn = identityOf(this.app.model.identities, p.id), ops = [];
    if (idn && idn.name !== name) ops.push(opFor('identity', idn, { ...JSON.parse(JSON.stringify(idn)), name }));
    ops.push({ op: 'person.edit', person: { ...JSON.parse(JSON.stringify(cur)), name }, before: JSON.parse(JSON.stringify(cur)) });
    this.app.push(ops.length > 1 ? ops : ops[0]);
  }
}
