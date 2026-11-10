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
  groundcover: [4000, 4000], plant: [8000, 140000], tree: [12000, 140000], rock: [12000, 140000], clutter: [8000, 30000],
  light: [6000, 8000], marker: [6000, 8000], default: [40000, 80000],
};
const PICK_RANK = { actor: 0, door: 1, furniture: 2, container: 2, clutter: 3, light: 3, activator: 3, marker: 3,
  building: 4, static: 5, rock: 6, tree: 7, plant: 8, groundcover: 9, water: 10, other: 6 };
export const pickRank = (k) => PICK_RANK[k] ?? 6;

// Textures inside a model are fetched here, not by the loader: a texture the server lacks (a missing normal map,
// or one the mod itself never shipped) falls back quietly instead of failing in the console. Normal maps are
// never fetched: the studio draws every model with one light, plain material (few shader programs, cheap pixels).
const WRAP = { 33071: THREE.ClampToEdgeWrapping, 33648: THREE.MirroredRepeatWrapping, 10497: THREE.RepeatWrapping };
const FLAT = (() => { const t = new THREE.DataTexture(new Uint8Array([128, 128, 255, 255]), 1, 1); t.needsUpdate = true; t.userData.flat = true; return t; })();
const texCache = new Map(); // url -> Promise<Texture|null>
// Detail set by the governor (governor.js): veg scales how far plants, trees, rocks and clutter are drawn,
// density thins far vegetation (every n-th), lod scales the distance the full model is used, tex caps texture size.
export const detail = { veg: 1, density: 1, lod: 1, tex: 4096 };
const BM = { imageOrientation: 'none', premultiplyAlpha: 'none', colorSpaceConversion: 'none' };
function fetchTexture(url, sampler) {
  if (!texCache.has(url)) {
    texCache.set(url, fetch(url, { credentials: 'same-origin' })
      // the server answers a texture it lacks with 200 and X-Argonia-Missing: 1 (or 404): both are missing
      .then((r) => (r.ok && r.headers.get('X-Argonia-Missing') !== '1' ? r.blob() : null))
      .then((b) => (b ? createImageBitmap(b, BM) : null))
      // textures larger than the governor's size are scaled down as they arrive (detail.tex)
      .then((bm) => (bm && Math.max(bm.width, bm.height) > detail.tex
        ? createImageBitmap(bm, { ...BM, resizeWidth: Math.max(1, Math.round(bm.width * detail.tex / Math.max(bm.width, bm.height))),
          resizeHeight: Math.max(1, Math.round(bm.height * detail.tex / Math.max(bm.width, bm.height))), resizeQuality: 'medium' }) : bm))
      .then((bm) => {
        if (!bm) return null;
        const t = new THREE.Texture(bm); t.flipY = false; t.anisotropy = 2;
        t.wrapS = WRAP[sampler?.wrapS] ?? THREE.RepeatWrapping; t.wrapT = WRAP[sampler?.wrapT] ?? THREE.RepeatWrapping;
        t.needsUpdate = true; return t;
      })
      .catch(() => null));
  }
  return texCache.get(url);
}
// Plants, rocks and small things are many and seen small: their textures are asked for at a quarter of the memory.
const SMALL_TEX = new Set(['tree', 'plant', 'groundcover', 'rock', 'clutter', 'light', 'marker', 'other']);
const sized = (uri, kind) => (SMALL_TEX.has(kind) ? uri.replace(/([?&]size=)(\d+)/, (m, a, n) => a + Math.min(Number(n), 256)) : uri);
class QuietTextures {
  constructor(parser, kind) { this.parser = parser; this.kind = kind; this.name = 'studio_quiet_textures'; }
  loadTexture(i) {
    const json = this.parser.json, def = json.textures[i], img = json.images?.[def.source];
    if (!img?.uri || img.uri.startsWith('data:')) return null;
    const normalOnly = !(json.materials || []).some((m) => m.pbrMetallicRoughness?.baseColorTexture?.index === i || m.emissiveTexture?.index === i);
    if (normalOnly) return Promise.resolve(FLAT);
    return fetchTexture(sized(img.uri, this.kind), json.samplers?.[def.sampler]).then((t) => {
      if (t) return t;
      const m = new THREE.Texture(); m.userData.missing = img.uri; return m;
    });
  }
}
const loaderFor = (kind) => new GLTFLoader().register((parser) => new QuietTextures(parser, kind));

