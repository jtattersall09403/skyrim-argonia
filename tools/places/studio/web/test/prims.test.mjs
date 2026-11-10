import assert from 'node:assert/strict';
import { halfExtents, hasPrim, isWall, primFacts, resized } from '../js/prims.js';

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
console.log('prims ok');
