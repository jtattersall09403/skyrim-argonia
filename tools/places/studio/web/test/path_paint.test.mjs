import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PULL_E, PULL_W, CORE_IN, CORE_OUT, TRACK_MIN, SCALE, STYLE_CLASS, ROAD_SETS, PATH_STYLE_LTEX, LTEX_PREFIX, pull, layerOpacities,
  roadWeights, roadMix, pathLtexes, pathLtex, roadSetName, cellLayers } from '../js/path_paint.js';

const rule = readFileSync(new URL('../../../../newworld/world/roadpaint.py', import.meta.url), 'utf8');
const build = readFileSync(new URL('../../../build.py', import.meta.url), 'utf8');
// the Python rule's own numbers (tools/tests/test_newworld_ground.py proves the file is what roadpaint.py gives)
const fixture = JSON.parse(readFileSync(new URL('./road_rule.json', import.meta.url), 'utf8'));
const pyTuple = (name) => JSON.parse(`[${rule.match(new RegExp(`^${name} = \\(([^)]*)\\)`, 'm'))[1]}]`);
const pyNum = (name) => Number(rule.match(new RegExp(`${name} = (-?[\\d.]+)`))[1]);

test('the studio paints paths by the world road rule: the ramp, the core, the classes and the road sets of roadpaint.py', () => {
  assert.deepEqual(PULL_E, pyTuple('PULL_E')); assert.deepEqual(PULL_W, pyTuple('PULL_W'));
  assert.equal(CORE_IN, Number(rule.match(/^CORE_IN, CORE_OUT = (-?[\d.]+), (-?[\d.]+)/m)[1]));
  assert.equal(CORE_OUT, Number(rule.match(/^CORE_IN, CORE_OUT = (-?[\d.]+), (-?[\d.]+)/m)[2]));
  assert.equal(TRACK_MIN, pyNum('TRACK_MIN'));
  assert.deepEqual(SCALE, JSON.parse(rule.match(/^SCALE = (\{[^}]*\})/m)[1]));
  assert.deepEqual(STYLE_CLASS, JSON.parse(rule.match(/^STYLE_CLASS = (\{[^}]*\})/m)[1]));
  for (const [name, set] of Object.entries(ROAD_SETS)) {
    const m = rule.match(new RegExp(`"${name}": \\(([^)]*)\\)`));
    assert.deepEqual(set, JSON.parse(`[${m[1]}]`), name);
  }
  assert.deepEqual(ROAD_SETS, fixture.road_sets);
  assert.deepEqual(PATH_STYLE_LTEX, JSON.parse(build.match(/^PATH_STYLE_LTEX = (\{[^}]*\})/m)[1]));
  assert.equal(LTEX_PREFIX, build.match(/^WORLD_LTEX_PREFIX = "([^"]*)"/m)[1]);
});
test('the ramp is full on the path, straight beyond it, and gone at its reach', () => {
  assert.equal(pull(-3, 1), 1); assert.ok(Math.abs(pull(4.05, 1) - 0.485) < 1e-9); assert.equal(pull(8.55, 1), 0);
  assert.ok(Math.abs(pull(4.05 * 0.8, 0.8) - 0.485) < 1e-9);
  // one vertex (1.83 m) further out never costs more than 0.31 (Skyrim's mean road ramp), on either class
  for (const scale of Object.values(SCALE)) for (let e = -5; e < 10; e += 0.25) assert.ok(Math.abs(pull(e, scale) - pull(e + 128 / 70, scale)) <= 0.31);
});
test('the along-road mix, the weights and the three layers are the Python rule\'s own numbers', () => {
  assert.ok(fixture.road_mix.length >= 5 && fixture.cases.length >= 50);
  for (const { x, y, value } of fixture.road_mix) assert.ok(Math.abs(roadMix(x, y) - value) < 2e-6, `${x},${y}: ${roadMix(x, y)} vs ${value}`);
  for (const c of fixture.cases) {
    roadWeights(c.e, c.scale, c.mix).forEach((v, i) => assert.ok(Math.abs(v - c.weights[i]) < 2e-6, `weights ${JSON.stringify(c)}: ${v}`));
    layerOpacities(c.e, c.scale, c.mix).forEach((v, i) => assert.ok(Math.abs(v - c.opacities[i]) < 2e-6, `opacities ${JSON.stringify(c)}: ${v}`));
  }
});
test('a style takes the road set of the ground, a one-texture style its texture, a picked key itself', () => {
  const ltex = { 'A:1': { edid: 'ANW_Ground_gravel_track' }, 'A:2': { edid: 'ANW_Ground_mud_track' }, 'A:3': { edid: 'ANW_Ground_verge' },
    'A:4': { edid: 'ANW_Ground_swamp_mud' }, 'A:5': { edid: 'ANW_Ground_sand_track' }, 'A:6': { edid: 'ANW_Ground_clay_verge' } };
  assert.deepEqual(pathLtexes('dirt', ltex, 'forest'), ['A:1', 'A:2', 'A:3']);
  assert.deepEqual(pathLtexes('road', ltex, 'marsh'), ['A:2', 'A:1', 'A:3']);
  assert.deepEqual(pathLtexes('mud', ltex), ['A:4', 'A:4', 'A:4']); assert.deepEqual(pathLtexes('A:2', ltex), ['A:2', 'A:2', 'A:2']);
  assert.equal(pathLtex('dirt', ltex, 'coast'), 'A:5'); assert.equal(pathLtexes('dirt', { 'B:1': { edid: 'Grass' } }), null);
  // a material is found by its whole name: `verge` is never `clay_verge`, whichever the land lists first
  const clayFirst = { 'A:6': ltex['A:6'], ...ltex };
  assert.deepEqual(pathLtexes('dirt', clayFirst, 'forest'), ['A:1', 'A:2', 'A:3']);
  const terrain = { ltex, list: [{ quadrants: [{ base: 'A:5', layers: [{ tex: 'A:6' }] }] }] };
  assert.equal(roadSetName(terrain), 'coast'); assert.equal(roadSetName({ ltex, list: [] }), 'forest');
});
test('a cell gets the three layer opacities at its grid points; a boardwalk only ashore', () => {
  const t = { size: 4096, grid: 33, step: 128, cells: new Map([['0,0', { water: { height: 0 } }]]), h: (c, r) => (r < 16 ? -100 : 50) };
  const p = { style: 'dirt', width: 128, points: [[0, 2048], [4096, 2048]] };
  const ops = cellLayers(p, [0, 0], t);
  const total = (i) => ops[0][i] + ops[1][i] + ops[2][i];  // the engine adds the layers
  assert.ok(total(16 * 33 + 5) > 0.97);       // on the line
  assert.ok(total(15 * 33 + 5) > 0.5);        // one grid step (128) off: still mostly path
  assert.ok(total(14 * 33 + 5) > 0.2 && total(14 * 33 + 5) < total(15 * 33 + 5));  // two steps: the ramp
  assert.equal(total(10 * 33 + 5), 0);        // far off
  assert.equal(cellLayers(p, [5, 5], t), null);
  const bw = cellLayers({ ...p, style: 'boardwalk' }, [0, 0], t);
  assert.equal(bw[2][15 * 33 + 5], 0); assert.ok(bw[2][16 * 33 + 5] > 0);  // under water: none; ashore: painted
});
