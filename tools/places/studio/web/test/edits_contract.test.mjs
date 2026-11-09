// The front end's edit mirror against the shared fixtures of tools/places/edits.py (tools/tests/places_edits/).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { modelFromFiles, modelToFiles, applyOp, inverse, EditLog, same } from '../js/edits.js';

const here = dirname(fileURLToPath(import.meta.url));
const FIX = join(here, '../../../../tests/places_edits');
const place = JSON.parse(readFileSync(join(FIX, 'place.json'), 'utf8'));
const canon = (f) => modelToFiles(modelFromFiles(f));

for (const name of readdirSync(FIX).filter((f) => f.endsWith('.json') && f !== 'place.json')) {
  const c = JSON.parse(readFileSync(join(FIX, name), 'utf8'));
  test(`fixture ${name}`, () => {
    const m = modelFromFiles(place);
    if (c.error) {
      assert.throws(() => { for (const op of c.ops) applyOp(m, op); }, new RegExp(c.error));
      return;
    }
    for (const op of c.ops) applyOp(m, op);
    const got = modelToFiles(m), want = canon(c.expected);
    assert.ok(same(got, want), `files differ:\n${JSON.stringify(got)}\n${JSON.stringify(want)}`);
    // every op has an inverse: the save then its inverse gives back the files
    for (const op of [...c.ops].reverse()) applyOp(m, inverse(op));
    assert.ok(same(modelToFiles(m), canon(place)), 'inverse did not restore the files');
  });
}

test('undo and redo through the log give the same files', () => {
  const c = JSON.parse(readFileSync(join(FIX, 'all_ops.json'), 'utf8'));
  const m = modelFromFiles(place), log = new EditLog(m);
  for (const op of c.ops) log.push({ ...op, n: undefined });
  const after = modelToFiles(m);
  while (log.canUndo()) log.undo();
  assert.ok(same(modelToFiles(m), canon(place)));
  while (log.canRedo()) log.redo();
  assert.ok(same(modelToFiles(m), after));
  log.setCall([2], 'taste', 'I like it there');
  assert.equal(log.ops[1].call, 'taste'); assert.equal(log.ops[1].note, 'I like it there');
});
