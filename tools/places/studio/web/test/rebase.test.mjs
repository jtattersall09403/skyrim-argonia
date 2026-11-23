// An owner's open session replayed over a draft an agent changed in answer to his notes (edits.py _rebased, the
// same rule): an op of the answered note is kept as no change, an op of another note on an answered row is his edit
// over the row as it stands, an op on a row nobody answered that no longer fits stops the load.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { modelFromFiles, EditLog } from '../js/edits.js';

const here = dirname(fileURLToPath(import.meta.url));
const place = JSON.parse(readFileSync(join(here, '../../../../tests/places_edits/place.json'), 'utf8'));

function drafted() {
  const files = JSON.parse(JSON.stringify(place));
  const refs = files.spaces.exterior.refs;
  const [a, b] = refs;
  const was = { a: [...a.pos], b: [...b.pos] };
  a.pos = [a.pos[0] + 107, a.pos[1], a.pos[2]];   // the agent's answer to g8, made over his move of 100
  b.pos = [b.pos[0] + 3, b.pos[1], b.pos[2]];     // and to g8 on b
  files.place = { ...(files.place || {}), agent_answers: [{ save: 'agent-a', stroke: 1, answers: 'g8', rows: [a.id, b.id] }] };
  return { files, a: a.id, b: b.id, was, c: refs[2]?.id };
}

test('his session replays over the agent\'s answers', () => {
  const { files, a, b, was } = drafted();
  const m = modelFromFiles(files), log = new EditLog(m);
  const ops = [
    { n: 1, op: 'ref.move', space: 'exterior', id: a, note_group: 'g8', before: { pos: was.a }, after: { pos: [was.a[0] + 100, was.a[1], was.a[2]] } },
    { n: 2, op: 'ref.move', space: 'exterior', id: b, note_group: 'g6', before: { pos: was.b }, after: { pos: [was.b[0] + 50, was.b[1], was.b[2]] } },
  ];
  const err = log.load(ops, [{ id: 'g8', text: 'fix it' }, { id: 'g6', text: 'hovering' }]);
  assert.equal(err, null);
  assert.equal(log.ops.length, 2);
  assert.equal(m.spaces.exterior.refs.get(a).pos[0], was.a[0] + 107);   // the answer stands
  assert.equal(m.spaces.exterior.refs.get(b).pos[0], was.b[0] + 50);    // his edit wins on another note
  log.undo(); log.undo();
  assert.equal(m.spaces.exterior.refs.get(a).pos[0], was.a[0] + 107);   // undoing his ops gives back the answered draft
  assert.equal(m.spaces.exterior.refs.get(b).pos[0], was.b[0] + 3);
});

test('a row nobody answered that no longer fits still stops the load', () => {
  const { files, c } = drafted();
  const m = modelFromFiles(files), log = new EditLog(m);
  const err = log.load([{ n: 1, op: 'ref.move', space: 'exterior', id: c, before: { pos: [0, 0, 0] }, after: { pos: [1, 0, 0] } }]);
  assert.ok(err);
});
