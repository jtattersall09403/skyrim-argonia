import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PMIN, OP_MIN, SCATTER_SCALE, SCATTER_CUT, cover, cellPaint, nextId } from '../js/paint_rule.js';

const rule = readFileSync(new URL('../../../paint.py', import.meta.url), 'utf8');
// the Python rule's own numbers (tools/tests/test_places_paint.py proves the file is what paint.py gives)
const fx = JSON.parse(readFileSync(new URL('./paint_rule.json', import.meta.url), 'utf8'));
const pyNum = (name) => Number(rule.match(new RegExp(`^${name} = (-?[\\d.]+)`, 'm'))[1]);

test('the studio paints ground by the rule of paint.py: its constants', () => {
  assert.equal(PMIN, pyNum('PMIN')); assert.equal(OP_MIN, pyNum('OP_MIN')); assert.equal(SCATTER_SCALE, pyNum('SCATTER_SCALE'));
  assert.deepEqual(SCATTER_CUT, JSON.parse(`[${rule.match(/^SCATTER_CUT = \(([^)]*)\)/m)[1]}]`));
});
test('each brush covers what paint.py says it covers', () => {
  fx.rows.forEach((r, i) => fx.points.forEach(([x, y], j) => {
    assert.ok(Math.abs(cover(r, x, y) - fx.covers[i][j]) < 2e-4, `${r.id} at ${x},${y}: ${cover(r, x, y)} != ${fx.covers[i][j]}`);
  }));
});
test('a cell composites the rows as paint.py does: soft, hard, scatter, eraser and polygon', () => {
  const got = cellPaint(fx.rows, fx.cell);
  for (let k = 0; k < fx.total.length; k++) assert.ok(Math.abs(got.total[k] - fx.total[k]) < 2e-4, `total ${k}`);
  assert.deepEqual([...got.w.keys()].sort(), Object.keys(fx.weights).sort());
  for (const [key, w] of Object.entries(fx.weights)) for (let k = 0; k < w.length; k++) assert.ok(Math.abs(got.w.get(key)[k] - w[k]) < 2e-4, `${key} ${k}`);
  assert.equal(cellPaint(fx.rows, [5, 5]), null);
  assert.equal(nextId(fx.rows), 'paint.0006');
});
