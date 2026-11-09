// The land drawn: a mesh per cell at every height point (every other point far away), splatted with the game's
// land textures near the camera (base per quadrant, alpha layers, paths on top) and coloured by each texture's
// average colour far away; water planes at each cell's water height.
import * as THREE from 'three';
import { getJSON, texUrl } from './api.js';

const TEX_PX = 512, Q = TEX_PX / 2, TILES = 3, NEAR_CELLS = 2.6, MAX_BAKED = 36;

// Land textures: the WebP table from the asset step, else the texture converter on the record's diffuse path.
export class LandTex {
  constructor() { this.table = null; this.imgs = new Map(); this.waiting = new Map(); }
  async init() { try { this.table = await getJSON('/asset/land', { optional: true }); } catch { this.table = null; } return this; }
  url(key, ltex) {
    const row = this.table?.[key];
    if (row?.file) return `${window.STUDIO_API || ''}/api/asset/land/${encodeURIComponent(row.file)}`;
    const diffuse = ltex?.[key]?.diffuse || (key && key.includes('/') ? key : null);
    return diffuse ? texUrl(diffuse.replace(/^textures\//, 'textures/'), 256) : null;
  }
  avg(key, ltex) {
    const a = this.table?.[key]?.avg; if (a) return a;
    const s = (ltex?.[key]?.edid || key || '').toLowerCase();
    return /road|path|dirt|mud/.test(s) ? '#6e5a41' : /sand|beach/.test(s) ? '#a89a72' : /rock|stone|cliff/.test(s) ? '#6c6a62' : '#4d5a2c';
  }
  load(key, ltex) {
    if (this.imgs.has(key)) return Promise.resolve(this.imgs.get(key));
    if (this.waiting.has(key)) return this.waiting.get(key);
    const url = this.url(key, ltex);
    const p = !url ? Promise.resolve(null) : new Promise((res) => {
      const im = new Image(); im.crossOrigin = 'use-credentials';
      im.onload = () => { this.imgs.set(key, im); res(im); }; im.onerror = () => { this.imgs.set(key, null); res(null); }; im.src = url;
    });
    this.waiting.set(key, p); return p;
  }
}

function fillTiled(ctx, img, x, y, w, h, fallback) {
  if (!img) { ctx.fillStyle = fallback; ctx.fillRect(x, y, w, h); return; }
  const tw = w / TILES, th = h / TILES;
  for (let i = 0; i < TILES; i++) for (let j = 0; j < TILES; j++) ctx.drawImage(img, x + i * tw, y + j * th, tw, th);
}
const hex = (h) => { const c = new THREE.Color(h); return [c.r, c.g, c.b]; };
const WATER = ['#3d6f78', '#4a6a5a', '#385f70', '#506b55', '#2f5f73'];
function waterColour(type) { let h = 0; for (const ch of String(type)) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return WATER[h % WATER.length]; }

export class TerrainMesh {
  constructor(terrain, origin, { paths = () => [], pathStyles = {}, landTex } = {}) {
    this.t = terrain; this.origin = origin; this.group = new THREE.Group(); this.paths = paths; this.pathStyles = pathStyles;
    this.lt = landTex; this.cells = new Map(); this.water = new THREE.Group(); this.group.add(this.water);
    this.showChanged = true; this.baked = new Set(); this.queue = []; this.onChange = () => {};
    const g = terrain.grid; this.fine = []; this.coarse = [];
    for (let r = 0; r < g - 1; r++) for (let c = 0; c < g - 1; c++) { const i = r * g + c; this.fine.push(i, i + 1, i + g, i + 1, i + g + 1, i + g); }
    for (let r = 0; r < g - 1; r += 2) for (let c = 0; c < g - 1; c += 2) { const i = r * g + c; this.coarse.push(i, i + 2, i + 2 * g, i + 2, i + 2 * g + 2, i + 2 * g); }
    this.farMat = new THREE.MeshLambertMaterial({ vertexColors: true });
  }
  async build() {
    const t = this.t, g = t.grid;
    for (const c of t.list) {
      const geo = new THREE.BufferGeometry();
      const pos = new Float32Array(g * g * 3), uv = new Float32Array(g * g * 2);
      for (let r = 0; r < g; r++) for (let col = 0; col < g; col++) {
        const i = r * g + col;
        pos[i * 3] = c.cell[0] * t.size + col * t.step - this.origin[0];
        pos[i * 3 + 1] = c.cell[1] * t.size + r * t.step - this.origin[1];
        uv[i * 2] = col / (g - 1); uv[i * 2 + 1] = r / (g - 1);
      }
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
      geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(g * g * 3), 3));
      geo.setIndex(this.coarse);
      const mesh = new THREE.Mesh(geo, this.farMat); mesh.userData.cell = c.cell; mesh.matrixAutoUpdate = false;
      this.group.add(mesh);
      const e = { c, mesh, geo, lod: 'far', centre: [(c.cell[0] + 0.5) * t.size - this.origin[0], (c.cell[1] + 0.5) * t.size - this.origin[1]] };
      this.cells.set(c.cell.join(','), e);
      this.splatColours(e); this.updateHeights(e);
      if (c.water) {
        const w = new THREE.Mesh(new THREE.PlaneGeometry(t.size, t.size), new THREE.MeshLambertMaterial({
          color: c.water.colour || waterColour(c.water.type), transparent: true, opacity: 0.6, depthWrite: false }));
        w.position.set(e.centre[0], e.centre[1], c.water.height - this.origin[2]);
        w.renderOrder = 2; w.userData.water = c.water; this.water.add(w);
      }
    }
    this.tint();
    return this;
  }
  // Far away: each vertex the blend of its quadrant's texture average colours, times the land's vertex colours.
  splatColours(e) {
    const g = this.t.grid, col = e.geo.attributes.color.array, lt = this.t.ltex, base = new Float32Array(g * g * 3);
    for (let r = 0; r < g; r++) for (let c = 0; c < g; c++) {
      const qi = (r >= 16 ? 2 : 0) + (c >= 16 ? 1 : 0), q = e.c.quadrants[qi];
      let rgb = hex(this.lt ? this.lt.avg(q.base, lt) : '#4d5a2c');
      const ar = Math.min(16, r - (r >= 16 ? 16 : 0)), ac = Math.min(16, c - (c >= 16 ? 16 : 0));
      for (const l of q.layers) {
        const a = l.alpha?.[ar * 17 + ac] || 0; if (!a) continue;
        const lc = hex(this.lt ? this.lt.avg(l.tex, lt) : '#6e5a41'); rgb = rgb.map((v, k) => v + (lc[k] - v) * a);
      }
      const i = (r * g + c) * 3, vc = e.c.vcol;
      for (let k = 0; k < 3; k++) base[i + k] = rgb[k] * (vc ? vc[i + k] / 255 : 1);
    }
    e.baseColour = base; col.set(base); e.geo.attributes.color.needsUpdate = true;
  }
  updateHeights(e) {
    const t = this.t, g = t.grid, pos = e.geo.attributes.position.array;
    for (let r = 0; r < g; r++) for (let col = 0; col < g; col++) pos[(r * g + col) * 3 + 2] = t.h(e.c.cell, r, col) - this.origin[2];
    // normals from every point, whichever level is drawn
    const idx = e.geo.index; e.geo.setIndex(this.fine); e.geo.computeVertexNormals(); e.geo.setIndex(idx);
    e.geo.attributes.position.needsUpdate = true; e.geo.computeBoundingSphere();
  }
  refreshCells(keys) { for (const k of keys) { const e = this.cells.get(k); if (e) this.updateHeights(e); } }
  // Cells near the camera's target get every height point and the full texture splat; far ones go light.
  update(target) {
    const near = [];
    for (const e of this.cells.values()) {
      const d = Math.hypot(e.centre[0] - target.x, e.centre[1] - target.y) / this.t.size;
      const want = d < NEAR_CELLS ? 'near' : 'far';
      if (want === 'near') near.push([d, e]);
      else if (e.lod === 'near') this.unbake(e);
    }
    near.sort((a, b) => a[0] - b[0]);
    for (const [, e] of near.slice(MAX_BAKED)) if (e.lod === 'near') this.unbake(e);
    for (const [, e] of near.slice(0, MAX_BAKED)) if (e.lod !== 'near' && !e.pending) { e.pending = true; this.queue.push(e); }
    this.pump();
  }
  async pump() {
    if (this.pumping) return; this.pumping = true;
    while (this.queue.length) {
      const e = this.queue.shift();
      const keys = new Set(); for (const q of e.c.quadrants) { keys.add(q.base); for (const l of q.layers) keys.add(l.tex); }
      for (const p of this.paths()) if (this.pathStyles[p.style]?.tex) keys.add(this.pathStyles[p.style].tex);
      await Promise.all([...keys].filter(Boolean).map((k) => this.lt?.load(k, this.t.ltex)));
      if (!e.canvas) { e.canvas = document.createElement('canvas'); e.canvas.width = e.canvas.height = TEX_PX; e.tex = new THREE.CanvasTexture(e.canvas); e.tex.colorSpace = THREE.SRGBColorSpace; e.tex.anisotropy = 4; }
      e.mat = e.mat || new THREE.MeshLambertMaterial({ map: e.tex, vertexColors: true });
      this.bake(e); e.mesh.material = e.mat; e.geo.setIndex(this.fine); e.lod = 'near'; e.pending = false; this.baked.add(e);
      this.tintCell(e); this.onChange();
      await new Promise((r) => setTimeout(r, 0));
    }
    this.pumping = false;
  }
  unbake(e) {
    e.mesh.material = this.farMat; e.geo.setIndex(this.coarse); e.lod = 'far';
    e.tex?.dispose(); e.mat?.dispose(); e.canvas = null; e.tex = null; e.mat = null; this.baked.delete(e); this.tintCell(e);
  }
  setPathStyles(styles) { this.pathStyles = styles; this.rebakeAll(); }
  // Texture layers, then paths over the land as the game will dress them.
  bake(e) {
    if (!e.canvas) return;
    const ctx = e.canvas.getContext('2d'), lt = this.t.ltex, img = (k) => this.lt?.imgs.get(k);
    const tmp = this._tmp || (this._tmp = document.createElement('canvas')); tmp.width = tmp.height = Q;
    const tctx = tmp.getContext('2d');
    const mask = this._mask || (this._mask = document.createElement('canvas')); mask.width = mask.height = 17;
    const mctx = mask.getContext('2d');
    for (let qi = 0; qi < 4; qi++) {
      // canvas y runs north to south; quadrants are SW, SE, NW, NE
      const qx = (qi % 2) * Q, qy = qi < 2 ? Q : 0, q = e.c.quadrants[qi];
      ctx.globalCompositeOperation = 'source-over';
      fillTiled(ctx, img(q.base), qx, qy, Q, Q, this.lt ? this.lt.avg(q.base, lt) : '#4d5a2c');
      for (const l of q.layers) {
        if (!l.alpha) continue;
        const data = mctx.createImageData(17, 17);
        for (let r = 0; r < 17; r++) for (let c = 0; c < 17; c++) data.data[((16 - r) * 17 + c) * 4 + 3] = Math.max(0, Math.min(255, l.alpha[r * 17 + c] * 255));
        mctx.putImageData(data, 0, 0);
        tctx.globalCompositeOperation = 'source-over'; tctx.clearRect(0, 0, Q, Q);
        fillTiled(tctx, img(l.tex), 0, 0, Q, Q, this.lt ? this.lt.avg(l.tex, lt) : '#6e5a41');
        tctx.globalCompositeOperation = 'destination-in'; tctx.imageSmoothingEnabled = true;
        tctx.drawImage(mask, 0, 0, 17, 17, 0, 0, Q, Q);
        ctx.drawImage(tmp, qx, qy);
      }
    }
    const cx0 = e.c.cell[0] * this.t.size, cy1 = (e.c.cell[1] + 1) * this.t.size, k = TEX_PX / this.t.size;
    for (const p of this.paths()) {
      const st = this.pathStyles[p.style] || {}, pim = st.tex ? img(st.tex) : null;
      ctx.save();
      ctx.strokeStyle = pim ? ctx.createPattern(pim, 'repeat') : (st.colour || (this.lt ? this.lt.avg(st.tex, lt) : '#8a7656'));
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.beginPath();
      p.points.forEach(([x, y], i) => { const sx = (x - cx0) * k, sy = (cy1 - y) * k; i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy); });
      ctx.globalAlpha = 0.35; ctx.lineWidth = p.width * k * 1.3; ctx.stroke(); // a soft verge, as the game blends
      ctx.globalAlpha = 0.95; ctx.lineWidth = p.width * k; ctx.stroke();
      ctx.restore();
    }
    e.tex.needsUpdate = true;
  }
  rebakeAll() {
    for (const e of this.cells.values()) this.splatPaths(e);
    for (const e of this.baked) this.bake(e);
    this.onChange();
  }
  // Far cells show paths in their vertex colours.
  splatPaths(e) {
    if (!e.baseColour) return;
    const g = this.t.grid, col = e.geo.attributes.color.array; col.set(e.baseColour);
    const x0 = e.c.cell[0] * this.t.size, y0 = e.c.cell[1] * this.t.size;
    for (const p of this.paths()) {
      const st = this.pathStyles[p.style] || {}, rgb = hex(st.colour || (this.lt ? this.lt.avg(st.tex, this.t.ltex) : '#6e5a41'));
      for (let r = 0; r < g; r++) for (let c = 0; c < g; c++) {
        const x = x0 + c * this.t.step, y = y0 + r * this.t.step;
        let near = false;
        for (let i = 1; i < p.points.length && !near; i++) near = segD(x, y, p.points[i - 1], p.points[i]) < p.width / 2;
        if (near) col.set(rgb, (r * g + c) * 3);
      }
    }
    e.farColour = Float32Array.from(col); this.tintCell(e);
  }
  // Changed land tinted amber so every patch is visible at a glance.
  tint() { for (const e of this.cells.values()) this.tintCell(e); this.onChange(); }
  tintCell(e) {
    const g = this.t.grid, col = e.geo.attributes.color.array;
    if (e.lod === 'near') col.fill(1); else if (e.farColour || e.baseColour) col.set(e.farColour || e.baseColour);
    const o = this.t.override?.get(e.c.cell.join(','));
    if (o && this.showChanged) for (const [idx, dz] of o) if (Math.abs(dz) > 0.5) { col[idx * 3] = 1.2; col[idx * 3 + 1] = 0.85; col[idx * 3 + 2] = 0.35; }
    e.geo.attributes.color.needsUpdate = true;
  }
}
function segD(x, y, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
  const t = l ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l)) : 0;
  return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy);
}
