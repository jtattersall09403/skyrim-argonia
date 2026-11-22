// A place's units (js/units.js): the one membership rule, and a unit's rigid move.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { unitsOf, rigid, spotIn } from '../js/units.js';

const B = {
  hull: { edid: 'ShipImperial', bounds: [[-600, -200, 0], [600, 200, 300]] },
  sail: { edid: 'ShipSail', bounds: [[-300, -150, 200], [300, 150, 1200]] },
  tent: { edid: 'ImperialTentLarge', bounds: [[-250, -250, 0], [250, 250, 300]] },
  bedroll: { edid: 'Bedroll01F', bounds: [[-40, -100, 0], [40, 100, 20]] },
  house: { edid: 'SOMRStonehouse01', bounds: [[-300, -250, 0], [300, 250, 400]] },
  door: { edid: 'DoorLoad', bounds: [[-60, -10, 0], [60, 10, 200]] },
  fern: { edid: 'Fern01', bounds: [[-30, -30, 0], [30, 30, 40]] },
  light: { edid: 'CandleLight', bounds: [[-5, -5, 0], [5, 5, 5]] },
  wall: { edid: 'CollisionMarker', bounds: null },
};
const r = (id, base, kind, pos, extra = {}) => ({ id, base, kind, pos, rot: [0, 0, 0], scale: 1, seat: { mode: 'free' }, ...extra });
const baseOf = (x) => B[x.base];

test('a ship of hull and sail, with what sits on it, is one unit named for its hull', () => {
  const refs = [r('hull', 'hull', 'building', [0, 0, 0]), r('sail', 'sail', 'building', [20, 0, 0]),
    r('door', 'door', 'door', [500, 0, 300], { seat: { mode: 'on', on: 'hull', dz: 300 } }), r('lamp', 'light', 'light', [100, 50, 320])];
  const { units, of } = unitsOf(refs, baseOf);
  assert.equal(units.size, 1);
  const u = [...units.values()][0];
  assert.deepEqual(new Set(u.members), new Set(['hull', 'sail', 'door', 'lamp']));
  assert.equal(u.head, 'hull'); assert.match(u.name, /ship/i);
  assert.equal(of.get('sail'), u.id);
});

test("a bedroll inside a tent belongs to the tent's unit; a fern there stays with the ground", () => {
  const refs = [r('tent', 'tent', 'static', [0, 0, 0], { cluster: 's01' }), r('peg', 'bedroll', 'static', [200, 200, 0], { cluster: 's01' }),
    r('roll', 'bedroll', 'furniture', [50, 0, 4]), r('fern', 'fern', 'plant', [10, 10, 0]), r('far', 'bedroll', 'furniture', [900, 0, 0])];
  const { units, of } = unitsOf(refs, baseOf);
  assert.equal(of.get('roll'), 's01');
  assert.equal(of.get('fern'), undefined);
  assert.equal(of.get('far'), undefined);
  assert.equal(units.get('s01').members.length, 3);
});

test("a ref's own unit wins: put in by hand, or taken out of every unit", () => {
  const refs = [r('house', 'house', 'building', [0, 0, 0]), r('door', 'door', 'door', [0, -250, 0]), r('roll', 'bedroll', 'furniture', [0, 0, 0], { unit: '' }),
    r('far', 'bedroll', 'furniture', [2000, 0, 0], { unit: 'u.house' })];
  const { of } = unitsOf(refs, baseOf);
  assert.equal(of.get('door'), 'u.house');
  assert.equal(of.get('roll'), undefined);
  assert.equal(of.get('far'), 'u.house');
});

test('a building with only its invisible wall is no unit', () => {
  const refs = [r('house', 'house', 'building', [0, 0, 0]), r('wall', 'wall', 'marker', [0, 0, 100], { seat: { mode: 'on', on: 'house', dz: 100 }, primitive: { bounds: [100, 10, 50] } })];
  assert.equal(unitsOf(refs, baseOf).units.size, 0);
});

test('a rigid move turns about the centre clockwise from above, as the game turns', () => {
  const xf = rigid([0, 0], Math.PI / 2, [10, 0, 5]);
  const p = xf([0, 100, 7]);   // north of the centre turns to east
  assert.ok(Math.abs(p[0] - 110) < 1e-9 && Math.abs(p[1]) < 1e-9 && p[2] === 12, p);
  assert.ok(spotIn({ box: { x0: 0, y0: 0, x1: 10, y1: 10 } }, [5, 5]));
});
