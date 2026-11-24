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

test('an op of an answered note on a row the answer removed is kept as no change', () => {
  const { files, a, was } = drafted();
  files.spaces.exterior.refs = files.spaces.exterior.refs.filter((r) => r.id !== a);   // the answer removed a, as he did
  const m = modelFromFiles(files), log = new EditLog(m);
  const ops = [
    { n: 1, op: 'ref.move', space: 'exterior', id: a, note_group: 'g8', before: { pos: was.a }, after: { pos: [was.a[0] + 1, was.a[1], was.a[2]] } },
    { n: 2, op: 'ref.remove', space: 'exterior', id: a, note_group: 'g8', before: { id: a, pos: [was.a[0] + 1, was.a[1], was.a[2]] } },
  ];
  assert.equal(log.load(ops, [{ id: 'g8', text: 'fix it' }]), null);
  assert.ok(!m.spaces.exterior.refs.get(a) || m.spaces.exterior.refs.get(a).removed);
});

test('his changes a later request of his undid replay as no change', () => {
  const { files, c } = drafted();
  const r = files.spaces.exterior.refs.find((x) => x.id === c);
  const was = [...r.pos];
  files.place.agent_answers.push({ answers: 'request-1', rows: [c], undoes: ['g2'] });
  const m = modelFromFiles(files), log = new EditLog(m);
  const ops = [
    { n: 1, op: 'ref.move', space: 'exterior', id: c, note_group: 'g2', before: { pos: was }, after: { pos: [was[0] + 9, was[1], was[2]] } },
    { n: 2, op: 'ref.remove', space: 'exterior', id: c, note_group: 'g2', before: { ...r, pos: [was[0] + 9, was[1], was[2]] } },
  ];
  assert.equal(log.load(ops, [{ id: 'g2', text: 'in the way' }]), null);
  assert.deepEqual(m.spaces.exterior.refs.get(c).pos, was);
  assert.ok(!m.spaces.exterior.refs.get(c).removed);
});

test('his unit moves and person edits replay over answers by the same rule', () => {
  const { files, a, b, was } = drafted();
  files.people = [...(files.people || []), { id: 'fx.p1', name: 'P', routine: [{ start: 8, kind: 'wander', at: { space: 'exterior', pos: [9, 9] } }] }];
  files.place.agent_answers.push({ save: 'agent-a', stroke: 2, answers: 'g12', rows: ['fx.p1'] });
  const p0 = { id: 'fx.p1', name: 'P', routine: [{ start: 8, kind: 'wander', at: { space: 'exterior', pos: [0, 0] } }] };
  const m = modelFromFiles(files), log = new EditLog(m);
  const ops = [
    { n: 1, op: 'unit.move', space: 'exterior', unit: 'u1', note_group: 'g8', refs: [
      { id: a, before: { pos: was.a }, after: { pos: [was.a[0] + 100, was.a[1], was.a[2]] } },
      { id: b, before: { pos: was.b }, after: { pos: [was.b[0] + 100, was.b[1], was.b[2]] } }] },
    { n: 2, op: 'person.edit', note_group: 'g12', person: { ...p0, routine: [{ start: 8, kind: 'wander', at: { space: 'exterior', pos: [5, 5] } }] }, before: p0 },
  ];
  assert.equal(log.load(ops, [{ id: 'g8', text: 'fix it' }, { id: 'g12', text: 'taste' }]), null);
  assert.equal(m.spaces.exterior.refs.get(a).pos[0], was.a[0] + 107);   // answered for g8: the answer stands
  assert.equal(m.spaces.exterior.refs.get(b).pos[0], was.b[0] + 3);     // b answered for g8 too: that answer stands
  assert.deepEqual(m.people.get('fx.p1').routine[0].at.pos, [9, 9]);    // g12 answered: the answer stands
});

test('an answer that keeps a row as the draft had it stands against his op of that note', () => {
  const { files, c } = drafted();
  const r = files.spaces.exterior.refs.find((x) => x.id === c), was = [...r.pos];
  files.place.agent_answers.push({ answers: 'g10', rows: [c] });
  const m = modelFromFiles(files), log = new EditLog(m);
  assert.equal(log.load([{ n: 1, op: 'ref.move', space: 'exterior', id: c, note_group: 'g10', before: { pos: was }, after: { pos: [was[0] + 300, was[1], was[2]] } }], [{ id: 'g10', text: 'tents' }]), null);
  assert.deepEqual(m.spaces.exterior.refs.get(c).pos, was);
});

test('his changes with no note are answered as unnoted, an add included', () => {
  const { files, c } = drafted();
  const r = files.spaces.exterior.refs.find((x) => x.id === c);
  const torch = { ...r, id: 'fx.torch', pos: [r.pos[0] + 5, r.pos[1], r.pos[2]] };
  files.spaces.exterior.refs.push({ ...torch });
  files.place.agent_answers.push({ answers: 'unnoted', rows: ['fx.torch'] });
  const m = modelFromFiles(files), log = new EditLog(m);
  assert.equal(log.load([{ n: 1, op: 'ref.add', space: 'exterior', ref: torch }]), null);
  assert.ok(m.spaces.exterior.refs.get('fx.torch'));
});