// One plain material per look, shared: the diffuse (or, when the texture is missing, a quiet colour of the
// thing's kind from the land's palette), cut-out alpha for leaves and lily pads (blending does not sort inside
// an instanced mesh, and draws a blended pad's empty rim as a pale ring), both faces where the model wants them.
const matCache = new Map();
export function plainMaterial(m, kind) {
  const missing = m.map?.userData.missing, map = m.map && !missing && m.map.image ? m.map : null;
  const cut = m.alphaTest > 0 || m.transparent;
  const colour = map ? m.color.getHexString() : (KIND_COLOUR[kind] || '#8a8270').replace('#', '');
  const key = `${map?.uuid || '-'}|${colour}|${cut}|${m.side}|${m.vertexColors}`;
  if (!matCache.has(key)) {
    matCache.set(key, new THREE.MeshLambertMaterial({ map, color: `#${colour}`, side: m.side, vertexColors: m.vertexColors,
      alphaTest: cut && map ? Math.max(0.35, m.alphaTest || 0.5) : 0, name: m.name }));
    if (missing) console.info(`studio: texture missing on the server, drawn plain: ${missing}`);
  }
  return matCache.get(key);
}

let inFlight = 0; const queue = [];
function pump() {
  while (inFlight < 4 && queue.length) {
    queue.sort((a, b) => a.pri - b.pri);
    const job = queue.shift(); inFlight++;
    job.run().finally(() => { inFlight--; pump(); });
  }
}
const meshCache = new Map(); // model -> Promise<[{geometry, material}]>
export function loadModel(model, pri = 0, level = 0, kind = 'other') {
  const key = `${model}|${level}`;
  if (!meshCache.has(key)) {
    meshCache.set(key, new Promise((resolve) => {
      queue.push({ pri, run: async () => {
        try {
          const buf = await getMesh(model, { level });
          const gltf = await loaderFor(kind).parseAsync(buf, '');
          gltf.scene.updateMatrixWorld(true);
          const parts = [];
          gltf.scene.traverse((o) => {
            if (!o.isMesh) return;
            // the converter's stand-in for a model it could not read: marked, so callers can leave it out
            if (o.name === 'placeholder' || o.material?.name === 'placeholder') parts.placeholder = true;
            // geometry the game never draws: editor markers (and all under them) show only in the Creation Kit
            for (let q = o; q; q = q.parent) if (/^editormarker/i.test(q.name || '')) return;
            const g = o.geometry.clone(); g.applyMatrix4(o.matrixWorld);
            for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv', 'color'].includes(k)) g.deleteAttribute(k);
            parts.push({ geometry: g, material: plainMaterial(o.material, kind) });
          });
          resolve(parts);
        } catch (e) { console.info(`studio: ${e.message}`); resolve(null); }
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
      // not yet loaded: a faint ghost of the bounds, never an opaque block
      : new THREE.MeshBasicMaterial({ color: KIND_COLOUR[kind] || '#999', transparent: true, opacity: 0.07, depthWrite: false }));
  }
  return boxMats.get(k);
}
const BIG = 420; // bounds (game units, 70 to the metre) past which a thing is never distance-culled: 6 m
const THIN = new Set(['tree', 'plant', 'groundcover', 'rock', 'clutter']);
const tmpM = new THREE.Matrix4(), tmpV = new THREE.Vector3(), boundsM = new THREE.Matrix4();
// A ref's matrix is kept with the pose it was worked out from: the world's 37,000 plants are not recomputed when
// a list is set again after an edit, and a ref moved in place (a drag) gets a new matrix because its pose differs.
const MATS = new WeakMap();
function matrixOf(ref, origin) {
  const p = ref.pos, r = ref.rot, sc = ref.scale ?? 1; let m = MATS.get(ref);
  if (m && m.o === origin && m.x === p[0] && m.y === p[1] && m.z === p[2] && m.sc === sc && m.rx === (r?.[0] || 0) && m.ry === (r?.[1] || 0) && m.rz === (r?.[2] || 0)) return m;
  m = new THREE.Matrix4().fromArray(refMatrix(p, r || [0, 0, 0], sc, origin));
  m.o = origin; m.x = p[0]; m.y = p[1]; m.z = p[2]; m.sc = sc; m.rx = r?.[0] || 0; m.ry = r?.[1] || 0; m.rz = r?.[2] || 0;
  MATS.set(ref, m); return m;
}
// Only the instances in use are sent to the GPU.
function sendInstances(mesh, n) {
  const a = mesh.instanceMatrix; a.clearUpdateRanges?.(); a.addUpdateRange?.(0, n * 16); a.needsUpdate = true;
}

// Models that have arrived wait here and are switched on a few at a time, their textures sent to the GPU first,
// so a burst of arrivals never stalls a frame (view.js calls drainReady before each draw).
const ready = { jobs: [], push(fn, parts, layer) { this.jobs.push({ fn, parts, layer }); } };
const sent = new WeakMap(); // renderer -> WeakSet of textures and materials already on its GPU
// Shader programs are linked off the main thread (compileAsync, parallel compile) before a model is switched
// on: a link done inside a draw stalls the page for a second or more on a slow GPU.
const PAR = new WeakMap();
const parallel = (r) => { if (!PAR.has(r)) PAR.set(r, !!r.extensions.has('KHR_parallel_shader_compile')); return PAR.get(r); };
export function drainReady(renderer, layers = [], scene = null, camera = null, budgetMs = 8) {
  const t0 = performance.now(), mine = sent.get(renderer) || new WeakSet(); sent.set(renderer, mine);
  let left = 0, newLook = false;
  for (let i = 0; i < ready.jobs.length; i++) {
    const j = ready.jobs[i];
    if (layers && !layers.includes(j.layer)) continue;
    left++;
    const fresh = j.parts.filter((p) => !mine.has(p.material));
    if (fresh.length && scene && camera) {
      // without parallel compile (software GL) the link happens at the first draw: one new look per frame
      if (!parallel(renderer)) {
        if (newLook) continue;
        newLook = true; for (const p of fresh) mine.add(p.material);
      } else {
      if (!j.compiling) {
        const probe = new THREE.Group();
        for (const p of fresh) { const m = new THREE.InstancedMesh(p.geometry, p.material, 1); m.frustumCulled = false; probe.add(m); }
        j.compiling = renderer.compileAsync(probe, camera, scene).catch(() => {}).then(() => { for (const p of fresh) mine.add(p.material); j.compiling = null; });
      }
      continue;
      }
    }
    if (performance.now() - t0 > budgetMs) continue;
    for (const p of j.parts) { const m = p.material.map; if (m && !mine.has(m)) { renderer.initTexture(m); mine.add(m); } }
    j.fn(); ready.jobs.splice(i--, 1); left--;
  }
  return left;
}

// An effect (mist, fog, gas, glow): under effects\, or a model or record Bethesda names fx*.
export const isEffect = (base) => /^effects[\\/]/i.test(base?.model || '') || /(^|[\\/])fx[^\\/]*\.nif$/i.test(base?.model || '') || /^fx/i.test(base?.edid || '');
// One base's instances.
class Group {
  constructor(layer, base, kind, ghost) {
    this.layer = layer; this.base = base; this.kind = kind; this.ghost = ghost; this.refs = [];
    this.full = null; this.cap = 0; this.box = null; this.wantModel = false; this.matrices = [];
    // effects: the game's effect meshes, wherever a mod keeps them (Bethesda names them fx*: Dragonborn's Apocrypha
    // mist lives in dlc02\dungeons, not effects\)
    this.fx = isEffect(base);
    // a thing with no model (a marker, a trigger volume, a sound) has nothing to show: it is neither drawn nor picked
    this.unseen = !base?.model && !ghost;
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
    // every part of one model shares one buffer of instance matrices
    let shared = null;
    this.full = this.fullParts.map((p) => {
      const m = new THREE.InstancedMesh(p.geometry, this.ghost ? boxMaterial(this.kind, true) : p.material, shared ? 1 : this.cap);
      if (shared) m.instanceMatrix = shared; else shared = m.instanceMatrix;
      m.count = 0; m.frustumCulled = false; m.userData.group = this; this.layer.root.add(m); return m;
    });
  }
  setRefs(refs) {
    this.refs = refs; this.ensure(refs.length);
    this.matrices = refs.map((r) => matrixOf(r, this.layer.origin));
    let s = 1; for (const r of refs) if ((r.scale ?? 1) > s) s = r.scale;
    this.big = this.radius * 2 * s > BIG;
  }
  // Fill instance buffers from what the camera can see.
  cull(cam, frustum, sphere) {
    // effects (mist, waterfall sheets, glows) are shader tricks of the game's: drawn here they are pale rings
    // and sheets over the land, so they stay unseen (still listed and pickable)
    if (this.fx || this.unseen) { this.box.visible = false; this.box.count = 0; return 0; }
    // everything placed (layer.always) is drawn whole at any distance: zoomed right out, every building, plant, tree
    // and rock shows, the ground cover placed one by one too; the grown grass (grass.js) thins itself by distance
    const always = !!this.layer.always;
    const [near, far] = RANGE[this.kind] || RANGE.default;
    // anything big (a building, dock, bridge, ship, big rock or tree: bounds over a few metres) is never thinned or
    // cut by distance, at any detail level; only small clutter and plants thin out (the frustum still applies)
    const big = this.big;
    // detail only changes how near the full model starts and how many small plants are skipped; plants and trees
    // are drawn out past the whole place (the far range) at every level, and trees are never skipped
    const thin = THIN.has(this.kind) && !big, scale = big ? 1 : this.layer.rangeScale * (thin ? detail.veg : 1);
    const farD = far * (big ? 1 : this.layer.rangeScale);
    // plants, trees and rocks use their light model all the way out once it has arrived: no stand-ins
    const nearD = LIGHT.has(this.kind) && this.full ? farD : near * scale * (thin ? detail.lod : 1);
    const skips = thin && detail.density > 1 && this.kind !== 'tree' && this.kind !== 'rock';
    let nf = 0, nb = 0, nearest = Infinity;
    for (let i = 0; i < this.refs.length; i++) {
      const m = this.matrices[i];
      tmpV.setFromMatrixPosition(m);
      const d = tmpV.distanceTo(cam.position);
      if (!big && !always && d > farD + this.radius) continue;
      sphere.center.copy(tmpV); sphere.radius = this.radius * (this.refs[i].scale ?? 1) * 1.8 + 50;
      if (!frustum.intersectsSphere(sphere)) continue;
      if (skips && d > near * scale * 0.5 && i % detail.density) continue;
      nearest = Math.min(nearest, d);
      if ((always || d < nearD) && this.full) this.full[0].setMatrixAt(nf++, m);
      // no stand-in boxes: a model not yet here, or too far for its kind, shows nothing (cleared plants keep their ghost)
      else if (this.ghost) { tmpM.multiplyMatrices(m, this.boxLocal); this.box.setMatrixAt(nb++, tmpM); }
    }
    // an empty instanced mesh still costs a draw setup: hide it
    this.box.count = nb; this.box.visible = nb > 0; if (nb) sendInstances(this.box, nb);
    if (this.full) { for (const fm of this.full) { fm.count = nf; fm.visible = nf > 0; } if (nf) sendInstances(this.full[0], nf); }
    if (!this.fullParts && !this.wantModel && nearest < (always ? Infinity : Math.max(near * scale * 1.3, LIGHT.has(this.kind) ? farD : 0)) && this.base?.model) {
      this.wantModel = true;
      loadModel(this.base.model, nearest, LIGHT.has(this.kind) ? 1 : 0, this.kind).then((parts) => {
        if (!parts || !parts.length) return;
        ready.push(() => { this.fullParts = parts; this.makeFull(); this.layer.dirty(); this.layer.onModel?.(this); }, parts, this.layer);
        this.layer.onDirty();   // a view at rest draws again, so a model that arrives is switched on without waiting for a touch
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
      if (g.unseen || g.fx) continue;
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
