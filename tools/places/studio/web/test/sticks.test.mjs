// web/sticks.js: the thumb sticks' maths.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { deflection, moveVelocity, turnRates, stepCamera, clampPitch, WALK, RUN, EYE, PITCH_MAX, PITCH_MIN } from '../js/sticks.js';

const near = (a, b, e = 1e-6) => assert.ok(Math.abs(a - b) < e, `${a} vs ${b}`);
const cam0 = { x: 0, y: 0, z: 500, yaw: 0, pitch: 0 };

test('deflection: dead zone, unit disc, edge', () => {
  assert.deepEqual(deflection(2, 2, 60), { x: 0, y: 0, m: 0 });
  const d = deflection(0, -120, 60); near(d.y, -1); near(d.x, 0); near(d.m, 1);
  near(deflection(0, -30, 60).y, -(0.5 - 0.08) / 0.92);
});
test('velocity proportional to push, runs at the edge, steps multiply', () => {
  const half = moveVelocity(deflection(0, -30, 60)), full = moveVelocity(deflection(0, -54, 60)), edge = moveVelocity(deflection(0, -60, 60));
  assert.ok(half.forward > 0 && half.forward < full.forward); near(edge.forward, RUN); assert.ok(full.forward <= WALK + 1e-9);
  near(moveVelocity(deflection(0, -60, 60), 4).forward, RUN * 4);
  const right = moveVelocity(deflection(60, 0, 60)); near(right.strafe, RUN); near(right.forward, 0);
});
test('forward goes where the camera faces; strafe right is to its right', () => {
  const north = { ...cam0, yaw: Math.PI / 2 };
  const a = stepCamera(north, { move: deflection(0, -60, 60) }, 0.1); near(a.x, 0, 1e-6); near(a.y, RUN * 0.1);
  const b = stepCamera(north, { move: deflection(60, 0, 60) }, 0.1); near(b.x, RUN * 0.1); near(b.y, 0, 1e-6);
});
test('frame-rate independent', () => {
  const inp = { move: deflection(20, -45, 60), look: { x: 0, y: 0 } };
  let a = cam0, b = cam0;
  for (let i = 0; i < 30; i++) a = stepCamera(a, inp, 1 / 30);
  for (let i = 0; i < 144; i++) b = stepCamera(b, inp, 1 / 144);
  near(a.x, b.x, 1e-6); near(a.y, b.y, 1e-6);
  const s = stepCamera(cam0, inp, 5); assert.ok(Math.hypot(s.x, s.y) <= RUN * 0.1 + 1e-9, 'a stalled frame is capped');
});
test('turn: stick right turns right, up looks up; pitch clamped', () => {
  assert.ok(turnRates({ x: 1, y: 0 }).yaw < 0); assert.ok(turnRates({ x: 0, y: -1 }).pitch > 0);
  let c = cam0; for (let i = 0; i < 100; i++) c = stepCamera(c, { look: { x: 0, y: -1 } }, 0.1); near(c.pitch, PITCH_MAX);
  for (let i = 0; i < 100; i++) c = stepCamera(c, { look: { x: 0, y: 1 } }, 0.1); near(c.pitch, PITCH_MIN);
  near(clampPitch(9), PITCH_MAX);
});
test('walk keeps the eye at a person\'s height over a fixture ground; flying keeps height and rises', () => {
  const ground = (x, y) => 100 + x * 0.5;   // a slope rising to the east
  let c = { ...cam0, z: 100 + EYE };
  for (let i = 0; i < 20; i++) c = stepCamera(c, { move: deflection(0, -60, 60) }, 0.05, { walk: true, ground });
  assert.ok(c.x > 300); near(c.z, ground(c.x, c.y) + EYE, 1e-6);
  const f = stepCamera(cam0, { move: deflection(0, -60, 60), rise: WALK }, 0.1); near(f.z, 500 + WALK * 0.1);
  const lost = stepCamera(c, { move: deflection(0, -60, 60) }, 0.1, { walk: true, ground: () => null }); near(lost.z, c.z);
});
