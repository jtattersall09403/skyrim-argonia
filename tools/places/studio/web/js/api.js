// The Studio API (docs/design/place-studio.md): the only thing the front end talks to.
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
export async function getMesh(model, { tries = 30, signal, level = 0 } = {}) {
  for (let i = 0; i < tries; i++) {
    const r = await fetch(`${BASE}/asset/mesh?model=${encodeURIComponent(model)}&level=${level}`, { signal, credentials: 'same-origin' });
    if (r.status === 200) return r.arrayBuffer();
    if (r.status !== 202) throw new Error(`mesh ${model}: ${r.status}`);
    const wait = Math.min(10, Number(r.headers.get('Retry-After')) || 1) * 1000;
    await new Promise((res) => setTimeout(res, wait));
  }
  throw new Error(`mesh ${model}: still converting`);
}
export const texUrl = (path, size = 256) => `${BASE}/asset/tex?path=${encodeURIComponent(path)}&size=${size}`;

export const api = {
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
    if (!r.ok) throw new Error(j.error || `saving: ${r.status}`);
    return j;
  },
  finalise: (id, save_id) => getJSON(`/place/${id}/finalise`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ save_id }) }),
  run: (id, rid) => getJSON(`/place/${id}/runs/${rid}`),
  seat: (id, x, y) => getJSON(`/place/${id}/seat?x=${x}&y=${y}`),
  // the built place's walking mesh (tools/places/navexport.py); null when the place has not been built
  nav: (id) => getJSON(`/place/${id}/nav`, { optional: true }),
  notes: (id) => getJSON(`/place/${id}/notes`),
  // add a note ({text, things, view, save}) or close or reopen one ({id, done})
  note: (id, body) => getJSON(`/place/${id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  heartbeat: () => fetch(BASE + '/heartbeat', { method: 'POST', credentials: 'same-origin', keepalive: true }).catch(() => {}),
};
