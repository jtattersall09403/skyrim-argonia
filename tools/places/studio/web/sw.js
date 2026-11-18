// The studio's service worker (docs/design/place-studio.md, Offline). Registered only while a place is held on this
// device; it serves the studio from the browser's own storage when the build machine cannot be reached.
//
// What the page tells it (the cache "studio-meta", key /__studio/state, and a message on each change):
//   {mode: online|offline, shell: the cache holding the app's files, held: [{place_id, cache}]}.
// Rules:
// - It never touches a write: PUT and POST go to the network as they are, and nothing they answer is kept.
// - The page and its files come from the held copy of the app (the page checks the app's version when it can
//   reach the machine and fetches the new one itself). A wake (?wake=), a sign-in (?signin=), the page's own probe
//   (X-Studio-Probe) and the Atlas always go to the network.
// - Online, a read of the API goes to the network. Only when that fails (no connection, the machine stopped, an
//   expired sign-in that turns the request away) is the held copy served, marked X-Studio-Offline: 1, and the page
//   told. A place's notes and saves read online are kept as last read.
// - Offline, a read is answered from the held copies; what is not held is a plain 503, marked the same way.
const META = 'studio-meta', STATE_KEY = '/__studio/state';
const DOWN = new Set([502, 503, 504, 521, 522, 523, 530]);
let state = null, texIndex = null;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('message', (e) => {
  if (e.data?.type === 'state') { state = e.data.state; texIndex = null; }
});

async function getState() {
  if (state) return state;
  try { const r = await (await caches.open(META)).match(STATE_KEY); state = r ? await r.json() : null; } catch { state = null; }
  return state || { mode: 'online', held: [], shell: null };
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.searchParams.has('wake') || url.searchParams.has('signin') || req.headers.get('X-Studio-Probe')) return;
  if (url.pathname.startsWith('/atlas/') || url.pathname === '/sw.js') return;
  e.respondWith(handle(req, url));
});

async function handle(req, url) {
  const st = await getState();
  if (!st.held?.length) return fetch(req);
  if (!url.pathname.startsWith('/api/')) return app(req, url, st);
  if (st.mode === 'offline') return (await held(req, url, st)) || miss();
  let res = null;
  try { res = await fetch(req); } catch { res = null; }
  const good = res && res.type !== 'opaqueredirect' && !DOWN.has(res.status) && !(res.redirected && new URL(res.url).origin !== self.location.origin);
  if (good) { if (res.ok) keepLastRead(url, res.clone(), st); return res; }
  const h = await held(req, url, st);
  if (h) { tell({ type: 'fell-back', url: url.pathname }); return h; }
  return res || miss();
}

// The app's own files: from the held copy of the app, else the network.
async function app(req, url, st) {
  const key = url.pathname === '/' || url.pathname === '/index.html' ? '/' : url.pathname;
  const c = st.shell && await caches.open(st.shell);
  const hit = c && await c.match(key, { ignoreSearch: true });
  if (hit) return hit;
  try { return await fetch(req); } catch { return miss(); }
}

// The held copy of an API read: exact, else (a texture asked for at another size, a mesh at its other level) the
// nearest thing held.
async function held(req, url, st) {
  for (const h of st.held) {
    const c = await caches.open(h.cache), r = await c.match(req, { ignoreVary: true });
    if (r) return mark(r);
  }
  if (url.pathname === '/api/asset/tex') {
    const want = url.searchParams.get('path'); if (!want) return null;
    if (!texIndex) texIndex = buildTexIndex(st);
    const u = (await texIndex).get(want.toLowerCase());
    if (u) for (const h of st.held) { const r = await (await caches.open(h.cache)).match(u); if (r) return mark(r); }
  }
  if (url.pathname === '/api/asset/mesh') {
    const other = new URL(url); other.searchParams.set('level', url.searchParams.get('level') === '1' ? '0' : '1');
    for (const h of st.held) { const r = await (await caches.open(h.cache)).match(other.href); if (r) return mark(r); }
  }
  return null;
}
async function buildTexIndex(st) {
  const m = new Map();
  for (const h of st.held) {
    for (const k of await (await caches.open(h.cache)).keys()) {
      const u = new URL(k.url);
      if (u.pathname === '/api/asset/tex') { const p = (u.searchParams.get('path') || '').toLowerCase(); if (p && !m.has(p)) m.set(p, k.url); }
    }
  }
  return m;
}

// Notes, saves and the status as last read, for a held place (the bundles and the rest change only by "Update").
const LAST_READ = /^\/api\/(status|place\/([^/]+)\/(notes|saves(\/[^/]+)?))$/;
async function keepLastRead(url, res, st) {
  const m = url.pathname.match(LAST_READ); if (!m) return;
  for (const h of st.held) {
    if (m[2] && h.place_id !== m[2]) continue;
    try { await (await caches.open(h.cache)).put(url.pathname, new Response(await res.clone().blob(), { status: 200, headers: plain(res.headers) })); } catch { /* full: kept as before */ }
  }
}
function plain(headers) {
  const h = new Headers(headers); h.delete('Content-Encoding'); h.delete('Content-Length'); h.delete('Set-Cookie'); return h;
}
function mark(r) {
  const h = new Headers(r.headers); h.set('X-Studio-Offline', '1');
  return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
}
function miss() {
  return new Response(JSON.stringify({ error: 'This is not held on this tablet, and the build machine cannot be reached now.', offline: true }),
    { status: 503, headers: { 'Content-Type': 'application/json', 'X-Studio-Offline': '1', 'Cache-Control': 'no-store' } });
}
async function tell(msg) {
  for (const c of await self.clients.matchAll({ type: 'window' })) c.postMessage(msg);
}
