// Reads an exterior's terrain (terrain.json and terrain.f32) off the main thread: decoded cells come back with
// their typed arrays transferred, so the page never stalls on the 13 MB file.
import { normaliseCell } from './terrain_cells.js';

self.onmessage = async ({ data: { id, jsonUrl, f32Url } }) => {
  try {
    const get = (u) => fetch(u, { credentials: 'same-origin' }).then((r) => (r.ok ? r : null));
    const [rj, rf] = await Promise.all([get(jsonUrl), get(f32Url)]);
    if (!rj || !rf) { self.postMessage({ id, none: true }); return; }
    const [json, buf] = await Promise.all([rj.json(), rf.arrayBuffer()]);
    const n = (json.grid || 33) ** 2, list = json.cells.map((c) => normaliseCell(c, n)), transfer = [buf];
    for (const c of list) { if (c.vcol) transfer.push(c.vcol.buffer); for (const q of c.quadrants) for (const l of q.layers) if (l.alpha?.buffer) transfer.push(l.alpha.buffer); }
    delete json.cells;
    self.postMessage({ id, json, list, f32: buf }, transfer);
  } catch (e) { self.postMessage({ id, error: String(e) }); }
};
