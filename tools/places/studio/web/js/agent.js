// The agent view: the studio's own scene drawn on request by tools/places/look.py. The page shows one canvas and no
// interface; window.agent answers the look tool: when the place is ready, apply or undo edits through the studio's
// own edit log, and draw one shot from a camera the tool chose (game coordinates, Z up) into a PNG.
import * as THREE from 'three';
import { pendingModels, drainAll } from './objects.js';

const css = `html.agent body > *:not(#stage) { display: none !important; }
html.agent #stage > *:not(#views), html.agent #views > *:not(#view-ours):not(.stage-canvas), html.agent #view-ours > *:not(.canvas-holder) { display: none !important; }
html.agent body, html.agent #stage, html.agent #views { margin: 0; padding: 0; overflow: hidden; }
html.agent #stage { position: fixed; inset: 0; } html.agent .view { flex: 1; }
html.agent dialog, html.agent .toast, html.agent .sheet, html.agent .panel { display: none !important; }`;

const tick = () => new Promise((r) => setTimeout(r, 30));

// The canopy over a height: every model whose name says tree, Hist, moss, vine or canopy (roots kept) clipped at z
// for one shot through its own materials (local clipping); returns the undo.
const CANOPY = /tree|hist|canopy|moss|vine|willow|mangrove|palm|fern|hanging|leaves|branch/i, ROOTS = /root|stump|log/i;
function canopyCut(view, c, o) {
  const plane = new THREE.Plane(new THREE.Vector3(0, 0, -1), c.z - o[2]), undo = [];
  view.renderer.localClippingEnabled = true;
  for (const lay of view.objects || []) for (const g of lay.groups?.values() || []) {
    const name = `${g.base?.edid || ''} ${g.base?.model || ''}`;
    if (!(g.kind === 'tree' || CANOPY.test(name)) || ROOTS.test(g.base?.edid || '')) continue;
    for (const m of g.full || []) {
      for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
        if (!mat || undo.some((u) => u[0] === mat)) continue;
        undo.push([mat, mat.clippingPlanes]); mat.clippingPlanes = [plane];
      }
    }
  }
  return () => { for (const [mat, was] of undo) mat.clippingPlanes = was; };
}


// Things the game never draws (editor markers, collision boxes, triggers, occlusion planes): hidden unless the helpers
// are asked for. The same rule as tools/places/look/capture.py helper_kind.
const HELPER = /(^|[\\/])(x?marker|editormarker|idlemarker|furnituremarker|patrolmarker|collision|trigger|occlusion|roommarker|portal)[^\\/]*$|markers?[\\/]/i;
export const isHelper = (g) => !/^crafting/i.test(g.base?.edid || '') && (g.kind === 'marker' || HELPER.test(g.base?.model || '') || /marker$|^xmarker|trigger|collision|occlusion/i.test(g.base?.edid || ''));

