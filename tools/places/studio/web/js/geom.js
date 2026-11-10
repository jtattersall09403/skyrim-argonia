// Small plane geometry shared by the tools.
export function segDist(p, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
  const t = l ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l)) : 0;
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
}
// A time of day on the 24-hour clock ("08:00"), as Skyrim's schedules count it: 0 to 24 hours.
export function clock(t) {
  let h = Math.floor(t), m = Math.round((t - h) * 60);
  if (m === 60) { h += 1; m = 0; }
  return `${String(h % 24).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}
// "8", "8:30" or "08:30" as hours (null when it is not a time of day).
export function parseClock(s) {
  const m = /^\s*(\d{1,2})(?::([0-5]\d))?\s*$/.exec(s || ''); if (!m) return null;
  const h = Number(m[1]); return h > 23 ? null : h + Number(m[2] || 0) / 60;
}
