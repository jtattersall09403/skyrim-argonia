import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DEPTH_MAX, INLAND_UNIT, depthGrid, isPlacedWater, rippleNormals, waterLook } from '../js/water_look.js';

const SAP = { edid: 'DefaultHistSapWater', shallow: [162, 82, 2], deep: [141, 60, 5], opacity: 100, reflect: [135, 77, 12], reflectivity: 0.79, fresnel: 0.07, fog_far: 140 };

test('a base with a water entry is drawn as water, any other is not', () => {
  assert.ok(isPlacedWater({ edid: 'WaterPuddleHist', water: SAP }));
  assert.ok(!isPlacedWater({ edid: 'MurkmireThatchHouse08' }) && !isPlacedWater(null));
});

test("the look is the water type's own colours and the record's opacity; a record without them gets middle values", () => {
  const L = waterLook(SAP);
  assert.deepEqual(L.shallow.map((v) => Math.round(v * 255)), [162, 82, 2]);
  assert.deepEqual(L.deep.map((v) => Math.round(v * 255)), [141, 60, 5]);
  assert.equal(L.opacity, 1); assert.equal(L.fogFar, 140); assert.equal(L.reflectivity, 0.79);
  const bare = waterLook({ shallow: [100, 100, 100], deep: [10, 10, 10] });
  assert.equal(bare.opacity, 0.5); assert.equal(bare.fogFar, 220); assert.ok(bare.reflect.every((v) => v > 0 && v <= 1));
});

test('depth is the surface over the ground, deeper where the hollow is, none where the ground stands above it', () => {
  // a bowl: ground 60 below the surface at the middle, rising to the surface at 100 units out, above it beyond
  const ground = (x, y) => -60 + (Math.hypot(x, y) / 100) * 60 + (Math.hypot(x, y) > 100 ? 40 : 0);
  const g = depthGrid([{ pos: [0, 0, 0], r: 160 }], ground);
  const at = (x, y) => { const i = Math.floor((x - g.min[0]) / g.step), j = Math.floor((y - g.min[1]) / g.step), k = (j * g.w + i) * 2; return [g.data[k], g.data[k + 1]]; };
  const unitsOf = (b) => ((b - 1) / 254) * DEPTH_MAX;
  const [dMid, inMid] = at(0, 0), [dRim, inRim] = at(80, 0), [dOut, inOut] = at(140, 0);
  assert.ok(unitsOf(dMid) > 50 && unitsOf(dMid) < 70, `middle ${unitsOf(dMid)}`);
  assert.ok(unitsOf(dRim) < unitsOf(dMid) && dRim > 0);
  assert.equal(dOut, 0); assert.equal(inOut, 0);
  assert.ok(inMid * INLAND_UNIT > inRim * INLAND_UNIT, 'further in from the edge at the middle');
  assert.equal(depthGrid([], ground), null);
});

test('a flat hollow still deepens toward its middle through the inland distance', () => {
  const floor = (x, y) => (Math.hypot(x, y) < 100 ? -3 : 50);
  const g = depthGrid([{ pos: [0, 0, 0], r: 150 }], floor);
  const inland = (x, y) => g.data[(Math.floor((y - g.min[1]) / g.step) * g.w + Math.floor((x - g.min[0]) / g.step)) * 2 + 1];
  assert.ok(inland(0, 0) > inland(80, 0) && inland(80, 0) > 0);
});

test('the ripple tile is the same every time, a unit tangent normal per texel, and meets itself at its edges', () => {
  const a = rippleNormals(32), b = rippleNormals(32);
  assert.deepEqual(a, b);
  for (let k = 0; k < a.length; k += 4) {
    const x = a[k] / 127.5 - 1, y = a[k + 1] / 127.5 - 1, z = a[k + 2] / 127.5 - 1;
    assert.ok(Math.abs(Math.hypot(x, y, z) - 1) < 0.03 && z > 0.5);
  }
  // periodic: neighbours across the seam differ no more than neighbours inside
  const step = (i, j, i2, j2) => Math.abs(a[(j * 32 + i) * 4] - a[(j2 * 32 + i2) * 4]);
  let inside = 0, seam = 0;
  for (let j = 0; j < 32; j++) { inside = Math.max(inside, step(10, j, 11, j)); seam = Math.max(seam, step(31, j, 0, j)); }
  assert.ok(seam <= inside * 2 + 2);
});
