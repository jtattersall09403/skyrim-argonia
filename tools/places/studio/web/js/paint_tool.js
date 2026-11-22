// Paint ground: the owner paints land textures onto the place's ground with the pen, like an art app. Pick a texture
// from the palette (the land textures the world and the source place use here, most used first, with their
// pictures), a brush (soft round, hard round, scatter, eraser), its size, softness and strength; press harder for a
// wider, stronger mark. Each stroke is one paint.add op (paint.jsonl, by the rule of paint_rule.js), so undo and redo
// and Save work as for every other edit; the eraser takes earlier paint away so the world's own ground shows again.
import { nextId, bounds } from './paint_rule.js';

export const BRUSH_KINDS = [['soft', 'Soft round'], ['hard', 'Hard round'], ['scatter', 'Scatter'], ['erase', 'Eraser']];
const rnd = (v, k = 1) => Math.round(v * k) / k;
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// `ANW_Ground_river_mud~coast` -> `River mud (coast)`; a source's `LDirt02` -> `Dirt`
export function plainName(edid, diffuse, key) {
  let s = String(edid || '').replace(/^ANW_Ground_/, '');
  if (!s) s = String(diffuse || key || '').split('/').pop().replace(/\.dds$/i, '');
  const [base, variant] = s.split('~');
  const w = base.replace(/^L(?=[A-Z])/, '').replace(/_?duplicate\d*/ig, '').replace(/\d+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
  const n = w ? w[0].toUpperCase() + w.slice(1) : key;
  return variant ? `${n} (${variant.replace(/-/g, ' ')})` : n;
}

// The palette: every land texture the place's ground and its source list, most used first (the place's own ground
// counted before the source's), each {key, name, used}; with the land table, only those it has a picture of.
export function palette(terrains, table = null) {
  const used = new Map(), ltex = {};
  terrains.forEach((t, i) => {
    if (!t) return;
    Object.assign(ltex, t.ltex || {});
    for (const c of t.list || []) for (const q of c.quadrants || []) for (const k of [q.base, ...(q.layers || []).map((l) => l.tex)]) if (k) used.set(k, (used.get(k) || 0) + (i === 0 ? 2 : 1));
  });
  return Object.keys(ltex).filter((key) => !table || table[key]?.file).map((key) => ({ key, name: plainName(ltex[key]?.edid, ltex[key]?.diffuse, key), used: used.get(key) || 0 }))
    .sort((a, b) => b.used - a.used || a.name.localeCompare(b.name));
}

export class PaintTool {
  constructor(app) {
    this.app = app;
    this.o = { texture: null, brush: 'soft', size: 384, softness: 0.6, strength: 0.8, seed: 1 };
    this.stroke = null; this.preview = null;
  }
  // the rows the land draws: the place's paint and the stroke being drawn
  rows() { const m = [...this.app.model.paint.values()]; return this.preview ? [...m, this.preview] : m; }
  row(points) {
    const o = this.o, erase = o.brush === 'erase';
    const r = { id: nextId([...this.app.model.paint.values()]), brush: erase ? 'soft' : o.brush, size: o.size, softness: o.softness, strength: o.strength, points, by: 'owner' };
    if (erase) r.erase = true; else r.texture = o.texture;
    if (o.brush === 'scatter') r.seed = o.seed;
    return r;
  }
  redraw(r) { const tm = this.app.ours.terrainMesh; if (tm && r) { tm.rebakeAll(bounds(r)); this.app.ours.view.redraw(); } }
  get tool() {
    const t = this, a = this.app;
    return this._tool || (this._tool = {
      wantsDrag: () => true,
      hover: (e) => a.tools.brushRing(e.view, e.ground(), t.o.size),
      tap: (e) => { if (t._tool.down(e) !== false) t._tool.up(e); },
      down: (e) => {
        if (a.ours.space !== 'exterior') { a.toast('Ground can be painted outside only.'); return false; }
        if (t.o.brush !== 'erase' && !t.o.texture) { a.toast('Pick a texture first.'); a.panels.open('paint'); return false; }
        const g = e.ground(); if (!g) return false;
        t.stroke = [[rnd(g[0]), rnd(g[1]), rnd(e.pressure, 100)]];
        t.preview = t.row(t.stroke); t.redraw(t.preview);
      },
      move: (e) => {
        const g = e.ground(); a.tools.brushRing(e.view, g, t.o.size * (0.35 + 0.65 * e.pressure));
        if (!g || !t.stroke) return;
        const last = t.stroke[t.stroke.length - 1];
        if (Math.hypot(g[0] - last[0], g[1] - last[1]) < Math.max(24, t.o.size / 6)) return;   // a point every sixth of the brush
        if (t.stroke.length >= 3900) return;
        t.stroke.push([rnd(g[0]), rnd(g[1]), rnd(e.pressure, 100)]);
        a.tools.soon('paint', () => { if (!t.stroke) return; t.preview = t.row(t.stroke); t.redraw(t.preview); });
      },
      up: () => t.end(),
      cancel: () => t.end(true),
    });
  }
  end(cancel) {
    const a = this.app, pts = this.stroke, r = this.preview; this.stroke = null; this.preview = null;
    if (!pts || !r) return;
    if (cancel) { this.redraw(r); return; }
    r.points = pts; if (this.o.brush === 'scatter') this.o.seed = (this.o.seed * 7919 + 13) % 65521;
    a.push([{ op: 'paint.add', paint: r }], 'exterior');
  }
  panel() {
    const a = this.app, o = this.o, P = a.panels;
    const body = document.createElement('div');
    const pal = palette([a.terrain, a.src?.terrain], a.landTex?.table);
    if (!o.texture && pal.length) o.texture = pal[0].key;
    body.innerHTML = `<p>Paint the ground with the pen: pick a texture and a brush, press harder for a wider, stronger mark. The eraser brings back the world's own ground. Undo and redo as for any edit; Save keeps it.</p>
      <div class="seg" role="group" aria-label="Brush">${BRUSH_KINDS.map(([v, l]) => `<button data-brush="${v}" aria-pressed="${v === o.brush}">${l}</button>`).join('')}</div>
      ${[['size', 'Size', 64, 2048, 32, (v) => `${Math.round(v / 70 * 10) / 10} m`], ['softness', 'Softness', 0, 1, 0.05, (v) => `${Math.round(v * 100)}%`], ['strength', 'Strength', 0.05, 1, 0.05, (v) => `${Math.round(v * 100)}%`]]
    .map(([k, l, mn, mx, st, f]) => `<label class="field">${l} <strong data-out="${k}">${f(o[k])}</strong><input type="range" data-k="${k}" min="${mn}" max="${mx}" step="${st}" value="${o[k]}"></label>`).join('')}
      <h3>Textures</h3>
      <div class="paint-palette" role="listbox" aria-label="Ground textures">${pal.map((t) => {
    const url = a.landTex?.url(t.key, a.ltexAll || a.terrain?.ltex);
    return `<button class="paint-swatch" role="option" data-key="${esc(t.key)}" aria-selected="${t.key === o.texture}" title="${esc(t.name)}">${url ? `<img alt="" loading="lazy" src="${esc(url)}">` : '<span class="noimg"></span>'}<span>${esc(t.name)}</span></button>`;
  }).join('') || '<p>No land textures here.</p>'}</div>
      <h3>Painted</h3><p class="tag">${a.model.paint.size} stroke${a.model.paint.size === 1 ? '' : 's'} on this place's ground.</p>`;
    const fmts = { size: (v) => `${Math.round(v / 70 * 10) / 10} m`, softness: (v) => `${Math.round(v * 100)}%`, strength: (v) => `${Math.round(v * 100)}%` };
    body.querySelectorAll('[data-brush]').forEach((b) => { b.onclick = () => { o.brush = b.dataset.brush; body.querySelectorAll('[data-brush]').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
    body.querySelectorAll('input[data-k]').forEach((inp) => { inp.oninput = () => { const k = inp.dataset.k; o[k] = Number(inp.value); body.querySelector(`[data-out="${k}"]`).textContent = fmts[k](o[k]); }; });
    body.querySelectorAll('.paint-swatch').forEach((b) => { b.onclick = () => { o.texture = b.dataset.key; if (o.brush === 'erase') { o.brush = 'soft'; body.querySelectorAll('[data-brush]').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.brush === 'soft'))); } body.querySelectorAll('.paint-swatch').forEach((x) => x.setAttribute('aria-selected', String(x === b))); }; });
    P.show('Paint ground', [body]);
  }
}
