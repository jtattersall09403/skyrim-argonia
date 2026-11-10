// The game's grass record rules, pure so node can test them (grass.js draws with them).
const DEG = Math.PI / 180;
// Spots in one 150-unit cell for a grass record's density (0 to 100): a whole number plus a hashed chance of one more.
export function spotsFor(density, u) { const n = Math.max(0, density ?? 40) / 40; return Math.floor(n) + (u < n - Math.floor(n) ? 1 : 0); }
// A record's slope limits (degrees) against the ground's slope (radians); rows without them allow up to 46 degrees.
export function slopeOk(g, slope) { const d = slope / DEG; return d >= (g.min_slope ?? 0) && d <= (g.max_slope ?? 46); }
// The record's water rule: d is how far the ground stands above the water (negative: below). The type is the
// game's, by name as the bundle writes it or by number. Rows without the fields keep clear of the water's edge.
const WATER_TYPE = { aboveatleast: 0, aboveatmost: 1, belowatleast: 2, belowatmost: 3, eitheratleast: 4, eitheratmost: 5,
  eitheratmostabove: 6, eitheratmostbelow: 7 };
export function waterOk(g, d) {
  const u = g.units_from_water, raw = g.units_from_water_type ?? 0;
  if (u == null) return d >= 8;
  const type = typeof raw === 'string' ? WATER_TYPE[raw.toLowerCase()] : Number(raw);
  switch (type) {
    case 0: return d >= u; case 1: return d <= u && d >= 0; case 2: return -d >= u; case 3: return -d <= u && d <= 0;
    case 4: return Math.abs(d) >= u; case 5: return Math.abs(d) <= u;
    case 6: return d >= 0 && d <= u; case 7: return d <= 0 && -d <= u;
    default: return d >= 8;
  }
}
// A blade's size: the record's height range is how far it varies either side of full size (0.35: 65% to 135%);
// a pair is taken as [least, most].
export function heightScale(g, u) {
  const r = g.height_range;
  if (Array.isArray(r)) return r[0] + (r[1] - r[0]) * u;
  const v = Math.max(0, Math.min(0.9, Number(r ?? 0.25) || 0));
  return 1 - v + 2 * v * u;
}
