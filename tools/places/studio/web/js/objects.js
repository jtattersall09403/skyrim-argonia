// Placed things drawn fast: one instanced mesh per base (a box of its bounds until its model arrives, and the
// box again far away), frustum and distance culling, models fetched lazily nearest first.
import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three-0.170.0/addons/loaders/GLTFLoader.js';
import { getMesh } from './api.js';
import { refMatrix } from './xform.js';

export const KIND_COLOUR = {
  building: '#a08f78', static: '#9a9488', clutter: '#c4a46a', tree: '#4f6b3a', plant: '#6f9a4a', groundcover: '#86a35a',
  rock: '#8b8a84', furniture: '#a5754b', door: '#c98b3c', container: '#9b6a3c', light: '#f2cf6a', activator: '#7aa3b8',
  marker: '#d05ad0', actor: '#4fa3d9', water: '#3d6f78', other: '#999999',
};
// How far each kind is drawn in full, and then as a box, in game units.
// Nearer than the first: the model (the light version for plants, trees and rocks); out to the second: a stand-in
// of the bounds (a cone for trees); beyond: not drawn.
const RANGE = {
  groundcover: [4000, 4000], plant: [8000, 12000], tree: [12000, 60000], rock: [12000, 30000], clutter: [8000, 10000],
  light: [6000, 8000], marker: [6000, 8000], default: [40000, 80000],
};
const PICK_RANK = { actor: 0, door: 1, furniture: 2, container: 2, clutter: 3, light: 3, activator: 3, marker: 3,
  building: 4, static: 5, rock: 6, tree: 7, plant: 8, groundcover: 9, water: 10, other: 6 };
export const pickRank = (k) => PICK_RANK[k] ?? 6;

const loader = new GLTFLoader();
const meshCache = new Map(); // model -> Promise<[{geometry, material}]>
let inFlight = 0; const queue = [];
function pump() {
  while (inFlight < 4 && queue.length) {
    queue.sort((a, b) => a.pri - b.pri);
    const job = queue.shift(); inFlight++;
    job.run().finally(() => { inFlight--; pump(); });
  }
}
export function loadModel(model, pri = 0, level = 0) {
  const key = `${model}|${level}`;
  if (!meshCache.has(key)) {
    meshCache.set(key, new Promise((resolve) => {
      queue.push({ pri, run: async () => {
        try {
          const buf = await getMesh(model, { level });
          const gltf = await loader.parseAsync(buf, '');
          gltf.scene.updateMatrixWorld(true);
          const parts = [];
          gltf.scene.traverse((o) => {
            if (!o.isMesh) return;
            const g = o.geometry.clone(); g.applyMatrix4(o.matrixWorld);
            const m = o.material; if (m.map) { m.map.anisotropy = 2; }
            parts.push({ geometry: g, material: m });
          });
          resolve(parts);
        } catch (e) { console.warn(e.message); resolve(null); }
      } });
      pump();
    }));
  }
  return meshCache.get(key);
}
// Plants, trees and rocks are many and seen from afar: they use the light version of their model.
const LIGHT = new Set(['tree', 'plant', 'groundcover', 'rock']);

const boxGeo = new THREE.BoxGeometry(1, 1, 1).translate(0.5, 0.5, 0.5);
const coneGeo = new THREE.ConeGeometry(0.5, 1, 6, 1).rotateX(Math.PI / 2).translate(0.5, 0.5, 0.5);
const boxMats = new Map();
function boxMaterial(kind, ghost) {
  const k = `${kind}|${ghost}`;
  if (!boxMats.has(k)) {
    boxMats.set(k, ghost
      ? new THREE.MeshBasicMaterial({ color: '#d9534f', transparent: true, opacity: 0.28, depthWrite: false })
      : new THREE.MeshLambertMaterial({ color: KIND_COLOUR[kind] || '#999' }));
  }
  return boxMats.get(k);
}
const tmpM = new THREE.Matrix4(), tmpV = new THREE.Vector3(), boundsM = new THREE.Matrix4();

