// A ref's primitive (pure: no three.js, no page): the invisible box or sphere a collision marker, trigger, room
// marker or sound volume is. `primitive` is {type: Box | Sphere | Plane | Line | Ellipsoid, bounds: [x, y, z] half
// extents round the ref's origin in its own frame, color, unknown}. A collision marker's box is an invisible wall:
// people and the player cannot pass it. Shown with the helpers (the Select and Add tools, or the Lights toggle).
export const hasPrim = (ref) => !!ref?.primitive?.bounds;
export const isRound = (ref) => /^(Sphere|Ellipsoid)$/i.test(ref?.primitive?.type || '');
export const isWall = (ref, base) => hasPrim(ref) && /^CollisionMarker/i.test(base?.edid || '');
// The half extents drawn and picked: a sphere's radius on all three axes; never under one unit.
export function halfExtents(ref) {
  const b = ref.primitive.bounds.map((v) => Math.max(1, Math.abs(Number(v) || 0)));
  return /^Sphere$/i.test(ref.primitive.type || '') ? [b[0], b[0], b[0]] : b;
}
const m = (u) => (u / 70).toFixed(1);
// What the Selected panel says of a primitive: what it is, the piece it belongs to, its size.
export function primFacts(ref, base, pieceName) {
  const h = halfExtents(ref), round = /^Sphere$/i.test(ref.primitive.type || '');
  const what = isWall(ref, base) ? 'an invisible wall: people and the player cannot pass'
    : `an invisible ${(ref.primitive.type || 'box').toLowerCase()} the game uses (a trigger, room or sound volume): nothing solid`;
  const facts = [['What it is', what]];
  if (ref.seat?.on) facts.push(['Belongs to', `${pieceName || ref.seat.on}: it was kept because it stands on this piece`]);
  facts.push(['Size', round ? `${Math.round(h[0])} units round its middle (${m(h[0])} m)`
    : `${Math.round(2 * h[0])} by ${Math.round(2 * h[1])} by ${Math.round(2 * h[2])} units (${m(2 * h[0])} by ${m(2 * h[1])} by ${m(2 * h[2])} m)`]);
  return facts;
}
// The primitive with its size changed: `size` is the full size [x, y, z] in units (a sphere: [radius]).
export function resized(prim, size) {
  const r = (v) => Math.round(Math.max(1, Number(v) || 1) * 100) / 100;
  if (/^Sphere$/i.test(prim.type || '')) return { ...prim, bounds: [r(size[0]), ...prim.bounds.slice(1)] };
  return { ...prim, bounds: size.map((v) => r(v / 2)) };
}
// A piece's invisible walls: the refs with a primitive seated `on` it (the tie the drafter's primitives stage
// records). They follow every move, turn, resize, copy and removal of the piece, as a light follows its fixture;
// one selected by itself moves or goes alone. Returns [[wall, piece]] for the pieces among `pieces`.
export function wallsOf(pieces, refs) {
  const by = new Map(pieces.map((p) => [p.id, p])), out = [];
  for (const w of refs) {
    const on = w.seat?.mode === 'on' && by.get(w.seat.on);
    if (on && on !== w && !w.removed && hasPrim(w)) out.push([w, on]);
  }
  return out;
}
// The primitive grown or shrunk by `k` with its piece (its half extents times k).
export function scaledPrim(prim, k) {
  return { ...prim, bounds: prim.bounds.map((v) => Math.round(Number(v) * k * 100) / 100) };
}
// What comes with a piece when it moves, turns, is resized, copied or removed: its invisible walls and lights.
export function comesWith(nWalls, nLights) {
  const n = (k, one, many) => (k === 1 ? `one ${one}` : `${k} ${many}`);
  const parts = [nWalls && n(nWalls, 'invisible wall', 'invisible walls'), nLights && n(nLights, 'light', 'lights')].filter(Boolean);
  if (!parts.length) return null;
  return `${parts.join(' and ')} ${nWalls + nLights === 1 ? 'goes' : 'go'} with it when it moves, turns, is resized, copied or removed`;
}
