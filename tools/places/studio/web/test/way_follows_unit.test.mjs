// A way drawn into a person's stop follows a unit it passes over or ends at, as the unit's other spots do
// (units.js spotsMoved); its stops' own positions move only when they stand in the unit.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spotsMoved, rigid } from '../js/units.js';

test('the drawn points standing in a moved unit move with it; the rest and the stop outside stay', () => {
  const u = { box: { x0: 0, y0: 0, x1: 1000, y1: 1000 }, members: [] };
  const person = { id: 'p', routine: [{ start: 8, hours: 8, kind: 'work', at: { space: 'exterior', pos: [2000, 2000, 0] },
    route: [[-500, 500, 0], [500, 500, 10], [900, 900, 10]] }] };
  const model = { people: new Map([['p', person]]), quests: new Map(), walk: new Map(), paths: new Map() };
  const moved = rigid([500, 500], 0, [300, 0, 0]);
  const got = spotsMoved(model, 'exterior', u, moved, 0, new Map());
  const r = got.people[0].person.routine[0];
  assert.deepEqual(r.route, [[-500, 500, 0], [800, 500, 10], [1200, 900, 10]]);
  assert.deepEqual(r.at.pos, [2000, 2000, 0]);
});
