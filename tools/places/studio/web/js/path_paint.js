// How a drawn path is painted onto the land, the way the build paints it (tools/places/build.py plan_paths): one
// alpha layer of the path's land texture per cell quadrant, opacity 1 within the half width and falling to 0 over
// PATH_FEATHER units beyond it, at every land grid point; a boardwalk's line only where it comes ashore. Pure, so
// node tests it against the build's own numbers.
export const PATH_FEATHER = 96;
// a path style word -> the end of the world land texture's editor id the build uses for it (default dirt_road)
export const PATH_STYLE_LTEX = { road: 'dirt_road', street: 'dirt_road', path: 'dirt_road', track: 'dirt_grass',
  skirt: 'road_skirt', mud: 'swamp_mud', sand: 'sand', stone: 'rock' };
export function segDist(x, y, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
  const t = l ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l)) : 0;
  return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy);
}
export function opacityAt(d, half) { return Math.max(0, Math.min(1, 1 - (d - half) / PATH_FEATHER)); }
// The land texture a path is painted with: a key the owner picked, else the land texture whose editor id ends with
// the style's word, as the build chooses it; null when the land lists none.
export function pathLtex(style, ltex) {
  if (style && ltex?.[style]) return style;
  const want = PATH_STYLE_LTEX[style] || 'dirt_road';
  for (const [k, v] of Object.entries(ltex || {})) if ((v?.edid || '').toLowerCase().endsWith(want)) return k;
  return null;
}
// A path's opacity at each of one cell's grid x grid points (row-major, row 0 at the south edge), or null when it
// does not reach the cell. terrain: bundle.js Terrain (size, step, grid, h, cells, waterAt) for the boardwalk rule.
export function cellOpacity(p, cell, t) {
  const half = (p.width ?? 256) / 2, reach = half + PATH_FEATHER, g = t.grid, x0 = cell[0] * t.size, y0 = cell[1] * t.size;
  const segs = [];
  for (let i = 1; i < p.points.length; i++) {
    const a = p.points[i - 1], b = p.points[i];
    if (Math.max(a[0], b[0]) + reach < x0 || Math.min(a[0], b[0]) - reach > x0 + t.size || Math.max(a[1], b[1]) + reach < y0 || Math.min(a[1], b[1]) - reach > y0 + t.size) continue;
    segs.push([a, b]);
  }
  if (!segs.length) return null;
  const op = new Float32Array(g * g); let any = false;
  const c = t.cells?.get(cell.join(',')), water = p.style === 'boardwalk' && c?.water ? c.water.height : null;
  for (let r = 0; r < g; r++) for (let col = 0; col < g; col++) {
    const x = x0 + col * t.step, y = y0 + r * t.step;
    let d = Infinity; for (const [a, b] of segs) d = Math.min(d, segDist(x, y, a, b));
    let o = opacityAt(d, half);
    // a boardwalk's line is walked on its decks: only where it comes ashore is it a path on the ground
    if (o > 0 && water != null && t.h(cell, r, col) < water - 8) o = 0;
    if (o > 0) { op[r * g + col] = o; any = true; }
  }
  return any ? op : null;
}
