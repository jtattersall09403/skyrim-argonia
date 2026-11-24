// web/xform.js against the shared vectors of tools/places/xform.py.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { refMatrix, decompose, rotationMatrix, turnRot, tiltRot } from '../js/xform.js';

const V = JSON.parse(readFileSync(fileURLToPath(new URL('../../../xform_vectors.json', import.meta.url)), 'utf8'));
const near = (a, b, msg) => assert.ok(Math.abs(a - b) < 1e-6, `${msg}: ${a} vs ${b}`);

test('convention', () => assert.equal(V.convention, 'Rx(-x)Ry(-y)Rz(-z)'));
V.cases.forEach((c, k) => test(`case ${k}`, () => {
  const m = refMatrix(c.pos, c.rot, c.scale);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) near(m[j * 4 + i], c.matrix[i][j], `m[${i}][${j}]`);
  for (const p of c.points) {
    const w = [0, 1, 2].map((i) => m[i] * p.local[0] + m[4 + i] * p.local[1] + m[8 + i] * p.local[2] + m[12 + i]);
    w.forEach((v, i) => near(v, p.world[i], 'point'));
  }
  const d = decompose(m);
  d.rot.forEach((v, i) => near(v, c.decomposed.rot[i], 'rot')); near(d.scale, c.decomposed.scale, 'scale');
}));

// turnRot and tiltRot: the same matrix as the world turn before, or the own-axis tilt after, the ref's rotation.
const m3 = (a, b) => { const o = new Array(9); for (let c = 0; c < 3; c++) for (let r = 0; r < 3; r++) o[c * 3 + r] = a[r] * b[c * 3] + a[3 + r] * b[c * 3 + 1] + a[6 + r] * b[c * 3 + 2]; return o; };
test('turnRot of a level piece adds to its heading', () => assert.deepEqual(turnRot([0, 0, 1], 0.5), [0, 0, 1.5]));
test('turnRot and tiltRot compose', () => {
  let seed = 3; const r = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647 * 2 - 1; };
  for (let n = 0; n < 100; n++) {
    const rot = [r(), r(), r() * 3], a = r() * 3;
    const R = rotationMatrix(rot);
    const want = m3(rotationMatrix([0, 0, a]), R);
    rotationMatrix(turnRot(rot, a)).forEach((v, i) => near(v, want[i], 'turn'));
    const tx = m3(R, rotationMatrix([a, 0, 0])), ty = m3(R, rotationMatrix([0, a, 0]));
    rotationMatrix(tiltRot(rot, 0, a)).forEach((v, i) => near(v, tx[i], 'tilt'));
    rotationMatrix(tiltRot(rot, 1, a)).forEach((v, i) => near(v, ty[i], 'roll'));
  }
});
