// The game's grass record rules, pure so node can test them (grass.js draws with them).
const DEG = Math.PI / 180;
// Spots in one 150-unit cell for a grass record's density (0 to 100): a whole number plus a hashed chance of one more.
export function spotsFor(density, u) { const n = Math.max(0, density ?? 40) / 40; return Math.floor(n) + (u < n - Math.floor(n) ? 1 : 0); }
// A record's slope limits (degrees) against the ground's slope (radians); rows without them allow up to 46 degrees.
export function slopeOk(g, slope) { const d = slope / DEG; return d >= (g.min_slope ?? 0) && d <= (g.max_slope ?? 46); }
// The record's water rule: d is how far the ground stands above the water (negative: below). Types are the game's:
// 0 above at least, 1 above at most, 2 below at least, 3 below at most, 4 above or below at least / 5 at most,
// 6 exactly above, 7 exactly below. Rows without the fields keep clear of the water's edge.
export function waterOk(g, d) {
  const u = g.units_from_water, type = g.units_from_water_type ?? 0;
  if (u == null) return d >= 8;
  switch (Number(type)) {
    case 0: return d >= u; case 1: return d <= u && d >= 0; case 2: return -d >= u; case 3: return -d <= u && d <= 0;
    case 4: return Math.abs(d) >= u; case 5: return Math.abs(d) <= u;
    case 6: return Math.abs(d - u) < 16; case 7: return Math.abs(-d - u) < 16;
    default: return d >= 8;
  }
}

