// The Studio API (docs/design/place-studio.md): the only thing the front end talks to. Offline (offline.js), every
// write is kept on this device and every read comes from what it holds; what needs the build machine says so.
import { off, Unavailable } from './offline.js';
import { seatAt } from './seat.js';
const BASE = (globalThis.STUDIO_API || '') + '/api';
export const API_BASE = BASE;

async function req(path, opts = {}) {
  const r = await fetch(BASE + path, { credentials: 'same-origin', ...opts });
  if (r.status === 404 && opts.optional) return null;
  if (!r.ok && r.status !== 202) throw new Error(`${opts.method || 'GET'} ${path}: ${r.status}`);
  return r;
}
export const getJSON = async (p, o) => { const r = await req(p, o); return r ? r.json() : null; };
export async function getText(p, o) { const r = await req(p, o); return r ? r.text() : null; }
export async function getBuffer(p, o) { const r = await req(p, o); return r ? r.arrayBuffer() : null; }
export function parseJsonl(text) {
  if (!text) return [];
  return text.split('\n').filter((l) => l.trim()).map((l) => JSON.parse(l));
}
export const getJsonl = async (p, o) => parseJsonl(await getText(p, o));

// A converted mesh: the server may answer 202 + Retry-After while it converts; wait and ask again.
// `alt`: a base key whose alternate textures make its own variant of the model (the base's alt_tex).
export async function getMesh(model, { tries = 30, signal, level = 0, alt = null } = {}) {
  const extra = alt ? `&alt=${encodeURIComponent(alt)}` : '';
  for (let i = 0; i < tries; i++) {
    const r = await fetch(`${BASE}/asset/mesh?model=${encodeURIComponent(model)}&level=${level}${extra}`, { signal, credentials: 'same-origin' });
    if (r.status === 200) return r.arrayBuffer();
    if (r.status !== 202) throw new Error(`mesh ${model}: ${r.status}`);
    const wait = Math.min(10, Number(r.headers.get('Retry-After')) || 1) * 1000;
    await new Promise((res) => setTimeout(res, wait));
  }
  throw new Error(`mesh ${model}: still converting`);
}
export const texUrl = (path, size = 256) => `${BASE}/asset/tex?path=${encodeURIComponent(path)}&size=${size}`;

