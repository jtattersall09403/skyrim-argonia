// The owner's notes on changes (docs/design/place-studio.md, Edits: notes on changes). Pure JavaScript, no DOM: node
// tests it. A note is one text for one or more changes: each op it covers carries the note's id in `note_group`,
// and the save lists the note once in `notes: [{id, text, at}]`. An older save's per-op `note` still reads as a
// note on that change (and on the changes beside it that carry the same words).

// One change is one op, or the ops of one stroke (a brush stroke, things moved together): undo takes it back whole.
export function changesOf(ops) {
  const out = [];
  for (const op of ops) {
    const last = out[out.length - 1];
    if (last && op.stroke && last[0].stroke === op.stroke) last.push(op); else out.push([op]);
  }
  return out;
}

const noted = (op) => !!(op.note_group || op.note);

// The changes since the last note: the applied changes after the last one that has a note, none of them noted.
export function pending(applied) {
  const ch = changesOf(applied);
  let i = ch.length;
  while (i > 0 && !ch[i - 1].some(noted)) i--;
  return ch.slice(i);
}

// The notes that cover applied changes, in the order of their first change: [{id, text, at, ops, changes, legacy}].
// A note whose changes were all undone is left out (it comes back with them on redo).
export function groupsOf(applied, notes) {
  const byId = new Map((notes instanceof Map ? [...notes.values()] : notes || []).map((n) => [n.id, n]));
  const out = new Map();
  let prevLegacy = null;
  for (const op of applied) {
    let key, note;
    if (op.note_group && byId.has(op.note_group)) { key = op.note_group; note = byId.get(key); prevLegacy = null; }
    else if (op.note) {
      // an older save: ops side by side with the same words were noted together
      if (prevLegacy && prevLegacy.text === op.note) key = prevLegacy.id;
      else { key = `old${op.n}`; prevLegacy = { id: key, text: op.note }; }
      note = { id: key, text: op.note, at: op.at, legacy: true };
    } else { prevLegacy = null; continue; }
    if (!out.has(key)) out.set(key, { id: key, text: note.text, at: note.at, legacy: !!note.legacy, ops: [] });
    out.get(key).ops.push(op);
  }
  return [...out.values()].map((g) => ({ ...g, changes: changesOf(g.ops) }));
}

// A fresh note id, never one in use (notes whose changes were undone keep theirs).
export function newNoteId(notes) {
  let max = 0;
  for (const id of (notes instanceof Map ? notes.keys() : (notes || []).map((n) => n.id))) {
    const m = /^g(\d+)$/.exec(id); if (m) max = Math.max(max, Number(m[1]));
  }
  return `g${max + 1}`;
}

// The ids of the things a change touched: refs, paths and people, each with its space.
export function touched(ops) {
  const out = [];
  for (const op of ops) {
    const id = op.ref?.id || op.id || op.path?.id || op.person?.id;
    if (id) out.push({ id, space: op.space || 'exterior', kind: op.op.split('.')[0] });
  }
  return out;
}
