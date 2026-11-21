// The Walking mesh view's data (pure: no drawing, no DOM): the built walking mesh split into islands (triangles that
// share an edge), each triangle's colour (the main mesh calm, an island cut off from it in warning), the labels of
// the islands and the doors, the pins of the checks' findings in plain words, and whether the mesh shown is older
// than the place. walk_layer.js draws them; test/walkmesh.test.mjs tests them on a fixture.

export const COLOURS = {
  main: [0.16, 0.62, 0.6],      // the main connected mesh: a calm teal
  world: [0.45, 0.58, 0.6],     // the world's mesh round the place, beyond its reach: quieter
  island: [0.93, 0.5, 0.13],    // cut off from the main mesh: warning amber
  water: [0.22, 0.45, 0.78],    // wading
  door: [0.55, 0.36, 0.95],     // a door's triangle
};
export const ZONE_COLOURS = { block: '#d8443c', walk: '#2f7fd6', join: '#2f7fd6' };
// the kinds of op whose changes reach the walking mesh at the next build
const MESH_OPS = /^(ref\.|land\.|path\.|walk\.)/;
const PIN_NEAR = 160;       // findings this close together share one pin

// Triangles sharing an edge are one island: {label: Int32Array (island of each triangle), sizes: [triangles per
// island], main: the largest island's label}.
export function islands({ tris, nb }) {
  const n = tris.length / 3, label = new Int32Array(n).fill(-1), sizes = [];
  const stack = [];
  for (let s = 0; s < n; s++) {
    if (label[s] >= 0) continue;
    const id = sizes.length; let count = 0; label[s] = id; stack.push(s);
    while (stack.length) {
      const t = stack.pop(); count++;
      for (let k = 0; k < 3; k++) {
        const o = nb[3 * t + k];
        if (o >= 0 && o < n && label[o] < 0) { label[o] = id; stack.push(o); }
      }
    }
    sizes.push(count);
  }
  let main = -1;
  for (let i = 0; i < sizes.length; i++) if (main < 0 || sizes[i] > sizes[main]) main = i;
  return { label, sizes, main };
}

const triArea = (v, a, b, c) => Math.abs((v[3 * b] - v[3 * a]) * (v[3 * c + 1] - v[3 * a + 1]) - (v[3 * c] - v[3 * a]) * (v[3 * b + 1] - v[3 * a + 1])) / 2;

