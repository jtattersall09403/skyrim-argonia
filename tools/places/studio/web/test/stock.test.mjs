// js/stock.js: the scale's verdict on an item, the rows a change builds, and the history's words for content ops.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { allowedItem, containerKind, withItem, withCount, withoutItem, withLock, withGold, withBackstory, opFor,
  describeContent, containerOf, looseAt, tierLabel, OWNER_WHY } from '../js/stock.js';
import { modelFromFiles, applyOp, inverse, same, modelToFiles } from '../js/edits.js';

const here = dirname(fileURLToPath(import.meta.url));
const REPO = join(here, '../../../../..');
const raw = JSON.parse(readFileSync(join(REPO, 'newworld/sources/stock/scale.json'), 'utf8'));
// the scale as the server sends it (tools/places/studio/stock.py scale_view)
const scale = { tiers: raw.tiers.map(({ id, rank, label }) => ({ id, rank, label })),
  container_kinds: raw.split.container_kinds, always_significant_containers: raw.split.always_significant_containers };
const base = JSON.parse(readFileSync(join(here, '../../../../tests/places_edits/stock/base.json'), 'utf8'));
const C1 = base.stock.containers[0];

test('an item above the ceiling or on the never list is refused with its reason', () => {
  assert.deepEqual(allowedItem({ tier: 'T2' }, 'T4', scale).ok, true);
  const high = allowedItem({ tier: 'T5' }, 'T4', scale);
  assert.equal(high.ok, false);
  assert.match(high.why, /T5 Precious, above this place's ceiling T4 Rare/);
  const nordic = allowedItem({ tier: 'T1', never: 'DLC2WeaponMaterialNordic is Skyrim\'s own gear' }, 'T4', scale);
  assert.equal(nordic.ok, false);
  assert.match(nordic.why, /^Not allowed: DLC2WeaponMaterialNordic/);
  assert.match(allowedItem({ tier: null }, 'T4', scale).why, /not measured yet/);
  assert.equal(tierLabel(scale, null), 'tier not measured yet');
});

test('a container kind from its base words, as the split reads it', () => {
  assert.deepEqual(containerKind({ edid: 'NobleChest01' }, scale), { kind: 'chest', always: true });
  assert.deepEqual(containerKind({ edid: 'BarrelFood01' }, scale), { kind: 'barrel', always: false });
  assert.deepEqual(containerKind({ edid: 'Fix_Thing' }, scale), { kind: 'other', always: false });
});

test('changes are whole rows; the op made from them applies and undoes', () => {
  let row = withItem(C1, 'Skyrim.esm:01397E', 2);
  assert.equal(row.items.at(-1).why, OWNER_WHY);
  assert.equal(withItem(row, 'Skyrim.esm:01397E', 1).items.at(-1).count, 3, 'the same item again raises its count');
  row = withCount(row, 'Skyrim.esm:01397E', 0);
  assert.equal(row.items.at(-1).count, 1, 'a count is never below one: removing is its own change');
  row = withLock(withGold(row, '45.4'), null);
  assert.equal(row.gold, 45); assert.ok(!('lock' in row));
  assert.equal(withoutItem(row, 'Skyrim.esm:013989').items.length, 1);
  assert.deepEqual(C1.items.length, 1, 'the row before is never changed');
  const m = modelFromFiles(base), before = modelToFiles(m);
  const op = { n: 1, ...opFor('container', containerOf(m.stock, 'House', 'fixture.chest1'), row) };
  applyOp(m, op);
  assert.equal(containerOf(m.stock, 'House', 'fixture.chest1').gold, 45);
  applyOp(m, inverse(op));
  assert.ok(same(modelToFiles(m), before));
  assert.equal(looseAt(m.stock, 'House', 'fixture.table1').length, 1, 'a thing lying on a ref is found by it');
  const p = withBackstory(base.identities.people.find((x) => x.id === 'fixture.p2'), 'He keeps the dock.');
  assert.deepEqual(p.notes[0], { aspect: 'backstory', text: 'He keeps the dock.', tier: 'AGENT_INVENTED', cites: [] });
});

test('the history says what changed in plain words', () => {
  const name = (k) => ({ 'Skyrim.esm:01397E': 'Iron War Axe', 'fixture.chest1': 'Chest', 'fixture.p1': 'Ada' }[k] || k);
  const row = withLock(withItem(C1, 'Skyrim.esm:01397E', 2), 'Apprentice');
  assert.equal(describeContent(opFor('container', C1, row), name), 'Chest: added 2 × Iron War Axe; lock Novice → Apprentice');
  const p0 = base.identities.people.find((x) => x.id === 'fixture.p1');
  assert.equal(describeContent(opFor('identity', p0, { ...withBackstory(p0, 'x'), wealth: 'W4' }), name), 'Ada: wealth W3 → W4; backstory');
  const t = base.stock.traders[0];
  assert.equal(describeContent(opFor('trader', t, { ...t, gold: 600 }), name), "Ada's wares: gold 500 → 600");
});
