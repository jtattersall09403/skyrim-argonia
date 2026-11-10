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
