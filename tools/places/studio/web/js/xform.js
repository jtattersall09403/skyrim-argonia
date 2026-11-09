// A placed record's position, angles and scale as a matrix: the one place this maths lives in the front end.
// Mirrors tools/places/xform.py; both are tested against test/xform_vectors.json.
// Skyrim's angles are radians, clockwise when seen down each axis; the game applies Z first, then Y, then X:
// R = Rx(-rx) * Ry(-ry) * Rz(-rz) acting on column vectors. Matrices here are column-major (WebGL order).

function rx(a) { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, c, s, 0, -s, c]; }
function ry(a) { const c = Math.cos(a), s = Math.sin(a); return [c, 0, -s, 0, 1, 0, s, 0, c]; }
function rz(a) { const c = Math.cos(a), s = Math.sin(a); return [c, s, 0, -s, c, 0, 0, 0, 1]; }
function mul3(a, b) { // column-major 3x3
  const o = new Array(9);
  for (let c = 0; c < 3; c++) for (let r = 0; r < 3; r++) {
    o[c * 3 + r] = a[r] * b[c * 3] + a[3 + r] * b[c * 3 + 1] + a[6 + r] * b[c * 3 + 2];
  }
  return o;
}

export function rotationMatrix(rot) {
  return mul3(mul3(rx(-rot[0]), ry(-rot[1])), rz(-rot[2]));
}

// 4x4 column-major matrix of pos, rot, scale; `origin` is subtracted from pos (render-local frame).
export function refMatrix(pos, rot, scale, origin = [0, 0, 0]) {
  const r = rotationMatrix(rot), s = scale ?? 1;
  return [r[0] * s, r[1] * s, r[2] * s, 0, r[3] * s, r[4] * s, r[5] * s, 0, r[6] * s, r[7] * s, r[8] * s, 0,
    pos[0] - origin[0], pos[1] - origin[1], pos[2] - origin[2], 1];
}

export function applyRot(rot, v) {
  const r = rotationMatrix(rot);
  return [r[0] * v[0] + r[3] * v[1] + r[6] * v[2], r[1] * v[0] + r[4] * v[1] + r[7] * v[2],
    r[2] * v[0] + r[5] * v[1] + r[8] * v[2]];
}

// The fit (place.json): a source position onto ours. p' = Rz(rot) * (p * scale) + [dx,dy,dz]; rot counter-clockwise.
export function fitPoint(fit, p) {
  const c = Math.cos(fit.rot || 0), s = Math.sin(fit.rot || 0), k = fit.scale || 1;
  return [c * p[0] * k - s * p[1] * k + (fit.dx || 0), s * p[0] * k + c * p[1] * k + (fit.dy || 0), p[2] * k + (fit.dz || 0)];
}
export function unfitPoint(fit, q) {
  const c = Math.cos(fit.rot || 0), s = Math.sin(fit.rot || 0), k = fit.scale || 1;
  const x = q[0] - (fit.dx || 0), y = q[1] - (fit.dy || 0);
  return [(c * x + s * y) / k, (-s * x + c * y) / k, (q[2] - (fit.dz || 0)) / k];
}
// A source ref's angles carried onto ours: the fit turns about Z, clockwise angles subtract it.
export function fitRot(fit, rot) { return [rot[0], rot[1], rot[2] - (fit.rot || 0)]; }

const wrap = (a) => { a %= 2 * Math.PI; if (a <= -Math.PI) a += 2 * Math.PI; else if (a > Math.PI) a -= 2 * Math.PI; return Math.abs(a) < 1e-12 ? 0 : a; };
// A column-major 4x4 back to pos, rot (each in (-pi, pi]) and scale, as tools/places/xform.py `decompose`.
export function decompose(m) {
  const pos = [m[12], m[13], m[14]], scale = Math.hypot(m[0], m[1], m[2]);
  const r = (i, j) => m[j * 4 + i] / scale; // row i, column j
  const sb = Math.max(-1, Math.min(1, r(0, 2))), b = Math.asin(sb);
  let a, c;
  if (Math.abs(sb) < 1 - 1e-9) { a = Math.atan2(-r(1, 2), r(2, 2)); c = Math.atan2(-r(0, 1), r(0, 0)); }
  else { c = 0; a = Math.atan2(r(2, 1), r(1, 1)); }
  return { pos, rot: [wrap(-a), wrap(-b), wrap(-c)], scale };
}
