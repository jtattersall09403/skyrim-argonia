// web/xform.js against the shared vectors of tools/places/xform.py.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { refMatrix, decompose } from '../js/xform.js';

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
