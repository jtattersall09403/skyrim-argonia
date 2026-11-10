import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Walk, along, thin } from '../js/routes.js';

const bases = new Map([['wall', { model: 'x/hut.nif', bounds: [[-600, -100, 0], [600, 100, 300]] }],
  ['deck', { model: 'x/docks/dockstr01.nif', bounds: [[-150, -700, 0], [150, 700, 40]] }]]);
const inBox = (p, b, pos) => p[0] > pos[0] + b[0][0] + 60 && p[0] < pos[0] + b[1][0] - 60 && p[1] > pos[1] + b[0][1] + 60 && p[1] < pos[1] + b[1][1] - 60;

test('a route goes round a building, not through it', () => {
  const w = new Walk({ refs: [{ kind: 'building', base: 'wall', pos: [0, 0, 0], rot: [0, 0, 0], scale: 1 }], bases });
  const r = w.route([0, -1000], [0, 1000]);
  assert.ok(r.length > 2, 'not the straight line');
  assert.ok(!r.some((p) => inBox(p, bases.get('wall').bounds, [0, 0])), 'no point inside the wall');
  assert.deepEqual(r[0], [0, -1000]); assert.deepEqual(r[r.length - 1], [0, 1000]);
});

test('a route takes the street when one leads the right way', () => {
  const street = { points: [[-2000, 600], [2000, 600]], width: 256 };
  const w = new Walk({ paths: [street] });
  const r = w.route([-2000, 0], [2000, 0]);
  const on = r.filter((p) => Math.abs(p[1] - 600) < 200).length;
  assert.ok(on >= r.length / 2, `most of the way is on the street (${on} of ${r.length})`);
});

test('open water is not walked, a deck over it is', () => {
  const terrain = { heightAt: (x, y) => (Math.abs(y) < 500 ? -100 : 10), waterAt: () => 0 };
  const dry = new Walk({ terrain });
  assert.equal(dry.route([0, -1500], [0, 1500]).length, 2, 'no way across: the straight line');
  const w = new Walk({ terrain, bases, refs: [{ kind: 'building', base: 'deck', pos: [900, 0, 0], rot: [0, 0, 0], scale: 1 }] });
  const r = w.route([0, -1500], [0, 1500]);
  const over = r.filter((p) => Math.abs(p[1]) < 400);
  assert.ok(over.length && over.every((p) => Math.abs(p[0] - 900) < 220), 'the crossing is on the deck');
});

test('along and thin', () => {
  assert.deepEqual(along([[0, 0], [100, 0], [100, 100]], 0.75), [100, 50]);
  assert.equal(thin([[0, 0], [50, 1], [100, 0]], 5).length, 2);
});

test('a leg that starts inside a building (a hatch on a ship) walks out of that building, and round any other', () => {
  const big = new Map([['ship', { model: 'x/ship.nif', bounds: [[-900, -300, 0], [900, 300, 400]] }], ['hut', { model: 'x/hut.nif', bounds: [[-300, -300, 0], [300, 300, 300]] }]]);
  const w = new Walk({ bases: big, refs: [{ kind: 'building', base: 'ship', pos: [0, 0, 0], rot: [0, 0, 0], scale: 1 }, { kind: 'building', base: 'hut', pos: [0, 1500, 0], rot: [0, 0, 0], scale: 1 }] });
  const r = w.route([-700, 0], [0, 3000]);
  assert.ok(r.length > 2, 'a way out of the ship was found');
  assert.ok(!r.some((p) => Math.abs(p[0]) < 200 && Math.abs(p[1] - 1500) < 200), 'not through the hut');
});