// The id pass: every drawn piece in a colour that names it (instance k of a group: id base + k), the land 1, the
// water 2, anything else 3, a helper 4; nothing 0. Cut-out leaves are cut as they are drawn; clipping kept.
const ID0 = 16;
const idVert = `#include <common>
#include <clipping_planes_pars_vertex>
uniform int uBase; varying vec2 vUv; flat varying int vId;
void main() {
  vUv = uv; vId = uBase;
  vec4 mvPosition = vec4(position, 1.0);
  #ifdef USE_INSTANCING
    mvPosition = instanceMatrix * mvPosition; vId = uBase + gl_InstanceID;
  #endif
  mvPosition = modelViewMatrix * mvPosition;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;
const idFrag = `#include <clipping_planes_pars_fragment>
uniform sampler2D map; uniform float alphaTest; varying vec2 vUv; flat varying int vId;
void main() {
  #include <clipping_planes_fragment>
  #ifdef CUT
    if (texture2D(map, vUv).a < alphaTest) discard;
  #endif
  gl_FragColor = vec4(float(vId & 255) / 255.0, float((vId >> 8) & 255) / 255.0, float((vId >> 16) & 255) / 255.0, 1.0);
}`;
const idMats = new WeakMap();
function idMaterial(mesh, src, id) {
  let m = idMats.get(mesh);
  const cut = !!(src?.map && src.alphaTest > 0);
  if (!m || m.userData.cut !== cut) {
    m = new THREE.ShaderMaterial({ vertexShader: idVert, fragmentShader: idFrag, clipping: true, defines: cut ? { CUT: '' } : {},
      uniforms: { uBase: { value: 0 }, map: { value: null }, alphaTest: { value: 0 } } });
    m.userData.cut = cut; idMats.set(mesh, m);
  }
  m.uniforms.uBase.value = id; m.uniforms.map.value = src?.map || null; m.uniforms.alphaTest.value = src?.alphaTest || 0;
  m.side = src?.side ?? THREE.FrontSide; m.clippingPlanes = src?.clippingPlanes || null;
  return m;
}
function readIds(r, sc, c, w, h) {
  const rt = new THREE.WebGLRenderTarget(w, h), buf = new Uint8Array(w * h * 4);
  const bg = sc.background, fog = sc.fog; sc.background = new THREE.Color(0, 0, 0); sc.fog = null;
  r.setRenderTarget(rt); r.setViewport(0, 0, w, h); r.clear(); r.render(sc, c); r.readRenderTargetPixels(rt, 0, 0, w, h, buf); r.setRenderTarget(null);
  sc.background = bg; sc.fog = fog; rt.dispose();
  return buf;
}
const b64 = (u8) => { let s = ''; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); };
function idPass(view, studio, c, w, h, subject, refW) {
  const sc = view.scene, r = view.renderer, table = [], swap = [];
  const land = studio.ours.terrainMesh?.group, water = studio.ours.terrainMesh?.water;
  const groupIds = new Map();
  for (const lay of view.objects || []) for (const g of lay.groups?.values() || []) {
    const n = g.full?.[0]?.visible ? g.full[0].count : 0;
    if (!n) continue;
    groupIds.set(g, table.length + ID0);
    for (let k = 0; k < n; k++) {
      const ref = g.refs[g.drawnIdx[k]];
      table.push([ref.id, g.kind, g.base?.model || '', g.fullParts?.placeholder ? 1 : 0, isHelper(g) ? 1 : 0]);
    }
  }
  const under = (o, root) => { for (let q = o; q; q = q.parent) if (q === root) return true; return false; };
  sc.traverse((o) => {
    if (!o.isMesh || !o.visible) return;
    const g = o.userData.group;
    let id = 3;
    if (g && groupIds.has(g) && g.full?.includes(o)) id = groupIds.get(g);
    else if (o.userData.prims || o.userData.lights) id = 4;
    else if (water && under(o, water)) id = 2;
    else if (land && under(o, land)) id = 1;
    else if (g) { swap.push([o, o.material, null]); o.visible = false; return; }   // a stand-in box: not a piece drawn
    swap.push([o, o.material]); o.material = idMaterial(o, Array.isArray(o.material) ? o.material[0] : o.material, id);
  });
  // the ids are drawn on a pass at most 768 wide whatever the image's size (a large image's pixels each take the id
  // of the pass pixel they lie in): software drawing costs by the pixel, and one view scores the same at any size
  const rw = Math.min(w, refW || 768), rh = Math.round(rw * h / w);
  const ids = readIds(r, sc, c, rw, rh);
  // the subject alone, from a camera three times as wide (its whole projection, inside the frame or not)
  let wide = null;
  if (subject?.length) {
    const want = new Set(subject), tmp = new THREE.Scene(), made = [];
    for (const lay of view.objects || []) for (const g of lay.groups?.values() || []) {
      if (!g.fullParts || !g.refs.some((x) => want.has(x.id))) continue;
      const mats = g.matrices.filter((_, i) => want.has(g.refs[i].id));
      for (const [pi, p] of g.fullParts.entries()) {
        const m = new THREE.InstancedMesh(p.geometry, undefined, mats.length);
        m.material = new THREE.ShaderMaterial({ vertexShader: idVert, fragmentShader: idFrag, clipping: true,
          defines: p.material.map && p.material.alphaTest > 0 ? { CUT: '' } : {}, side: p.material.side,
          uniforms: { uBase: { value: 5 }, map: { value: p.material.map || null }, alphaTest: { value: p.material.alphaTest || 0 } } });
        m.material.clippingPlanes = (g.full?.[pi]?.material || p.material).clippingPlanes || null;
        mats.forEach((mm, i) => m.setMatrixAt(i, mm)); m.frustumCulled = false; tmp.add(m); made.push(m);
      }
    }
    let wc;
    if (c.isOrthographicCamera) { wc = c.clone(); for (const k of ['left', 'right', 'top', 'bottom']) wc[k] *= 3; }
    else { wc = c.clone(); wc.fov = 2 * THREE.MathUtils.radToDeg(Math.atan(3 * Math.tan(THREE.MathUtils.degToRad(c.fov) / 2))); }
    wc.updateProjectionMatrix();
    const ww = Math.round(rw / 2), wh = Math.round(rh / 2), buf = readIds(r, tmp, wc, ww, wh);
    let total = 0, centre = 0;
    for (let y = 0; y < wh; y++) for (let x = 0; x < ww; x++) {
      if (buf[(y * ww + x) * 4] !== 5) continue;
      total++; if (x >= ww / 3 && x < ww * 2 / 3 && y >= wh / 3 && y < wh * 2 / 3) centre++;
    }
    // counted at a quarter of the pixels over nine times the area: scaled to the frame's own pixels
    const k = (9 * rw * rh) / (ww * wh);
    // the subject alone in this very frame at the pass's own resolution: what is seen is counted against it pixel
    // for pixel (thin branches across it count as they cover it); the wide pass only adds the part outside the frame
    const ab = readIds(r, tmp, c, rw, rh);
    let alone = 0;
    for (let i = 0; i < rw * rh; i++) if (ab[i * 4] === 5) alone++;
    wide = { total: total * k, in_frame: centre * k, alone };
    for (const m of made) { m.material.dispose(); m.dispose(); }
  }
  for (const [o, mat, hid] of swap) { o.material = mat; if (hid === null) o.visible = true; }
  return { ids: b64(ids), ref: [rw, rh], table, id0: ID0, wide };
}

// What the place layer holds and what this frame drew: refs sent to the scene, refs whose model arrived, refs drawn as
// a stand-in (a model that would not load, listed with why), refs never drawn by rule (effects, no model), helpers
// hidden, and the instances drawn in the frame by kind. Returned with every shot: nothing that exists goes unreported.
function census(layer) {
  const c = { sent: 0, loaded: 0, stand_in: 0, waiting: 0, empty: 0, effects: 0, no_model: 0, lights: 0, helpers_hidden: 0, drawn: {}, failed: [] };
  for (const g of layer?.groups?.values() || []) {
    const n = g.refs.length; c.sent += n;
    if (g.fx) { c.effects += n; continue; }
    if (g.unseen) { c.no_model += n; continue; }
    if (g.bulb || g.prim) { c.lights += n; continue; }
    if (g.empty) { c.empty += n; continue; }   // a model with nothing drawable in it (a furniture marker)
    if (!g.fullParts) c.waiting += n;
    else if (g.fullParts.placeholder) { c.stand_in += n; c.failed.push({ model: g.base?.model || '', refs: n, why: g.fullParts.why || 'the converter could not read it' }); }
    else c.loaded += n;
    if (isHelper(g)) { if (!g.full?.[0]?.visible) c.helpers_hidden += n; }
    const k = g.full?.[0]?.visible ? g.full[0].count : 0;
    if (k) c.drawn[g.kind || 'other'] = (c.drawn[g.kind || 'other'] || 0) + k;
  }
  return c;
}

export function install(studio) {
  const st = document.createElement('style'); st.textContent = css; document.head.append(st);
  const v = () => studio.ours.view;
  const agent = {
    async ready(timeoutMs = 600000) {
      const t0 = performance.now();
      while (!studio.ready) { if (performance.now() - t0 > timeoutMs) throw new Error('the place did not load'); await new Promise((r) => setTimeout(r, 200)); }
      for (const d of document.querySelectorAll('dialog[open]')) d.close();
      return { place: studio.place.place_id, origin: studio.ours.origin, ops: studio.log.cursor, ms: Math.round(performance.now() - t0) };
    },
    // Edits: the same ops a save holds, pushed through the studio's own log (one stroke per call); undo takes the last stroke.
    push(ops) { const out = studio.log.push(ops.map((o) => ({ ...o }))); return out.map((o) => o.n); },
    undo() { return studio.log.undo().length; },
    reset() { studio.log.goto(0); studio.log.ops.length = 0; studio.log.cursor = 0; return true; },
    // Which space the view shows: 'exterior' or a room, as the studio enters it (main.js showSpace); a room is lit by
    // its own lighting (the game's, the studio's night mode), read from the cell it is copied from before the first shot.
    async space(sid) {
      if (sid !== 'exterior' && !studio.model.spaces[sid]) throw new Error(`no space ${sid}`);
      if (studio.ours.space !== sid) studio.showSpace(studio.ours, sid);
      const lg = v().lighting;
      if (sid !== 'exterior') {
        const t0 = performance.now(), info = studio.spaceInfo?.[sid];
        const k = info?.copy_of && !info.light ? info.copy_of : null;
        studio.roomInfo(studio.ours, sid);
        while (k && studio._rooms?.has(k) && studio._rooms.get(k) === null && performance.now() - t0 < 8000) await tick();
        lg?.invalidate(); lg?.setMode('night');
      } else lg?.setMode('day');
      const refs = [...(studio.model.spaces[sid]?.refs.values() || [])];
      return { space: sid, floorZ: v().floorZ ?? null, refs: refs.filter((r) => !r.removed).length, mode: lg?.mode };
    },
    // Openings onto the void: from each point, six square looks (a cube) at size px with the background a colour no
    // model has; every look where that colour shows is a way out of the room's shell. Returns per point the faces
    // that see out: {face, frac, dir (mean direction of the escaping pixels, game axes)}.
    async voids(points, size = 48) {
      const view = v(), r = view.renderer, o = studio.ours.origin, sc = view.scene;
      const bg = sc.background, fog = sc.fog;
      sc.background = new THREE.Color(1, 0, 1);
      const fn = fog ? [fog.near, fog.far] : null; if (fog) { fog.near = 1e9; fog.far = 2e9; }
      const rt = new THREE.WebGLRenderTarget(size, size), buf = new Uint8Array(size * size * 4);
      const faces = { e: [1, 0, 0], w: [-1, 0, 0], n: [0, 1, 0], s: [0, -1, 0], up: [0, 0, 1], down: [0, 0, -1] };
      const out = [];
      r.setScissorTest(false);
      for (const p of points) {
        const pos = new THREE.Vector3(p[0] - o[0], p[1] - o[1], p[2] - o[2]), seen = [];
        for (const [name, d] of Object.entries(faces)) {
          const c = new THREE.PerspectiveCamera(90, 1, 4, 60000);
          c.up.set(...(Math.abs(d[2]) > 0.5 ? [0, 1, 0] : [0, 0, 1])); c.position.copy(pos);
          c.lookAt(pos.clone().add(new THREE.Vector3(...d))); c.updateMatrixWorld(); c.updateProjectionMatrix();
          for (const lay of view.objects || []) lay.cull(c);
          for (let i = 0; i < 200 && pendingModels(); i++) { drainAll(r); await tick(); }
          r.setRenderTarget(rt); r.setViewport(0, 0, size, size); r.render(sc, c); r.readRenderTargetPixels(rt, 0, 0, size, size, buf); r.setRenderTarget(null);
          let n = 0; const m = new THREE.Vector3();
          for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
            const i = (y * size + x) * 4;
            if (buf[i] > 240 && buf[i + 1] < 16 && buf[i + 2] > 240) {
              n++; m.add(new THREE.Vector3((x + 0.5) / size * 2 - 1, (y + 0.5) / size * 2 - 1, 0.5).unproject(c).sub(c.position).normalize());
            }
          }
          if (n) seen.push({ face: name, frac: n / (size * size), dir: m.normalize().toArray().map((x) => Math.round(x * 100) / 100) });
        }
        out.push({ at: p, out: seen });
      }
      rt.dispose(); sc.background = bg; if (fog) [fog.near, fog.far] = fn; r.setScissorTest(true);
      return out;
    },
    applied() { return studio.log.applied ? studio.log.applied() : studio.log.ops.slice(0, studio.log.cursor); },
    // One shot. cam: {w, h, pos, target, up?, fov?, ortho?: {halfW, halfH}, near?, far?, clip?: [[nx,ny,nz,d], ...]
    // (keeps n.p + d >= 0, game coordinates), grass?: bool}. Returns {png (data URL), ms, waits}.
    async shot(cam) {
      const t0 = performance.now(), view = v(), o = studio.ours.origin, r = view.renderer;
      const L = (p) => new THREE.Vector3(p[0] - o[0], p[1] - o[1], p[2] - o[2]);
      const w = cam.w || 768, h = cam.h || 576;
      const c = cam.ortho
        ? new THREE.OrthographicCamera(-cam.ortho.halfW, cam.ortho.halfW, cam.ortho.halfH, -cam.ortho.halfH, cam.near ?? 1, cam.far ?? 200000)
        : new THREE.PerspectiveCamera(cam.fov || 50, w / h, cam.near ?? 10, cam.far ?? 200000);
      c.up.set(...(cam.up || [0, 0, 1])); c.position.copy(L(cam.pos)); c.lookAt(L(cam.target)); c.updateMatrixWorld(); c.updateProjectionMatrix();
      c.userData.focus = L(cam.target);
      if (studio.ours.grass) studio.ours.grass.root.visible = !!cam.grass;
      // the editor's helpers (light bulbs, collision boxes) only when asked: the agent judges what the player sees
      for (const l of [studio.ours.place, studio.ours.world]) l?.setShowLights(!!cam.helpers);
      view.overlay.visible = !!cam.helpers;
      const tgt = L(cam.target);
      studio.ours.terrainMesh?.update(tgt);
      // --no-canopy: tree crowns and hanging moss cut away over a height (game z), their trunks kept
      r.clippingPlanes = (cam.clip || []).map(([nx, ny, nz, d]) => new THREE.Plane(new THREE.Vector3(nx, ny, nz), d + nx * o[0] + ny * o[1] + nz * o[2]));
      // every model the camera can see, loaded and switched on; the land's near cells baked
      let waits = 0;
      for (;;) {
        for (const lay of view.objects || []) lay.cull(c);
        drainAll(r);
        const tm = studio.ours.terrainMesh;
        if (!pendingModels() && !(tm && (tm.pumping || tm.queue.length))) break;
        if (performance.now() - t0 > 120000) break;
        waits++; await tick();
      }
      for (const lay of view.objects || []) lay.cull(c);
      // the canopy cut once every model the shot draws has arrived (one cut before would miss those loaded here)
      const cut = cam.canopy ? canopyCut(view, cam.canopy, o) : null;
      // what the game never draws stays out of the picture unless the helpers are asked for
      const hidden = [];
      if (!cam.helpers) for (const lay of view.objects || []) for (const g of lay.groups?.values() || []) {
        if (!isHelper(g)) continue;
        for (const m of g.full || []) if (m.visible) { m.visible = false; hidden.push(m); }
      }
      const counts = census(studio.ours.place);
      const tw = performance.now();
      r.setPixelRatio(1); r.setSize(w, h, false); r.setScissorTest(false); r.setViewport(0, 0, w, h);
      view.lighting?.beforeDraw();
      // --lit: a neutral fill over the place's own light, indoors or out, for judging shape (the viewer's light is not the game's)
      const hemi = view.lighting?.hemi, sun = view.lighting?.sun;
      const keep = cam.fill && hemi ? [hemi.color.clone(), hemi.groundColor.clone(), hemi.intensity] : null;
      const keepSun = cam.fill && sun ? [sun.color.clone(), sun.intensity] : null;
      if (keep) { hemi.color.setRGB(0.55, 0.55, 0.55); hemi.groundColor.setRGB(0.35, 0.35, 0.35); hemi.intensity = Math.PI; }
      if (keepSun) { sun.color.setRGB(1, 1, 1); sun.intensity = 1.0; }
      // drawn into a target without the canvas's multisampling (in software it costs most of a large shot), then read back
      const rt = new THREE.WebGLRenderTarget(w, h, { samples: 0, colorSpace: THREE.SRGBColorSpace });
      r.setRenderTarget(rt); r.clear(); r.render(view.scene, c);
      const pix = new Uint8Array(w * h * 4); r.readRenderTargetPixels(rt, 0, 0, w, h, pix); r.setRenderTarget(null); rt.dispose();
      if (keep) [hemi.color, hemi.groundColor, hemi.intensity] = keep;
      if (keepSun) [sun.color, sun.intensity] = keepSun;
      r.getContext().finish();
      const tr = performance.now();
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      const im = new ImageData(w, h);
      for (let y = 0; y < h; y++) im.data.set(pix.subarray((h - 1 - y) * w * 4, (h - y) * w * 4), y * w * 4);
      cv.getContext('2d').putImageData(im, 0, 0);
      const png = cv.toDataURL('image/png');
      const tid = performance.now();
      const idp = cam.ids ? idPass(view, studio, c, w, h, cam.subject, cam.ref_w) : null;
      const tdone = performance.now();
      cut?.();
      for (const m of hidden) m.visible = true;
      r.clippingPlanes = []; r.setScissorTest(true);
      const info = { calls: r.info.render.calls, triangles: r.info.render.triangles, render_ms: Math.round(tr - tw), png_ms: Math.round(tid - tr), ids_ms: Math.round(tdone - tid) };
      return { png, ms: Math.round(performance.now() - t0), draw_ms: Math.round(performance.now() - tw), waits, census: counts, ...info, ...(idp || {}) };
    },
    // Several shots in one call (a survey's tiles): the same scene, warm, one page round trip.
    async shots(cams) { const out = []; for (const c of cams) out.push(await this.shot(c)); return out; },
  };
  window.agent = agent;
}