const NEEDS_MACHINE = {
  finalise: 'Finalising needs the build machine. Your work is kept on this tablet: when you are back online, send it and finalise from the Offline panel.',
  sendNotes: 'Sending notes to the agent needs the build machine. Your notes are kept on this tablet and go with your offline work when you send it.',
  run: 'A finalise run can only be followed online.',
  useVariant: 'Choosing which draft is the place needs the build machine: do it when you are back online.',
};
const isNetFail = (e) => e instanceof TypeError || /: 5\d\d$/.test(String(e?.message));
const online = {
  places: () => getJSON('/places'),
  status: () => getJSON('/status'),
  search: (q) => getJSON('/search?' + new URLSearchParams(q)),
  saves: (id) => getJSON(`/place/${id}/saves`),
  save: (id, sid) => getJSON(`/place/${id}/saves/${encodeURIComponent(sid)}`),
  // 200 {save_id, rev, at, kept}; 409 {error, current} when another tab moved the save on or it is final.
  async putSave(id, sid, body) {
    const r = await fetch(`${BASE}/place/${id}/saves/${encodeURIComponent(sid)}`, {
      method: 'PUT', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (r.status === 409) return { conflict: true, ...j };
    if (!r.ok) throw Object.assign(new Error(j.error || `saving: ${r.status}`), { status: r.status });
    return j;
  },
  finalise: (id, save_id) => getJSON(`/place/${id}/finalise`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ save_id }) }),
  run: (id, rid) => getJSON(`/place/${id}/runs/${rid}`),
  // "Use this version": a variant draft becomes its place (tools/places/variant.py use); {place_id, said}
  async useVariant(id) {
    const r = await fetch(`${BASE}/place/${id}/variant/use`, { method: 'POST', credentials: 'same-origin' });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || `using the draft: ${r.status}`);
    return j;
  },
  seat: (id, x, y) => getJSON(`/place/${id}/seat?x=${x}&y=${y}`),
  // the built place's walking mesh (tools/places/navexport.py); null when the place has not been built
  nav: (id) => getJSON(`/place/${id}/nav`, { optional: true }),
  // the Walking mesh view's state: {nav: {from, built_at}, files_at, check, run, busy}; null from an older server
  walkmesh: (id) => getJSON(`/place/${id}/walkmesh`, { optional: true }),
  // rebuild the walking mesh from a save (a job): {job} or {error} in plain words (another build runs)
  async rebuildWalk(id, save_id) {
    try {
      const r = await fetch(`${BASE}/place/${id}/walkmesh/rebuild`, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ save_id }) });
      const j = await r.json().catch(() => ({}));
      return r.ok ? j : { error: j.error || `The rebuild could not start (${r.status}).` };
    } catch { return { error: 'The build machine did not answer: the walking mesh can be rebuilt when it is back.' }; }
  },
  notes: (id) => getJSON(`/place/${id}/notes`),
  // what the stories need of the place, in plain words; null when the server has none (an older server)
  needs: (id) => getJSON(`/place/${id}/needs`, { optional: true }),
  // the things the quests put at the place, when each is in the world, its spot and its story explorer links; null
  // when the server has none (an older server)
  quests: (id) => getJSON(`/place/${id}/quests`, { optional: true }),
  // the owner carried on past a need's warning: {need | person, change, what, save}
  needChanged: (id, body) => getJSON(`/place/${id}/needs/changed`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  // who the place's people are and what it holds (the database's sources), with the items' facts and the scale;
  // null when the server has none for the place
  stock: (id) => getJSON(`/place/${id}/stock`, { optional: true }),
  // items by name for adding to a holder: each says whether this place may hold it, and why not
  items: (id, q) => getJSON(`/place/${id}/items?` + new URLSearchParams(q)),
  // add a note ({text, things, view, save}); change ({id, text}) or delete ({id, delete: true}) one not sent yet;
  // close or reopen a sent one ({id, done})
  note: (id, body) => getJSON(`/place/${id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  // every unsent note to the agent as one batch, which starts it: {batch, sent, job}
  sendNotes: (id) => getJSON(`/place/${id}/notes/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }),
  heartbeat: () => fetch(BASE + '/heartbeat', { method: 'POST', credentials: 'same-origin', keepalive: true }).catch(() => {}),
};
// Offline: writes to this device, reads from what it holds (the service worker answers the plain reads).
const tablet = {
  async places() {
    const held = await off.heldList(), list = await getJSON('/places').catch(() => []);
    return held.map((h) => ({ ...(list.find((p) => p.place_id === h.place_id) || {}), ...h.place }));
  },
  async saves(id) { return off.mergeSaves(id, await getJSON(`/place/${id}/saves`).catch(() => [])); },
  async save(id, sid) { return (await off.localSave(id, sid)) || getJSON(`/place/${id}/saves/${encodeURIComponent(sid)}`); },
  putSave: (id, sid, body) => off.putSave(id, sid, body),
  async notes(id) { return off.mergeNotes(id, await getJSON(`/place/${id}/notes`).catch(() => [])); },
  note: (id, body) => off.note(id, body),
  needChanged: (id, body) => off.needChanged(id, body),
  search: async (q) => off.search(q),
  items: async (id, q) => off.items(q),
  async seat(id, x, y) { const t = off.providers.terrain?.(); if (!t) throw new Unavailable('The ground is not loaded.'); return seatAt(t.terrain, x, y, t.water); },
  heartbeat: async () => {},
};
for (const k of Object.keys(NEEDS_MACHINE)) tablet[k] = async () => { throw new Unavailable(NEEDS_MACHINE[k]); };

export const api = new Proxy(online, {
  get(o, k) {
    if (off.active && k in tablet) return tablet[k];
    if (k === 'putSave') {
      // the connection lost while editing a held place: the save is kept on this device and the studio goes offline
      return async (id, sid, body) => {
        try { return await o.putSave(id, sid, body); }
        catch (e) {
          if (!isNetFail(e) && !(e.status >= 500) || !(await off.heldFor(id))) throw e;
          await off.setMode(true, 'down'); return off.putSave(id, sid, body);
        }
      };
    }
    return o[k];
  },
});
export { off, Unavailable };
