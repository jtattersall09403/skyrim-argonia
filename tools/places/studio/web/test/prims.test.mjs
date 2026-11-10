import assert from 'node:assert/strict';
import { comesWith, halfExtents, hasPrim, isWall, primFacts, resized, scaledPrim, wallsOf } from '../js/prims.js';
import { localOf, poseFor } from '../js/lights.js';

const wallBase = { edid: 'CollisionMarker' };
const W = { id: 'w', base: 'cm', kind: 'marker', pos: [0, 0, 0], rot: [0, 0, 0], seat: { mode: 'on', on: 'p.deck' },
  primitive: { type: 'Box', bounds: [3467.5, 128, 40.8], color: [255, 255, 0], unknown: 0.15 } };
const S = { id: 's', base: 'trig', kind: 'activator', pos: [0, 0, 0], primitive: { type: 'Sphere', bounds: [300, 0, 0] } };

assert.ok(hasPrim(W) && hasPrim(S) && !hasPrim({ id: 'x' }));
assert.ok(isWall(W, wallBase) && !isWall(S, { edid: 'TriggerBox' }));
assert.deepEqual(halfExtents(S), [300, 300, 300]);
const f = Object.fromEntries(primFacts(W, wallBase, 'Fix Deck'));
assert.equal(f['What it is'], 'an invisible wall: people and the player cannot pass');
assert.match(f['Belongs to'], /^Fix Deck/);
assert.equal(f.Size, '6935 by 256 by 82 units (99.1 by 3.7 by 1.2 m)');
assert.match(Object.fromEntries(primFacts(S, {}, null))['What it is'], /nothing solid/);
// resizing by the full size keeps the type, colour and the rest
assert.deepEqual(resized(W.primitive, [1000, 256, 300]), { ...W.primitive, bounds: [500, 128, 150] });
assert.deepEqual(resized(S.primitive, [120]).bounds, [120, 0, 0]);
// a piece's walls are the primitives seated on it (the recorded tie), never a removed one or one on another piece
const P = { id: 'p.deck', pos: [0, 0, 0], rot: [0, 0, 0], scale: 1 };
const W2 = { ...W, id: 'w2', seat: { mode: 'on', on: 'p.other' } };
const W3 = { ...W, id: 'w3', removed: true };
const L = { id: 'l', kind: 'light', pos: [0, 0, 0], seat: { mode: 'on', on: 'p.deck' } };
assert.deepEqual(wallsOf([P], [W, W2, W3, L, S]).map(([w, p]) => [w.id, p.id]), [['w', 'p.deck']]);
assert.deepEqual(wallsOf([], [W]), []);
// a wall keeps its offset from its piece through a move and a turn (the lights' frame), and grows with a resize
const wall = { id: 'w', pos: [100, 50, 20], rot: [0, 0, 0.5] }, piece = { id: 'p', pos: [0, 0, 0], rot: [0, 0, 0], scale: 1 };
const local = localOf(wall, piece);
const moved = { ...piece, pos: [32, -10, 5] };
const [mp, mr] = poseFor(local, moved, wall);
assert.deepEqual(mp.map((v) => Math.round(v * 1000) / 1000), [132, 40, 25]);
assert.equal(mr[2], 0.5);
const turned = { ...piece, rot: [0, 0, Math.PI / 2] };
const [tp, tr] = poseFor(local, turned, wall);
assert.deepEqual(tp.map((v) => Math.round(v)), [50, -100, 20]);  // a quarter turn clockwise seen from above
assert.ok(Math.abs(tr[2] - (0.5 + Math.PI / 2)) < 1e-9);
const [sp] = poseFor(local, { ...piece, scale: 2 }, wall);
assert.deepEqual(sp, [200, 100, 40]);
assert.deepEqual(scaledPrim(W.primitive, 2).bounds, [6935, 256, 81.6]);
assert.equal(scaledPrim(W.primitive, 2).color, W.primitive.color);
// what the Selected panel of a piece says comes with it
assert.equal(comesWith(2, 1), '2 invisible walls and one light go with it when it moves, turns, is resized, copied or removed');
assert.equal(comesWith(0, 1), 'one light goes with it when it moves, turns, is resized, copied or removed');
assert.equal(comesWith(1, 0), 'one invisible wall goes with it when it moves, turns, is resized, copied or removed');
assert.equal(comesWith(0, 0), null);
console.log('prims ok');
