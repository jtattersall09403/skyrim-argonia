// The warning before a change to something a story needs: which ops touch a need, and how.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { needChanges } from '../js/needs.js';

const need = { kind: 'need', n: { seq: 4, thing: 'a hall' } };
const use = { kind: 'use', pid: 'p1', person: { name: 'Xilsa' }, use: { for: 'tends roots' } };
const idx = new Map([['ref:door', [need]], ['person:p1', [use]]]);

test('removing a needed thing warns that it was removed', () => {
  const out = needChanges([{ op: 'ref.remove', id: 'door', before: {} }], idx);
  assert.deepEqual(out.map((o) => [o.u, o.change]), [[need, 'removed']]);
});

test('a small nudge does not warn; a move of more than ten metres or into another cell does', () => {
  assert.equal(needChanges([{ op: 'ref.move', id: 'door', before: { pos: [100, 100, 0] }, after: { pos: [132, 100, 0] } }], idx).length, 0);
  assert.equal(needChanges([{ op: 'ref.move', id: 'door', before: { pos: [100, 100, 0] }, after: { pos: [900, 100, 0] } }], idx)[0].change, 'moved');
  assert.equal(needChanges([{ op: 'ref.move', id: 'door', before: { pos: [4090, 100, 0] }, after: { pos: [4100, 100, 0] } }], idx)[0].change, 'moved');
});

test('things nobody needs never warn', () => {
  assert.equal(needChanges([{ op: 'ref.remove', id: 'other', before: {} }, { op: 'person.remove', person: { id: 'p2' } }], idx).length, 0);
});

test('a person a story uses: taken out, sent to work elsewhere, or renamed', () => {
  assert.equal(needChanges([{ op: 'person.remove', person: { id: 'p1' } }], idx)[0].change, 'removed');
  const moved = needChanges([{ op: 'person.edit', person: { id: 'p1', work: { space: 'hall' } }, before: { id: 'p1', work: { space: 'exterior', pos: [0, 0] } } }], idx);
  assert.equal(moved[0].change, 'moved');
  const routine = needChanges([{ op: 'person.edit', person: { id: 'p1', work: { space: 'exterior', pos: [10, 0] } }, before: { id: 'p1', work: { space: 'exterior', pos: [0, 0] } } }], idx);
  assert.equal(routine.length, 0);
  const renamed = needChanges([{ op: 'identity.edit', person: { id: 'p1', name: 'B' }, before: { id: 'p1', name: 'A' } }], idx);
  assert.deepEqual([renamed[0].change, renamed[0].what], ['renamed', 'renamed from A to B']);
});

test('one change touching a need twice warns once', () => {
  const out = needChanges([{ op: 'ref.remove', id: 'door', before: {} }, { op: 'ref.remove', id: 'door', before: {} }], idx);
  assert.equal(out.length, 1);
});
