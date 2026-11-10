// A cell of an exterior's terrain.json as the drawing code wants it (shared by bundle.js and the worker that
// reads terrain off the main thread).
const QUAD = { BottomLeft: 0, BottomRight: 1, TopLeft: 2, TopRight: 3 };
function b64(s) { const bin = atob(s), out = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i); return out; }
// One cell as the drawing code wants it: heights offset, water (none at the game's "no water" height),
// four quadrants (SW, SE, NW, NE) each a base land texture and alpha layers of 17x17 opacities, vertex colours.
export function normaliseCell(c, n) {
  const water = c.water && c.water.height < 1e30 ? c.water : null;
  const out = { cell: c.cell, heights: c.heights_index != null ? c.heights_index * n : c.heights, water, quadrants: [0, 1, 2, 3].map(() => ({ base: null, layers: [] })), vcol: null };
  for (const l of c.layers || []) {
    const q = out.quadrants[QUAD[l.quad] ?? l.quad];
    if (!q) continue;
    if (l.layer === -1) q.base = l.tex;
    else q.layers.push({ tex: l.tex, layer: l.layer, alpha: typeof l.alpha === 'string' ? Float32Array.from(b64(l.alpha), (v) => v / 255) : l.alpha });
  }
  for (const q of out.quadrants) q.layers.sort((x, y) => x.layer - y.layer);
  if (c.vertex_colours) out.vcol = b64(c.vertex_colours);
  return out;
}