// What to draw for one space's mesh. focus {x, y, r}: islands whose middle lies farther off are the world's (drawn
// quieter, never warned). Returns {positions: Float32Array (three corners per triangle, z lifted by `lift`), colours:
// Float32Array, islands: [{label, tris, area_m2, at: [x, y, z]}] (the cut-off ones in reach, largest first), doors:
// [{tri, ref, at}], counts: {tris, islands, main}}.
export function meshDraw(space, { focus = null, lift = 6 } = {}) {
  const v = space.verts, t = space.tris, n = t.length / 3, kind = space.kind || [];
  const { label, sizes, main } = islands(space);
  const sum = sizes.map(() => [0, 0, 0, 0, 0]);   // x, y, z, area, triangles
  for (let i = 0; i < n; i++) {
    const a = t[3 * i], b = t[3 * i + 1], c = t[3 * i + 2], s = sum[label[i]], ar = triArea(v, a, b, c);
    s[0] += ((v[3 * a] + v[3 * b] + v[3 * c]) / 3) * ar; s[1] += ((v[3 * a + 1] + v[3 * b + 1] + v[3 * c + 1]) / 3) * ar;
    s[2] += ((v[3 * a + 2] + v[3 * b + 2] + v[3 * c + 2]) / 3) * ar; s[3] += ar; s[4]++;
  }
  const mid = sum.map((s) => (s[3] > 0 ? [s[0] / s[3], s[1] / s[3], s[2] / s[3]] : [0, 0, 0]));
  const inReach = (l) => !focus || Math.hypot(mid[l][0] - focus.x, mid[l][1] - focus.y) <= focus.r;
  const doorTri = new Set((space.doors || []).map(([ti]) => ti));
  const positions = new Float32Array(n * 9), colours = new Float32Array(n * 9);
  for (let i = 0; i < n; i++) {
    const l = label[i];
    const col = doorTri.has(i) ? COLOURS.door : l === main ? (kind[i] === 2 ? COLOURS.water : COLOURS.main) : inReach(l) ? COLOURS.island : COLOURS.world;
    for (let k = 0; k < 3; k++) {
      const p = t[3 * i + k];
      positions[9 * i + 3 * k] = v[3 * p]; positions[9 * i + 3 * k + 1] = v[3 * p + 1]; positions[9 * i + 3 * k + 2] = v[3 * p + 2] + lift;
      colours[9 * i + 3 * k] = col[0]; colours[9 * i + 3 * k + 1] = col[1]; colours[9 * i + 3 * k + 2] = col[2];
    }
  }
  const cut = [];
  for (let l = 0; l < sizes.length; l++) {
    if (l === main || !inReach(l)) continue;
    cut.push({ label: l, tris: sizes[l], area_m2: Math.max(1, Math.round(sum[l][3] / (70 * 70))), at: mid[l] });
  }
  cut.sort((a, b) => b.tris - a.tris);
  const doors = (space.doors || []).map(([ti, ref]) => {
    const a = t[3 * ti], b = t[3 * ti + 1], c = t[3 * ti + 2];
    return { tri: ti, ref, at: [(v[3 * a] + v[3 * b] + v[3 * c]) / 3, (v[3 * a + 1] + v[3 * b + 1] + v[3 * c + 1]) / 3, (v[3 * a + 2] + v[3 * b + 2] + v[3 * c + 2]) / 3] };
  });
  return { positions, colours, islands: cut, doors, counts: { tris: n, islands: cut.length, main: main >= 0 ? sizes[main] : 0 } };
}

// An island's label in plain words.
export function islandText(isl) {
  return `Cut off: ${isl.tris} triangle${isl.tris === 1 ? '' : 's'} (about ${isl.area_m2} m²) that people cannot reach from the rest`;
}

// ---------- the checks' findings as pins ----------
const COORD = /\[(-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?)(?:, (-?\d+(?:\.\d+)?))?\]/;
const PLAIN = [
  [/^door .*arrival point .* is on no navmesh/, 'A door\'s arrival point is off the walking mesh: people coming through this door have nowhere to stand.'],
  [/^door .*arrival point is inside (\S+)/, 'This door\'s arrival point is inside another piece: people come through into a wall.'],
  [/^door .*its navmesh is an island \((\d+) triangles\)/, (m) => `This door opens onto a cut-off piece of walking mesh (${m[1]} triangles): people go no further.`],
  [/^door .*no door triangle|^door .*no navmesh under/, 'This door has no walking mesh where people arrive.'],
  [/^street .* is off the built walkable network/, 'This street runs off the walking mesh here: people cannot follow it.'],
  [/patrol point .* is off the built walkable network/, 'A guard\'s patrol point is off the walking mesh.'],
  [/patrol marker (\d+) of (\d+) at .* is off the navmesh/, (m) => `A guard's patrol point (${m[1]} of ${m[2]}) is off the walking mesh.`],
  [/patrol marker (\d+) of (\d+) is not reachable from marker (\d+)/, (m) => `A guard cannot walk from patrol point ${m[3]} to ${m[1]}: the walking mesh does not join them.`],
  [/stop .* is off the navmesh/, 'Someone\'s stop is off the walking mesh.'],
  [/is not reachable from the stop before/, 'Someone cannot walk here from their stop before: the walking mesh does not join them.'],
  [/open seam edge at .* \(unjoined\)/, 'Two pieces of walking mesh meet here but do not join: people stop at this line.'],
];
export function plainLine(line) {
  for (const [re, say] of PLAIN) { const m = line.match(re); if (m) return typeof say === 'function' ? say(m) : say; }
  return line;
}

