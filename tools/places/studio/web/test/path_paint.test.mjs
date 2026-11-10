import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PATH_FEATHER, PATH_STYLE_LTEX, opacityAt, pathLtex, cellOpacity } from '../js/path_paint.js';

const build = readFileSync(new URL('../../../build.py', import.meta.url), 'utf8');
test('the studio paints paths with the build numbers: the feather and the style to land texture table', () => {
  assert.equal(PATH_FEATHER, Number(build.match(/^PATH_FEATHER = ([\d.]+)/m)[1]));
  const table = build.match(/^PATH_STYLE_LTEX = (\{[\s\S]*?\})/m)[1];
  assert.deepEqual(PATH_STYLE_LTEX, JSON.parse(table));
  assert.ok(/op = np\.clip\(1 - \(d - half\) \/ PATH_FEATHER, 0, 1\)/.test(build), 'the build still feathers linearly');
});
test('opacity is full within the half width and falls to nothing over the feather', () => {
  assert.equal(opacityAt(0, 80), 1); assert.equal(opacityAt(80, 80), 1);
  assert.equal(opacityAt(80 + PATH_FEATHER / 2, 80), 0.5); assert.equal(opacityAt(80 + PATH_FEATHER, 80), 0);
});
test('a style word takes the land texture whose editor id ends with its word, as the build does', () => {
  const ltex = { 'A:1': { edid: 'ANW_Ground_dirt_road' }, 'A:2': { edid: 'ANW_Ground_dirt_grass' }, 'A:3': { edid: 'ANW_Ground_swamp_mud' } };
  assert.equal(pathLtex('dirt', ltex), 'A:1'); assert.equal(pathLtex('boardwalk', ltex), 'A:1');
  assert.equal(pathLtex('track', ltex), 'A:2'); assert.equal(pathLtex('mud', ltex), 'A:3'); assert.equal(pathLtex('A:2', ltex), 'A:2');
  assert.equal(pathLtex('dirt', { 'B:1': { edid: 'Grass' } }), null);
});
test('a cell gets the feathered opacity at its grid points; a boardwalk only ashore', () => {
  const t = { size: 4096, grid: 33, step: 128, cells: new Map([['0,0', { water: { height: 0 } }]]), h: (c, r) => (r < 16 ? -100 : 50) };
  const p = { style: 'dirt', width: 128, points: [[0, 2048], [4096, 2048]] };
  const op = cellOpacity(p, [0, 0], t);
  assert.equal(op[16 * 33 + 5], 1);          // on the line
  assert.ok(Math.abs(op[15 * 33 + 5] - (1 - (128 - 64) / PATH_FEATHER)) < 1e-6);  // one grid step (128) off: in the feather
  assert.equal(op[10 * 33 + 5], 0);          // far off
  assert.equal(cellOpacity(p, [5, 5], t), null);
  const bw = cellOpacity({ ...p, style: 'boardwalk' }, [0, 0], t);
  assert.equal(bw[15 * 33 + 5], 0); assert.equal(bw[16 * 33 + 5], 1);  // under water: none; ashore: painted
});
