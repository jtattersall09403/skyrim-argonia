// A quest thing's spot as an edit (pure, no DOM: test/quests.test.mjs). The row is the place's quests.jsonl row
// (tools/places/quest_spots.py); the ops are edits.py's quest.add / quest.edit / quest.remove.
const rnd = (v) => Math.round(v * 100) / 100;
const clone = (o) => JSON.parse(JSON.stringify(o));

// The row for an item at a spot: where it stands and its heading (radians, clockwise from north).
export function spotRow(item, space, pos, heading) {
  return { id: item.id, quest: item.quest, ref: item.ref, space, pos: pos.map(rnd), rot: [0, 0, rnd(heading)] };
}
// The op that moves an item from the spot it has (or none) to a new one, or clears it (after null); null when nothing changes.
export function moveOp(before, after) {
  if (!after) return before ? { op: 'quest.remove', quest: clone(before), before: clone(before) } : null;
  if (!before) return { op: 'quest.add', quest: after };
  if (JSON.stringify(before) === JSON.stringify(after)) return null;
  return { op: 'quest.edit', quest: after, before: clone(before) };
}
// A heading turned by `by` radians, kept in [0, 2 pi).
export function turned(heading, by) {
  const t = 2 * Math.PI, h = ((heading || 0) + by) % t;
  return h < 0 ? h + t : h;
}
// A drafted spot (a row with `drafted` and `why`) kept as it stands: the same row without them, owner-set.
export function keptRow(row) {
  const { drafted, why, ...rest } = row; // eslint-disable-line no-unused-vars
  return rest;
}
