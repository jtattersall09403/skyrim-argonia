// How a placed water is drawn, as data (the three.js side is water.js). A placed water is a base with a `water` entry in
// the catalogue: the colours of its water type (shallow, deep, and the record's reflection colour), and when the
// extractor has them its opacity (0..100, as the record writes it), reflectivity, fresnel and the distance over which
// the water turns from its shallow to its deep colour (fog above water, far plane). The game shades such a surface
// from these; the studio does the same from the same numbers, so what is seen is what the record says.
export const isPlacedWater = (base) => !!base?.water;

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const unit = (c, d) => (Array.isArray(c) && c.length >= 3 ? c.slice(0, 3).map((v) => clamp(Number(v) / 255, 0, 1)) : d);
const num = (v, d) => (v == null || Number.isNaN(Number(v)) ? d : Number(v));

// The look of one water type, every field present. A record that does not give a field gets the middle of
// Skyrim's own water types (opacity 0.5, reflectivity 0.8, fresnel 0.1, deep over 220 units).
export function waterLook(w) {
  const shallow = unit(w?.shallow, [0.24, 0.43, 0.47]);
  const deep = unit(w?.deep, shallow.map((v) => v * 0.45));
  return {
    shallow, deep,
    reflect: unit(w?.reflect, shallow.map((v) => 0.35 + v * 0.5)),
    opacity: clamp(num(w?.opacity, 50) / 100, 0, 1),
    reflectivity: clamp(num(w?.reflectivity, 0.8), 0, 1),
    fresnel: clamp(num(w?.fresnel, 0.1), 0, 1),
    fogFar: Math.max(40, num(w?.fog_far, 220)),
  };
}

// Two bytes per texel on a grid over the placed waters' footprints: the depth of the water over the ground (0 where
// there is no water or the ground stands above the surface, else 1 + depth, DEPTH_MAX game units being 255), and how
// far in from the water's edge the texel lies (INLAND_UNIT game units a step, so a flat hollow still deepens toward its
// middle). refs: [{pos:[x,y,z], r}] (r the footprint's half-width, units); groundAt(x, y) the ground's height. The
// grid is in game units; texels are at most `maxSide` a side, the step growing to fit.
export const DEPTH_MAX = 192, INLAND_UNIT = 4;
export function depthGrid(refs, groundAt, { step = 16, maxSide = 256, margin = 48 } = {}) {
  if (!refs.length) return null;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const f of refs) { x0 = Math.min(x0, f.pos[0] - f.r); y0 = Math.min(y0, f.pos[1] - f.r); x1 = Math.max(x1, f.pos[0] + f.r); y1 = Math.max(y1, f.pos[1] + f.r); }
  x0 -= margin; y0 -= margin; x1 += margin; y1 += margin;
  const s = Math.max(step, (x1 - x0) / maxSide, (y1 - y0) / maxSide);
  const w = Math.ceil((x1 - x0) / s), h = Math.ceil((y1 - y0) / s), data = new Uint8Array(w * h * 2), depth = new Uint8Array(w * h);
  for (const f of refs) {
    const i0 = Math.max(0, Math.floor((f.pos[0] - f.r - x0) / s)), i1 = Math.min(w - 1, Math.ceil((f.pos[0] + f.r - x0) / s));
    const j0 = Math.max(0, Math.floor((f.pos[1] - f.r - y0) / s)), j1 = Math.min(h - 1, Math.ceil((f.pos[1] + f.r - y0) / s));
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      const x = x0 + (i + 0.5) * s, y = y0 + (j + 0.5) * s, g = groundAt(x, y);
      if (g == null) continue;
      const d = f.pos[2] - g;
      if (d > 0) depth[j * w + i] = Math.max(depth[j * w + i], Math.min(255, Math.round((d / DEPTH_MAX) * 254) + 1));
    }
  }
  // distance in from the edge (a two-pass chamfer over the covered texels), in game units
  const dist = new Float32Array(w * h).map((_, k) => (depth[k] ? 1e9 : 0)), at = (i, j) => (i < 0 || j < 0 || i >= w || j >= h ? 0 : dist[j * w + i]);
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) if (dist[j * w + i]) dist[j * w + i] = Math.min(at(i - 1, j) + 1, at(i, j - 1) + 1, at(i - 1, j - 1) + 1.4, at(i + 1, j - 1) + 1.4, 1e9);
  for (let j = h - 1; j >= 0; j--) for (let i = w - 1; i >= 0; i--) if (dist[j * w + i]) dist[j * w + i] = Math.min(dist[j * w + i], at(i + 1, j) + 1, at(i, j + 1) + 1, at(i + 1, j + 1) + 1.4, at(i - 1, j + 1) + 1.4);
  for (let k = 0; k < w * h; k++) { data[k * 2] = depth[k]; data[k * 2 + 1] = dist[k] >= 1e8 ? 0 : Math.min(255, Math.round((dist[k] * s) / INLAND_UNIT)); }
  return { data, w, h, min: [x0, y0], size: [w * s, h * s], step: s };
}

// One tile of ripple: a tangent-space normal map, RGBA bytes, `n` a side, tiling. The height under it is smooth value
// noise (a hashed lattice, smoothstep-blended) at three octaves whose lattices wrap at the tile's edge, so it tiles
// without a seam, yet no cell grid shows: no octave's lattice lines up with another's, and the slopes are small (a
// still pool's faint swell, never a weave). The same bytes every time.
export function rippleNormals(n = 128) {
  const out = new Uint8Array(n * n * 4);
  const hash = (i, j, o) => { let h = (i * 374761393 + j * 668265263 + o * 2147483647) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967295; };
  const ease = (t) => t * t * (3 - 2 * t);
  const octaves = [[5, 1.0], [11, 0.5], [23, 0.25]];   // lattice cells across the tile (primes: no shared grid), weight
  const H = new Float32Array(n * n);
  for (const [c, w] of octaves) for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const x = (i / n) * c, y = (j / n) * c, x0 = Math.floor(x), y0 = Math.floor(y), fx = ease(x - x0), fy = ease(y - y0);
    const v = (a, b) => hash(((x0 + a) % c + c) % c, ((y0 + b) % c + c) % c, c);
    const top = v(0, 0) + (v(1, 0) - v(0, 0)) * fx, bot = v(0, 1) + (v(1, 1) - v(0, 1)) * fx;
    H[j * n + i] += (top + (bot - top) * fy) * w;
  }
  const at = (i, j) => H[((j + n) % n) * n + ((i + n) % n)], AMP = n * 0.011;   // slope scale: low contrast
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const dx = (at(i + 1, j) - at(i - 1, j)) * AMP, dy = (at(i, j + 1) - at(i, j - 1)) * AMP;
    const l = Math.hypot(dx, dy, 1), k = (j * n + i) * 4;
    out[k] = Math.round((-dx / l * 0.5 + 0.5) * 255); out[k + 1] = Math.round((-dy / l * 0.5 + 0.5) * 255); out[k + 2] = Math.round((1 / l * 0.5 + 0.5) * 255); out[k + 3] = 255;
  }
  return out;
}