// One base's instances.
class Group {
  constructor(layer, base, kind, ghost) {
    this.layer = layer; this.base = base; this.kind = kind; this.ghost = ghost; this.refs = [];
    this.full = null; this.cap = 0; this.box = null; this.wantModel = false; this.matrices = [];
    // effects and markers carry the record's "everything" bounds; draw them as a small box
    let b = base?.bounds || [[-32, -32, 0], [32, 32, 64]];
    if (b[1].some((v, i) => v - b[0][i] > 20000)) b = [[-32, -32, 0], [32, 32, 64]];
    this.bmin = b[0]; this.bsize = [0, 1, 2].map((i) => Math.max(1, b[1][i] - b[0][i]));
    this.radius = Math.hypot(...this.bsize) / 2;
    boundsM.makeScale(...this.bsize); boundsM.setPosition(...this.bmin); this.boxLocal = boundsM.clone();
  }
  ensure(n) {
    if (n <= this.cap) return;
    this.cap = Math.max(8, Math.ceil(n * 1.5));
    const mk = (geo, mat) => { const m = new THREE.InstancedMesh(geo, mat, this.cap); m.count = 0; m.frustumCulled = false; m.userData.group = this; this.layer.root.add(m); return m; };
    if (this.box) { this.layer.root.remove(this.box); this.box.dispose(); }
    this.box = mk(this.kind === 'tree' ? coneGeo : boxGeo, boxMaterial(this.kind, this.ghost));
    if (this.fullParts) this.makeFull();
  }
  makeFull() {
    if (this.full) for (const m of this.full) { this.layer.root.remove(m); m.dispose(); }
    this.full = this.fullParts.map((p) => {
      const m = new THREE.InstancedMesh(p.geometry, this.ghost ? boxMaterial(this.kind, true) : p.material, this.cap);
      m.count = 0; m.frustumCulled = false; m.userData.group = this; this.layer.root.add(m); return m;
    });
  }
  setRefs(refs) {
    this.refs = refs; this.ensure(refs.length);
    this.matrices = refs.map((r) => new THREE.Matrix4().fromArray(refMatrix(r.pos, r.rot || [0, 0, 0], r.scale ?? 1, this.layer.origin)));
  }
  // Fill instance buffers from what the camera can see.
  cull(cam, frustum, sphere) {
    const [near, far] = RANGE[this.kind] || RANGE.default;
    const scale = this.layer.rangeScale;
    let nf = 0, nb = 0, nearest = Infinity;
    for (let i = 0; i < this.refs.length; i++) {
      const m = this.matrices[i];
      tmpV.setFromMatrixPosition(m);
      const d = tmpV.distanceTo(cam.position);
      if (d > far * scale + this.radius) continue;
      sphere.center.copy(tmpV); sphere.radius = this.radius * (this.refs[i].scale ?? 1) * 1.8 + 50;
      if (!frustum.intersectsSphere(sphere)) continue;
      nearest = Math.min(nearest, d);
      if (d < near * scale && this.full) { for (const fm of this.full) fm.setMatrixAt(nf, m); nf++; }
      else { tmpM.multiplyMatrices(m, this.boxLocal); this.box.setMatrixAt(nb++, tmpM); }
    }
    this.box.count = nb; this.box.instanceMatrix.needsUpdate = true;
    if (this.full) for (const fm of this.full) { fm.count = nf; fm.instanceMatrix.needsUpdate = true; }
    if (!this.fullParts && !this.wantModel && nearest < near * scale * 1.3 && this.base?.model) {
      this.wantModel = true;
      loadModel(this.base.model, nearest, LIGHT.has(this.kind) ? 1 : 0).then((parts) => {
        if (!parts || !parts.length) return;
        this.fullParts = parts; this.makeFull(); this.layer.dirty(); this.layer.onModel?.(this);
      });
    }
    return nf + nb;
  }
  dispose() {
    for (const m of [this.box, ...(this.full || [])]) if (m) { this.layer.root.remove(m); m.dispose(); }
  }
}

