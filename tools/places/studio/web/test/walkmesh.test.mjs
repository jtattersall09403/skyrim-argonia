// js/walkmesh.js: the Walking mesh view's data (islands, colours, labels, the checks' pins, the mesh's age), and the
// walking zones' ops through the edit log (draw, save, reload, undo, redo, a note).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { islands, meshDraw, islandText, pinsFromCheck, plainLine, staleness, COLOURS } from '../js/walkmesh.js';
import { EditLog, modelFromFiles, modelToFiles, describe } from '../js/edits.js';

const here = dirname(fileURLToPath(import.meta.url));
const check = JSON.parse(readFileSync(join(here, 'walk_check.json'), 'utf8'));

// two triangles joined (the main mesh, a square 0..1000), one more far off (an island in reach), one beyond reach,
// a door on the first
const space = {
  verts: [0, 0, 0, 1000, 0, 0, 1000, 1000, 0, 0, 1000, 0, 2000, 0, 50, 2300, 0, 50, 2000, 300, 50, 90000, 0, 0, 90300, 0, 0, 90000, 300, 0],
  tris: [0, 1, 2, 0, 2, 3, 4, 5, 6, 7, 8, 9],
  nb: [-1, -1, 1, 0, -1, -1, -1, -1, -1, -1, -1, -1],
  kind: [0, 0, 0, 0],
  doors: [[0, 'fx.door1']],
};
const col = (d, i) => [...d.colours.slice(9 * i, 9 * i + 3)].map((v) => Math.round(v * 100) / 100);
const round = (c) => c.map((v) => Math.round(v * 100) / 100);

test('islands: triangles that share an edge are one; the largest is the main mesh', () => {
  const { label, sizes, main } = islands(space);
  assert.deepEqual(sizes, [2, 1, 1]); assert.equal(main, 0);
  assert.equal(label[0], label[1]); assert.notEqual(label[2], label[0]); assert.notEqual(label[3], label[2]);
});

test('colours: main calm, a cut-off island in reach in warning, the world beyond quieter, a door marked', () => {
  const d = meshDraw(space, { focus: { x: 500, y: 500, r: 5000 }, lift: 6 });
  assert.deepEqual(col(d, 0), round(COLOURS.door));
  assert.deepEqual(col(d, 1), round(COLOURS.main));
  assert.deepEqual(col(d, 2), round(COLOURS.island));
  assert.deepEqual(col(d, 3), round(COLOURS.world));
  assert.equal(d.positions[2], 6);    // lifted off the surface it lies on
  assert.equal(d.islands.length, 1);  // only the cut-off piece in reach is warned
  assert.equal(d.islands[0].tris, 1); assert.ok(Math.abs(d.islands[0].at[0] - 2100) < 1);
  assert.match(islandText(d.islands[0]), /^Cut off: 1 triangle \(about \d+ m²\)/);
  assert.equal(d.doors[0].ref, 'fx.door1');
  assert.deepEqual(d.counts, { tris: 4, islands: 1, main: 2 });
});

test('pins: each finding where it stands, in plain words; close ones share a pin', () => {
  const refs = { 'fx.door1': { id: 'fx.door1', space: 'exterior', pos: [100, 100, 0], door: { arrival: [150, 120, 4] } } };
  const people = {
    'fx.guard': { id: 'fx.guard', patrol: { points: [[10, 10], [4000, 4000], [20, 20]], loop: true } },
    'fx.cook': { id: 'fx.cook', routine: [{ at: { space: 'exterior', pos: [1, 1, 0] } }, { at: { space: 'FxHouse', pos: [7, 8, 9] } }] },
  };
  const ctx = { ref: (id) => refs[id] || null, person: (id) => people[id] || null, stop: (s) => (Array.isArray(s) ? s : s.pos) };
  const pins = pinsFromCheck(check, ctx);
  const at = (x, y) => pins.find((p) => Math.hypot(p.pos[0] - x, p.pos[1] - y) < 1);
  assert.deepEqual(at(150, 120).lines, ['This door\'s arrival point is inside another piece: people come through into a wall.']);
  assert.match(at(5100, 2000).lines[0], /off the walking mesh/);
  assert.match(at(8000, 8192).lines[0], /meet here but do not join/);
  const st = at(3000, 3000); assert.equal(st.raw.length, 2); assert.equal(st.lines.length, 1);   // two street points, one pin
  assert.match(at(4000, 4000).lines[0], /cannot walk from patrol point 1 to 2/);
  const cook = pins.find((p) => p.space === 'FxHouse'); assert.deepEqual(cook.pos, [7, 8, 9]);
  // a finding that names no place has no pin: the triangle-link line and the cook's "not a stop"
  assert.equal(pins.length, 7);
  assert.equal(plainLine('something new'), 'something new');
});

test('the mesh shown says when it is older than the place', () => {
  const builtAt = '2026-11-21T10:00:00Z';
  assert.equal(staleness({ builtAt, filesAt: '2026-11-21T09:00:00Z', ops: [] }).stale, false);
  const s = staleness({ builtAt, filesAt: '2026-11-21T11:00:00Z', ops: [] });
  assert.ok(s.stale); assert.match(s.words, /^What you see is from the last build/);
  const o = staleness({ builtAt, ops: [{ op: 'walk.add', at: '2026-11-21T10:05:00Z' }, { op: 'identity.edit', at: '2026-11-21T10:06:00Z' }] });
  assert.ok(o.stale); assert.match(o.words, /1 change since then is not in it yet/);
  assert.match(staleness({ builtAt, ops: [], from: 'preview' }).words, /with your changes/);
  assert.equal(staleness({ builtAt: null }).stale, false);
});

test('a walking zone: drawn, saved, reloaded, undone and redone, given a note', () => {
  const files = { place: { place_id: 'fx' }, spaces: { exterior: { refs: [], space: null } } };
  const m = modelFromFiles(files), log = new EditLog(m);
  const row = { id: 'fx.w1', kind: 'block', space: 'exterior', by: 'owner', outline: [[0, 0, 5], [400, 0, 5], [400, 400, 9]] };
  log.push({ op: 'walk.add', walk: row });
  const saved = modelToFiles(m);
  assert.deepEqual(saved.walk, [row]);
  assert.equal(describe(log.ops[0]), 'Marked "No walking here"');
  // the save as the server keeps it, applied again on a fresh load
  const m2 = modelFromFiles(files), log2 = new EditLog(m2); log2.load(JSON.parse(JSON.stringify(log.applied())), []);
  assert.deepEqual(modelToFiles(m2).walk, [row]);
  log2.undo(); assert.equal(modelToFiles(m2).walk, undefined);   // walk.jsonl kept only when it has rows
  log2.redo(); assert.deepEqual(modelToFiles(m2).walk, [row]);
  log2.push({ op: 'walk.edit', walk: { ...row, note: 'the guards should not cut through the hatchery' }, before: row });
  assert.equal(m2.walk.get('fx.w1').note, 'the guards should not cut through the hatchery');
  assert.equal(describe(log2.ops.at(-1)), 'Gave a walking zone a note');
  log2.push({ op: 'walk.remove', walk: m2.walk.get('fx.w1'), before: m2.walk.get('fx.w1') });
  assert.equal(m2.walk.size, 0); log2.undo(); assert.equal(m2.walk.size, 1);
});
