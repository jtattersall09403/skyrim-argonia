import assert from 'node:assert/strict';
import { whereOf, whereRows } from '../js/where.js';

// one thing outside: whole numbers, its cell (floor of position / 4096, negatives round down), its turn in degrees
const one = whereOf([{ pos: [-46749.92, -613207.04, 22.81], rot: [0, 0, Math.PI / 2] }]);
assert.deepEqual(one.pos, [-46750, -613207, 23]);
assert.deepEqual(one.cell, [-12, -150]);
assert.equal(one.turn, 90);
assert.equal(one.tilt, undefined);
// a negative turn reads as its compass equivalent
assert.equal(whereOf([{ pos: [0, 0, 0], rot: [0, 0, -Math.PI / 4] }]).turn, 315);
// several: the middle of their positions, no single turn
const two = whereOf([{ pos: [0, 0, 0] }, { pos: [4096, 100, 50] }]);
assert.deepEqual(two.pos, [2048, 50, 25]); assert.ok(two.several); assert.equal(two.turn, undefined);
// inside a room there is no exterior cell
assert.equal(whereOf([{ pos: [10, 20, 30] }], { exterior: false }).cell, undefined);
assert.deepEqual(whereRows(one).map((r) => r[0]), ['Position (game units)', 'Cell', 'Turned']);
assert.equal(whereRows(one)[0][1], 'x -46750, y -613207, z 23');
assert.equal(whereOf([]), null);
console.log('where ok');