// Where a finding stands. ctx: {ref(id) -> row | null (with its space), person(id) -> people.jsonl row | null, stop(stop)
// -> [x, y, z] | null}. Returns {pos, space} or null when the finding names no place.
export function findingWhere(line, ctx = {}) {
  const sp = (line.match(/\] in (\S+?)(?: |$)/) || [])[1] || 'exterior';
  const c = line.match(COORD);
  if (c && !/patrol marker \d+ of \d+ is not reachable/.test(line)) return { pos: [Number(c[1]), Number(c[2]), c[3] != null ? Number(c[3]) : null], space: sp };
  const door = line.match(/^door (\S+?):/);
  if (door) {
    const r = ctx.ref?.(door[1]); if (!r) return null;
    const at = r.door?.arrival || r.pos; return { pos: [at[0], at[1], at[2] ?? null], space: r.space || 'exterior' };
  }
  const who = line.match(/^(\S+?): (\S+)/);
  if (who) {
    const p = ctx.person?.(who[1]); if (!p) return null;
    const pm = line.match(/patrol marker (\d+) of \d+ is not reachable/);
    if (pm) {
      const pts = p.patrol?.points || (Array.isArray(p.patrol) ? p.patrol : []), q = pts[Number(pm[1]) - 1];
      const at = Array.isArray(q) ? q : q ? ctx.stop?.(q) : null;
      return at ? { pos: [at[0], at[1], at[2] ?? null], space: q?.space || 'exterior' } : null;
    }
    const k = who[2].match(/_[a-z]+(\d+)$/);
    const step = k ? p.routine?.[Number(k[1])] : null;
    const at = step?.at ? ctx.stop?.(step.at) : null;
    return at ? { pos: [at[0], at[1], at[2] ?? null], space: step.at.space || 'exterior' } : null;
  }
  return null;
}

// The checks' findings as pins: [{pos, space, lines: [plain], raw: [line], check}], findings close together in one pin.
export function pinsFromCheck(check, ctx = {}) {
  const pins = [];
  for (const [name, r] of Object.entries(check?.results || {})) {
    for (const line of r.failures || []) {
      const w = findingWhere(line, ctx); if (!w) continue;
      const near = pins.find((p) => p.space === w.space && Math.hypot(p.pos[0] - w.pos[0], p.pos[1] - w.pos[1]) < PIN_NEAR);
      const plain = plainLine(line);
      if (near) { near.raw.push(line); if (!near.lines.includes(plain)) near.lines.push(plain); continue; }
      pins.push({ pos: w.pos, space: w.space, lines: [plain], raw: [line], check: name });
    }
  }
  return pins;
}

// Is the mesh shown older than the place? {stale, words}: stale when the place files changed after the mesh was built,
// or a change made since (applied, of a kind that reaches the mesh) is newer than it.
export function staleness({ builtAt, filesAt, ops = [], from = 'build' }) {
  if (!builtAt) return { stale: false, words: '' };
  const b = Date.parse(builtAt), f = filesAt ? Date.parse(filesAt) : 0;
  const later = ops.filter((o) => MESH_OPS.test(o.op) && Date.parse(o.at || 0) > b);
  const when = new Date(b).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  const src = from === 'preview' ? 'your last rebuild' : 'the last build';
  if (f > b + 1000 || later.length) {
    const n = later.length;
    return { stale: true, words: `What you see is from ${src} (${when}).${n ? ` ${n} change${n === 1 ? '' : 's'} since then ${n === 1 ? 'is' : 'are'} not in it yet.` : ' The place has changed since.'}` };
  }
  return { stale: false, words: `Built ${when}${from === 'preview' ? ', with your changes' : ''}.` };
}
