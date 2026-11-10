// Where a selected thing stands in the game: its position in game units (whole numbers), its exterior cell
// (4096 units a side) and its turn in degrees; for several things, the middle of their positions (pure, node tests it).
const CELL = 4096, DEG = 180 / Math.PI;
export function whereOf(refs, { exterior = true } = {}) {
  const ps = refs.map((r) => r.pos).filter((p) => p && p.length >= 3);
  if (!ps.length) return null;
  const mid = [0, 1, 2].map((i) => (Math.min(...ps.map((p) => p[i])) + Math.max(...ps.map((p) => p[i]))) / 2);
  const out = { pos: mid.map(Math.round), several: ps.length > 1 };
  if (exterior) out.cell = [Math.floor(mid[0] / CELL), Math.floor(mid[1] / CELL)];
  if (ps.length === 1) {
    const r = refs.find((q) => q.pos) || {}, rot = r.rot || [0, 0, 0], d = (v) => ((Math.round((v || 0) * DEG) % 360) + 360) % 360;
    out.turn = d(rot[2]); if (Math.abs(rot[0] || 0) > 1e-3 || Math.abs(rot[1] || 0) > 1e-3) out.tilt = [d(rot[0]), d(rot[1])];
  }
  return out;
}
// The facts rows for the Selected panel: [label, words].
export function whereRows(w) {
  if (!w) return [];
  const rows = [[w.several ? 'Middle of them (game units)' : 'Position (game units)', `x ${w.pos[0]}, y ${w.pos[1]}, z ${w.pos[2]}`]];
  if (w.cell) rows.push(['Cell', `${w.cell[0]}, ${w.cell[1]}`]);
  if (w.turn != null) rows.push(['Turned', `${w.turn}°${w.tilt ? ` (tilted ${w.tilt[0]}° about x, ${w.tilt[1]}° about y)` : ''}`]);
  return rows;
}
