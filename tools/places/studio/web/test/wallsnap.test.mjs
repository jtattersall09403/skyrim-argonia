// A wall thing hung on the wall face under the pen (from the wall's triangles), facing out, and a light source added
// with its light (js/wallsnap.js).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { wallMount, rayTriangles, onWall, lightFor } from '../js/wallsnap.js';
import { applyRot } from '../js/xform.js';

const SCONCE = { key: 'Skyrim.esm:0E7C2C', edid: 'DweWallSconce01OnSputter', model: 'dungeons/dwemer/dwewallsconce01onsputter.nif', bounds: [[-16, -74, -84], [133, 75, 85]] };
// a wall: a slab 20 thick whose west face is the plane x = 100, turned 30 degrees about Z, as triangles
function slab(turn) {
  const c = Math.cos(turn), s = Math.sin(turn), P = [];
  const quad = (a, b, cc, d) => P.push(...a, ...b, ...cc, ...a, ...cc, ...d);
  const p = (x, y, z) => [c * x - s * y, s * x + c * y, z];
  for (const x of [100, 120]) quad(p(x, -300, 0), p(x, 300, 0), p(x, 300, 400), p(x, -300, 400));
  quad(p(100, -300, 400), p(120, -300, 400), p(120, 300, 400), p(100, 300, 400));
  return new Float32Array(P);
}

test('a sconce is a wall thing that faces out along its own +X; a crate is not', () => {
  assert.deepEqual(wallMount(SCONCE).out, [1, 0]);
  assert.equal(wallMount({ edid: 'Crate01', model: 'clutter/crate01.nif', bounds: [[-40, -40, 0], [40, 40, 60]] }), null);
});

test('a sconce snapped to a wall sits on the face within 2 cm, facing out', () => {
  for (const turn of [0, Math.PI / 6, -2.1]) {
    const wall = slab(turn), c = Math.cos(turn), s = Math.sin(turn);
    const o = [-200 * c - 40 * -s, -200 * s - 40 * c, 180], d = [c, s, 0.05];   // the pen's ray, from in front of the wall
    const hit = rayTriangles(o, d, wall);
    assert.ok(hit, 'the ray meets the wall');
    const pose = onWall(wallMount(SCONCE), hit.point, hit.normal);
    const n = [-c, -s, 0];                                 // the face's outward normal
    const off = (pose.pos[0] - 100 * c) * n[0] + (pose.pos[1] - 100 * s) * n[1];   // the origin's distance off the face plane
    assert.ok(Math.abs(off) < 1.4, `on the face: ${off}`);
    const out = applyRot(pose.rot, [1, 0, 0]);
    assert.ok(out[0] * n[0] + out[1] * n[1] > 0.99, 'faces out of the wall');
  }
});

test('a floor is not a wall', () => {
  assert.equal(onWall(wallMount(SCONCE), [0, 0, 0], [0, 0, 1]), null);
});

test('an added torch sconce comes with its light: learned from a lit one of its base, else Skyrim\'s default', () => {
  const base = { key: 'X:1', edid: 'TorchSconce01', model: 'clutter/torchsconce01.nif', bounds: [[0, -10, -20], [30, 10, 40]] };
  const bases = new Map([['X:1', base], ['L:1', { key: 'L:1', edid: 'TorchLightX' }]]);
  const fix = { id: 'new', base: 'X:1', kind: 'static', pos: [1000, 1000, 200], rot: [0, 0, Math.PI / 2], scale: 1 };
  // the measured table: its light at its offset in the fixture's own frame (here 30 out along +X, 50 up)
  const table = { 'X:1': { light: 'Skyrim.esm:088243', offset: [30, 0, 50] } };
  const plain = lightFor(fix, base, [fix], (r) => bases.get(r.base), table);
  assert.equal(plain.base, 'Skyrim.esm:088243');
  assert.equal(plain.kind, 'light');
  assert.deepEqual(plain.pos, [1000, 970, 250]);
  assert.equal(lightFor(fix, base, [fix], (r) => bases.get(r.base), {}), null, 'no table row and none lit in the place: none');
  const lit = { id: 'f1', base: 'X:1', kind: 'static', pos: [0, 0, 100], rot: [0, 0, 0], scale: 1 };
  const light = { id: 'l1', base: 'L:1', kind: 'light', pos: [20, 0, 140], rot: [0, 0, 0], scale: 1 };
  const got = lightFor(fix, base, [fix, lit, light], (r) => bases.get(r.base));
  assert.equal(got.base, 'L:1');
  // the same place in the fixture's own frame: 20 out along its +X, turned a quarter clockwise, is 20 to the south
  assert.deepEqual(got.pos, [1000, 980, 240]);
  assert.equal(got.id, undefined);
  const crate = { id: 'c', base: 'C', kind: 'static', pos: [0, 0, 0], rot: [0, 0, 0] };
  assert.equal(lightFor(crate, { edid: 'Crate01' }, [crate], () => null), null);
});
