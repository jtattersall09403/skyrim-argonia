// Lights and the fixtures they belong to (pure: no three.js, no page). A light belongs to the nearest man-made
// fixture (a lantern, sconce, candle, torch, brazier, fire, chandelier, lamp or window) within FIXTURE_REACH of it;
// moving, turning or removing a fixture takes its lights with it, and a light can still be moved or removed alone.
export const FIXTURE_REACH = 128;
export const FIXTURE = /lantern|sconce|candle|torch|brazier|fire|chandel|lamp|window|glow|ember|hearth/i;

export const isLight = (ref) => ref.kind === 'light';
export function isFixture(ref, base) {
  if (isLight(ref)) return false;
  return FIXTURE.test(`${base?.edid || ''} ${base?.model || ''} ${base?.name || ''}`);
}
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

// The fixture a light belongs to: the nearest fixture within reach, else null. `posOf` gives the drawn position.
export function fixtureOf(light, refs, baseOf, posOf = (r) => r.pos, reach = FIXTURE_REACH) {
  return nearest(light, refs.filter((r) => r !== light && !r.removed && isFixture(r, baseOf(r))), posOf, reach);
}
function nearest(light, fixtures, posOf, reach = FIXTURE_REACH) {
  let best = null, bd = reach;
  const p = posOf(light);
  for (const r of fixtures) {
    const d = dist(p, posOf(r));
    if (d <= bd) { best = r; bd = d; }
  }
  return best;
}

// Every light among `refs` that belongs to one of `fixtures`: [[light, fixture]].
export function lightsOf(fixtures, refs, baseOf, posOf = (r) => r.pos) {
  const mine = fixtures.filter((f) => isFixture(f, baseOf(f))), out = [];
  if (!mine.length) return out;
  const want = new Set(mine.map((f) => f.id)), near = (l) => mine.some((f) => dist(posOf(l), posOf(f)) <= FIXTURE_REACH);
  const lights = refs.filter((l) => isLight(l) && !l.removed && near(l));
  if (!lights.length) return out;
  const pool = [...mine, ...refs.filter((r) => !r.removed && isFixture(r, baseOf(r)))];  // every fixture competes
  for (const l of lights) {
    const f = nearest(l, pool, posOf);
    if (f && want.has(f.id)) out.push([l, f]);
  }
  return out;
}

// The game's Z turn (clockwise seen from above is positive) applied to a vector in plan.
export const turn = (v, a) => [Math.cos(-a) * v[0] - Math.sin(-a) * v[1], Math.sin(-a) * v[0] + Math.cos(-a) * v[1]];

// Where a light sits in its fixture's own frame (so it follows a move, a turn and a resize).
export function localOf(light, fix, posOf = (r) => r.pos) {
  const lp = posOf(light), fp = posOf(fix), s = fix.scale ?? 1;
  const [x, y] = turn([lp[0] - fp[0], lp[1] - fp[1]], -(fix.rot?.[2] || 0));
  return { x: x / s, y: y / s, z: (lp[2] - fp[2]) / s, rz: (light.rot?.[2] || 0) - (fix.rot?.[2] || 0) };
}
// The light's pose for the fixture's pose now: [pos, rot].
export function poseFor(local, fix, light, posOf = (r) => r.pos) {
  const fp = posOf(fix), s = fix.scale ?? 1, a = fix.rot?.[2] || 0;
  const [x, y] = turn([local.x * s, local.y * s], a);
  return [[fp[0] + x, fp[1] + y, fp[2] + local.z * s], [light.rot?.[0] || 0, light.rot?.[1] || 0, local.rz + a]];
}

// A light's colour as [r, g, b]: the bundles write it as three numbers, or (the extractor's byte arrays) as those
// three bytes in base64.
export function colourOf(v) {
  if (Array.isArray(v)) return v.slice(0, 3).map(Number);
  if (typeof v === 'string' && v.length >= 4) { try { const s = atob(v); return [0, 1, 2].map((i) => s.charCodeAt(i) || 0); } catch { return null; } }
  return null;
}

// What the Selected panel says of a light: radius, colour, shadow casting.
export function lightFacts(ref, base) {
  const l = base?.light || {};
  const c = colourOf(l.colour), flags = String(l.flags || '');
  return { radius: ref.radius || l.radius || 0, colour: c, hex: c ? '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('') : null,
    shadow: /shadow/i.test(flags), flags };
}
