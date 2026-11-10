import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spotsFor, slopeOk, waterOk } from '../js/grass_rules.js';
test('density gives spots per cell, slope limits are degrees, water rule follows the type', () => {
  assert.equal(spotsFor(0, 0.1), 0); assert.equal(spotsFor(40, 0.9), 1); assert.equal(spotsFor(100, 0.0), 3); assert.equal(spotsFor(100, 0.9), 2);
  const deg = (d) => (d * Math.PI) / 180;
  assert.ok(slopeOk({ min_slope: 0, max_slope: 30 }, deg(20))); assert.ok(!slopeOk({ min_slope: 0, max_slope: 30 }, deg(40)));
  assert.ok(!slopeOk({ min_slope: 10, max_slope: 30 }, deg(5))); assert.ok(slopeOk({}, deg(40)));
  assert.ok(waterOk({ units_from_water: 100, units_from_water_type: 0 }, 150)); assert.ok(!waterOk({ units_from_water: 100, units_from_water_type: 0 }, 50));
  assert.ok(waterOk({ units_from_water: 100, units_from_water_type: 1 }, 50)); assert.ok(!waterOk({}, 3)); assert.ok(waterOk({}, 20));
});
test('the bundle writes the water type by name and the height range as one number', async () => {
  const { heightScale } = await import('../js/grass_rules.js');
  assert.ok(waterOk({ units_from_water: 0, units_from_water_type: 'EitherAtLeast' }, -50));
  assert.ok(waterOk({ units_from_water: 10, units_from_water_type: 'AboveAtLeast' }, 20)); assert.ok(!waterOk({ units_from_water: 10, units_from_water_type: 'AboveAtLeast' }, -5));
  assert.equal(heightScale({ height_range: 0.35 }, 0), 0.65); assert.equal(heightScale({ height_range: 0.35 }, 1), 1.35);
  assert.equal(heightScale({ height_range: [0.8, 1.2] }, 0.5), 1);
});
test('grass thins with distance instead of stopping: full near, fewer and larger far, the ring widening with the view', async () => {
  const { grassKeep, ringRadius, GRASS_NEAR, GRASS_FAR } = await import('../js/grass_rules.js');
  assert.deepEqual(grassKeep(GRASS_NEAR), { p: 1, scale: 1 });
  const at = (d) => grassKeep(d);
  assert.ok(at(9000).p > 0 && at(9000).p < 1 && at(18000).p < at(9000).p, 'kept, but fewer, further out');
  assert.ok(Math.abs(at(9000).p * at(9000).scale ** 2 - 1) < 1e-9, 'cover kept to twice the near range');
  assert.equal(at(40000).scale, 2);
  assert.ok(GRASS_FAR >= 20000, 'a town viewed from 200 m still has grass');
  assert.equal(ringRadius(1000), 3600); assert.equal(ringRadius(9000), 10800); assert.equal(ringRadius(80000), 16000);
});
