// Small plane geometry shared by the tools.
export function segDist(p, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
  const t = l ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l)) : 0;
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
}
export function clock(t) { const h = Math.floor(t) % 24, m = Math.round((t - Math.floor(t)) * 60); return `${h}:${String(m).padStart(2, '0')}`; }
