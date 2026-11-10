import assert from 'node:assert/strict';
import { colourOf, fixtureOf, isFixture, lightFacts, lightsOf, localOf, poseFor } from '../js/lights.js';

const bases = new Map([
  ['lantern', { edid: 'CandleLanternwithCandle01', model: 'clutter/common/candlelanternwithcandle01.nif' }],
  ['table', { edid: 'CommonTable01', model: 'furniture/commontable01.nif' }],
  ['window', { edid: 'BMWindowGlow01', model: 'bm/windowglow01.nif' }],
  ['bulb', { edid: 'RiftenLight01', light: { radius: 400, colour: [255, 200, 120], flags: 'ShadowOmnidirectional' } }],
]);
const baseOf = (r) => bases.get(r.base);
const L = { id: 'l', base: 'bulb', kind: 'light', pos: [100, 0, 50], rot: [0, 0, 0] };
const F = { id: 'f', base: 'lantern', kind: 'clutter', pos: [0, 0, 0], rot: [0, 0, 0] };
const T = { id: 't', base: 'table', kind: 'furniture', pos: [100, 0, 0], rot: [0, 0, 0] };
const W = { id: 'w', base: 'window', kind: 'static', pos: [300, 0, 0], rot: [0, 0, 0] };

// a fixture is a man-made light-giver by its record; a light or a table is not
assert.ok(isFixture(F, baseOf(F)) && isFixture(W, baseOf(W)));
assert.ok(!isFixture(T, baseOf(T)) && !isFixture(L, baseOf(L)));
// a light belongs to the nearest fixture within 128 units (the table nearer it is no fixture)
assert.equal(fixtureOf(L, [F, T, W], baseOf).id, 'f');
assert.equal(fixtureOf({ ...L, pos: [600, 0, 0] }, [F, T, W], baseOf), null);
// a fixture's lights; a table's none; a light nearer another fixture is that one's
assert.deepEqual(lightsOf([F], [L, T, W], baseOf).map(([l, f]) => [l.id, f.id]), [['l', 'f']]);
assert.deepEqual(lightsOf([T], [L, F, W], baseOf), []);
assert.deepEqual(lightsOf([F], [{ ...L, pos: [250, 0, 0] }, W], baseOf), []);
// the light keeps its place in the fixture's frame: a quarter turn of the fixture carries it round
const local = localOf(L, F);
const [p, rot] = poseFor(local, { ...F, pos: [1000, 0, 0], rot: [0, 0, Math.PI / 2] }, L);
assert.ok(Math.abs(p[0] - 1000) < 1e-6 && Math.abs(p[1] + 100) < 1e-6 && p[2] === 50, String(p));
assert.ok(Math.abs(rot[2] - Math.PI / 2) < 1e-9);
// doubling the fixture doubles the offset
const [p2] = poseFor(local, { ...F, scale: 2 }, L);
assert.deepEqual(p2, [200, 0, 100]);
// what the panel shows of a light
const f = lightFacts(L, baseOf(L));
assert.equal(f.radius, 400); assert.equal(f.hex, '#ffc878'); assert.ok(f.shadow);
assert.equal(lightFacts({ ...L, radius: 650 }, baseOf(L)).radius, 650);
// a colour the extractor writes as its three bytes in base64 reads the same
assert.deepEqual(colourOf('t2ke'), [183, 105, 30]);
assert.equal(lightFacts(L, { light: { colour: 't2ke', radius: 256 } }).hex, '#b7691e');
console.log('lights ok');
