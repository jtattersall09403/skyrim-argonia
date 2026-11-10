// Notes on changes: one note for the changes since the last note, trimmed, edited, removed; undo and a save's
// round trip keep each note with exactly its changes.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EditLog, emptyModel } from '../js/edits.js';
import { pending, groupsOf, changesOf, newNoteId, touched } from '../js/note_groups.js';

const add = (id, x = 0) => ({ op: 'ref.add', ref: { id, base: 'B', pos: [x, 0, 0], rot: [0, 0, 0], scale: 1 } });
const move = (id, a, b) => ({ op: 'ref.move', id, before: { pos: [a, 0, 0] }, after: { pos: [b, 0, 0] } });
function log3() {
  const L = new EditLog(emptyModel());
  L.push(add('a')); L.push(add('b')); L.push(add('c'));
  return L;
}
const ns = (ops) => ops.map((o) => o.n);

test('three changes, one note: the note covers all three and the next count starts at nothing', () => {
  const L = log3();
  assert.equal(pending(L.applied()).length, 3);
  L.setNote(ns(pending(L.applied()).flat()), 'stalls must never block a walkway', 'fault');
  const g = groupsOf(L.applied(), L.notes);
  assert.equal(g.length, 1);
  assert.equal(g[0].text, 'stalls must never block a walkway');
  assert.deepEqual(ns(g[0].ops), [1, 2, 3]);
  assert.equal(pending(L.applied()).length, 0);
  L.push(move('a', 0, 5));
  assert.deepEqual(ns(pending(L.applied()).flat()), [4]);
  assert.equal(L.notesFor().length, 1, 'the note is written once');
  assert.ok(L.applied().slice(0, 3).every((o) => o.note_group === g[0].id && !('note' in o)));
});

test('a count trimmed to the last change; changes never noted stay unnoted', () => {
  const L = log3();
  L.setNote(ns(pending(L.applied()).slice(-1).flat()), 'too close to the door', 'taste');
  assert.deepEqual(L.applied().map((o) => [o.call, !!o.note_group]), [['fault', false], ['fault', false], ['taste', true]]);
  assert.equal(pending(L.applied()).length, 0, 'the changes before a note are no longer counted');
});

test('a stroke is one change', () => {
  const L = new EditLog(emptyModel());
  L.push([add('a'), add('b')]);
  L.push(add('c'));
  assert.equal(changesOf(L.applied()).length, 2);
  L.setNote([1], 'one stroke', 'fault');
  assert.deepEqual(groupsOf(L.applied(), L.notes)[0].ops.map((o) => o.n), [1, 2]);
});

test('undo keeps it consistent: the note covers what is applied, comes back on redo, the save holds it once', () => {
  const L = log3();
  L.setNote([1, 2, 3], 'move them', 'fault');
  L.undo();
  let g = groupsOf(L.applied(), L.notes);
  assert.deepEqual(ns(g[0].ops), [1, 2]);
  L.undo(); L.undo();
  assert.equal(groupsOf(L.applied(), L.notes).length, 0);
  assert.deepEqual(L.notesFor(), []);
  L.redo(); L.redo(); L.redo();
  g = groupsOf(L.applied(), L.notes);
  assert.deepEqual(ns(g[0].ops), [1, 2, 3]);
  // the save's round trip
  const save = { ops: JSON.parse(JSON.stringify(L.applied())), notes: L.notesFor() };
  const M = new EditLog(emptyModel());
  assert.equal(M.load(save.ops, save.notes), null);
  assert.deepEqual(groupsOf(M.applied(), M.notes).map((x) => [x.text, ns(x.ops)]), [['move them', [1, 2, 3]]]);
});

test('a note edited in place, picked changes renoted, a note removed', () => {
  const L = log3();
  L.setNote([1, 2], 'first words');
  const id = L.ops[0].note_group;
  L.setNote([1, 2], 'better words');
  assert.equal(L.ops[0].note_group, id);
  assert.equal(L.notes.get(id).text, 'better words');
  L.setNote([2, 3], 'other words');
  const g = groupsOf(L.applied(), L.notes);
  assert.deepEqual(g.map((x) => [x.text, ns(x.ops)]), [['better words', [1]], ['other words', [2, 3]]]);
  L.setNote([1], '');
  assert.equal(L.ops[0].note_group, undefined);
  assert.ok(!L.notes.has(id), 'a note with no changes left is dropped');
  assert.equal(newNoteId(L.notes), 'g3');
});

test('an older save: per-op notes still read as notes on their changes', () => {
  const L = new EditLog(emptyModel());
  const ops = [{ ...add('a'), n: 1, note: 'by the water' }, { ...add('b'), n: 2, note: 'by the water' }, { ...add('c'), n: 3 }, { ...add('d'), n: 4, note: 'other' }];
  assert.equal(L.load(ops), null);
  const g = groupsOf(L.applied(), L.notes);
  assert.deepEqual(g.map((x) => [x.text, ns(x.ops), x.legacy]), [['by the water', [1, 2], true], ['other', [4], true]]);
  assert.equal(pending(L.applied()).length, 0);
  L.setNote([1, 2], 'by the water, always');
  assert.ok(!('note' in L.ops[0]) && L.ops[0].note_group);
  assert.deepEqual(touched(L.ops.slice(0, 1)), [{ id: 'a', space: 'exterior', kind: 'ref' }]);
});