export class ObjectLayer {
  constructor(origin, bases) {
    this.origin = origin; this.bases = bases; this.root = new THREE.Group(); this.groups = new Map();
    this.rangeScale = 1; this.refs = []; this.byId = new Map(); this._dirty = true; this.onDirty = () => {};
  }
  dirty() { this._dirty = true; this.onDirty(); }
  // refs: [{ref, ghost?}] for the current space.
  setRefs(list) {
    const buckets = new Map();
    this.refs = list; this.byId = new Map(list.map((e) => [e.ref.id, e]));
    for (const e of list) {
      const base = this.bases.get(e.ref.base), kind = e.ref.kind || base?.kind || 'other';
      const k = `${e.ref.base}|${e.ghost ? 1 : 0}`;
      if (!buckets.has(k)) buckets.set(k, { base, kind, ghost: !!e.ghost, refs: [] });
      buckets.get(k).refs.push(e.ref);
    }
    for (const [k, g] of this.groups) if (!buckets.has(k)) { g.dispose(); this.groups.delete(k); }
    for (const [k, b] of buckets) {
      let g = this.groups.get(k);
      if (!g) { g = new Group(this, b.base, b.kind, b.ghost); this.groups.set(k, g); }
      g.setRefs(b.refs);
    }
    this.dirty();
  }
  cull(camera) {
    const frustum = new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse));
    const sphere = new THREE.Sphere(); let n = 0;
    for (const g of this.groups.values()) n += g.cull(camera, frustum, sphere);
    this._dirty = false; this.drawn = n; return n;
  }
  // Everything the ray passes through, best pick first: kind rank, then distance.
  pick(ray, { kinds, includeGhosts = false } = {}) {
    const hits = [], inv = new THREE.Matrix4(), lr = new THREE.Ray(), box = new THREE.Box3(), p = new THREE.Vector3();
    for (const g of this.groups.values()) {
      if (g.ghost && !includeGhosts) continue;
      if (kinds && !kinds.has(g.kind)) continue;
      box.min.set(...g.bmin); box.max.set(g.bmin[0] + g.bsize[0], g.bmin[1] + g.bsize[1], g.bmin[2] + g.bsize[2]);
      for (let i = 0; i < g.refs.length; i++) {
        const m = g.matrices[i];
        tmpV.setFromMatrixPosition(m);
        if (ray.distanceSqToPoint(tmpV) > (g.radius * (g.refs[i].scale ?? 1) * 2 + 40) ** 2) continue;
        inv.copy(m).invert(); lr.copy(ray).applyMatrix4(inv);
        if (lr.intersectBox(box, p)) {
          p.applyMatrix4(m);
          hits.push({ ref: g.refs[i], kind: g.kind, ghost: g.ghost, dist: p.distanceTo(ray.origin), point: p.clone() });
        }
      }
    }
    hits.sort((a, b) => pickRank(a.kind) - pickRank(b.kind) || a.dist - b.dist);
    return hits;
  }
  // World-space box corners of a ref, for selection outlines and lasso tests.
  worldBox(ref) {
    const base = this.bases.get(ref.base), b = base?.bounds || [[-32, -32, 0], [32, 32, 64]];
    const m = new THREE.Matrix4().fromArray(refMatrix(ref.pos, ref.rot || [0, 0, 0], ref.scale ?? 1, this.origin));
    const pts = [];
    for (const x of [b[0][0], b[1][0]]) for (const y of [b[0][1], b[1][1]]) for (const z of [b[0][2], b[1][2]]) pts.push(new THREE.Vector3(x, y, z).applyMatrix4(m));
    return pts;
  }
}
