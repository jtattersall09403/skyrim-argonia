// Offline: one place held on this device, edited with no connection, sent when the owner chooses
// (docs/design/place-studio.md, Offline). The pure store and the send; offline_ui.js is what the owner sees.
//
// Where things are kept on the device:
// - the Cache API: the app's files ("studio-shell-<version>") and each held place's every file and answer
//   ("studio-place-<place>-<n>"), as the manifest GET /api/place/<id>/offline lists them; the service worker (sw.js)
//   serves them when the build machine cannot be reached;
// - IndexedDB "argonia-studio": `held` (each held place: its cache, its stamps, its place row, size, when),
//   `saves` (each save written offline: the body, the server rev it was based on, a token per version), `notes` (each
//   note for the agent written offline, by its client id), `changes` (the owner's "carry on" past a need's warning)
//   and `meta` (the store's own version). Nothing in it is deleted until the server has confirmed it stored it.
const DB = 'argonia-studio', SCHEMA = 1, META = 'studio-meta', STATE_KEY = '/__studio/state';
const API = (globalThis.STUDIO_API || '') + '/api';

export class Unavailable extends Error {}   // a thing that needs the build machine, said plainly; never an error state

// ---------- IndexedDB, small ----------
let dbp = null;
function db() {
  if (!dbp) dbp = new Promise((res, rej) => {
    const r = indexedDB.open(DB, SCHEMA);
    r.onupgradeneeded = () => {
      const d = r.result;
      if (!d.objectStoreNames.contains('held')) d.createObjectStore('held', { keyPath: 'place_id' });
      if (!d.objectStoreNames.contains('saves')) d.createObjectStore('saves', { keyPath: ['place_id', 'save_id'] });
      if (!d.objectStoreNames.contains('notes')) d.createObjectStore('notes', { keyPath: 'client_id' });
      if (!d.objectStoreNames.contains('changes')) d.createObjectStore('changes', { keyPath: 'client_id' });
      if (!d.objectStoreNames.contains('meta')) d.createObjectStore('meta', { keyPath: 'key' });
    };
    r.onsuccess = () => { const d = r.result; d.onversionchange = () => { d.close(); dbp = null; }; res(d); };
    r.onerror = () => rej(r.error); r.onblocked = () => rej(new Error('the offline store is open in an older tab: close it'));
  });
  return dbp;
}
async function tx(store, mode, fn) {
  const d = await db();
  return new Promise((res, rej) => {
    const t = d.transaction(store, mode), s = t.objectStore(store); let out;
    Promise.resolve(fn(s)).then((v) => { out = v; });
    t.oncomplete = () => res(out); t.onerror = () => rej(t.error); t.onabort = () => rej(t.error || new Error('aborted'));
  });
}
const req2p = (r) => new Promise((res, rej) => { r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
export const idb = {
  get: (store, key) => tx(store, 'readonly', (s) => req2p(s.get(key))),
  all: (store) => tx(store, 'readonly', (s) => req2p(s.getAll())),
  put: (store, v) => tx(store, 'readwrite', (s) => { s.put(v); }),
  del: (store, key) => tx(store, 'readwrite', (s) => { s.delete(key); }),
};

const uid = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`).replace(/[^A-Za-z0-9._-]/g, '');
const nowIso = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');

// ---------- the mode: online, or offline (and why) ----------
export const off = {
  active: false,       // true: every write is kept on this device; reads come from what is held
  why: null,           // 'net' (no connection), 'down' (the build machine is stopped or not answering), 'signed-out'
  status: null,        // the server's /api/status when it answered
  listeners: new Set(),
  providers: {},       // set by the studio: bases() for the search, items() for the item search, terrain() for seat
  on(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); },
  emit(what) { for (const f of this.listeners) try { f(what); } catch (e) { console.error(e); } },

  // Can the build machine be reached, and is the sign-in still good? Never cached, never answered by the worker.
  async probe(ms = 5000) {
    const ac = new AbortController(), t = setTimeout(() => ac.abort(), ms);
    try {
      const r = await fetch(`${API}/status`, { headers: { 'X-Studio-Probe': '1' }, cache: 'no-store', redirect: 'manual', credentials: 'same-origin', signal: ac.signal });
      if (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403) return { state: 'signed-out' };
      if (!r.ok) return { state: 'down' };
      const j = await r.json().catch(() => null);
      return j && j.versions ? { state: 'online', status: j } : { state: (r.headers.get('content-type') || '').includes('html') ? 'signed-out' : 'down' };
    } catch { return { state: navigator.onLine === false ? 'net' : 'down' }; } finally { clearTimeout(t); }
  },

  // At the page's start: which mode, before anything is fetched. A device that holds no place is online as before.
  async boot() {
    const held = await this.heldList().catch(() => []);
    const p = await this.probe();
    if (p.state === 'online') { this.status = p.status; await this.setMode(false); return { held, online: true }; }
    if (held.length) { this.why = p.state === 'signed-out' ? 'signed-out' : p.state; await this.setMode(true); }
    return { held, online: false };
  },
  async setMode(offline, why) {
    this.active = !!offline; if (why) this.why = why; if (!offline) this.why = null;
    await this.tellWorker();
    this.emit('mode');
  },
  async tellWorker() {
    const held = await this.heldList().catch(() => []);
    const st = { mode: this.active ? 'offline' : 'online', shell: held.find((h) => h.shell)?.shell || null, held: held.map((h) => ({ place_id: h.place_id, cache: h.cache })) };
    try { await (await caches.open(META)).put(STATE_KEY, new Response(JSON.stringify(st), { headers: { 'Content-Type': 'application/json' } })); } catch { /* no Cache API: nothing held */ }
    navigator.serviceWorker?.controller?.postMessage({ type: 'state', state: st });
    return st;
  },

  // ---------- held places ----------
  async heldList() { if (!('indexedDB' in globalThis)) return []; return (await idb.all('held')) || []; },
  async heldFor(pid) { return (await idb.get('held', pid)) || null; },

  // Take a place offline (or update it): everything the manifest lists, into a new cache; the old copy is dropped
  // only when the new one is whole. progress({done, of, bytes, total, phase}).
  async download(place, progress = () => {}, { signal } = {}) {
    if (!('caches' in globalThis) || !('serviceWorker' in navigator)) throw new Unavailable('This browser cannot keep pages for use offline (it has no service workers or Cache API).');
    progress({ phase: 'list', done: 0, of: 0, bytes: 0, total: 0 });
    const t0 = performance.now();
    const r = await fetch(`${API}/place/${place.place_id}/offline`, { credentials: 'same-origin', cache: 'no-store' });
    if (!r.ok) throw new Error(`the list of what ${place.title || place.place_id} needs could not be read (${r.status})`);
    const man = await r.json();
    place = { ...place, stamps: { ...(place.stamps || {}), draft: man.stamps.draft ? { ...(place.stamps?.draft || {}), key: man.stamps.draft } : place.stamps?.draft } };
    const total = man.bytes, persisted = await (navigator.storage?.persist?.().catch(() => false)) ?? false;
    const est = await navigator.storage?.estimate?.().catch(() => null);
    const before = await this.heldFor(place.place_id);
    const free = est?.quota != null ? est.quota - (est.usage || 0) + (before?.bytes || 0) : null;
    if (free != null && free < total * 1.1) {
      throw new Unavailable(`There is not enough room: ${place.title || place.place_id} needs about ${mb(total)}, and this browser offers ${mb(Math.max(0, free))} more. Remove another place held offline, or free space on the tablet, then try again.`);
    }
    await this.register();
    const shellName = `studio-shell-${man.web}`, cacheName = `studio-place-${place.place_id}-${Date.now().toString(36)}`;
    const shell = await caches.open(shellName), cache = await caches.open(cacheName);
    const files = man.files, of = files.length; let done = 0, bytes = 0, failed = [];
    progress({ phase: 'files', done, of, bytes, total, persisted });
    const one = async (f) => {
      const into = f.kind === 'app' ? shell : cache;
      for (let i = 0; i < 3; i++) {
        if (signal?.aborted) throw new Error('stopped');
        try {
          const res = await fetch(f.url, { credentials: 'same-origin', cache: 'no-store' });
          if (!res.ok && res.status !== 404) throw new Error(String(res.status));
          // streamed straight into the cache (the page never holds the bytes); the size is the manifest's
          await into.put(f.url, res);
          bytes += f.bytes; return;
        } catch (e) { if (i === 2 || e.name === 'QuotaExceededError') { failed.push({ url: f.url, why: e.name === 'QuotaExceededError' ? 'the browser ran out of room' : e.message }); return; } }
      }
    };
    const queue = files.slice(); const workers = [];
    for (let w = 0; w < 6; w++) workers.push((async () => { while (queue.length) { await one(queue.shift()); done++; progress({ phase: 'files', done, of, bytes, total, persisted }); } })());
    await Promise.all(workers);
    if (failed.length) {
      await caches.delete(cacheName);
      const room = failed.some((f) => /room/.test(f.why));
      throw new Unavailable(room ? `The browser ran out of room part way, so ${place.title || place.place_id} is not held offline. Free some space and try again.`
        : `${failed.length} of ${of} files could not be fetched (the first: ${failed[0].url}, ${failed[0].why}), so the place is not held offline. Try again.`);
    }
    const rec = { place_id: place.place_id, title: place.title || place.place_id, cache: cacheName, shell: shellName, web: man.web, stamps: man.stamps,
      place, bytes, files: of, at: nowIso(), seconds: Math.round((performance.now() - t0) / 100) / 10, persisted, schema: SCHEMA };
    await idb.put('held', rec);
    for (const h of await this.heldList()) if (h.shell !== shellName) await idb.put('held', { ...h, shell: shellName, web: man.web });
    if (before?.cache && before.cache !== cacheName) await caches.delete(before.cache);
    await this.dropUnused();
    await this.tellWorker();
    this.emit('held');
    return rec;
  },
  async remove(pid) {
    const h = await this.heldFor(pid); if (!h) return;
    await idb.del('held', pid); await caches.delete(h.cache); await this.dropUnused(); await this.tellWorker();
    if (!(await this.heldList()).length) await this.unregister();
    this.emit('held');
  },
  // Caches no held place names (an update stopped part way, an older app) are deleted.
  async dropUnused() {
    const held = await this.heldList(), keep = new Set([META, ...held.map((h) => h.cache), ...held.map((h) => h.shell)]);
    for (const k of await caches.keys()) if (k.startsWith('studio-') && !keep.has(k)) await caches.delete(k);
  },
  // The app's own files at a new version, for every held place (the bundles are not touched).
  async updateShell(web) {
    const r = await fetch(`${API}/place/${(await this.heldList())[0]?.place_id}/offline`, { credentials: 'same-origin', cache: 'no-store' });
    if (!r.ok) return false;
    const man = await r.json(), name = `studio-shell-${man.web}`, c = await caches.open(name);
    for (const f of man.files.filter((x) => x.kind === 'app')) {
      const res = await fetch(f.url, { credentials: 'same-origin', cache: 'no-store' });
      if (!res.ok) { await caches.delete(name); return false; }
      await c.put(f.url, new Response(await res.blob(), { status: 200, headers: plainHeaders(res.headers) }));
    }
    for (const h of await this.heldList()) await idb.put('held', { ...h, shell: name, web: man.web });
    await this.dropUnused(); await this.tellWorker();
    return man.web === web || !web;
  },
  async register() {
    if (!navigator.serviceWorker) return;
    await navigator.serviceWorker.register(new URL('../sw.js', import.meta.url).pathname, { scope: '/' });
    await navigator.serviceWorker.ready;
  },
  async unregister() {
    for (const r of await navigator.serviceWorker?.getRegistrations?.() || []) await r.unregister();
  },

  // ---------- writes kept on this device ----------
  // A save written offline: kept whole; `base_rev` is the server's rev it was based on (the rev the tab had read),
  // and the answer keeps that rev, so the tab goes on writing at it. Every version has its own token.
  async putSave(pid, sid, body) {
    const was = await idb.get('saves', [pid, sid]);
    if (was?.final) return { conflict: true, error: 'this save is final' };
    const rec = { place_id: pid, save_id: sid, body: { ...body }, base_rev: was ? was.base_rev : Number(body.rev || 0),
      token: uid(), at: nowIso(), local_rev: (was?.local_rev || 0) + 1, final: !!body.final };
    await idb.put('saves', rec); this.emit('work');
    return { save_id: sid, rev: Number(body.rev || 0), at: rec.at, kept: 'tablet' };
  },
  async localSaves(pid) { return ((await idb.all('saves')) || []).filter((s) => !pid || s.place_id === pid); },
  async localSave(pid, sid) {
    const s = await idb.get('saves', [pid, sid]);
    return s ? { ...s.body, save_id: sid, place_id: pid, rev: s.base_rev, at: s.at, tablet: true } : null;
  },
  // The saves list as the server last gave it, with this device's own over it.
  async mergeSaves(pid, server) {
    const list = [...(server || [])], local = await this.localSaves(pid);
    for (const s of local) {
      const row = { save_id: s.save_id, name: s.body.name, at: s.at, rev: s.base_rev, final: !!s.final, ops: (s.body.ops || []).length,
        kept: 'tablet', base: s.body.base };
      const i = list.findIndex((x) => x.save_id === s.save_id);
      if (i >= 0) list[i] = row; else list.push(row);
    }
    return list;
  },
  async note(pid, body) {
    if (body.id && !String(body.id).startsWith('t-')) throw new Unavailable('This note is kept on the build machine; changing it needs the connection. Notes written on this tablet can be changed here.');
    if (body.id) {
      const n = await idb.get('notes', body.id); if (!n) throw new Unavailable('That note is no longer on this tablet.');
      if (body.delete) { await idb.del('notes', body.id); this.emit('work'); return { id: body.id, deleted: true }; }
      if ('text' in body) { n.text = String(body.text).trim(); await idb.put('notes', n); this.emit('work'); return asNote(n); }
      throw new Unavailable('A note is closed by the agent once it is sent.');
    }
    const n = { client_id: `t-${uid()}`.slice(0, 64), place_id: pid, text: String(body.text || '').trim(), things: body.things || [], view: body.view || null,
      save: body.save || null, at: nowIso() };
    if (!n.text) throw new Error('a note needs some words');
    await idb.put('notes', n); this.emit('work');
    return asNote(n);
  },
  async localNotes(pid) { return ((await idb.all('notes')) || []).filter((n) => !pid || n.place_id === pid); },
  async mergeNotes(pid, server) { return [...(server || []), ...(await this.localNotes(pid)).map(asNote)]; },
  async needChanged(pid, body) {
    const c = { client_id: `t-${uid()}`.slice(0, 64), place_id: pid, body: { ...body }, at: nowIso() };
    await idb.put('changes', c); this.emit('work'); return c;
  },
  async localChanges(pid) { return ((await idb.all('changes')) || []).filter((c) => !pid || c.place_id === pid); },
  // What this device holds that the server has not confirmed: {saves, notes, changes, n}.
  async unsent(pid) {
    const [saves, notes, changes] = await Promise.all([this.localSaves(pid), this.localNotes(pid), this.localChanges(pid)]);
    return { saves, notes, changes, n: saves.length + notes.length + changes.length };
  },

  // ---------- sending: saves through the PUT and its rev rule, notes as unsent notes ----------
  // decide(conflict) is asked for each save the server moved on meanwhile: 'keep' (a new named save) or 'drop'.
  // Each item leaves this device only once the server has answered that it is stored; a send stopped part way is
  // sent again from where it stopped, and an item sent twice is stored once (its token or client id).
  async send(pid, { decide, progress = () => {} } = {}) {
    const u = await this.unsent(pid), out = { saved: [], kept: [], dropped: [], notes: 0, changes: 0, left: 0, stopped: null };
    const put = async (sid, body) => {
      const r = await fetch(`${API}/place/${pid}/saves/${encodeURIComponent(sid)}`, { method: 'PUT', credentials: 'same-origin', redirect: 'manual',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403) throw new SignIn();
      const j = await r.json().catch(() => ({}));
      if (r.status === 409) return { conflict: true, ...j };
      if (!r.ok) throw new Error(j.error || `the server answered ${r.status}`);
      return j;
    };
    try {
      // the autosave last: a named save of the same work lands first
      for (const s of [...u.saves].sort((a, b) => (a.save_id === 'autosave') - (b.save_id === 'autosave'))) {
        progress(`Sending ${s.save_id === 'autosave' ? 'your latest work' : `"${s.body.name || s.save_id}"`}`);
        const body = { ...s.body, rev: s.base_rev, client_token: s.token };
        const r = await put(s.save_id, body);
        if (!r.conflict) { await idb.del('saves', [pid, s.save_id]); out.saved.push({ save_id: s.save_id, rev: r.rev }); continue; }
        const choice = decide ? await decide({ save: s, current: r.current || {}, error: r.error }) : 'keep';
        if (choice === 'drop') { await idb.del('saves', [pid, s.save_id]); out.dropped.push(s.save_id); continue; }
        if (choice !== 'keep') { out.left++; continue; }
        const stamp = s.at.replace(/[-:TZ]/g, '').slice(0, 12), sid = `${s.save_id === 'autosave' ? 'offline' : s.save_id}-tablet-${stamp}`.slice(0, 64);
        const name = `${s.save_id === 'autosave' ? 'Offline work' : s.body.name || s.save_id} (from the tablet, ${new Date(s.at).toLocaleString()})`;
        const k = await put(sid, { ...body, save_id: sid, name, rev: 0, client_token: `${s.token}.kept` });
        if (k.conflict) { out.left++; continue; }
        await idb.del('saves', [pid, s.save_id]); out.kept.push({ from: s.save_id, save_id: sid, name, rev: k.rev });
      }
      for (const n of u.notes) {
        progress('Sending your notes');
        const r = await fetch(`${API}/place/${pid}/notes`, { method: 'POST', credentials: 'same-origin', redirect: 'manual', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: n.text, things: n.things, view: n.view, save: n.save || undefined, client_id: n.client_id, written_at: n.at }) });
        if (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403) throw new SignIn();
        if (!r.ok) throw new Error(`a note was not kept (${r.status})`);
        await idb.del('notes', n.client_id); out.notes++;
      }
      for (const c of u.changes) {
        const r = await fetch(`${API}/place/${pid}/needs/changed`, { method: 'POST', credentials: 'same-origin', redirect: 'manual', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...c.body, client_id: c.client_id }) });
        if (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403) throw new SignIn();
        if (r.ok || r.status === 400) { await idb.del('changes', c.client_id); out.changes++; } else throw new Error(`a story change was not kept (${r.status})`);
      }
    } catch (e) {
      out.stopped = e instanceof SignIn ? 'Your sign-in to the studio has run out. Sign in again to send; nothing has been lost.' : `The send stopped: ${e.message}. What was not sent is still on this tablet; send again to carry on.`;
      out.signin = e instanceof SignIn;
    }
    out.left = (await this.unsent(pid)).n;
    this.emit('work');
    return out;
  },

  // ---------- what the server would answer, done here from what is held ----------
  search(q) {
    const words = String(q.q || '').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
    const kinds = q.kind ? new Set(String(q.kind).split(',')) : null, lim = Number(q.limit) || 40;
    const seen = new Set(), out = [];
    for (const b of this.providers.bases?.() || []) {
      if (!b?.key || seen.has(b.key) || (kinds && !kinds.has(b.kind))) continue; seen.add(b.key);
      const name = (b.name || '').toLowerCase(), edid = (b.edid || '').toLowerCase();
      const text = `${name} ${edid.replace(/([a-z])([A-Z0-9])/g, '$1 $2')} ${(b.model || '').toLowerCase()} ${b.kind || ''}`.toLowerCase();
      let score = 0;
      for (const w of words) { if (text.includes(w)) score += 1; else { score = -1; break; } }
      if (score < 0 || !words.length) continue;
      if (name === words.join(' ') || edid === words.join('')) score += 5;
      if (name.startsWith(words[0]) || edid.startsWith(words[0])) score += 1;
      out.push({ key: b.key, edid: b.edid, name: b.name, model: b.model, type: b.type, kind: b.kind, nordic: !!b.nordic, plugin: b.plugin, score,
        thumb: b.model ? `${API}/asset/thumb?model=${encodeURIComponent(b.model)}` : null });
    }
    out.sort((a, b) => b.score - a.score || String(a.name || a.edid).localeCompare(String(b.name || b.edid)));
    return { q: q.q, scope: q.scope, results: out.slice(0, lim), offline: true };
  },
  items(q) {
    const words = String(q.q || '').toLowerCase().split(/\s+/).filter(Boolean), out = [];
    for (const [id, it] of this.providers.items?.() || []) {
      const text = `${it.name || ''} ${it.edid || ''} ${it.kind || ''}`.toLowerCase();
      if (!words.every((w) => text.includes(w))) continue;
      out.push({ id, ...it, allowed: !it.never, why: it.never ? 'never allowed (decision 0006)' : '' });
    }
    return { q: q.q, results: out.slice(0, Number(q.limit) || 30), offline: true };
  },
};
class SignIn extends Error { constructor() { super('signed out'); } }
const asNote = (n) => ({ id: n.client_id, at: n.at, text: n.text, things: n.things || [], view: n.view, sent: false, done: false, tablet: true });
const plainHeaders = (h) => { const o = new Headers(h); o.delete('Content-Encoding'); o.delete('Content-Length'); o.delete('Set-Cookie'); return o; };
export const mb = (b) => (b >= 1e9 ? `${(b / 1e9).toFixed(1)} GB` : `${Math.max(0.1, b / 1e6).toFixed(b >= 1e7 ? 0 : 1)} MB`);
