// A drag on the screen to a move in the world (js/move_map.js) at three camera angles: nearly straight down, three-
// quarter and nearly level. Right on the screen is always right in the view, up the screen always away from the
// camera, and the thing under the pen stays under it while the view looks down on it.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dragDelta, dragMode, groundFrame, planeHit, snapFaces } from '../js/move_map.js';

const norm = (v) => { const l = Math.hypot(...v); return v.map((x) => x / l); };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
// The studio's orbit camera (view.js updateCamera) as a pinhole: a ray through the screen point (sx, sy) pixels from
// the middle, y down, focal length f pixels.
function camera(yaw, pitch, dist = 3000, f = 900) {
  const c = [dist * Math.cos(pitch) * Math.cos(yaw), dist * Math.cos(pitch) * Math.sin(yaw), dist * Math.sin(pitch)];
  const F = norm(c.map((v) => -v)), R = norm(cross(F, [0, 0, 1])), U = cross(R, F);
  return { ray: (sx, sy) => ({ o: c, d: norm([0, 1, 2].map((i) => F[i] * f + R[i] * sx - U[i] * sy)) }), perPx: dist / f };
}
const dot = (a, b) => a[0] * b[0] + a[1] * b[1];

for (const [name, pitch] of [['nearly straight down', 1.45], ['three-quarter', 0.8], ['nearly level', 0.12]]) {
  for (const yaw of [-Math.PI / 2, 0.7, 2.9]) {
    test(`${name}, yaw ${yaw.toFixed(2)}: right is right, up is away`, () => {
      const cam = camera(yaw, pitch), r0 = cam.ray(0, 0), mode = dragMode(r0), { right, forward } = groundFrame(yaw);
      assert.equal(mode, pitch < 0.17 ? 'screen' : 'plane');
      const move = (px) => dragDelta({ mode, r0, r1: cam.ray(px[0], px[1]), z: 0, px, perPx: cam.perPx, yaw });
      const r = move([60, 0]), u = move([0, -60]);
      assert.ok(dot(r, right) > 0.9 * Math.hypot(...r) && Math.hypot(...r) > 50, `right: ${r}`);
      assert.ok(dot(u, forward) > 0.9 * Math.hypot(...u) && Math.hypot(...u) > 50, `up: ${u}`);
      // an axis handle keeps only its axis
      const x = dragDelta({ mode, r0, r1: cam.ray(40, -30), z: 0, px: [40, -30], perPx: cam.perPx, yaw, axis: 'x' });
      assert.equal(x[1], 0);
      if (mode === 'plane') {   // the point under the pen stays under it
        const at = planeHit(cam.ray(60, 0), 0), was = planeHit(r0, 0);
        assert.ok(Math.abs(was[0] + r[0] - at[0]) < 1e-6 && Math.abs(was[1] + r[1] - at[1]) < 1e-6);
      }
    });
  }
}

test('a box comes flush with a neighbour within the tolerance, and only then', () => {
  const box = { x0: 0, y0: 0, x1: 100, y1: 100 }, wall = { x0: 110, y0: 20, x1: 300, y1: 80 };
  assert.deepEqual(snapFaces(box, [wall]), [10, 0]);
  assert.deepEqual(snapFaces(box, [{ ...wall, x0: 200 }]), [0, 0]);
});
