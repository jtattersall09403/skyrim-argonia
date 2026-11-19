// A quest thing's spot as an edit: placing, moving, turning and clearing it go through the edit log like any change,
// and undo gives the spot back.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spotRow, moveOp, turned } from '../js/quest_ops.js';
import { modelFromFiles, modelToFiles, applyOp, revertOp } from '../js/edits.js';

const item = { id: 'quest.main.mn04/thing.mn04.cage', quest: 'quest.main.mn04', ref: 'thing.mn04.cage' };

test('the row names the quest and ref and rounds the spot', () => {
  assert.deepEqual(spotRow(item, 'exterior', [1.234, 2.345, 3.456], 1.23456),
    { id: item.id, quest: 'quest.main.mn04', ref: 'thing.mn04.cage', space: 'exterior', pos: [1.23, 2.35, 3.46], rot: [0, 0, 1.23] });
});

test('place, move, clear and undo through the edit model', () => {
  const m = modelFromFiles({ spaces: { exterior: [] } });
  const a = spotRow(item, 'exterior', [100, 200, 5], 0), b = spotRow(item, 'exterior', [400, 200, 9], turned(0, -Math.PI / 12));
  const add = { n: 1, ...moveOp(null, a) }, edit = { n: 2, ...moveOp(a, b) }, clear = { n: 3, ...moveOp(b, null) };
  assert.equal(add.op, 'quest.add'); assert.equal(edit.op, 'quest.edit'); assert.equal(clear.op, 'quest.remove');
  applyOp(m, add); applyOp(m, edit);
  assert.deepEqual(modelToFiles(m).quests, [b]);
  assert.ok(Math.abs(b.rot[2] - (2 * Math.PI - Math.PI / 12)) < 0.01, 'a left turn from north wraps round');
  applyOp(m, clear); assert.equal(modelToFiles(m).quests, undefined, 'no rows: no list');
  revertOp(m, clear); revertOp(m, edit); assert.deepEqual(modelToFiles(m).quests, [a]);
});

test('no change is no op', () => {
  const a = spotRow(item, 'exterior', [1, 2, 3], 0);
  assert.equal(moveOp(a, { ...a }), null);
  assert.equal(moveOp(null, null), null);
});
