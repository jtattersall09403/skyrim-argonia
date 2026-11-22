// From a drag on the screen to a move in the world (pure: no three.js, no page; test/move_map.test.mjs).
//
// The default drag slides a thing along a level plane at its own height, fixed when the drag starts: the point under
// the pen stays under the pen, as The Sims and Planet Coaster move things over the ground. When the view looks
// along the ground (the pen's ray meets that plane at a grazing angle, where a small movement of the pen would throw
// the thing far away), the drag maps the screen instead: right on the screen is right in the view, up the screen is
// away from the camera, at the scale of the thing's distance. Which of the two is chosen once, when the drag starts,
// and never changes during it. An axis handle keeps only the move along its axis (east-west or north-south).

export const GRAZE = 0.17;   // a ray climbing or falling less steeply than this (about 10 degrees) grazes the plane

// Where a ray {o, d} (game coordinates, d of unit length) meets the level plane at height z, or null.
export function planeHit(ray, z) {
  if (Math.abs(ray.d[2]) < 1e-6) return null;
  const t = (z - ray.o[2]) / ray.d[2];
  return t < 0 ? null : [ray.o[0] + t * ray.d[0], ray.o[1] + t * ray.d[1]];
}

// The view's frame on the ground for its yaw (the camera stands at the target plus (cos yaw, sin yaw)): forward is
// away from the camera, right is forward turned clockwise seen from above.
export function groundFrame(yaw) {
  const f = [-Math.cos(yaw), -Math.sin(yaw)];
  return { forward: f, right: [f[1], -f[0]] };
}

// How a drag that starts with the ray `r0` maps: 'plane' or 'screen' (decided once, at the start).
export const dragMode = (r0) => (Math.abs(r0.d[2]) < GRAZE ? 'screen' : 'plane');

// The world move [dx, dy] of a drag: from r0 to r1 (the pen's rays), at height z, the screen movement px [dx, dy] in
// pixels and perPx (world units per pixel at the thing's distance), for the view's yaw; axis 'x', 'y' or null.
export function dragDelta({ mode, r0, r1, z, px, perPx, yaw, axis = null }) {
  let d = null;
  if (mode === 'plane') {
    const a = planeHit(r0, z), b = planeHit(r1, z);
    if (a && b) d = [b[0] - a[0], b[1] - a[1]];
  }
  if (!d) {
    const { forward, right } = groundFrame(yaw);
    d = [(right[0] * px[0] - forward[0] * px[1]) * perPx, (right[1] * px[0] - forward[1] * px[1]) * perPx];
  }
  if (axis === 'x') d = [d[0], 0];
  if (axis === 'y') d = [0, d[1]];
  return d;
}

// A plan box {x0, y0, x1, y1} brought flush with a neighbour within tol: its side against the other's opposite side,
// the nearer per axis, for neighbours beside it on the other axis. Returns the extra
// [sx, sy] to add.
export function snapFaces(box, others, tol = 24) {
  let best = [null, null];
  const consider = (i, gap) => { if (Math.abs(gap) <= tol && (best[i] === null || Math.abs(gap) < Math.abs(best[i]))) best[i] = gap; };
  for (const o of others) {
    const nearY = box.y1 >= o.y0 - tol && box.y0 <= o.y1 + tol, nearX = box.x1 >= o.x0 - tol && box.x0 <= o.x1 + tol;
    if (nearY) for (const g of [o.x0 - box.x1, o.x1 - box.x0]) consider(0, g);
    if (nearX) for (const g of [o.y0 - box.y1, o.y1 - box.y0]) consider(1, g);
  }
  return [best[0] ?? 0, best[1] ?? 0];
}
