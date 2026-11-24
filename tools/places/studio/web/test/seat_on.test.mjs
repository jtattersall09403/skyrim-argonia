// A thing seated on another (a door on its hut) stands on the support's seated height, as tools/places/seat.py
// seat_all does: the support's stored z may be stale after the land under it changed, and the door must not spring.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { seatZ } from '../js/bundle.js';

test('a door on its hut follows the hut\'s seated height, with its own dz', () => {
  const terrain = { heightAt: () => 500, waterAt: () => null };
  const hut = { id: 'hut', pos: [0, 0, 300], rot: [0, 0, 0], seat: { mode: 'above', dz: 10 } };   // stored z stale
  const door = { id: 'door', pos: [0, 100, 0], rot: [0, 0, 0], seat: { mode: 'on', on: 'hut', dz: 40 } };
  const by = new Map([[hut.id, hut], [door.id, door]]);
  assert.equal(seatZ(terrain, hut, by), 510);
  assert.equal(seatZ(terrain, door, by), 550);
  door.seat = { ...door.seat, dz: 25 };   // lowered by 15
  assert.equal(seatZ(terrain, door, by), 535);
});
