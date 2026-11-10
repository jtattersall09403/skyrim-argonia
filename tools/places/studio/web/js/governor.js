// Detail governor: holds a target frame rate on any tablet by trading detail, in order: how far plants and small
// clutter are drawn, how dense far vegetation is, where the full model gives way, texture size, pixel ratio, and how
// often the second view is drawn while the first is moving. It only measures frames that are drawn, so when nothing
// moves nothing is drawn and the governor costs nothing. The manual setting (low, medium, high, auto) is per device.
import { detail } from './objects.js';

// highest detail last; each step changes one more thing than the one above it
export const LEVELS = [
  { veg: 0.2, density: 4, lod: 0.4, tex: 256, ratio: 0.6, srcEvery: 12 },
  { veg: 0.3, density: 3, lod: 0.5, tex: 512, ratio: 0.75, srcEvery: 6 },
  { veg: 0.4, density: 2, lod: 0.6, tex: 1024, ratio: 1, srcEvery: 3 },
  { veg: 0.5, density: 2, lod: 1, tex: 2048, ratio: 1.25, srcEvery: 1 },
  { veg: 0.7, density: 1, lod: 1, tex: 2048, ratio: 1.5, srcEvery: 1 },
  { veg: 1, density: 1, lod: 1, tex: 4096, ratio: 1.5, srcEvery: 1 },
];
export const MANUAL = { low: 1, medium: 3, high: 5 };
const KEY = 'studio.detail.v1';

export class Governor {
  constructor(views, { targetFps = 30, onChange = () => {} } = {}) {
    this.views = views; this.budget = 1000 / targetFps; this.onChange = onChange;
    let m = 'auto'; try { m = localStorage.getItem(KEY) || 'auto'; } catch { /* private window */ }
    this.mode = m in MANUAL || m === 'auto' ? m : 'auto';
    this.level = this.mode === 'auto' ? 4 : MANUAL[this.mode];
    this.avg = 0; this.lastDrawn = 0; this.lastStep = 0; this.goodSince = 0; this.history = [];
    this.apply();
  }
  setMode(m) {
    this.mode = m; try { localStorage.setItem(KEY, m); } catch { /* fine */ }
    if (m !== 'auto') this.set(MANUAL[m]);
  }
  set(level) {
    level = Math.max(0, Math.min(LEVELS.length - 1, level));
    if (level === this.level) return;
    this.level = level; this.apply(); this.history.push({ t: Math.round(performance.now()), level });
  }
  apply() {
    const L = LEVELS[this.level], dpr = window.devicePixelRatio || 1;
    detail.veg = L.veg; detail.density = L.density; detail.lod = L.lod; detail.tex = L.tex;
    for (const v of this.views) {
      const r = Math.min(dpr, L.ratio);
      if (Math.abs(v.renderer.getPixelRatio() - r) > 0.01) { v.renderer.setPixelRatio(r); v.resize(); }
      for (const o of v.objects || []) o.dirty?.();
      v.redraw();
    }
    this.onChange(this);
  }
  // called once per animation frame with whether anything was drawn and how long the draw took
  frame(now, drew, cost) {
    if (!drew) { this.lastDrawn = 0; return; }
    // the interval between two drawn frames in a row is the felt frame time; a lone frame counts its own cost
    const dt = this.lastDrawn ? Math.max(now - this.lastDrawn, cost) : cost;
    this.lastDrawn = now;
    this.avg = this.avg ? this.avg * 0.8 + dt * 0.2 : dt;
    if (this.mode !== 'auto') return;
    if (this.avg > this.budget * 1.2 && now - this.lastStep > 700) { this.set(this.level - 1); this.lastStep = now; this.goodSince = 0; }
    else if (this.avg < this.budget * 0.55) {
      if (!this.goodSince) this.goodSince = now;
      if (now - this.goodSince > 3000 && now - this.lastStep > 3000) { this.set(this.level + 1); this.lastStep = now; this.goodSince = 0; }
    } else this.goodSince = 0;
  }
  // the second view, while the first one moves, is drawn every srcEvery-th frame
  srcEvery() { return LEVELS[this.level].srcEvery; }
  state() { return { mode: this.mode, level: this.level, avgMs: Math.round(this.avg), history: this.history.slice(-20), ...LEVELS[this.level] }; }
}
