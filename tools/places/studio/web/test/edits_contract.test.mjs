// The front end's edit mirror against the shared fixtures of tools/places/edits.py (tools/tests/places_edits/).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { modelFromFiles, modelToFiles, applyOp, inverse, checkDoors, EditLog, same } from '../js/edits.js';

const here = dirname(fileURLToPath(import.meta.url));
const FIX = join(here, '../../../../tests/places_edits');
const place = JSON.parse(readFileSync(join(FIX, 'place.json'), 'utf8'));
const canon = (f) => modelToFiles(modelFromFiles(f));

const cases = [
  ...readdirSync(FIX).filter((f) => f.endsWith('.json') && f !== 'place.json'),
  ...readdirSync(join(FIX, 'copy_refs')).filter((f) => f.endsWith('.json')).map((f) => join('copy_refs', f)),
];
for (const name of cases) {
  const c = JSON.parse(readFileSync(join(FIX, name), 'utf8'));
  test(`fixture ${name}`, () => {
    const m = modelFromFiles(place); m.source = c.source;
    if (c.error) {
      assert.throws(() => { for (const op of c.ops) applyOp(m, op); checkDoors(m, c.ops); }, new RegExp(c.error));
      return;
    }
    for (const op of c.ops) applyOp(m, op);
    checkDoors(m, c.ops);
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

// The content ops (identity.edit, stock.*) on a people and a stock source: the same files as edits.py.
const STOCK = join(FIX, 'stock'), stockBase = JSON.parse(readFileSync(join(STOCK, 'base.json'), 'utf8'));
for (const name of readdirSync(STOCK).filter((f) => f.endsWith('.json') && f !== 'base.json')) {
  const c = JSON.parse(readFileSync(join(STOCK, name), 'utf8'));
  test(`content fixture ${name}`, () => {
    const m = modelFromFiles({ ...place, ...stockBase });
    if (c.error) { assert.throws(() => { for (const op of c.ops) applyOp(m, op); }, new RegExp(c.error)); return; }
    for (const op of c.ops) applyOp(m, op);
    const got = modelToFiles(m), want = modelToFiles(modelFromFiles({ ...place, ...c.expected }));
    assert.ok(same(got.identities, want.identities) && same(got.stock, want.stock), `sources differ:\n${JSON.stringify(got.stock)}\n${JSON.stringify(want.stock)}`);
    for (const op of [...c.ops].reverse()) applyOp(m, inverse(op));
    assert.ok(same(modelToFiles(m), canon({ ...place, ...stockBase })), 'inverse did not restore the sources');
  });
}

test('content ops undo and redo through the log, and need their source', () => {
  const c = JSON.parse(readFileSync(join(STOCK, 'content_all.json'), 'utf8'));
  const m = modelFromFiles({ ...place, ...stockBase }), log = new EditLog(m), start = modelToFiles(m);
  for (const op of c.ops) log.push({ ...op, n: undefined });
  const after = modelToFiles(m);
  while (log.canUndo()) log.undo();
  assert.ok(same(modelToFiles(m), start));
  while (log.canRedo()) log.redo();
  assert.ok(same(modelToFiles(m), after));
  assert.throws(() => applyOp(modelFromFiles(place), c.ops[0]), /no people source/);
});

// The studio's model holds a copied room's refs resolved (the draft bundle's rows: source rows with ours over
// them, so every piece of furniture is a row and none is "unlisted"). Moving or removing one there must give
// the room finalise writes, read back through the bundle's rule (draft_bundle.copy_space).
test('a copied room edited as resolved rows equals the files finalise writes, resolved', () => {
  const resolve = (rows, source) => {
    const out = new Map(source.map((r) => [r.id, r]));
    for (const r of rows) {
      if (r.src) { if (!out.has(r.src)) continue; if (r.removed) { out.delete(r.src); continue; } const o = { ...out.get(r.src), ...r }; out.delete(r.src); out.set(r.id, o); }
      else if (!r.removed) out.set(r.id, r);
    }
    return [...out.values()].sort((a, b) => (a.id < b.id ? -1 : 1));
  };
  for (const name of ['copy_move.json', 'copy_remove.json']) {
    const c = JSON.parse(readFileSync(join(FIX, 'copy_refs', name), 'utf8')), sid = c.ops[0].space;
    const listed = modelFromFiles(place); listed.source = c.source;
    for (const op of c.ops) applyOp(listed, op);
    const want = resolve(modelToFiles(listed).spaces[sid].refs, c.source[sid]);
    const studio = modelFromFiles({ ...place, spaces: { ...place.spaces, [sid]: { refs: c.source[sid], space: { copy_of: 'bmv.fixture/' + sid } } } });
    for (const op of c.ops) applyOp(studio, op);
    assert.ok(same(modelToFiles(studio).spaces[sid].refs, want), `${name}: studio rows differ from finalise's room`);
  }
});
